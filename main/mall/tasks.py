from celery import shared_task
from django.utils import timezone
import logging
from django.db import transaction
from django.core.cache import cache

from .models import Store, ProductImage
from order.models import StoreOrder
from order.shipbubble_service import ShipbubbleService
from .cloudinary_utils import CloudinaryOptimizer
from .cache_utils import CacheManager

logger = logging.getLogger(__name__)

# Product and Order Management Tasks
@shared_task(bind=True, max_retries=3, retry_backoff=60)
def upload_image(self, product_id, file_content, file_name, content_type):
    task_id = f'upload_image_{product_id}'
    
    if not cache.add(task_id, True, timeout=60):
        return
    
    try:
        with transaction.atomic():
            logger.info(f"Uploading optimized image {file_name}")
            productimage = ProductImage.objects.select_for_update().get(id=product_id)
            
            # Use optimized upload
            result = CloudinaryOptimizer.upload_optimized(
                file_content,
                folder="products",
                transformation_type='large'
            )
            
            productimage.image = result.get('secure_url')
            productimage.save()
            
            # Invalidate related cache
            CacheManager.invalidate_store(productimage.product.store.first().id if productimage.product.store.exists() else None)
            
    except ProductImage.DoesNotExist:
        logger.error(f"ProductImage {product_id} not found")
        return
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        self.retry(exc=e)
    finally:
        cache.delete(task_id)


@shared_task(bind=True, max_retries=3, retry_backoff=60)
def check_shipping_status(self):
    shipbubble_service = ShipbubbleService()
    orders = StoreOrder.objects.exclude(tracking_status='completed').select_related()
    
    for order in orders:
        try:
            response = shipbubble_service.track_shipping_status(order.tracking_id)
            if response.get('data'):
                status = response['data'][0]['status']
                if order.tracking_status != status:
                    order.tracking_status = status
                    order.save(update_fields=['tracking_status'])
                    logger.info(f"Updated order {order.id} status to {status}")
        except Exception as e:
            logger.error(f"Error tracking order {order.id}: {e}")


@shared_task(bind=True, max_retries=3, retry_backoff=60)
def cancel_unpaid_shipments(self):
    shipbubble_service = ShipbubbleService()
    keys = cache.keys('shipment_*')
    
    for key in keys:
        try:
            shipment_feedback = cache.get(key)
            if shipment_feedback and 'data' in shipment_feedback:
                order_id = shipment_feedback['data']['order_id']
                cancel_response = shipbubble_service.cancelled_shipping_label(order_id)
                
                if cancel_response.get('status') == 'success':
                    StoreOrder.objects.filter(tracking_id=order_id).update(status='Cancelled')
                    logger.info(f"Cancelled shipment for order {order_id}")
                    cache.delete(key)
        except Exception as e:
            logger.error(f"Error cancelling shipment {key}: {e}")


@shared_task
def log_webhook_attempt(reference, email, purpose, status):
    """Log webhook processing attempts for debugging"""
    logger.info(f"Webhook processed - Reference: {reference}, Email: {email}, Purpose: {purpose}, Status: {status}")
    return f"Logged webhook attempt for {reference}"
