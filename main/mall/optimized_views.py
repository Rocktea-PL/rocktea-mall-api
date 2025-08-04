"""
Optimized views for better performance
Replaces inefficient views with optimized versions
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.db.models import Count, Sum, Prefetch

from .models import Product, Store, StoreProductPricing, MarketPlace, CustomUser
from .serializers import SimpleProductSerializer, MarketPlaceSerializer
from .performance_optimizers import (
    QueryOptimizer, CacheManager, DatabaseOptimizer, 
    PerformanceMonitor, cache_result
)
from .pagination import OptimizedPageNumberPagination
from order.models import StoreOrder
from order.pagination import CustomPagination

class OptimizedProductViewSet(viewsets.ModelViewSet):
    """Optimized product viewset with better query performance"""
    
    pagination_class = OptimizedPageNumberPagination
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        category_id = self.request.query_params.get('category')
        return QueryOptimizer.get_optimized_products(category_id=category_id)
    
    @PerformanceMonitor.monitor_query_time
    @action(detail=False, methods=['get'], url_path='by-shop')
    def my_products_list(self, request):
        """Optimized store products list with caching"""
        store = getattr(request.user, 'owners', None)
        if not store:
            return Response(
                {"error": "You are not associated with a store."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get cached stats first
            stats = DatabaseOptimizer.get_store_dashboard_stats(store.id)
            
            # Get products with optimized query
            store_products = QueryOptimizer.get_store_products_with_pricing(store.id)
            
            # Apply pagination
            paginator = CustomPagination()
            paginated_data = paginator.paginate_queryset(store_products, request)
            
            # Serialize efficiently
            serializer = SimpleProductSerializer(
                [pricing.product for pricing in paginated_data],
                many=True,
                context={'store': store}
            )
            
            return paginator.get_paginated_response({
                "summary": {
                    "total_products_added": stats.get('listed_products', 0),
                    "total_products_available": len([p for p in paginated_data if p.product.is_available]),
                    "total_products_sold": stats.get('total_orders', 0),
                },
                "products": serializer.data
            })
            
        except Exception as e:
            return Response(
                {"error": f"Error retrieving products: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class OptimizedMarketPlaceView(viewsets.ModelViewSet):
    """Optimized marketplace view with better performance"""
    
    serializer_class = MarketPlaceSerializer
    pagination_class = OptimizedPageNumberPagination
    
    @PerformanceMonitor.monitor_query_time
    def get_queryset(self):
        store_id = self.request.query_params.get("mall")
        if not store_id:
            return MarketPlace.objects.none()
        
        # Use optimized query
        return QueryOptimizer.get_marketplace_products(store_id)

class OptimizedDashboardView(viewsets.ViewSet):
    """Optimized dashboard with cached statistics"""
    
    permission_classes = [IsAuthenticated]
    
    @cache_result(timeout=1800)  # Cache for 30 minutes
    @action(detail=False, methods=['get'], url_path='stats')
    def get_dashboard_stats(self, request):
        """Get dashboard statistics with caching"""
        store_id = request.query_params.get("mall")
        if not store_id:
            return Response(
                {"error": "Store ID required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            stats = DatabaseOptimizer.get_store_dashboard_stats(store_id)
            return Response(stats, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error retrieving stats: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], url_path='best-selling')
    def get_best_selling_products(self, request):
        """Get best selling products with optimized query"""
        store_id = request.query_params.get("mall")
        
        # Use optimized query with aggregation
        products = QueryOptimizer.get_optimized_products(
            store_id=store_id
        ).order_by('-sales_count')[:5]
        
        serializer = SimpleProductSerializer(products, many=True)
        return Response(serializer.data)

class OptimizedStoreProductPricingView(viewsets.ViewSet):
    """Optimized store product pricing operations"""
    
    permission_classes = [IsAuthenticated]
    
    @transaction.atomic
    @action(detail=False, methods=['post'], url_path='bulk-create')
    def bulk_create_pricing(self, request):
        """Bulk create product pricing for better performance"""
        store = getattr(request.user, 'owners', None)
        if not store:
            return Response(
                {"error": "You are not associated with a store."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_data = request.data.get('products', [])
        if not product_data:
            return Response(
                {"error": "No product data provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Use bulk create for better performance
            created_objects = DatabaseOptimizer.bulk_create_store_products(
                store.id, product_data
            )
            
            # Invalidate cache
            CacheManager.invalidate_store_cache(store.id)
            
            return Response({
                "message": f"Successfully created {len(created_objects)} product pricings",
                "count": len(created_objects)
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Error creating pricing: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @transaction.atomic
    @action(detail=False, methods=['delete'], url_path='bulk-delete')
    def bulk_delete_pricing(self, request):
        """Bulk delete product pricing"""
        store = getattr(request.user, 'owners', None)
        if not store:
            return Response(
                {"error": "You are not associated with a store."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        product_ids = request.data.get('product_ids', [])
        if not product_ids:
            return Response(
                {"error": "No product IDs provided"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Bulk delete for better performance
            deleted_count = StoreProductPricing.objects.filter(
                store=store,
                product_id__in=product_ids
            ).delete()[0]
            
            # Invalidate cache
            CacheManager.invalidate_store_cache(store.id)
            
            return Response({
                "message": f"Successfully deleted {deleted_count} product pricings",
                "count": deleted_count
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {"error": f"Error deleting pricing: {str(e)}"},
                status=status.HTTP_400_BAD_REQUEST
            )