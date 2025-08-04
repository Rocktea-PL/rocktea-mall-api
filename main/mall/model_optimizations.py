"""
Model optimizations and database improvements
"""
from django.db import models
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .performance_optimizers import CacheManager

# Custom managers for optimized queries
class OptimizedProductManager(models.Manager):
    """Optimized manager for Product model"""
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'category', 'subcategory', 'producttype', 'brand'
        ).prefetch_related('images', 'product_variants')
    
    def available(self):
        """Get only available products"""
        return self.get_queryset().filter(
            is_available=True, 
            upload_status='Approved'
        )
    
    def by_category(self, category_id):
        """Get products by category with optimized query"""
        return self.available().filter(category_id=category_id)
    
    def best_selling(self, limit=10):
        """Get best selling products"""
        return self.available().order_by('-sales_count')[:limit]

class OptimizedStoreManager(models.Manager):
    """Optimized manager for Store model"""
    
    def get_queryset(self):
        return super().get_queryset().select_related('owner', 'category')
    
    def completed(self):
        """Get only completed stores"""
        return self.get_queryset().filter(completed=True)
    
    def with_products(self):
        """Get stores with their products"""
        return self.completed().prefetch_related(
            'pricings__product__images'
        )

class OptimizedMarketPlaceManager(models.Manager):
    """Optimized manager for MarketPlace model"""
    
    def get_queryset(self):
        return super().get_queryset().select_related(
            'store', 'product__category', 'product__brand'
        ).prefetch_related('product__images')
    
    def listed(self):
        """Get only listed products"""
        return self.get_queryset().filter(list_product=True)
    
    def by_store(self, store_id):
        """Get marketplace products by store"""
        return self.listed().filter(store_id=store_id)

# Signal handlers for cache invalidation
@receiver([post_save, post_delete], sender='mall.Product')
def invalidate_product_cache(sender, instance, **kwargs):
    """Invalidate product-related cache when product changes"""
    cache.delete('categories_list')
    if hasattr(instance, 'store'):
        for store in instance.store.all():
            CacheManager.invalidate_store_cache(store.id)

@receiver([post_save, post_delete], sender='mall.StoreProductPricing')
def invalidate_store_pricing_cache(sender, instance, **kwargs):
    """Invalidate store cache when pricing changes"""
    CacheManager.invalidate_store_cache(instance.store.id)

@receiver([post_save, post_delete], sender='mall.MarketPlace')
def invalidate_marketplace_cache(sender, instance, **kwargs):
    """Invalidate marketplace cache when listing changes"""
    CacheManager.invalidate_store_cache(instance.store.id)

# Database optimization suggestions for models.py
MODEL_OPTIMIZATIONS = """
Add these optimizations to your existing models:

1. In Product model, add:
   objects = OptimizedProductManager()

2. In Store model, add:
   objects = OptimizedStoreManager()

3. In MarketPlace model, add:
   objects = OptimizedMarketPlaceManager()

4. Add these indexes to improve query performance:
   
   class Meta:
       indexes = [
           models.Index(fields=['category', 'is_available']),
           models.Index(fields=['upload_status', 'is_available']),
           models.Index(fields=['sales_count']),
           models.Index(fields=['created_at']),
       ]

5. For StoreProductPricing model:
   
   class Meta:
       indexes = [
           models.Index(fields=['store', 'product']),
           models.Index(fields=['store', 'retail_price']),
           models.Index(fields=['created_at']),
       ]
       unique_together = [['store', 'product']]  # Prevent duplicates

6. For MarketPlace model:
   
   class Meta:
       indexes = [
           models.Index(fields=['store', 'list_product']),
           models.Index(fields=['product', 'list_product']),
           models.Index(fields=['store', 'product', 'list_product']),
       ]
"""

# Database migration suggestions
DATABASE_OPTIMIZATIONS = """
Run these database optimizations:

1. Add composite indexes:
   CREATE INDEX CONCURRENTLY idx_product_category_available 
   ON mall_product(category_id, is_available) 
   WHERE is_available = true;

2. Add partial indexes for better performance:
   CREATE INDEX CONCURRENTLY idx_product_approved 
   ON mall_product(upload_status) 
   WHERE upload_status = 'Approved';

3. Optimize foreign key indexes:
   CREATE INDEX CONCURRENTLY idx_store_product_pricing_composite 
   ON mall_storeproductpricing(store_id, product_id, retail_price);

4. Add indexes for common query patterns:
   CREATE INDEX CONCURRENTLY idx_marketplace_store_listed 
   ON mall_marketplace(store_id, list_product) 
   WHERE list_product = true;
"""