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

@app.task(bind=True, default_retry_delay=60, max_retries=3)
def create_store_domain_task(self, store_id):
    """Async task to create store domain after payment confirmation"""
    try:
        from mall.models import Store
        from mall.signals import create_store_domain_after_payment
        
        store = Store.objects.get(id=store_id)
        logger.info(f"Creating domain for store: {store.name} (ID: {store_id})")
        
        create_store_domain_after_payment(store)
        
        logger.info(f"Domain creation completed for store: {store.name}")
        return f"Domain created for store: {store.name}"
        
    except Store.DoesNotExist:
        logger.error(f"Store not found: {store_id}")
        return f"Store not found: {store_id}"
        
    except Exception as e:
        logger.error(f"Domain creation failed for store {store_id}: {e}")
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