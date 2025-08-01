from rest_framework import serializers
from .models import Product, Store, Category
from .cloudinary_utils import optimize_product_image

class OptimizedProductSerializer(serializers.ModelSerializer):
    """Optimized serializer to prevent N+1 queries"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    optimized_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category_name', 'subcategory_name', 
                 'brand_name', 'optimized_image', 'sales_count', 'is_available']
    
    def get_optimized_image(self, obj):
        # Use prefetched images to avoid N+1
        if hasattr(obj, 'prefetched_images'):
            first_image = obj.prefetched_images[0] if obj.prefetched_images else None
        else:
            first_image = obj.images.first()
        
        if first_image:
            return optimize_product_image(first_image.images.url)
        return None

class OptimizedStoreSerializer(serializers.ModelSerializer):
    """Optimized store serializer"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'domain_name', 'has_made_payment', 'product_count']
    
    def get_product_count(self, obj):
        # Use annotation instead of counting in serializer
        return getattr(obj, 'product_count', 0)