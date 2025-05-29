from django.db import transaction
from django.db.models import Sum, Q
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.parsers import MultiPartParser, FormParser
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

logger = logging.getLogger(__name__)

class AdminProductViewSet(viewsets.ModelViewSet):
    """Admin Product Management ViewSet"""
    queryset = Product.objects.select_related(
        'category', 'subcategory', 'producttype', 'brand'
    ).prefetch_related('images', 'product_variants')
    permission_classes = [IsAuthenticated, IsAdminUser]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = CustomPagination

    def get_serializer_class(self):
        if self.action == 'create':
            return AdminProductCreateSerializer
        elif self.action == 'list':
            return AdminProductListSerializer
        elif self.action == 'retrieve':
            return AdminProductDetailSerializer
        return AdminProductSerializer

    def get_queryset(self):
        """Filter products based on query parameters"""
        queryset = self.queryset
        
        # Filter by category
        category_id = self.request.query_params.get('category')
        if category_id:
            try:
                queryset = queryset.filter(category_id=int(category_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by brand
        brand_id = self.request.query_params.get('brand')
        if brand_id:
            try:
                queryset = queryset.filter(brand_id=int(brand_id))
            except (ValueError, TypeError):
                pass
        
        # Filter by stock status
        stock_status = self.request.query_params.get('stock_status')
        if stock_status == 'out_of_stock':
            queryset = queryset.filter(quantity=0)
        elif stock_status == 'low_stock':
            queryset = queryset.filter(quantity__lte=10, quantity__gt=0)
        elif stock_status == 'in_stock':
            queryset = queryset.filter(quantity__gt=10)
        
        # Filter by upload status
        upload_status = self.request.query_params.get('upload_status')
        if upload_status:
            queryset = queryset.filter(upload_status=upload_status)
        
        # Search by name or SKU
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | 
                Q(sku__icontains=search) |
                Q(description__icontains=search)
            )

        return queryset.order_by('-created_at')

    @transaction.atomic
    def perform_create(self, serializer):
        """Create product with automatic SKU generation"""
        try:
            product = serializer.save()
            
            # Handle image uploads if provided
            images = self.request.FILES.getlist('images')
            for image in images:
                try:
                    # Create ProductImage with 'images' field
                    product_image = ProductImage.objects.create(images=image)
                    product.images.add(product_image)
                except Exception as e:
                    logger.error(f"Failed to create product image: {e}")
            
            return product
        except Exception as e:
            logger.error(f"Error creating product: {e}")
            raise
    
    @transaction.atomic
    def update(self, request, *args, **kwargs):
      """Handle full update - signals will manage Cloudinary deletion"""
      return super().update(request, *args, **kwargs)
    
    @transaction.atomic
    def partial_update(self, request, *args, **kwargs):
      """Handle partial update - signals will manage Cloudinary deletion"""
      return super().partial_update(request, *args, **kwargs)

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