"""
Performance optimization utilities for RockTea Mall
Centralized query optimizations, caching, and performance monitoring
"""
from django.db import models
from django.core.cache import cache
from django.db.models import Prefetch, Count, Sum, Q
from django.utils import timezone
from typing import Optional, Dict, Any, List
import logging
from functools import wraps
import time

logger = logging.getLogger(__name__)

class QueryOptimizer:
    """Centralized query optimization for common database operations"""
    
    @staticmethod
    def get_optimized_products(category_id: Optional[str] = None, store_id: Optional[str] = None):
        """Get optimized product queryset with all necessary relations"""
        from .models import Product, Category
        
        queryset = Product.objects.select_related(
            'category', 'subcategory', 'producttype', 'brand'
        ).prefetch_related(
            'images',
            Prefetch('store', queryset=models.QuerySet.from_queryset(
                lambda qs: qs.select_related('owner')
            )),
            'product_variants'
        )
        
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        if store_id:
            queryset = queryset.filter(store__id=store_id)
            
        return queryset.filter(is_available=True, upload_status='Approved')
    
    @staticmethod
    def get_optimized_stores():
        """Get optimized store queryset"""
        from .models import Store
        
        return Store.objects.select_related('owner', 'category').prefetch_related(
            'pricings__product__images'
        ).filter(completed=True)
    
    @staticmethod
    def get_store_products_with_pricing(store_id: str):
        """Get store products with pricing in single query"""
        from .models import StoreProductPricing
        
        return StoreProductPricing.objects.filter(
            store_id=store_id
        ).select_related(
            'product__category',
            'product__subcategory', 
            'product__brand',
            'store'
        ).prefetch_related(
            'product__images',
            'product__product_variants'
        )
    
    @staticmethod
    def get_marketplace_products(store_id: str):
        """Optimized marketplace query"""
        from .models import MarketPlace
        
        return MarketPlace.objects.filter(
            store_id=store_id, 
            list_product=True
        ).select_related(
            'product__category',
            'product__subcategory',
            'product__producttype',
            'product__brand',
            'store'
        ).prefetch_related(
            'product__images',
            'product__product_variants'
        ).order_by('-id')

class CacheManager:
    """Centralized caching for frequently accessed data"""
    
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def get_categories():
        """Get cached categories"""
        return cache.get('categories_list')
    
    @staticmethod
    def set_categories(data):
        """Cache categories data"""
        cache.set('categories_list', data, CacheManager.CACHE_TIMEOUT)
    
    @staticmethod
    def get_store_stats(store_id: str):
        """Get cached store statistics"""
        return cache.get(f'store_stats_{store_id}')
    
    @staticmethod
    def set_store_stats(store_id: str, data: Dict):
        """Cache store statistics"""
        cache.set(f'store_stats_{store_id}', data, CacheManager.CACHE_TIMEOUT // 2)
    
    @staticmethod
    def invalidate_store_cache(store_id: str):
        """Invalidate store-related cache"""
        cache.delete(f'store_stats_{store_id}')
        cache.delete(f'store_products_{store_id}')
    
    @staticmethod
    def get_product_details(product_id: str):
        """Get cached product details"""
        return cache.get(f'product_{product_id}')
    
    @staticmethod
    def set_product_details(product_id: str, data: Dict):
        """Cache product details"""
        cache.set(f'product_{product_id}', data, CacheManager.CACHE_TIMEOUT)

class PerformanceMonitor:
    """Monitor and log performance metrics"""
    
    @staticmethod
    def monitor_query_time(func):
        """Decorator to monitor database query execution time"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            if execution_time > 1.0:  # Log slow queries (>1 second)
                logger.warning(
                    f"Slow query detected in {func.__name__}: {execution_time:.2f}s"
                )
            
            return result
        return wrapper
    
    @staticmethod
    def log_cache_hit_rate(cache_key: str, hit: bool):
        """Log cache hit/miss for monitoring"""
        status = "HIT" if hit else "MISS"
        logger.info(f"Cache {status}: {cache_key}")

class DatabaseOptimizer:
    """Database-level optimizations"""
    
    @staticmethod
    def bulk_create_store_products(store_id: str, product_data: List[Dict]):
        """Bulk create store product pricing for better performance"""
        from .models import StoreProductPricing
        
        pricing_objects = [
            StoreProductPricing(
                store_id=store_id,
                product_id=data['product_id'],
                retail_price=data['retail_price']
            )
            for data in product_data
        ]
        
        return StoreProductPricing.objects.bulk_create(
            pricing_objects, 
            ignore_conflicts=True
        )
    
    @staticmethod
    def get_store_dashboard_stats(store_id: str) -> Dict[str, Any]:
        """Get all store dashboard stats in single query"""
        from .models import MarketPlace, CustomUser
        from order.models import StoreOrder
        
        # Check cache first
        cached_stats = CacheManager.get_store_stats(store_id)
        if cached_stats:
            return cached_stats
        
        # Single query for all stats
        stats = {
            'listed_products': MarketPlace.objects.filter(
                store_id=store_id, list_product=True
            ).count(),
            'total_orders': StoreOrder.objects.filter(store_id=store_id).count(),
            'customers': CustomUser.objects.filter(
                associated_domain_id=store_id
            ).count()
        }
        
        # Cache the results
        CacheManager.set_store_stats(store_id, stats)
        return stats

def cache_result(timeout: int = 3600):
    """Decorator for caching function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}_{hash(str(args) + str(kwargs))}"
            
            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                PerformanceMonitor.log_cache_hit_rate(cache_key, True)
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            PerformanceMonitor.log_cache_hit_rate(cache_key, False)
            
            return result
        return wrapper
    return decorator

class PaginationOptimizer:
    """Optimized pagination for large datasets"""
    
    @staticmethod
    def get_optimized_page_size(request) -> int:
        """Dynamic page size based on request type"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        # Mobile devices get smaller page sizes
        if any(mobile in user_agent for mobile in ['mobile', 'android', 'iphone']):
            return 10
        
        # Desktop gets larger page sizes
        return 20
    
    @staticmethod
    def cursor_paginate(queryset, cursor_field: str = 'id', limit: int = 20):
        """Cursor-based pagination for better performance on large datasets"""
        # Implementation for cursor pagination
        # This is more efficient than offset-based pagination for large datasets
        pass

# Performance monitoring middleware
class QueryCountMiddleware:
    """Middleware to monitor database query count per request"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        from django.db import connection
        
        queries_before = len(connection.queries)
        response = self.get_response(request)
        queries_after = len(connection.queries)
        
        query_count = queries_after - queries_before
        
        # Log excessive queries
        if query_count > 10:
            logger.warning(
                f"High query count for {request.path}: {query_count} queries"
            )
        
        # Add query count to response headers in debug mode
        if hasattr(response, 'headers'):
            response.headers['X-Query-Count'] = str(query_count)
        
        return response