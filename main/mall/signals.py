from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save, pre_delete
import logging
import re

from .models import Store, Wallet, StoreProductPricing, MarketPlace, Notification, CustomUser
from .utils import generate_store_slug, determine_environment_config
from .middleware import get_current_request
from workshop.route53 import create_cname_record, delete_store_dns_record

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
    """Create DNS record for new stores - only send email after DNS success"""
    if not created or instance.dns_record_created:
        return
        
    # Use transaction.on_commit to ensure email is sent after successful DB commit
    from django.db import transaction
    
    def send_store_email():
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
                # Only send email after DNS is successfully created
                send_store_success_email(instance, instance.domain_name, env_config['environment'])
            else:
                send_store_dns_failure_email(instance, full_domain)
                
        except Exception as e:
            logger.error(f"DNS creation failed for {instance.name}: {e}")
            send_store_dns_error_email(instance, str(e))
    
    # Schedule email sending after transaction commits
    transaction.on_commit(send_store_email)

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
    if not instance.is_store_owner:
        return
        
    try:
        # Get the store associated with this dropshipper
        if hasattr(instance, 'owners') and instance.owners:
            store = instance.owners
            
            # Store data before deletion for email
            user_email = instance.email
            user_name = instance.get_full_name() or instance.first_name or instance.email
            store_name = store.name
            store_domain = store.domain_name
            
            # Only delete DNS if it was actually created
            if store.dns_record_created and store.slug:
                logger.info(f"Processing DNS deletion for dropshipper: {user_email}, store: {store_name}")
                
                try:
                    success = delete_store_dns_record(store.slug)
                    
                    if success:
                        logger.info(f"Successfully deleted DNS record for store: {store_name}")
                        # Send success email after deletion
                        _send_deletion_success_email(user_email, user_name, store_name, store_domain)
                    else:
                        logger.error(f"Failed to delete DNS record for store: {store_name}")
                        _send_deletion_failure_email(user_email, user_name, store_name, store_domain)
                        
                except Exception as dns_error:
                    logger.error(f"DNS deletion error for store {store_name}: {dns_error}")
                    _send_deletion_failure_email(user_email, user_name, store_name, store_domain)
            else:
                logger.info(f"No DNS record to delete for store: {store_name}")
                
    except Exception as e:
        logger.error(f"Error in delete_dropshipper_domain for {instance.email}: {e}")


def _send_deletion_success_email(user_email, user_name, store_name, store_domain):
    """Send email notification when store and domain are successfully deleted"""
    from setup.email_service import send_store_deletion_email
    send_store_deletion_email(user_email, user_name, store_name, store_domain, success=True)
    logger.info(f"Store deletion email sent to {user_email} for store: {store_name}")

def _send_deletion_failure_email(user_email, user_name, store_name, store_domain):
    """Send email when DNS deletion fails"""
    from setup.email_service import send_store_deletion_email
    send_store_deletion_email(user_email, user_name, store_name, store_domain, success=False)
    logger.info(f"Store deletion failure email sent to {user_email} for store: {store_name}")