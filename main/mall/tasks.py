from celery import shared_task
from django.utils import timezone
import logging
from django.db import transaction
from django.core.cache import cache

from .models import Store, ProductImage
from .utils import determine_environment_config, generate_store_domain
from workshop.route53 import create_cname_record, delete_store_dns_record
from setup.utils import sendEmail
from order.models import StoreOrder
from order.shipbubble_service import ShipbubbleService
from .cloudinary_utils import CloudinaryOptimizer
from .cache_utils import CacheManager

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_store_dns_async(self, store_id):
    """
    Asynchronously create DNS record for store to improve performance
    """
    try:
        store = Store.objects.get(id=store_id)
        
        # Skip if already created
        if store.dns_record_created:
            logger.info(f"DNS already created for store: {store.name}")
            return f"DNS already exists for store: {store.name}"
        
        # Get environment configuration
        env_config = determine_environment_config()
        logger.info(f"Environment is: {env_config}")
        
        # Skip DNS provisioning when server is running locally
        if env_config['environment'] == 'local':
            logger.info("Server running locally - skipping DNS provisioning")
            final_url = f"http://localhost:8000?mall={store.id}"
            store.domain_name = final_url
            store.save(update_fields=['domain_name'])
            
            # Send local development email
            from .signals import send_local_development_email
            send_local_development_email(store, final_url)
            return f"Local development setup completed for store: {store.name}"
        
        # Generate the subdomain
        full_domain = generate_store_domain(store.slug, env_config['environment'])
        
        if not full_domain:
            raise Exception(f"No domain generated for store {store.name}")
        
        logger.info(f"Creating DNS record for store: {store.name} (ID: {store.id})")
        
        # Create DNS record
        response = create_cname_record(
            zone_id=env_config['hosted_zone_id'],
            subdomain=full_domain,
            target=env_config['target_domain']
        )
        
        if response:
            # Update store with DNS info
            store.dns_record_created = True
            store.domain_name = full_domain
            store.save(update_fields=['dns_record_created', 'domain_name'])

            # Build the clickable URL
            final_url = f"https://{full_domain}?mall={store.id}"

            # Send success email
            from .signals import send_store_success_email
            send_store_success_email(store, final_url, env_config['environment'])
            
            logger.info(f"Successfully created DNS record for store: {store.name}")
            return f"DNS record created successfully for store: {store.name}"
        else:
            raise Exception(f"Failed to create DNS record for store {store.name}")
            
    except Store.DoesNotExist:
        logger.error(f"Store with ID {store_id} not found")
        return f"Store with ID {store_id} not found"
        
    except Exception as e:
        logger.error(f"Error creating DNS record for store ID {store_id}: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying DNS creation for store ID {store_id} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # Final failure - send error email
        try:
            store = Store.objects.get(id=store_id)
            from .signals import send_store_dns_error_email
            send_store_dns_error_email(store, str(e))
        except Store.DoesNotExist:
            pass
            
        return f"Failed to create DNS record for store ID {store_id}: {e}"


@shared_task(bind=True, max_retries=2, default_retry_delay=30)
def delete_store_dns_async(self, store_slug, user_email, store_name):
    """
    Asynchronously delete DNS record for better performance
    """
    try:
        logger.info(f"Deleting DNS record for store: {store_name}")
        
        success = delete_store_dns_record(store_slug)
        
        if success:
            logger.info(f"Successfully deleted DNS record for store: {store_name}")
            # Send deletion success email
            from .signals import send_store_deletion_email
            send_store_deletion_email({'email': user_email}, {'name': store_name})
            return f"DNS record deleted successfully for store: {store_name}"
        else:
            raise Exception(f"Failed to delete DNS record for store: {store_name}")
            
    except Exception as e:
        logger.error(f"Error deleting DNS record for store {store_name}: {e}")
        
        # Retry logic
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying DNS deletion for store {store_name} (attempt {self.request.retries + 1})")
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        # Final failure - send error email
        from .signals import send_store_deletion_failure_email
        send_store_deletion_failure_email({'email': user_email}, {'name': store_name})
        return f"Failed to delete DNS record for store {store_name}: {e}"


def send_local_development_email_async(store_instance, store_url):
    """Send welcome email for local development environment"""
    try:
        subject = "🎉 Your Dropshipper Store Created (Local Server)"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name,
            "store_name": store_instance.name,
            "store_domain": store_url,
            "environment": "LOCAL SERVER",
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "is_local": True,
        }
        
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_welcome_success.html',
            context=context,
            subject=subject,
            tags=["store-created", "local-server", "async"]
        )
        
    except Exception as e:
        logger.error(f"Error sending local development email: {e}")


def send_store_success_email_async(store_instance, store_url, environment):
    """Send success email when store and DNS are created successfully"""
    try:
        subject = "🎉 Your Dropshipper Store is Live – Welcome to RockTeaMall!"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name,
            "store_name": store_instance.name,
            "store_domain": store_url,
            "environment": environment.upper(),
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "is_local": False,
        }
        
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_welcome_success.html',
            context=context,
            subject=subject,
            tags=["store-created", "domain-provisioned", "success", "async"]
        )
        
    except Exception as e:
        logger.error(f"Error sending success email: {e}")


def send_store_dns_error_email_async(store_instance, error_message):
    """Send email when DNS record creation encounters an error"""
    try:
        subject = "🔧 Store Created - Technical Issue with Domain Setup"
        
        error_ref = f"DNS_ERROR_{store_instance.id}_{timezone.now().strftime('%Y%m%d_%H%M')}"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name,
            "store_name": store_instance.name,
            "store_id": store_instance.id,
            "error_reference": error_ref,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_dns_error.html',
            context=context,
            subject=subject,
            tags=["store-created", "dns-error", "technical-issue", "async"]
        )
        
    except Exception as e:
        logger.error(f"Error sending DNS error email: {e}")


def send_deletion_success_email_async(user_email, store_name):
    """Send email notification when store domain is successfully deleted"""
    try:
        subject = "🗑️ Your Store Has Been Removed - RockTeaMall"
        
        context = {
            "store_name": store_name,
            "deletion_date": timezone.now().strftime("%B %d, %Y at %I:%M %p"),
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        sendEmail(
            recipientEmail=user_email,
            template_name='emails/store_deletion_success.html',
            context=context,
            subject=subject,
            tags=["store-deleted", "domain-removed", "async"]
        )
        
    except Exception as e:
        logger.error(f"Error sending deletion success email: {e}")


def send_deletion_failure_email_async(user_email, store_name):
    """Send email when DNS deletion fails"""
    try:
        subject = "⚠️ Store Removal - Domain Cleanup Issue"
        
        context = {
            "store_name": store_name,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        sendEmail(
            recipientEmail=user_email,
            template_name='emails/store_deletion_failure.html',
            context=context,
            subject=subject,
            tags=["store-deleted", "dns-cleanup-failed", "async"]
        )
        
    except Exception as e:
        logger.error(f"Error sending deletion failure email: {e}")


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
            
            # Determine optimal transformation based on content type and size
            transformation_type = 'product_card' if 'product' in file_name.lower() else 'large'
            
            # Upload with optimizations
            result = CloudinaryOptimizer.upload_optimized(
                file_content,
                folder='products',
                transformation_type=transformation_type,
                eager=[
                    CloudinaryOptimizer.TRANSFORMATIONS['thumbnail'],
                    CloudinaryOptimizer.TRANSFORMATIONS['medium'],
                    CloudinaryOptimizer.TRANSFORMATIONS['large']
                ],
                eager_async=True
            )
            
            # Store the secure URL and public_id for future transformations
            productimage.image = result.get('secure_url')
            
            # Only set public_id if the field exists (after migration)
            if hasattr(productimage, 'public_id'):
                productimage.public_id = result.get('public_id')
            
            productimage.save()
            
            # Generate responsive URLs for different screen sizes
            responsive_urls = CloudinaryOptimizer.get_responsive_urls(result.get('public_id'))
            
            # Cache responsive URLs for quick access
            cache.set(f'responsive_urls_{product_id}', responsive_urls, timeout=3600)
            
            # Invalidate related cache
            CacheManager.invalidate_store(productimage.product.store.first().id if productimage.product.store.exists() else None)
            
            logger.info(f"Successfully uploaded and optimized image {file_name} with public_id: {result.get('public_id')}")
            
    except ProductImage.DoesNotExist:
        logger.error(f"ProductImage {product_id} not found")
        return
    except Exception as e:
        logger.error(f"Error uploading image: {e}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e)
        else:
            logger.error(f"Failed to upload image after {self.max_retries} retries: {e}")
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
