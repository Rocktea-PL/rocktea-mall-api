from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete, pre_save, pre_delete
import logging
import re

from .models import Store, Wallet, StoreProductPricing, MarketPlace, Notification, CustomUser, Product, ProductImage

# Conditional import to prevent server errors
try:
    from .cache_utils import CacheManager
except ImportError:
    class CacheManager:
        @staticmethod
        def invalidate_product(product_id):
            pass
        @staticmethod
        def invalidate_store(store_id):
            pass
from .utils import generate_store_slug, determine_environment_config
from .middleware import get_current_request
from workshop.route53 import create_cname_record, delete_store_dns_record

from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Store)
def generate_store_slug_only(sender, instance, **kwargs):
    """
    Generate only the slug before saving the store.
    Domain name will be set after successful DNS creation.
    """
    if not instance.slug and instance.name:
        instance.slug = generate_store_slug(instance.name)

@receiver(post_save, sender=Store)
def create_wallet(sender, instance, created, **kwargs):
    """Create Wallet for every Store"""
    if created:
        Wallet.objects.get_or_create(store=instance)

@receiver(post_save, sender=Store)
def create_wallet(sender, instance, created, **kwargs):
    """Create Wallet for every Store"""
    if created:
        Wallet.objects.get_or_create(store=instance)

def send_local_development_email(store_instance, store_url):
    """Send welcome email for local development environment"""
    from setup.email_service import send_store_welcome_email
    send_store_welcome_email(store_instance, "LOCAL SERVER", is_local=True)

def send_store_success_email(store_instance, store_url, environment):
    """Send success email when store and DNS are created successfully"""
    from setup.email_service import send_store_welcome_email
    logger.info(f"Sending store welcome email for {store_instance.name}")
    send_store_welcome_email(store_instance, environment)

def send_store_dns_failure_email(store_instance, attempted_domain):
    """Send email when DNS record creation fails"""
    from setup.email_service import send_store_dns_failure_email
    send_store_dns_failure_email(store_instance, attempted_domain)
    logger.info(f"DNS failure email sent for store: {store_instance.name}")

def send_store_dns_error_email(store_instance, error_message):
    """Send email when DNS record creation encounters an error"""
    from setup.email_service import send_store_dns_error_email
    send_store_dns_error_email(store_instance, error_message)
    logger.error(f"DNS error email sent for store: {store_instance.name}. Error: {error_message}")

@receiver(post_save, sender=StoreProductPricing)
def create_marketplace(sender, instance, created, **kwargs):
    if not created:
        return
        
    # Create marketplace entry and notification
    MarketPlace.objects.get_or_create(store=instance.store, product=instance.product)
    Notification.objects.create(
        store=instance.store, 
        message=f"{instance.store.name} you just added a new product to your Marketplace."
    )

@receiver(pre_delete, sender=CustomUser)
def delete_dropshipper_domain(sender, instance, **kwargs):
    """Delete DNS record when dropshipper is deleted"""
    logger.info(f"Delete signal triggered for user: {instance.email}, is_store_owner: {instance.is_store_owner}")
    
    if not instance.is_store_owner:
        logger.info(f"User {instance.email} is not a store owner, skipping DNS deletion")
        return
        
    user_email = instance.email
    user_name = instance.get_full_name() or instance.first_name or instance.email
    
    try:
        # Get store using the OneToOne relationship from Store model
        store = getattr(instance, 'owners', None)
        
        if store and store.dns_record_created:
            logger.info(f"Found store for user {instance.email}: {store.name} (ID: {store.id})")
            
            # Extract clean domain from domain_name
            if store.domain_name:
                from urllib.parse import urlparse
                parsed_url = urlparse(store.domain_name)
                clean_domain = parsed_url.netloc
                logger.info(f"Extracted clean domain: {clean_domain} from {store.domain_name}")
                
                try:
                    success = delete_store_dns_record(clean_domain)
                    
                    if success:
                        logger.info(f"Successfully deleted DNS record for store: {store.name}")
                        _send_deletion_success_email(user_email, user_name, store.name, store.domain_name)
                    else:
                        logger.error(f"Failed to delete DNS record for store: {store.name}")
                        _send_deletion_failure_email(user_email, user_name, store.name, store.domain_name)
                        
                except Exception as dns_error:
                    logger.error(f"DNS deletion error for store {store.name}: {dns_error}")
                    _send_deletion_failure_email(user_email, user_name, store.name, store.domain_name)
            else:
                logger.info(f"No domain_name found for store: {store.name}")
        else:
            logger.info(f"No store with DNS record found for user: {instance.email}")
                
    except Exception as e:
        logger.error(f"Error in delete_dropshipper_domain for {instance.email}: {e}")


def _send_deletion_success_email(user_email, user_name, store_name, store_domain):
    """Send email notification when store and domain are successfully deleted"""
    try:
        from setup.email_service import send_store_deletion_email
        send_store_deletion_email(user_email, user_name, store_name, store_domain, success=True)
        logger.info(f"Store deletion email sent to {user_email} for store: {store_name}")
    except Exception as e:
        logger.error(f"Failed to send deletion success email to {user_email}: {e}")

def _send_deletion_failure_email(user_email, user_name, store_name, store_domain):
    """Send email when DNS deletion fails"""
    try:
        from setup.email_service import send_store_deletion_email
        send_store_deletion_email(user_email, user_name, store_name, store_domain, success=False)
        logger.info(f"Store deletion failure email sent to {user_email} for store: {store_name}")
    except Exception as e:
        logger.error(f"Failed to send deletion failure email to {user_email}: {e}")

def create_store_domain_after_payment(store):
    """Create domain for store after payment confirmation"""
    logger.info(f"Starting domain creation for store: {store.name} (ID: {store.id})")
    
    if store.dns_record_created:
        logger.info(f"DNS already created for store: {store.name}")
        return
        
    try:
        env_config = determine_environment_config(get_current_request())
        logger.info(f"Environment config: {env_config}")
        
        # Handle local environment
        if env_config.get('is_local', False):
            logger.info(f"Local environment detected for store: {store.name}")
            # Set domain name for local environment only after marking DNS as created
            store.dns_record_created = True
            store.domain_name = f"http://localhost:8000?mall={store.id}"
            store.save(update_fields=['dns_record_created', 'domain_name'])
            send_local_development_email(store, store.domain_name)
            return
        
        # Generate full domain using existing slug
        if not store.slug:
            logger.error(f"No slug found for store {store.name}")
            return
            
        full_domain = f"{store.slug}.{env_config['target_domain']}"
        logger.info(f"Creating DNS record for domain: {full_domain}")
        
        # Create DNS record
        logger.info(f"Attempting DNS creation with zone_id: {env_config['hosted_zone_id']}, domain: {full_domain}, target: {env_config['target_domain']}")
        
        dns_result = create_cname_record(
            zone_id=env_config['hosted_zone_id'],
            subdomain=full_domain,
            target=env_config['target_domain']
        )
        
        logger.info(f"DNS creation result: {dns_result is not None}, Result: {dns_result}")
        
        if dns_result is not None:
            # Set domain name only after successful DNS creation
            store.dns_record_created = True
            store.domain_name = f"https://{full_domain}?mall={store.id}"
            store.save(update_fields=['dns_record_created', 'domain_name'])
            logger.info(f"DNS record and domain name set for store: {store.name}")
            
            # Send success email
            send_store_success_email(store, store.domain_name, env_config['environment'])
            logger.info(f"Success email sent for store: {store.name}")
        else:
            logger.error(f"DNS creation failed for store: {store.name}")
            # Still send failure email so user knows what happened
            send_store_dns_failure_email(store, full_domain)
            logger.info(f"DNS failure email sent for store: {store.name}")
            
    except Exception as e:
        logger.error(f"DNS creation failed for {store.name}: {e}", exc_info=True)
        send_store_dns_error_email(store, str(e))

# Cache invalidation signals
@receiver(post_save, sender=Product)
@receiver(post_delete, sender=Product)
def invalidate_product_cache(sender, instance, **kwargs):
    try:
        from django.core.cache import cache
        cache.delete('categories_list')
        # Use delete_many instead of delete_pattern for better compatibility
        cache_keys = [f'store_stats_{store.id}' for store in instance.store.all()]
        if cache_keys:
            cache.delete_many(cache_keys)
    except Exception as e:
        logger.error(f"Cache invalidation error: {e}")

# Safe image deletion when product is deleted
@receiver(pre_delete, sender=Product)
def delete_product_images(sender, instance, **kwargs):
    """Delete all associated images when product is deleted"""
    for image in instance.images.all():
        try:
            if image.images:
                # Delete from Cloudinary using stored public_id
                if hasattr(image, 'public_id') and image.public_id:
                    try:
                        import cloudinary.uploader as uploader
                        uploader.destroy(image.public_id)
                    except Exception as cloudinary_error:
                        logger.error(f"Error deleting from Cloudinary: {cloudinary_error}")
                
                # Delete the file field
                image.images.delete(save=False)
        except Exception as e:
            logger.error(f"Error deleting product image {image.id}: {e}")

@receiver(pre_delete, sender=ProductImage)
def delete_product_image_file(sender, instance, **kwargs):
    """Delete image file when ProductImage is deleted"""
    try:
        if instance.images:
            # Delete from Cloudinary using stored public_id
            if hasattr(instance, 'public_id') and instance.public_id:
                try:
                    import cloudinary.uploader as uploader
                    uploader.destroy(instance.public_id)
                except Exception as cloudinary_error:
                    logger.error(f"Error deleting from Cloudinary: {cloudinary_error}")
            
            # Delete the file field
            instance.images.delete(save=False)
    except Exception as e:
        logger.error(f"Error deleting image file for ProductImage {instance.id}: {e}")
@receiver(pre_save, sender=CustomUser)
def delete_old_profile_image(sender, instance, **kwargs):
    """Delete old profile image when user updates it"""
    if not instance.pk:
        return
    
    try:
        old_instance = CustomUser.objects.get(pk=instance.pk)
        if old_instance.profile_image and old_instance.profile_image != instance.profile_image:
            if hasattr(old_instance.profile_image, 'public_id') and old_instance.profile_image.public_id:
                try:
                    import cloudinary.uploader as uploader
                    uploader.destroy(old_instance.profile_image.public_id)
                except Exception as e:
                    logger.error(f"Error deleting old profile image from Cloudinary: {e}")
            old_instance.profile_image.delete(save=False)
    except CustomUser.DoesNotExist:
        pass

@receiver(pre_save, sender=Store)
def delete_old_store_images(sender, instance, **kwargs):
    """Delete old store logo and cover image when updated"""
    if not instance.pk:
        return
    
    try:
        old_instance = Store.objects.get(pk=instance.pk)
        
        # Handle logo deletion
        if old_instance.logo and old_instance.logo != instance.logo:
            if hasattr(old_instance.logo, 'public_id') and old_instance.logo.public_id:
                try:
                    import cloudinary.uploader as uploader
                    uploader.destroy(old_instance.logo.public_id)
                except Exception as e:
                    logger.error(f"Error deleting old logo from Cloudinary: {e}")
            old_instance.logo.delete(save=False)
        
        # Handle cover image deletion
        if old_instance.cover_image and old_instance.cover_image != instance.cover_image:
            if hasattr(old_instance.cover_image, 'public_id') and old_instance.cover_image.public_id:
                try:
                    import cloudinary.uploader as uploader
                    uploader.destroy(old_instance.cover_image.public_id)
                except Exception as e:
                    logger.error(f"Error deleting old cover image from Cloudinary: {e}")
            old_instance.cover_image.delete(save=False)
    except Store.DoesNotExist:
        pass