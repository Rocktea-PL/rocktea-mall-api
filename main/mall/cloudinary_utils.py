from cloudinary import CloudinaryImage
from cloudinary.utils import cloudinary_url
import cloudinary.uploader as uploader

class CloudinaryOptimizer:
    """Optimized Cloudinary operations"""
    
    # Predefined transformations for different use cases
    TRANSFORMATIONS = {
        'thumbnail': [
            {'width': 150, 'height': 150, 'crop': 'fill'},
            {'quality': 'auto:low'},
            {'fetch_format': 'auto'}
        ],
        'medium': [
            {'width': 400, 'height': 400, 'crop': 'limit'},
            {'quality': 'auto:good'},
            {'fetch_format': 'auto'}
        ],
        'large': [
            {'width': 800, 'height': 800, 'crop': 'limit'},
            {'quality': 'auto:best'},
            {'fetch_format': 'auto'}
        ],
        'product_card': [
            {'width': 300, 'height': 300, 'crop': 'fill'},
            {'quality': 'auto:good'},
            {'fetch_format': 'auto'},
            {'dpr': 'auto'}
        ],
        'store_logo': [
            {'width': 200, 'height': 200, 'crop': 'fit'},
            {'quality': 'auto:best'},
            {'fetch_format': 'auto'},
            {'background': 'white'}
        ]
    }
    
    @classmethod
    def get_optimized_url(cls, public_id, transformation_type='medium'):
        """Get optimized URL for an image"""
        if not public_id:
            return None
            
        transformations = cls.TRANSFORMATIONS.get(transformation_type, cls.TRANSFORMATIONS['medium'])
        url, _ = cloudinary_url(public_id, transformation=transformations)
        return url
    
    @classmethod
    def upload_optimized(cls, file_content, folder="products", transformation_type='large'):
        """Upload with optimizations"""
        transformations = cls.TRANSFORMATIONS.get(transformation_type, cls.TRANSFORMATIONS['large'])
        
        return uploader.upload(
            file_content,
            folder=folder,
            transformation=transformations,
            eager_async=True,
            eager=transformations,
            resource_type="auto",
            quality="auto:best",
            fetch_format="auto"
        )
    
    @classmethod
    def get_responsive_urls(cls, public_id):
        """Get multiple sizes for responsive images"""
        if not public_id:
            return {}
            
        return {
            'thumbnail': cls.get_optimized_url(public_id, 'thumbnail'),
            'medium': cls.get_optimized_url(public_id, 'medium'),
            'large': cls.get_optimized_url(public_id, 'large')
        }

def optimize_product_image(image_url):
    """Optimize product image URL"""
    if not image_url or 'cloudinary.com' not in image_url:
        return image_url
    
    # Extract public_id from URL
    try:
        public_id = image_url.split('/')[-1].split('.')[0]
        return CloudinaryOptimizer.get_optimized_url(public_id, 'product_card')
    except:
        return image_url