from django.core.cache import cache
from django.conf import settings
import hashlib
import json

def get_cache_key(prefix, *args, **kwargs):
    """Generate a consistent cache key"""
    key_data = f"{prefix}:{':'.join(str(arg) for arg in args)}"
    if kwargs:
        key_data += f":{hashlib.md5(json.dumps(kwargs, sort_keys=True).encode()).hexdigest()}"
    return key_data

def cache_result(key, timeout=None):
    """Decorator to cache function results"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            cache_key = get_cache_key(key, *args, **kwargs)
            result = cache.get(cache_key)
            if result is None:
                result = func(*args, **kwargs)
                cache.set(cache_key, result, timeout or getattr(settings, 'CACHE_TIMEOUTS', {}).get(key, 300))
            return result
        return wrapper
    return decorator

def invalidate_cache_pattern(pattern):
    """Invalidate cache keys matching pattern"""
    try:
        cache.delete_pattern(f"rocktea:{pattern}*")
    except AttributeError:
        # Fallback for cache backends that don't support delete_pattern
        pass

class CacheManager:
    """Centralized cache management"""
    
    @staticmethod
    def get_products(store_id=None, category_id=None):
        key = f"products:store_{store_id}:cat_{category_id}"
        return cache.get(key)
    
    @staticmethod
    def set_products(data, store_id=None, category_id=None, timeout=None):
        key = f"products:store_{store_id}:cat_{category_id}"
        timeout = timeout or getattr(settings, 'CACHE_TIMEOUTS', {}).get('products', 900)
        cache.set(key, data, timeout)
    
    @staticmethod
    def get_categories():
        return cache.get("categories:all")
    
    @staticmethod
    def set_categories(data, timeout=None):
        timeout = timeout or getattr(settings, 'CACHE_TIMEOUTS', {}).get('categories', 3600)
        cache.set("categories:all", data, timeout)
    
    @staticmethod
    def get_store(store_id):
        return cache.get(f"store:{store_id}")
    
    @staticmethod
    def set_store(store_id, data, timeout=None):
        timeout = timeout or getattr(settings, 'CACHE_TIMEOUTS', {}).get('stores', 1800)
        cache.set(f"store:{store_id}", data, timeout)
    
    @staticmethod
    def invalidate_store(store_id):
        invalidate_cache_pattern(f"store:{store_id}")
        invalidate_cache_pattern(f"products:store_{store_id}")