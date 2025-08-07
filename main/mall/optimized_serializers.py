from rest_framework import serializers
from .models import Product, Store, Category
from .cloudinary_utils import optimize_product_image

class OptimizedProductSerializer(serializers.ModelSerializer):
    """Optimized serializer to prevent N+1 queries"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    subcategory_name = serializers.CharField(source='subcategory.name', read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    producttype_name = serializers.CharField(source='producttype.name', read_only=True)
    optimized_image = serializers.SerializerMethodField()
    product_images = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'description', 'category_name', 'subcategory_name', 
                 'brand_name', 'producttype_name', 'optimized_image', 'product_images', 'sales_count', 'is_available']
    
    def get_optimized_image(self, obj):
        """Return optimized image URL for the product"""
        # Use prefetched images to avoid N+1
        if hasattr(obj, 'prefetched_images'):
            first_image = obj.prefetched_images[0] if obj.prefetched_images else None
        else:
            first_image = obj.images.first()
        
        if first_image and first_image.images:
            try:
                # Use stored public_id if available for Cloudinary optimization
                if hasattr(first_image, 'public_id') and first_image.public_id:
                    from .cloudinary_utils import CloudinaryOptimizer
                    return CloudinaryOptimizer.get_optimized_url(first_image.public_id, 'product_card')
                else:
                    # Fallback to original URL
                    return first_image.images.url
            except Exception:
                # Fallback to original URL on any error
                return first_image.images.url
        return None
    
    def get_product_images(self, obj):
        """Return optimized image URLs for all product images"""
        optimized_images = []
        
        # Use prefetched images to avoid N+1
        if hasattr(obj, 'prefetched_images'):
            images = obj.prefetched_images
        else:
            images = obj.images.all()
        
        for img in images:
            if img.images:
                try:
                    # Use stored public_id if available for Cloudinary optimization
                    if hasattr(img, 'public_id') and img.public_id:
                        from .cloudinary_utils import CloudinaryOptimizer
                        optimized_url = CloudinaryOptimizer.get_optimized_url(img.public_id, 'product_card')
                        optimized_images.append(optimized_url)
                    else:
                        # Fallback to original URL
                        optimized_images.append(img.images.url)
                except Exception:
                    # Fallback to original URL on any error
                    optimized_images.append(img.images.url)
        return optimized_images

class OptimizedStoreSerializer(serializers.ModelSerializer):
    """Optimized store serializer"""
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Store
        fields = ['id', 'name', 'domain_name', 'has_made_payment', 'product_count']
    
    def get_product_count(self, obj):
        # Use annotation instead of counting in serializer
        return getattr(obj, 'product_count', 0)