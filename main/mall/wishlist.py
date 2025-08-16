from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from .models import SavedProduct, Product, Store
from .serializers import ProductSerializer
from .pagination import OptimizedPageNumberPagination

class WishlistViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def save(self, request):
        product_id = request.data.get('product_id')
        store_id = request.data.get('store_id')
        
        if not product_id or not store_id:
            return Response({'error': 'product_id and store_id required'}, status=400)
        
        try:
            saved_product, created = SavedProduct.objects.get_or_create(
                user=request.user,
                product_id=product_id,
                store_id=store_id
            )
            return Response({'saved': created})
        except IntegrityError:
            return Response({'saved': False})
    
    @action(detail=False, methods=['delete'])
    def unsave(self, request):
        product_id = request.data.get('product_id')
        store_id = request.data.get('store_id')
        
        if not product_id or not store_id:
            return Response({'error': 'product_id and store_id required'}, status=400)
        
        deleted = SavedProduct.objects.filter(
            user=request.user,
            product_id=product_id,
            store_id=store_id
        ).delete()[0]
        
        return Response({'unsaved': bool(deleted)})
    
    def get_queryset(self):
        # Always filter by authenticated user only
        saved_product_ids = SavedProduct.objects.filter(user=self.request.user)\
            .values_list('product_id', flat=True)
        
        if not saved_product_ids:
            return Product.objects.none()
        
        # Return user's saved products with pricing context
        return Product.objects.filter(
            id__in=saved_product_ids,
            is_available=True,
            upload_status='Approved'
        ).select_related('category', 'subcategory', 'brand', 'producttype')\
         .prefetch_related('images').distinct().order_by('-created_at')
    
    def list(self, request):
        try:
            # Get summary data for saved products
            total_saved_products = SavedProduct.objects.filter(user=request.user).count()
            total_available_saved = SavedProduct.objects.filter(
                user=request.user,
                product__is_available=True,
                product__upload_status='Approved'
            ).count()
            
            summary = {
                "total_saved_products": total_saved_products,
                "total_available_saved": total_available_saved,
            }
            
            # Get saved products with store context
            saved_products = SavedProduct.objects.filter(user=request.user)\
                .select_related('product', 'store')\
                .order_by('-created_at')
            
            # Apply pagination
            paginator = OptimizedPageNumberPagination()
            paginated_data = paginator.paginate_queryset(saved_products, request)
            
            # Get store context for pricing if mall parameter is provided
            store_context = None
            store_id = request.query_params.get('mall')
            if store_id:
                try:
                    store_context = Store.objects.get(id=store_id)
                except Store.DoesNotExist:
                    pass
            
            # Serialize products with full details like ProductViewSet
            from .optimized_serializers import OptimizedProductSerializer
            context = {'request': request}
            if store_context:
                context['store'] = store_context
                
            serializer = OptimizedProductSerializer(
                [sp.product for sp in paginated_data],
                many=True,
                context=context
            )
            
            # Return paginated response with summary like my_products_list
            return paginator.get_paginated_response({
                "summary": summary,
                "products": serializer.data
            })
            
        except Exception as e:
            return Response(
                {"error": "An error occurred while retrieving saved products."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )