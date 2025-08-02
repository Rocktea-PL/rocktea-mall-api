from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
import logging
import re

from .models import Store, Wallet, StoreProductPricing, MarketPlace, Notification, CustomUser
from .utils import generate_store_slug, determine_environment_config
from .middleware import get_current_request
from workshop.route53 import create_cname_record, delete_store_dns_record

from django.utils import timezone

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Store)
def generate_store_domain_info(sender, instance, **kwargs):
    """
    Generate domain information before saving the store.
    """
    if instance.domain_name or instance.dns_record_created:
        return
        
    # Get environment configuration once
    env_config = determine_environment_config(get_current_request())
    
    # Generate domain based on environment
    if env_config.get('is_local', False):
        instance.domain_name = f"http://localhost:8000?mallcli={instance.id}"
    else:
        slug = generate_store_slug(instance.name)
        full_domain = f"{slug}.{env_config['target_domain']}"
        instance.domain_name = f"https://{full_domain}?mallcli={instance.id}"

@receiver(post_save, sender=Store)
def create_wallet(sender, instance, created, **kwargs):
    """Create Wallet for every Store"""
    if created:
        Wallet.objects.get_or_create(store=instance)

@receiver(post_save, sender=Store)
def create_dropshipper_dns_record(sender, instance, created, **kwargs):
    """Create DNS record for new stores - FIXED VERSION"""
    if not created or instance.dns_record_created:
        return
        
    env_config = determine_environment_config(get_current_request())
    
    # Handle local environment - Send email immediately
    if env_config.get('is_local', False):
        send_local_development_email_sync(instance, instance.domain_name)
        return
    
    # For production/dev environments, use async task with proper error handling
    try:
        # Import here to avoid circular imports
        from .tasks import create_store_dns_async
        
        # Use async task for DNS creation and email sending
        result = create_store_dns_async.delay(instance.id)
        logger.info(f"DNS creation task queued for store {instance.name} with task ID: {result.id}")
        
    except Exception as e:
        logger.error(f"Failed to queue DNS creation task for {instance.name}: {e}")
        # Fallback to synchronous processing
        _create_store_dns_sync(instance, env_config)

def _create_store_dns_sync(instance, env_config):
    """Synchronous DNS creation fallback"""
    try:
        # Extract domain from domain_name for DNS creation
        domain_match = re.search(r'https://([^?]+)', instance.domain_name or '')
        if not domain_match:
            logger.error(f"Invalid domain_name for store {instance.name}")
            return
            
        full_domain = domain_match.group(1)
        
        # Create DNS record
        if create_cname_record(
            zone_id=env_config['hosted_zone_id'],
            subdomain=full_domain,
            target=env_config['target_domain']
        ):
            instance.dns_record_created = True
            instance.save(update_fields=['dns_record_created'])
            send_store_success_email_sync(instance, instance.domain_name, env_config['environment'])
        else:
            send_store_dns_failure_email_sync(instance, full_domain)
            
    except Exception as e:
        logger.error(f"DNS creation failed for {instance.name}: {e}")
        send_store_dns_error_email_sync(instance, str(e))

def send_local_development_email_sync(store_instance, store_url):
    """Send welcome email for local development environment - SYNCHRONOUS"""
    try:
        # Import sendEmail function directly instead of using Celery task
        from setup.utils import sendEmail
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "store_name": store_instance.name,
            "store_domain": store_url,
            "environment": "LOCAL SERVER",
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "owner_email": store_instance.owner.email,
            "is_local": True,
            "note": "This store was created on a local development server. No AWS DNS records were created.",
        }
        
        # Use direct sendEmail function instead of Celery task
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_welcome_success.html',
            context=context,
            subject="🎉 Your Dropshipper Store Created (Local Server)",
            tags=["store-created", "local-server"]
        )
        
        logger.info(f"Local development email sent successfully to {store_instance.owner.email}")
        
    except Exception as e:
        logger.error(f"Error sending local development email: {e}")

def send_store_success_email_sync(store_instance, store_url, environment):
    """Send success email when store and DNS are created successfully - SYNCHRONOUS"""
    try:
        # Import sendEmail function directly instead of using Celery task
        from setup.utils import sendEmail
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "store_name": store_instance.name,
            "store_domain": store_url,
            "environment": environment.upper(),
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "owner_email": store_instance.owner.email,
            "is_local": False,
        }
        
        # Use direct sendEmail function instead of Celery task
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_welcome_success.html',
            context=context,
            subject="🎉 Your Dropshipper Store is Live – Welcome to RockTeaMall!",
            tags=["store-created", "domain-provisioned", "success"]
        )
        
        logger.info(f"Store success email sent successfully to {store_instance.owner.email}")
        
    except Exception as e:
        logger.error(f"Error sending store success email: {e}")

def send_store_dns_failure_email_sync(store_instance, attempted_domain):
    """Send email when DNS record creation fails - SYNCHRONOUS"""
    try:
        # Import sendEmail function directly instead of using Celery task
        from setup.utils import sendEmail
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "store_name": store_instance.name,
            "attempted_domain": attempted_domain,
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        # Use direct sendEmail function instead of Celery task
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_dns_failure.html',
            context=context,
            subject="⚠️ Store Created - Domain Setup in Progress",
            tags=["store-created", "dns-failure", "pending"]
        )
        
        logger.info(f"DNS failure email sent successfully to {store_instance.owner.email}")
        
    except Exception as e:
        logger.error(f"Error sending DNS failure email: {e}")

def send_store_dns_error_email_sync(store_instance, error_message):
    """Send email when DNS record creation encounters an error - SYNCHRONOUS"""
    try:
        # Import sendEmail function directly instead of using Celery task
        from setup.utils import sendEmail
        
        error_ref = f"DNS_ERROR_{store_instance.id}_{timezone.now().strftime('%Y%m%d_%H%M')}"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "store_name": store_instance.name,
            "store_id": store_instance.id,
            "error_reference": error_ref,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        # Use direct sendEmail function instead of using Celery task
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_dns_error.html',
            context=context,
            subject="🔧 Store Created - Technical Issue with Domain Setup",
            tags=["store-created", "dns-error", "technical-issue"]
        )
        
        logger.error(f"DNS error email sent. Error: {error_message}")
        
    except Exception as e:
        logger.error(f"Error sending DNS error email: {e}")

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
    """Delete DNS record when dropshipper is deleted - FIXED VERSION"""
    if not instance.is_store_owner:
        return
        
    try:
        # Get the store associated with this dropshipper
        if hasattr(instance, 'owners') and instance.owners:
            store = instance.owners
            
            # Only delete DNS if it was actually created
            if store.dns_record_created and store.slug:
                logger.info(f"Processing DNS deletion for dropshipper: {instance.email}, store: {store.name}")
                
                # Check if Celery is available and properly configured
                try:
                    from celery import current_app
                    if current_app.control.inspect().stats():
                        # Celery is running, use async task
                        from .tasks import delete_store_dns_async
                        result = delete_store_dns_async.delay(
                            store.slug, 
                            instance.email, 
                            store.name
                        )
                        logger.info(f"Queued DNS deletion task for store: {store.name} with task ID: {result.id}")
                    else:
                        # Celery not running, use sync processing
                        _delete_store_dns_sync(instance, store)
                except:
                    # Celery not available, use sync processing
                    _delete_store_dns_sync(instance, store)
            else:
                logger.info(f"No DNS record to delete for store: {store.name if store else 'Unknown'}")
                
    except Exception as e:
        logger.error(f"Error processing DNS deletion for dropshipper {instance.email}: {e}")
        # Fallback to synchronous processing
        try:
            if hasattr(instance, 'owners') and instance.owners:
                _delete_store_dns_sync(instance, instance.owners)
        except Exception as fallback_error:
            logger.error(f"Fallback DNS deletion also failed: {fallback_error}")

def _delete_store_dns_sync(user_instance, store_instance):
    """Synchronous DNS deletion fallback"""
    try:
        # Extract domain from domain_name for DNS deletion
        if store_instance.domain_name:
            domain_match = re.search(r'https://([^?]+)', store_instance.domain_name)
            if domain_match:
                full_domain = domain_match.group(1)
                success = delete_store_dns_record(full_domain)
            else:
                # Fallback to slug-based domain
                success = delete_store_dns_record(store_instance.slug)
        else:
            success = delete_store_dns_record(store_instance.slug)
        
        if success:
            logger.info(f"Successfully deleted DNS record for store: {store_instance.name}")
            send_store_deletion_email_sync(user_instance, store_instance)
        else:
            logger.error(f"Failed to delete DNS record for store: {store_instance.name}")
            send_store_deletion_failure_email_sync(user_instance, store_instance)
            
    except Exception as e:
        logger.error(f"Error in synchronous DNS deletion: {e}")
        send_store_deletion_failure_email_sync(user_instance, store_instance)

def send_store_deletion_email_sync(user_instance, store_instance):
    """Send email notification when store and domain are successfully deleted - SYNCHRONOUS"""
    try:
        # Import sendEmail function directly instead of using Celery task
        from setup.utils import sendEmail
        
        context = {
            "full_name": user_instance.get_full_name() or user_instance.first_name or user_instance.email,
            "store_name": store_instance.name,
            "store_domain": store_instance.domain_name,
            "deletion_date": timezone.now().strftime("%B %d, %Y at %I:%M %p"),
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        # Use direct sendEmail function instead of Celery task
        sendEmail(
            recipientEmail=user_instance.email,
            template_name='emails/store_deletion_success.html',
            context=context,
            subject="🗑️ Your Store Has Been Removed - RockTeaMall",
            tags=["store-deleted", "domain-removed", "account-closure"]
        )
        
        logger.info(f"Store deletion email sent successfully to {user_instance.email}")
        
    except Exception as e:
        logger.error(f"Error sending store deletion email: {e}")

def send_store_deletion_failure_email_sync(user_instance, store_instance):
    """Send email when DNS deletion fails - SYNCHRONOUS"""
    try:
        # Import sendEmail function directly instead of using Celery task
        from setup.utils import sendEmail
        
        context = {
            "full_name": user_instance.get_full_name() or user_instance.first_name or user_instance.email,
            "store_name": store_instance.name,
            "store_domain": store_instance.domain_name,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        # Use direct sendEmail function instead of Celery task
        sendEmail(
            recipientEmail=user_instance.email,
            template_name='emails/store_deletion_failure.html',
            context=context,
            subject="⚠️ Store Removal - Domain Cleanup Issue",
            tags=["store-deleted", "dns-cleanup-failed", "manual-intervention"]
        )
        
        logger.info(f"Store deletion failure email sent successfully to {user_instance.email}")
        
    except Exception as e:
        logger.error(f"Error sending store deletion failure email: {e}")
