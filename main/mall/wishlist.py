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
        queryset = self.get_queryset()
        context = {'request': request}
        
        # Add store context for pricing if mall parameter is provided
        store_id = request.query_params.get('mall')
        if store_id:
            try:
                store = Store.objects.get(id=store_id)
                context['store'] = store
            except Store.DoesNotExist:
                pass
        
        # Use pagination like ProductViewSet
        paginator = OptimizedPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        
        from .optimized_serializers import OptimizedProductSerializer
        serializer = OptimizedProductSerializer(page, many=True, context=context)
        
        return paginator.get_paginated_response(serializer.data)