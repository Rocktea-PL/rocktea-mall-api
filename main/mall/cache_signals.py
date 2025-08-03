from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Category, Store, StoreProductPricing
from .cache_utils import CacheManager, invalidate_cache_pattern

@receiver(post_save, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalidate product-related cache when product is saved"""
    # Invalidate product caches
    invalidate_cache_pattern("products:*")
    invalidate_cache_pattern("marketplace:*")
    
    # Invalidate store-specific caches
    for store in instance.store.all():
        CacheManager.invalidate_store(store.id)

@receiver(post_delete, sender=Product)
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    """Invalidate product-related cache when product is deleted"""
    invalidate_cache_pattern("products:*")
    invalidate_cache_pattern("marketplace:*")

@receiver(post_save, sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """Invalidate category cache when category is saved"""
    invalidate_cache_pattern("categories:*")

@receiver(post_save, sender=Store)
def invalidate_store_cache(sender, instance, **kwargs):
    """Invalidate store cache when store is saved"""
    CacheManager.invalidate_store(instance.id)

@receiver(post_save, sender=StoreProductPricing)
def invalidate_pricing_cache(sender, instance, **kwargs):
    """Invalidate cache when pricing is updated"""
    CacheManager.invalidate_store(instance.store.id)
    invalidate_cache_pattern(f"products:store_{instance.store.id}:*")