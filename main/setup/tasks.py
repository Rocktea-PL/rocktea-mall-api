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

__all__ = ['send_email_task']