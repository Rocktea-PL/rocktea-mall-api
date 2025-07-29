from django.dispatch import receiver
from django.db.models.signals import post_save, pre_save
from django.shortcuts import get_object_or_404
import logging

from .models import Store, Wallet, StoreProductPricing, MarketPlace, Notification
from .utils import generate_store_slug, determine_environment_config
from .middleware import get_current_request
from workshop.route53 import create_cname_record

logger = logging.getLogger(__name__)

@receiver(pre_save, sender=Store)
def generate_store_domain_info(sender, instance, **kwargs):
    """
    Generate domain information before saving the store.
    This ensures consistency and happens only once.
    """
    if not instance.domain_name and not instance.dns_record_created:
        # Generate slug from store name
        slug = generate_store_slug(instance.name)
        
        # Get environment configuration
        request = get_current_request()
        env_config = determine_environment_config(request)
        
        # Generate full domain
        full_domain = f"{slug}.{env_config['target_domain']}"
        instance.domain_name = f"https://{full_domain}?mallcli={instance.id}"
        
        logger.info(f"Generated domain for store {instance.name}: {instance.domain_name}")

@receiver(post_save, sender=Store)
def create_wallet(sender, instance, created, **kwargs):
    """Create Wallet for every Store"""
    if created:
        Wallet.objects.get_or_create(store=instance)

@receiver(post_save, sender=Store)
def create_dropshipper_dns_record(sender, instance, created, **kwargs):
    """Create DNS record for new stores"""
    if created and not instance.dns_record_created:
        try:
            # Get environment configuration
            request = get_current_request()
            env_config = determine_environment_config(request)
            
            logger.info(f"Creating DNS record for store: {instance.name} in {env_config['environment']} environment")
            
            # Extract subdomain from the already generated domain_name
            if instance.domain_name:
                # Parse the subdomain from the domain_name
                import re
                domain_match = re.search(r'https://([^?]+)', instance.domain_name)
                if domain_match:
                    full_domain = domain_match.group(1)
                else:
                    # Fallback: generate it again
                    slug = generate_store_slug(instance.name)
                    full_domain = f"{slug}.{env_config['target_domain']}"
            else:
                # Generate it if somehow missing
                slug = generate_store_slug(instance.name)
                full_domain = f"{slug}.{env_config['target_domain']}"
                instance.domain_name = f"https://{full_domain}?mallcli={instance.id}"
            
            # Create DNS record
            response = create_cname_record(
                zone_id=env_config['hosted_zone_id'],
                subdomain=full_domain,
                target=env_config['target_domain']
            )
            
            if response:
                # Update store with DNS info
                instance.dns_record_created = True
                instance.save(update_fields=['dns_record_created', 'domain_name'])
                
                logger.info(f"Successfully created DNS record for store {instance.id}: {full_domain} -> {env_config['target_domain']}")
            else:
                logger.error(f"Failed to create DNS record for store {instance.name}")
                
        except Exception as e:
            logger.error(f"Error creating DNS record for store {instance.name}: {e}")
            # Don't raise the exception to prevent store creation from failing
            # You might want to implement a retry mechanism here

@receiver(post_save, sender=StoreProductPricing)
def create_marketplace(sender, instance, created, **kwargs):
    if created:
        related_product = instance.product
        related_store_id = instance.store.id

        # Fetch the store object first
        store = get_object_or_404(Store, id=related_store_id)

        # Now we can create the MarketPlace object
        MarketPlace.objects.get_or_create(store=store, product=related_product)
        
        # Create Notification with the correct store name
        notification_message = f"{store.name} you just added a new product to your Marketplace."
        Notification.objects.create(store=store, message=notification_message)