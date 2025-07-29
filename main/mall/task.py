from setup.celery import app
from .models import Product, ProductImage
from cloudinary.uploader import upload_large
from cloudinary.utils import cloudinary_url
from celery import shared_task
import uuid
import logging
from django.db import transaction
from django.core.cache import cache
from order.models import StoreOrder
from order.shipbubble_service import ShipbubbleService

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

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

@app.task(bind=True, max_retries=3, retry_backoff=60)
def check_shipping_status(self):
    shipbubble_service = ShipbubbleService()
    orders = StoreOrder.objects.exclude(tracking_status='completed')
    for order in orders:
        response = shipbubble_service.track_shipping_status(order.tracking_id)
        if response['data']:
            status = response['data'][0]['status']
            if order.tracking_status != status:
                order.tracking_status = status
                order.save()
                logger.info(f"Updated status for order {order.id} to {status}")
# @app.task(bind=True, max_retries=3, retry_backoff=60)
# def cancel_unpaid_shipments(self):
#     shipbubble_service = ShipbubbleService()
#     keys = cache.keys('shipment_*')
#     for key in keys:
#         shipment_feedback = cache.get(key)
#         if shipment_feedback:
#             user_id = key.split('_')[1]
#             order_id = shipment_feedback['data']['order_id']
#             # Cancel the shipment
#             cancel_response = shipbubble_service.cancelled_shipping_label(order_id)
#             if cancel_response.get('status') == 'success':
#                 # Update the order status to cancelled
#                 StoreOrder.objects.filter(tracking_id=order_id).update(status='Cancelled')
#                 logger.info(f"Cancelled shipment for order {order_id}")
#                 # Delete the cache
#                 cache.delete(key)