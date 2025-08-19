"""
Shared image optimization utilities using existing mall infrastructure
"""
import logging
from typing import Optional, Dict, Any
from django.core.files.uploadedfile import InMemoryUploadedFile
from mall.cloudinary_utils import CloudinaryOptimizer

logger = logging.getLogger(__name__)

class ImageOptimizer:
    """Centralized image optimization using existing mall infrastructure"""
    
    # Image validation constants
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    ALLOWED_FORMATS = ['image/jpeg', 'image/jpg', 'image/png', 'image/webp']
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'webp']
    
    @classmethod
    def validate_image(cls, image_file: InMemoryUploadedFile) -> Dict[str, Any]:
        """Validate image file format and size"""
        if not image_file:
            return {'valid': False, 'error': 'No image file provided'}
        
        # Check file size
        if image_file.size > cls.MAX_FILE_SIZE:
            return {'valid': False, 'error': 'Image size must be less than 5MB'}
        
        # Check content type
        if image_file.content_type not in cls.ALLOWED_FORMATS:
            return {'valid': False, 'error': 'Only JPEG, PNG, and WebP images are allowed'}
        
        # Check file extension
        if hasattr(image_file, 'name') and image_file.name:
            extension = image_file.name.split('.')[-1].lower()
            if extension not in cls.ALLOWED_EXTENSIONS:
                return {'valid': False, 'error': 'Invalid file extension'}
        
        return {'valid': True, 'error': None}
    
    @classmethod
    def optimize_store_image(cls, image_file: InMemoryUploadedFile, image_type: str) -> Optional[str]:
        """Optimize store images using mall's CloudinaryOptimizer"""
        try:
            folder_map = {
                'store_logo': 'store_logos',
                'store_cover': 'store_covers',
                'profile': 'profile_images'
            }
            
            transformation_map = {
                'store_logo': 'store_logo',
                'store_cover': 'store_cover',
                'profile': 'profile_image'
            }
            
            folder = folder_map.get(image_type, 'uploads')
            transformation = transformation_map.get(image_type, 'medium')
            
            # Reset file pointer to beginning
            image_file.seek(0)
            
            result = CloudinaryOptimizer.upload_optimized(
                image_file.read(),
                folder=folder,
                transformation_type=transformation
            )
            return result.get('secure_url')
        except Exception as e:
            logger.error(f"Error optimizing {image_type}: {e}")
            return None
    
    @classmethod
    def handle_image_upload(cls, image_file: InMemoryUploadedFile, image_type: str) -> Dict[str, Any]:
        """Handle image upload with validation using mall's infrastructure"""
        try:
            # Validate image
            validation = cls.validate_image(image_file)
            if not validation['valid']:
                return {'success': False, 'url': None, 'error': validation['error']}
            
            # Use mall's optimization for all image types
            optimized_url = cls.optimize_store_image(image_file, image_type)
            if optimized_url:
                return {'success': True, 'url': optimized_url, 'error': None}
            else:
                return {'success': False, 'url': None, 'error': 'Image optimization failed'}
        except Exception as e:
            logger.error(f"Image upload handler error: {str(e)}")
            return {'success': False, 'url': None, 'error': f'Upload failed: {str(e)}'}