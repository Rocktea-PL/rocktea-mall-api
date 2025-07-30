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
            # Send success email
            send_store_success_email(instance, final_url, env_config['environment'])
        else:
            logger.error(f"Failed to create DNS record for store {instance.name}")
            # Send failure email
            send_store_dns_failure_email(instance, full_domain)
            
    except Exception as e:
        logger.error(f"Error creating DNS record for store {instance.name}: {e}")
        # Send error email
        send_store_dns_error_email(instance, str(e))
        # Don't raise the exception to prevent store creation from failing

def send_store_success_email(store_instance, store_url, environment):
    """Send success email when store and DNS are created successfully"""
    try:
        subject = "🎉 Your Dropshipper Store is Live – Welcome to RockTeaMall!"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "first_name": store_instance.owner.first_name or "there",
            "store_name": store_instance.name,
            "store_domain": store_url,
            "store_slug": store_instance.slug,
            "environment": environment.upper(),
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "owner_email": store_instance.owner.email,
        }
        
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_welcome_success.html',
            context=context,
            subject=subject,
            tags=["store-created", "domain-provisioned", "success"]
        )
        
        logger.info(f"Success email sent to {store_instance.owner.email} for store: {store_instance.name}")
        
    except Exception as e:
        logger.error(f"Error sending success email for store {store_instance.name}: {e}")


def send_store_dns_failure_email(store_instance, attempted_domain):
    """Send email when DNS record creation fails"""
    try:
        subject = "⚠️ Store Created - Domain Setup in Progress"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "first_name": store_instance.owner.first_name or "there",
            "store_name": store_instance.name,
            "attempted_domain": attempted_domain,
            "store_id": store_instance.id,
            "current_year": timezone.now().year,
            "support_email": "support@yourockteamall.com",
        }
        
        sendEmail(
            recipientEmail=store_instance.owner.email,
            template_name='emails/store_dns_failure.html',
            context=context,
            subject=subject,
            tags=["store-created", "dns-failure", "pending"]
        )
        
        logger.info(f"DNS failure email sent to {store_instance.owner.email} for store: {store_instance.name}")
        
    except Exception as e:
        logger.error(f"Error sending DNS failure email for store {store_instance.name}: {e}")


def send_store_dns_error_email(store_instance, error_message):
    """Send email when DNS record creation encounters an error"""
    try:
        subject = "🔧 Store Created - Technical Issue with Domain Setup"
        
        # Create a sanitized error reference
        error_ref = f"DNS_ERROR_{store_instance.id}_{timezone.now().strftime('%Y%m%d_%H%M')}"
        
        context = {
            "full_name": store_instance.owner.get_full_name() or store_instance.owner.first_name or store_instance.owner.email,
            "first_name": store_instance.owner.first_name or "there",
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
            tags=["store-created", "dns-error", "technical-issue"]
        )
        
        # Also log the full error for debugging
        logger.error(f"DNS error email sent to {store_instance.owner.email} for store: {store_instance.name}. Error: {error_message}")
        
    except Exception as e:
        logger.error(f"Error sending DNS error email for store {store_instance.name}: {e}")

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