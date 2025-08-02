from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
from django.shortcuts import get_object_or_404
import logging
import re

from .models import Store, Wallet, StoreProductPricing, MarketPlace, Notification, CustomUser
from .utils import generate_store_slug, determine_environment_config
from .middleware import get_current_request
from workshop.route53 import create_cname_record, delete_store_dns_record

from setup.utils import sendEmail
from django.utils import timezone
from django.conf import settings

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
    """Create DNS record for new stores"""
    if not created or instance.dns_record_created:
        return
        
    env_config = determine_environment_config(get_current_request())
    
    # Handle local environment
    if env_config.get('is_local', False):
        send_local_development_email(instance, instance.domain_name)
        return
    
    # Extract domain from domain_name for DNS creation
    domain_match = re.search(r'https://([^?]+)', instance.domain_name or '')
    if not domain_match:
        logger.error(f"Invalid domain_name for store {instance.name}")
        return
        
    full_domain = domain_match.group(1)
    
    try:
        # Create DNS record
        if create_cname_record(
            zone_id=env_config['hosted_zone_id'],
            subdomain=full_domain,
            target=env_config['target_domain']
        ):
            instance.dns_record_created = True
            instance.save(update_fields=['dns_record_created'])
            send_store_success_email(instance, instance.domain_name, env_config['environment'])
        else:
            send_store_dns_failure_email(instance, full_domain)
            
    except Exception as e:
        logger.error(f"DNS creation failed for {instance.name}: {e}")
        send_store_dns_error_email(instance, str(e))

def send_local_development_email(store_instance, store_url):
    """Send welcome email for local development environment"""
    try:
        from setup.tasks import send_email_task
        
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
        
        send_email_task.delay(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_welcome_success.html',
            context=context,
            subject="🎉 Your Dropshipper Store Created (Local Server)",
            tags=["store-created", "local-server"]
        )
        
        logger.info(f"Local development email queued for {store_instance.owner.email}")
        
    except Exception as e:
        logger.error(f"Error sending local development email: {e}")


def send_store_success_email(store_instance, store_url, environment):
    """Send success email when store and DNS are created successfully"""
    try:
        from setup.tasks import send_email_task
        
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
        
        result = send_email_task.delay(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_welcome_success.html',
            context=context,
            subject="🎉 Your Dropshipper Store is Live – Welcome to RockTeaMall!",
            tags=["store-created", "domain-provisioned", "success"]
        )
        
        logger.info(f"Store success email queued for {store_instance.owner.email}")
        
    except Exception as e:
        logger.error(f"Error sending store success email: {e}")


def send_store_dns_failure_email(store_instance, attempted_domain):
    """Send email when DNS record creation fails"""
    try:
        from setup.tasks import send_email_task
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "store_name": store_instance.name,
            "attempted_domain": attempted_domain,
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        send_email_task.delay(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_dns_failure.html',
            context=context,
            subject="⚠️ Store Created - Domain Setup in Progress",
            tags=["store-created", "dns-failure", "pending"]
        )
        
        logger.info(f"DNS failure email queued for {store_instance.owner.email}")
        
    except Exception as e:
        logger.error(f"Error sending DNS failure email: {e}")


def send_store_dns_error_email(store_instance, error_message):
    """Send email when DNS record creation encounters an error"""
    try:
        from setup.tasks import send_email_task
        
        error_ref = f"DNS_ERROR_{store_instance.id}_{timezone.now().strftime('%Y%m%d_%H%M')}"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "store_name": store_instance.name,
            "store_id": store_instance.id,
            "error_reference": error_ref,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        send_email_task.delay(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_dns_error.html',
            context=context,
            subject="🔧 Store Created - Technical Issue with Domain Setup",
            tags=["store-created", "dns-error", "technical-issue"]
        )
        
        logger.error(f"DNS error email queued. Error: {error_message}")
        
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
    """Delete DNS record when dropshipper is deleted using async task for better performance"""
    if not instance.is_store_owner:
        return
        
    try:
        # Get the store associated with this dropshipper
        if hasattr(instance, 'owners') and instance.owners:
            store = instance.owners
            
            # Only delete DNS if it was actually created
            if store.dns_record_created and store.slug:
                logger.info(f"Queuing DNS deletion for dropshipper: {instance.email}, store: {store.name}")
                
                # Check if Celery is available
                if hasattr(settings, 'CELERY_BROKER_URL') and settings.CELERY_BROKER_URL:
                    # Use async task for better performance
                    from .tasks import delete_store_dns_async
                    delete_store_dns_async.delay(
                        store.slug, 
                        instance.email, 
                        store.name
                    )
                    logger.info(f"Queued DNS deletion task for store: {store.name}")
                else:
                    # Fallback to synchronous processing
                    logger.info(f"Celery not configured, processing DNS deletion synchronously")
                    _delete_store_dns_sync(instance, store)
            else:
                logger.info(f"No DNS record to delete for store: {store.name if store else 'Unknown'}")
                
    except Exception as e:
        logger.error(f"Error queuing DNS deletion for dropshipper {instance.email}: {e}")
        # Fallback to synchronous processing if available
        try:
            if hasattr(instance, 'owners') and instance.owners:
                _delete_store_dns_sync(instance, instance.owners)
        except:
            pass


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
            send_store_deletion_email(user_instance, store_instance)
        else:
            logger.error(f"Failed to delete DNS record for store: {store_instance.name}")
            send_store_deletion_failure_email(user_instance, store_instance)
            
    except Exception as e:
        logger.error(f"Error in synchronous DNS deletion: {e}")
        send_store_deletion_failure_email(user_instance, store_instance)


def send_store_deletion_email(user_instance, store_instance):
    """Send email notification when store and domain are successfully deleted"""
    try:
        from setup.tasks import send_email_task
        
        context = {
            "full_name": user_instance.get_full_name() or user_instance.first_name or user_instance.email,
            "store_name": store_instance.name,
            "store_domain": store_instance.domain_name,
            "deletion_date": timezone.now().strftime("%B %d, %Y at %I:%M %p"),
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        send_email_task.delay(
            recipientEmail=user_instance.email,
            template_name='emails/store_deletion_success.html',
            context=context,
            subject="🗑️ Your Store Has Been Removed - RockTeaMall",
            tags=["store-deleted", "domain-removed", "account-closure"]
        )
        
        logger.info(f"Store deletion email queued for {user_instance.email}")
        
    except Exception as e:
        logger.error(f"Error sending store deletion email: {e}")


def send_store_deletion_failure_email(user_instance, store_instance):
    """Send email when DNS deletion fails"""
    try:
        from setup.tasks import send_email_task
        
        context = {
            "full_name": user_instance.get_full_name() or user_instance.first_name or user_instance.email,
            "store_name": store_instance.name,
            "store_domain": store_instance.domain_name,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        send_email_task.delay(
            recipientEmail=user_instance.email,
            template_name='emails/store_deletion_failure.html',
            context=context,
            subject="⚠️ Store Removal - Domain Cleanup Issue",
            tags=["store-deleted", "dns-cleanup-failed", "manual-intervention"]
        )
        
        logger.info(f"Store deletion failure email queued for {user_instance.email}")
        
    except Exception as e:
        logger.error(f"Error sending store deletion failure email: {e}")