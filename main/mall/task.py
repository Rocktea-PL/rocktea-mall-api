from setup.celery import app
from .models import Product, ProductImage
from cloudinary.uploader import upload_large
from cloudinary.utils import cloudinary_url
from celery import shared_task
import uuid
import logging
from django.db import transaction
from django.core.cache import cache

logger = logging.getLogger(__name__)

@app.task(bind=True, max_retries=3, retry_backoff=60)
def upload_image(self, product_id, file_content, file_name, content_type):
   task_id = f'upload_image_{product_id}'  # Unique identifier for the task

   # Check if the task is in progress or has been executed recently
   if not cache.add(task_id, True, timeout=60):
      # Mark the task as in progress
      return 
   try:
      with transaction.atomic():
         logger.info(f"Uploading Image {file_name}")
         productimage = ProductImage.objects.get(id=product_id)
         
         # Define the transformations you want to apply to the image
         transformations = [
            {'width': 1000, 'crop': 'scale'},
            {'quality': 'auto:best'},
            {'fetch_format': 'auto'}
         ]
         
         # Apply the transformations using Cloudinary's URL generation
         transformed_url, _ = cloudinary_url(file_name, transformation=transformations, resource_type='image')
         
         # Upload the transformed image
         result = upload_large(
            file_content,
            filename=file_name,
            resource_type='image',
            public_id=f"product_image/{uuid.uuid4()}",
            content_type=content_type,
            chunk_size=1600000,  # Adjust the chunk size as needed
            eager_async=True,
            eager=[{'url': transformed_url}],
         )
         
         # Assuming you have an image field in your Product model
         productimage.image = result.get('secure_url', None)
         productimage.save()  # Save the changes to the product object in the database
   except Exception as e:
      self.retry(exc=e)
      logger.error(f"Error uploading image: {e}")
      raise
   finally:
      # Remove the task from the cache when it's completed
      cache.delete(task_id)