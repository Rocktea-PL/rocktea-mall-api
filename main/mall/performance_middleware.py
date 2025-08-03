import time
import logging
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware:
    """Monitor API performance and cache hit rates"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        # Track cache hits/misses
        cache_hits_before = getattr(cache, '_cache_hits', 0)
        cache_misses_before = getattr(cache, '_cache_misses', 0)
        
        response = self.get_response(request)
        
        # Calculate response time
        response_time = time.time() - start_time
        
        # Log slow requests
        if response_time > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                f"Slow request: {request.method} {request.path} "
                f"took {response_time:.2f}s"
            )
        
        # Add performance headers in debug mode
        if settings.DEBUG:
            response['X-Response-Time'] = f"{response_time:.3f}s"
            
            cache_hits_after = getattr(cache, '_cache_hits', 0)
            cache_misses_after = getattr(cache, '_cache_misses', 0)
            
            response['X-Cache-Hits'] = cache_hits_after - cache_hits_before
            response['X-Cache-Misses'] = cache_misses_after - cache_misses_before
        
        return response

class CacheHitRateMiddleware:
    """Track cache hit rates for optimization"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Monkey patch cache to track hits/misses
        original_get = cache.get
        original_set = cache.set
        
        def tracked_get(key, default=None, version=None):
            result = original_get(key, default, version)
            if result is not None:
                cache._cache_hits = getattr(cache, '_cache_hits', 0) + 1
            else:
                cache._cache_misses = getattr(cache, '_cache_misses', 0) + 1
            return result
        
        def tracked_set(key, value, timeout=None, version=None):
            return original_set(key, value, timeout, version)
        
        cache.get = tracked_get
        cache.set = tracked_set
        
        response = self.get_response(request)
        
        # Restore original methods
        cache.get = original_get
        cache.set = original_set
        
        return response