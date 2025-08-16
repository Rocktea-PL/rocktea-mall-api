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
    
    def list(self, request):
        saved_products = SavedProduct.objects.filter(user=request.user)\
            .select_related('product', 'store')\
            .order_by('-created_at')
        
        paginator = OptimizedPageNumberPagination()
        page = paginator.paginate_queryset(saved_products, request)
        
        # Get products and serialize them like ProductViewSet
        products = [sp.product for sp in page]
        context = {'request': request}
        
        from .optimized_serializers import OptimizedProductSerializer
        serializer = OptimizedProductSerializer(products, many=True, context=context)
        
        return paginator.get_paginated_response(serializer.data)