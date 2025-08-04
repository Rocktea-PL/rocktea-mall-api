"""
Centralized email service for RockTea Mall
Handles all email operations with consistent templates and error handling
"""
from django.conf import settings
from django.utils import timezone
from django.template.loader import render_to_string
from django.utils.html import strip_tags
import logging
import requests
from typing import Dict, List, Optional
from .celery import app

logger = logging.getLogger(__name__)

# Email Templates Constants
class EmailTemplates:
    STORE_WELCOME_SUCCESS = 'emails/store_welcome_success.html'
    STORE_DNS_FAILURE = 'emails/store_dns_failure.html'
    STORE_DNS_ERROR = 'emails/store_dns_error.html'
    STORE_DELETION_SUCCESS = 'emails/store_deletion_success.html'
    STORE_DELETION_FAILURE = 'emails/store_deletion_failure.html'
    EMAIL_VERIFICATION = 'emails/email_verification.html'
    PASSWORD_RESET = 'emails/password_reset.html'
    ORDER_CONFIRMATION = 'emails/order_confirmation.html'

# Email Subjects Constants
class EmailSubjects:
    STORE_WELCOME = "🎉 Your Dropshipper Store is Live – Welcome to RockTeaMall!"
    STORE_LOCAL = "🎉 Your Dropshipper Store Created (Local Server)"
    STORE_DNS_PENDING = "⚠️ Store Created - Domain Setup in Progress"
    STORE_DNS_ERROR = "🔧 Store Created - Technical Issue with Domain Setup"
    STORE_DELETED = "🗑️ Your Store Has Been Removed - RockTeaMall"
    STORE_DELETE_ISSUE = "⚠️ Store Removal - Domain Cleanup Issue"

class EmailService:
    """Centralized email service with common context and error handling"""
    
    @staticmethod
    def get_base_context() -> Dict:
        """Get common context used in all emails"""
        return {
            'current_year': timezone.now().year,
            'support_email': 'support@yourockteamall.com',
            'company_name': 'RockTeaMall',
        }
    
    @staticmethod
    def get_user_context(user) -> Dict:
        """Get user-specific context"""
        return {
            'full_name': user.get_full_name() or user.first_name or user.email,
            'user_email': user.email,
        }
    
    @staticmethod
    def get_store_context(store) -> Dict:
        """Get store-specific context"""
        return {
            'store_name': store.name,
            'store_id': str(store.id),
            'store_domain': store.domain_name,
            **EmailService.get_user_context(store.owner)
        }
    
    @staticmethod
    def send_store_email(store, template: str, subject: str, extra_context: Dict = None, tags: List[str] = None):
        """Send store-related email with consistent context"""
        context = {
            **EmailService.get_base_context(),
            **EmailService.get_store_context(store),
            **(extra_context or {})
        }
        
        return send_email_task.delay(
            recipient_email=store.owner.email,
            template_name=template,
            context=context,
            subject=subject,
            tags=tags or []
        )
    
    @staticmethod
    def send_user_email(user, template: str, subject: str, extra_context: Dict = None, tags: List[str] = None):
        """Send user-related email with consistent context"""
        context = {
            **EmailService.get_base_context(),
            **EmailService.get_user_context(user),
            **(extra_context or {})
        }
        
        return send_email_task.delay(
            recipient_email=user.email,
            template_name=template,
            context=context,
            subject=subject,
            tags=tags or []
        )

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

# Convenience functions for common email types
def send_store_welcome_email(store, environment: str, is_local: bool = False):
    """Send store welcome email"""
    subject = EmailSubjects.STORE_LOCAL if is_local else EmailSubjects.STORE_WELCOME
    extra_context = {
        'environment': environment.upper(),
        'is_local': is_local,
    }
    if is_local:
        extra_context['note'] = "This store was created on a local development server. No AWS DNS records were created."
    
    tags = ["store-created", "local-server" if is_local else "domain-provisioned", "success"]
    
    return EmailService.send_store_email(
        store=store,
        template=EmailTemplates.STORE_WELCOME_SUCCESS,
        subject=subject,
        extra_context=extra_context,
        tags=tags
    )

def send_store_dns_failure_email(store, attempted_domain: str):
    """Send DNS failure email"""
    return EmailService.send_store_email(
        store=store,
        template=EmailTemplates.STORE_DNS_FAILURE,
        subject=EmailSubjects.STORE_DNS_PENDING,
        extra_context={'attempted_domain': attempted_domain},
        tags=["store-created", "dns-failure", "pending"]
    )

def send_store_dns_error_email(store, error_message: str):
    """Send DNS error email"""
    error_ref = f"DNS_ERROR_{store.id}_{timezone.now().strftime('%Y%m%d_%H%M')}"
    
    return EmailService.send_store_email(
        store=store,
        template=EmailTemplates.STORE_DNS_ERROR,
        subject=EmailSubjects.STORE_DNS_ERROR,
        extra_context={'error_reference': error_ref},
        tags=["store-created", "dns-error", "technical-issue"]
    )

def send_store_deletion_email(user_email: str, user_name: str, store_name: str, store_domain: str, success: bool = True):
    """Send store deletion email"""
    template = EmailTemplates.STORE_DELETION_SUCCESS if success else EmailTemplates.STORE_DELETION_FAILURE
    subject = EmailSubjects.STORE_DELETED if success else EmailSubjects.STORE_DELETE_ISSUE
    
    context = {
        **EmailService.get_base_context(),
        'full_name': user_name,
        'store_name': store_name,
        'store_domain': store_domain,
        'deletion_date': timezone.now().strftime("%B %d, %Y at %I:%M %p"),
    }
    
    tags = ["store-deleted", "domain-removed" if success else "dns-cleanup-failed", 
            "account-closure" if success else "manual-intervention"]
    
    return send_email_task.delay(
        recipient_email=user_email,
        template_name=template,
        context=context,
        subject=subject,
        tags=tags
    )