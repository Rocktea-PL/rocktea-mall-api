from django.core.management.base import BaseCommand
from django.db import transaction
from mall.models import ProductImage
from mall.cloudinary_utils import CloudinaryOptimizer
import cloudinary.uploader as uploader
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Optimize existing product images and store public_ids'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of images to process in each batch'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be optimized without making changes'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        
        # Get images without public_id
        images_to_optimize = ProductImage.objects.filter(
            public_id__isnull=True,
            images__isnull=False
        ).exclude(images='')
        
        total_images = images_to_optimize.count()
        self.stdout.write(f"Found {total_images} images to optimize")
        
        if dry_run:
            self.stdout.write("DRY RUN - No changes will be made")
            for image in images_to_optimize[:10]:  # Show first 10
                self.stdout.write(f"Would optimize: {image.images.url}")
            return
        
        processed = 0
        errors = 0
        
        for i in range(0, total_images, batch_size):
            batch = images_to_optimize[i:i + batch_size]
            
            with transaction.atomic():
                for image in batch:
                    try:
                        # Extract public_id from existing Cloudinary URL
                        if 'cloudinary.com' in str(image.images.url):
                            public_id = self._extract_public_id(image.images.url)
                            if public_id:
                                image.public_id = public_id
                                image.save(update_fields=['public_id'])
                                processed += 1
                                self.stdout.write(f"Updated public_id for image {image.id}: {public_id}")
                            else:
                                # Re-upload and optimize if can't extract public_id
                                self._reupload_and_optimize(image)
                                processed += 1
                        else:
                            # Upload to Cloudinary with optimization
                            self._reupload_and_optimize(image)
                            processed += 1
                            
                    except Exception as e:
                        errors += 1
                        logger.error(f"Error processing image {image.id}: {e}")
                        self.stdout.write(
                            self.style.ERROR(f"Error processing image {image.id}: {e}")
                        )
            
            self.stdout.write(f"Processed batch {i//batch_size + 1}/{(total_images-1)//batch_size + 1}")
        
        self.stdout.write(
            self.style.SUCCESS(
                f"Optimization complete! Processed: {processed}, Errors: {errors}"
            )
        )
    
    def _extract_public_id(self, url):
        """Extract public_id from Cloudinary URL"""
        try:
            # Example URL: https://res.cloudinary.com/cloud/image/upload/v123/folder/image.jpg
            parts = url.split('/')
            if 'cloudinary.com' in url and 'upload' in parts:
                upload_index = parts.index('upload')
                if upload_index + 2 < len(parts):
                    # Skip version if present (starts with 'v')
                    start_index = upload_index + 1
                    if parts[start_index].startswith('v') and parts[start_index][1:].isdigit():
                        start_index += 1
                    
                    # Join remaining parts and remove file extension
                    public_id_parts = parts[start_index:]
                    public_id = '/'.join(public_id_parts)
                    # Remove file extension
                    if '.' in public_id:
                        public_id = public_id.rsplit('.', 1)[0]
                    return public_id
        except Exception as e:
            logger.error(f"Error extracting public_id from {url}: {e}")
        return None
    
    def _reupload_and_optimize(self, image):
        """Re-upload image with optimization"""
        try:
            # Download current image
            import requests
            response = requests.get(image.images.url)
            if response.status_code == 200:
                # Simple upload without complex transformations
                result = uploader.upload(
                    response.content,
                    folder="products",
                    resource_type="auto",
                    quality="auto:best",
                    fetch_format="auto",
                    use_filename=True,
                    unique_filename=True
                )
                
                # Update image record
                image.images = result.get('secure_url')
                if hasattr(image, 'public_id'):
                    image.public_id = result.get('public_id')
                image.save()
                
                self.stdout.write(f"Re-uploaded and optimized image {image.id}")
            else:
                raise Exception(f"Failed to download image: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Error re-uploading image {image.id}: {e}")
            raise