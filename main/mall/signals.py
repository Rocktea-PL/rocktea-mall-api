from django.dispatch import receiver
from django.db.models.signals import post_save
from django.shortcuts import get_object_or_404
import logging

from .models import Store, Wallet, StoreProductPricing, MarketPlace, Notification
from .utils import determine_environment_config, generate_store_domain
from .middleware import get_current_request
from workshop.route53 import create_cname_record

from setup.utils import sendEmail
from django.utils import timezone

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Store)
def create_wallet(sender, instance, created, **kwargs):
    """Create Wallet for every Store"""
    if created:
        Wallet.objects.get_or_create(store=instance)

@receiver(post_save, sender=Store)
def create_store_dns_record(sender, instance, created, **kwargs):
    """Create DNS record for new stores"""
    if not created or instance.dns_record_created:
        return
        
    try:
        # Get environment configuration
        request = get_current_request()
        env_config = determine_environment_config(request)
        
        logger.info(f"Creating DNS record for store: {instance.name} (ID: {instance.id})")
        
        # Generate the subdomain
        full_domain = generate_store_domain(instance.slug, env_config['environment'])
        
        # Create DNS record
        response = create_cname_record(
            zone_id=env_config['hosted_zone_id'],
            subdomain=full_domain,
            target=env_config['target_domain']
        )
        
        if response:
            # Update store with DNS info
            instance.dns_record_created = True
            instance.save(update_fields=['dns_record_created'])

            # Build the clickable URL
            final_url = f"https://{full_domain}?mallcli={instance.id}"

            subject = "Your Dropshipper Store is Live – Welcome!"
            context = {
                "full_name": instance.owner.get_full_name() or instance.owner.email,
                "store_name": instance.name,
                "store_domain": final_url,
                'current_year': timezone.now().year,
            }
            sendEmail(
                recipientEmail=instance.owner.email,
                template_name='emails/store_welcome.html',
                context=context,
                subject=subject,
                tags=["store-created", "domain-provisioned"]
            )
        else:
            logger.error(f"Failed to create DNS record for store {instance.name}")
            
    except Exception as e:
        logger.error(f"Error creating DNS record for store {instance.name}: {e}")

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