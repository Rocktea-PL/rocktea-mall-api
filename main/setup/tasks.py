from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import requests
from .celery import app

logger = logging.getLogger(__name__)

@app.task(bind=True, default_retry_delay=300, max_retries=3)
def send_email_task(self, recipient_email: str, template_name: str, context: dict, subject: str, tags: list = None):
    """Optimized Celery task for sending emails via Brevo API"""
    try:
        # Render templates
        html_content = render_to_string(template_name, context)
        plain_text_content = strip_tags(html_content)

        # Prepare payload
        payload = {
            "sender": {
                "name": settings.SENDER_NAME,
                "email": settings.SENDER_EMAIL,
            },
            "to": [{"email": recipient_email}],
            "subject": subject,
            "htmlContent": html_content,
            "textContent": plain_text_content
        }
        
        if tags:
            payload["tags"] = tags

        # Send email
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers={
                "accept": "application/json",
                'api-key': settings.BREVO_API_KEY,
                "content-type": "application/json",
            },
            timeout=30  # Add timeout
        )
        response.raise_for_status()

        logger.info(f"Email sent to {recipient_email}: {subject} (Status: {response.status_code})")
        return response.json()
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Email failed to {recipient_email}: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Brevo API response: {e.response.text}")
        
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for email to {recipient_email}")
        return None
        
    except Exception as e:
        logger.error(f"Unexpected email error to {recipient_email}: {e}")
        return None

@app.task(bind=True, default_retry_delay=60, max_retries=3, queue='domains')
def create_store_domain_task(self, store_id):
    """Async task to create DNS record and update domain after payment confirmation"""
    logger.info(f"=== DOMAIN CREATION TASK STARTED for store_id: {store_id} ===")
    
    try:
        from mall.models import Store
        from mall.utils import determine_environment_config, generate_store_slug
        from workshop.route53 import create_cname_record
        from mall.signals import send_store_success_email, send_store_dns_failure_email, send_local_development_email
        
        store = Store.objects.get(id=store_id)
        logger.info(f"Found store: {store.name} (ID: {store_id})")
        
        if store.dns_record_created:
            logger.info(f"DNS already created for store: {store.name}")
            return f"DNS already exists for store: {store.name}"
        
        # Get environment config
        env_config = determine_environment_config(None)
        logger.info(f"Environment config: {env_config}")
        
        if env_config.get('is_local', False):
            # Local environment - set domain name and mark as created
            store.domain_name = f"http://localhost:8000?mall={store.id}"
            store.dns_record_created = True
            store.save(update_fields=['domain_name', 'dns_record_created'])
            send_local_development_email(store, store.domain_name)
            logger.info(f"Local domain setup completed for store: {store.name}")
            return f"Local domain created for store: {store.name}"
        
        # Generate full domain using slug
        if not store.slug:
            logger.error(f"No slug found for store {store.name}")
            return f"No slug for store: {store.name}"
            
        full_domain = f"{store.slug}.{env_config['target_domain']}"
        logger.info(f"Creating DNS record for domain: {full_domain}")
        
        # Create DNS record
        dns_result = create_cname_record(
            zone_id=env_config['hosted_zone_id'],
            subdomain=full_domain,
            target=env_config['target_domain']
        )
        
        logger.info(f"DNS creation result: {dns_result is not None}")
        
        if dns_result is not None:
            # DNS creation successful - now set domain name
            store.domain_name = f"https://{full_domain}?mall={store.id}"
            store.dns_record_created = True
            store.save(update_fields=['domain_name', 'dns_record_created'])
            logger.info(f"DNS record and domain name set for store: {store.name}")
            
            # Send success email
            send_store_success_email(store, store.domain_name, env_config['environment'])
            logger.info(f"Success email sent for store: {store.name}")
            
            return f"DNS and email sent for store: {store.name}"
        else:
            # DNS creation failed
            logger.error(f"DNS creation failed for store: {store.name}")
            send_store_dns_failure_email(store, full_domain)
            logger.info(f"Failure email sent for store: {store.name}")
            
            return f"DNS failed but email sent for store: {store.name}"
        
    except Store.DoesNotExist:
        logger.error(f"Store not found: {store_id}")
        return f"Store not found: {store_id}"
        
    except Exception as e:
        logger.error(f"Domain creation failed for store {store_id}: {e}", exc_info=True)
        try:
            self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for domain creation: {store_id}")
        return None

@app.task(bind=True, default_retry_delay=300, max_retries=3)
def log_webhook_attempt(self, reference, email, purpose, status):
    """Log webhook processing attempts for monitoring"""
    try:
        logger.info(f"Webhook processed - Ref: {reference}, Email: {email}, Purpose: {purpose}, Status: {status}")
        return f"Logged webhook: {reference}"
    except Exception as e:
        logger.error(f"Failed to log webhook {reference}: {e}")
        return None

__all__ = ['send_email_task', 'create_store_domain_task', 'log_webhook_attempt']