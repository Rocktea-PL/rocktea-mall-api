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
        ],
        'profile_image': [
            {'width': 200, 'height': 200, 'crop': 'fill', 'gravity': 'face'},
            {'quality': 'auto:best'},
            {'fetch_format': 'auto'},
            {'radius': 'max'}
        ],
        'store_cover': [
            {'width': 1200, 'height': 400, 'crop': 'fill'},
            {'quality': 'auto:good'},
            {'fetch_format': 'auto'}
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
    def upload_optimized(cls, file_content, folder="products", transformation_type='large', **kwargs):
        """Upload with optimizations"""
        transformations = cls.TRANSFORMATIONS.get(transformation_type, cls.TRANSFORMATIONS['large'])
        
        # Basic upload options
        upload_options = {
            'folder': folder,
            'resource_type': 'auto',
            'quality': 'auto:best',
            'fetch_format': 'auto',
            'use_filename': True,
            'unique_filename': True,
            'overwrite': False
        }
        
        # Add transformations if provided
        if transformations:
            upload_options['transformation'] = transformations
        
        # Add eager transformations if provided in kwargs
        if 'eager' in kwargs:
            upload_options['eager'] = kwargs.pop('eager')
            upload_options['eager_async'] = kwargs.pop('eager_async', True)
        
        # Merge remaining kwargs
        upload_options.update(kwargs)
        
        return uploader.upload(file_content, **upload_options)
    
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
    
    @classmethod
    def delete_image_from_url(cls, image_url):
        """Delete image from Cloudinary using URL"""
        if not image_url or 'cloudinary.com' not in image_url:
            return False
        
        try:
            # Extract public_id from URL
            # URL format: https://res.cloudinary.com/{cloud_name}/image/upload/{transformations}/{public_id}.{format}
            parts = image_url.split('/')
            # Find 'upload' index and get everything after it
            upload_index = parts.index('upload')
            # Get public_id (remove version if present and file extension)
            public_id_with_ext = '/'.join(parts[upload_index + 1:])
            # Remove transformations (anything starting with v followed by numbers)
            if public_id_with_ext.startswith('v') and public_id_with_ext.split('/')[0][1:].isdigit():
                public_id_with_ext = '/'.join(public_id_with_ext.split('/')[1:])
            # Remove file extension
            public_id = public_id_with_ext.rsplit('.', 1)[0]
            
            # Delete from Cloudinary
            result = uploader.destroy(public_id)
            return result.get('result') == 'ok'
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"Failed to delete image from Cloudinary: {e}")
            return False

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