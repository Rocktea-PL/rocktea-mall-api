from django.http import Http404
from django.db import transaction
from django.db.models import Sum
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from mall.models import Product, ProductImage
from .serializers import (
    AdminProductSerializer, 
    AdminProductCreateSerializer,
    AdminProductDetailSerializer,
    AdminProductListSerializer,
    BulkStockUpdateSerializer,
    ProductApprovalSerializer
)
from order.models import OrderItems
import logging
from order.pagination import CustomPagination
from .filters import ProductFilter
from django_filters.rest_framework import DjangoFilterBackend

logger = logging.getLogger(__name__)

class AdminProductViewSet(viewsets.ModelViewSet):
    """Admin Product Management ViewSet"""
    queryset = Product.objects.select_related(
        'category', 'subcategory', 'producttype', 'brand'
    ).prefetch_related('images', 'product_variants')
    permission_classes = [IsAuthenticated, IsAdminUser]
    # Allow both JSON and multipart requests
    parser_classes = [JSONParser, MultiPartParser, FormParser]
    pagination_class = CustomPagination
    ordering = ['-created_at']

    # Add filter backends and custom filter class
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter
    ]
    filterset_class = ProductFilter
    search_fields = [
        'name', 
        'sku',
        'category__name', 
        'brand__name',
        'description',
        'product_variants__wholesale_price',
        'quantity'
    ]
    ordering_fields = ['created_at', 'quantity', 'name']
    lookup_field = 'identifier'

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProductCreateSerializer
        elif self.action == 'list':
            return AdminProductListSerializer
        elif self.action == 'retrieve':
            return AdminProductDetailSerializer
        return AdminProductSerializer

    def get_object(self):
        """Allow lookup by ID or SKU"""
        identifier = self.kwargs.get('identifier')
        
        try:
            # Try to find by UUID (primary key)
            return self.get_queryset().get(id=identifier)
        except (Product.DoesNotExist, ValueError):
            try:
                # Try to find by SKU
                return self.get_queryset().get(sku=identifier)
            except Product.DoesNotExist:
                raise Http404("No product found with the provided identifier")
            
    def filter_queryset(self, queryset):
        """Handle custom search for stock status"""
        # First handle the search parameter
        search_term = self.request.query_params.get('search', '').strip().lower()
        
        if search_term:
            # Map search terms to stock status values
            stock_status_map = {
                'out': 'out_of_stock',
                'out_of_stock': 'out_of_stock',
                'out of stock': 'out_of_stock',
                'oos': 'out_of_stock',
                '0': 'out_of_stock',
                
                'low': 'low_stock',
                'low_stock': 'low_stock',
                'low stock': 'low_stock',
                'lstock': 'low_stock',
                
                'in': 'in_stock',
                'in_stock': 'in_stock',
                'in stock': 'in_stock',
                'available': 'in_stock',
                'instock': 'in_stock',
                'stock': 'in_stock'
            }
            
            # Check if search term matches any stock status keyword
            status_value = stock_status_map.get(search_term)
            
            if status_value == 'out_of_stock':
                return queryset.filter(quantity=0)
            elif status_value == 'low_stock':
                return queryset.filter(quantity__lte=10, quantity__gt=0)
            elif status_value == 'in_stock':
                return queryset.filter(quantity__gt=10)
        
        # Apply standard filtering
        return super().filter_queryset(queryset)
            
    def retrieve(self, request, *args, **kwargs):
        """Custom retrieve with proper error handling"""
        try:
            return super().retrieve(request, *args, **kwargs)
        except Http404:
            return Response(
                {
                    "error": "Product not found",
                    "message": "No product exists with the provided identifier. "
                               "Please check the product ID or SKU."
                },
                status=status.HTTP_404_NOT_FOUND
            )

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Enhanced create method with better error handling"""
        try:
            # Log the incoming data for debugging
            logger.info(f"Creating product with data: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                logger.error(f"Product creation validation errors: {serializer.errors}")
                return Response(
                    {
                        'error': 'Validation failed',
                        'details': serializer.errors,
                        'message': 'Please check the provided data and try again.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Save the product
            product = serializer.save()
            
            # Return success response with created product data
            response_serializer = AdminProductDetailSerializer(product)
            logger.info(f"Successfully created product: {product.name} (ID: {product.id})")
            
            return Response(
                {
                    'message': 'Product created successfully',
                    'product': response_serializer.data
                },
                status=status.HTTP_201_CREATED
            )
            
        except Exception as e:
            logger.error(f"Unexpected error creating product: {str(e)}")
            return Response(
                {
                    'error': 'Product creation failed',
                    'message': str(e)
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
        """Handle full update - signals will manage Cloudinary deletion"""
        # Handle JSON requests by changing parser behavior
        if not request.FILES and not request.data.get('images'):
            request.parsers = [JSONParser()]
        # return super().update(request, *args, **kwargs)
        #  Get partial parameter
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        
        # Use the update serializer
        serializer = AdminProductSerializer(
            instance, 
            data=request.data, 
            partial=partial,
            context=self.get_serializer_context()
        )
        
        try:
            serializer.is_valid(raise_exception=True)
            # self.perform_update(serializer)

            updated_instance = serializer.save()

            detailed_serializer = AdminProductDetailSerializer(
                updated_instance,  # Use the updated instance
                context=self.get_serializer_context()
            )
            return Response(detailed_serializer.data)
        except Exception as e:
            logger.error(f"Update error: {str(e)}")
            return Response(
                {"error": "Update failed", "details": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Return detailed representation
        # detailed_serializer = AdminProductDetailSerializer(
        #     instance, 
        #     context=self.get_serializer_context()
        # )
        # return Response(detailed_serializer.data)
    
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
        """Handle partial update - signals will manage Cloudinary deletion"""
        # Handle JSON requests by changing parser behavior
        # if not request.FILES and not request.data.get('images'):
        #     request.parsers = [JSONParser()]
        # return super().partial_update(request, *args, **kwargs)
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @transaction.atomic
    def perform_destroy(self, instance):
        """Delete product and associated images"""
        try:
            # Delete product variants first
            variants = instance.product_variants.all()
            for variant in variants:
                # Remove the product from the variant's many-to-many relationship
                variant.product.remove(instance)
                # If the variant has no other products, delete it
                if not variant.product.exists():
                    variant.delete()

            # Delete product images
            for image in instance.images.all():
                try:
                    # Delete from Cloudinary
                    if image.images:
                        image.images.delete()
                except Exception as e:
                    logger.error(f"Failed to delete image from Cloudinary: {e}")
                
                # Delete the ProductImage instance
                try:
                    image.delete()
                except Exception as e:
                    logger.error(f"Failed to delete ProductImage instance: {e}")
            
            # Clear the many-to-many relationship
            instance.images.clear()
            
            # Finally delete the product
            instance.delete()
            
        except Exception as e:
            logger.error(f"Error deleting product: {e}")
            raise

    @action(detail=False, methods=['get'])
    def dashboard_summary(self, request):
        """Get admin dashboard summary"""
        try:
            # Basic product stats
            total_products = Product.objects.count()
            active_products = Product.objects.filter(is_available=True).count()
            pending_approval = Product.objects.filter(upload_status='Pending').count()
            
            # Stock status counts
            out_of_stock = Product.objects.filter(quantity=0).count()
            low_stock = Product.objects.filter(quantity__lte=10, quantity__gt=0).count()
            in_stock = Product.objects.filter(quantity__gt=10).count()
            
            # Calculate total units sold across all products
            total_units_sold = OrderItems.objects.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            # Top selling products
            top_products = Product.objects.annotate(
                total_sold=Sum('orderitems__quantity')
            ).order_by('-total_sold')[:5]
            
            top_products_data = []
            for product in top_products:
                units_sold = product.total_sold or 0
                stock_status = self._get_stock_status(product.quantity)
                
                top_products_data.append({
                    'id': product.id,
                    'name': product.name,
                    'sku': product.sku,
                    'quantity': product.quantity,
                    'units_sold': units_sold,
                    'stock_status': stock_status,
                    'wholesale_price': self._get_wholesale_price(product)
                })
            
            summary = {
                'total_products': total_products,
                'active_products': active_products,
                'pending_approval': pending_approval,
                'stock_status': {
                    'in_stock': in_stock,
                    'low_stock': low_stock,
                    'out_of_stock': out_of_stock
                },
                'total_units_sold': total_units_sold,
                'top_selling_products': top_products_data
            }
            
            return Response(summary)
            
        except Exception as e:
            logger.error(f"Error generating dashboard summary: {e}")
            return Response(
                {'error': 'Failed to generate dashboard summary'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @action(detail=True, methods=['get'])
    def sales_analytics(self, request, pk=None):
        """Get detailed sales analytics for a specific product"""
        try:
            product = self.get_object()
            
            # Get all order items for this product
            order_items = OrderItems.objects.filter(product=product).select_related(
                'userorder', 'userorder__store', 'userorder__buyer'
            )
            
            # Calculate total units sold
            total_units_sold = order_items.aggregate(
                total=Sum('quantity')
            )['total'] or 0
            
            # Calculate stock status
            stock_status = self._get_stock_status(product.quantity)
            
            # Get sales by store
            sales_by_store = {}
            total_revenue = 0
            
            for item in order_items:
                store_name = item.userorder.store.name
                if store_name not in sales_by_store:
                    sales_by_store[store_name] = {'quantity': 0, 'orders': 0}
                
                sales_by_store[store_name]['quantity'] += item.quantity
                sales_by_store[store_name]['orders'] += 1
                
                # Calculate revenue based on wholesale price
                wholesale_price = self._get_wholesale_price(product)
                if wholesale_price:
                    total_revenue += wholesale_price * item.quantity
            
            # Recent orders
            recent_orders = order_items.order_by('-userorder__created_at')[:10]
            recent_orders_data = []
            
            for item in recent_orders:
                recent_orders_data.append({
                    'order_id': item.userorder.id,
                    'store': item.userorder.store.name,
                    'quantity': item.quantity,
                    'order_date': item.userorder.created_at.strftime('%Y-%m-%d %H:%M:%S'),
                    'buyer': f"{item.userorder.buyer.first_name} {item.userorder.buyer.last_name}"
                })
            
            analytics = {
                'product_id': product.id,
                'product_name': product.name,
                'sku': product.sku,
                'current_quantity': product.quantity,
                'total_units_sold': total_units_sold,
                'stock_status': stock_status,
                'wholesale_price': wholesale_price,
                'total_revenue': '{:,.2f}'.format(total_revenue),
                'sales_by_store': sales_by_store,
                'recent_orders': recent_orders_data
            }
            
            return Response(analytics)
            
        except Exception as e:
            logger.error(f"Error generating sales analytics: {e}")
            return Response(
                {'error': 'Failed to generate sales analytics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _get_stock_status(self, current_quantity):
        """Determine stock status based on quantity"""
        if current_quantity == 0:
            return 'out_of_stock'
        elif current_quantity <= 10:
            return 'low_stock'
        else:
            return 'in_stock'

    def _get_wholesale_price(self, product):
        """Get the wholesale price for a product"""
        try:
            variant = product.product_variants.first()
            if variant:
                return float(variant.wholesale_price)
        except Exception:
            pass
        return None


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def bulk_update_stock(request):
    """Bulk update product stock quantities"""
    try:
        serializer = BulkStockUpdateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        updates = serializer.validated_data['updates']
        updated_count = 0
        
        with transaction.atomic():
            for update in updates:
                product_id = int(update['product_id'])
                new_quantity = int(update['quantity'])
                
                updated = Product.objects.filter(id=product_id).update(
                    quantity=new_quantity
                )
                if updated:
                    updated_count += 1
        
        return Response({
            'message': f'Successfully updated {updated_count} products',
            'updated_count': updated_count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk stock update: {e}")
        return Response(
            {'error': 'Failed to update stock'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def approve_products(request):
    """Bulk approve or reject products"""
    try:
        serializer = ProductApprovalSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {'error': 'Invalid data', 'details': serializer.errors}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_ids = serializer.validated_data['product_ids']
        action = serializer.validated_data.get('action', 'approve')
        
        # Determine the new status based on action
        new_status = 'Approved' if action == 'approve' else 'Rejected'
        
        with transaction.atomic():
            updated_count = Product.objects.filter(id__in=product_ids).update(
                upload_status=new_status
            )
        
        action_past_tense = 'approved' if action == 'approve' else 'rejected'
        return Response({
            'message': f'Successfully {action_past_tense} {updated_count} products',
            'updated_count': updated_count,
            'action': action
        })
        
    except Exception as e:
        logger.error(f"Error in product approval: {e}")
        return Response(
            {'error': f'Failed to {action} products'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsAdminUser])
def bulk_delete_products(request):
    """Bulk delete products"""
    try:
        product_ids = request.data.get('product_ids', [])
        if not product_ids:
            return Response(
                {'error': 'No product IDs provided'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate product IDs
        valid_ids = []
        for product_id in product_ids:
            try:
                valid_ids.append(int(product_id))
            except (ValueError, TypeError):
                return Response(
                    {'error': f'Invalid product ID: {product_id}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        deleted_count = 0
        
        with transaction.atomic():
            products = Product.objects.filter(id__in=valid_ids)
            
            for product in products:
                try:
                    # Delete associated images from Cloudinary
                    for image in product.images.all():
                        try:
                            if image.images:
                                image.images.delete()
                        except Exception as e:
                            logger.error(f"Failed to delete image from Cloudinary: {e}")
                        image.delete()
                    
                    # Clear relationships
                    product.images.clear()
                    
                    # Delete product variants relationships
                    for variant in product.product_variants.all():
                        variant.product.remove(product)
                        if not variant.product.exists():
                            variant.delete()
                    
                    # Delete the product
                    product.delete()
                    deleted_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to delete product {product.id}: {e}")
        
        return Response({
            'message': f'Successfully deleted {deleted_count} products',
            'deleted_count': deleted_count
        })
        
    except Exception as e:
        logger.error(f"Error in bulk product deletion: {e}")
        return Response(
            {'error': 'Failed to delete products'}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )