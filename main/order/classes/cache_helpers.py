from django.core.cache import cache

class CacheHelper:
    @staticmethod
    def clear_user_cache(user_id): 
        cache.delete(f'shipment_{user_id}')
