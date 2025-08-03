from django.db.models import Prefetch, Count, Q
from .models import Product, ProductImage, Store

class QueryOptimizer:
    """Centralized query optimizations"""
    
    @staticmethod
    def get_optimized_products(store_id=None, category_id=None):
        """Get products with optimized queries"""
        queryset = Product.objects.select_related(
            'category', 'subcategory', 'producttype', 'brand'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.only('images')[:1], to_attr='prefetched_images'),
            Prefetch('store', queryset=Store.objects.only('id', 'name'))
        ).only(
            'id', 'name', 'description', 'sales_count', 'is_available',
            'category__name', 'subcategory__name', 'brand__name'
        ).filter(is_available=True)
        
        if store_id:
            queryset = queryset.filter(store__id=store_id)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
            
        return queryset.order_by('-created_at')
    
    @staticmethod
    def get_optimized_stores():
        """Get stores with product counts"""
        return Store.objects.annotate(
            product_count=Count('store_products', filter=Q(store_products__is_available=True))
        ).only('id', 'name', 'domain_name', 'has_made_payment')
    
    @staticmethod
    def get_marketplace_products(store_id):
        """Optimized marketplace query"""
        return Product.objects.select_related(
            'category', 'subcategory'
        ).prefetch_related(
            Prefetch('images', queryset=ProductImage.objects.only('images')[:1])
        ).filter(
            store__id=store_id,
            is_available=True
        ).only(
            'id', 'name', 'description', 'category__name'
        )[:50]  # Limit to prevent memory issues