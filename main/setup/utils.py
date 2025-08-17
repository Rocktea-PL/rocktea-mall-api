from django.conf import settings
import logging
from .tasks import send_email_task

logger = logging.getLogger(__name__)

def get_store_domain(request):
   return request.META.get("HTTP_ORIGIN")

# Backward compatibility wrapper - use EmailService directly for new code
def sendEmail(recipientEmail: str, template_name: str, context: dict, subject: str, tags: list = None):
    """
    DEPRECATED: Use EmailService.send_user_email() or EmailService.send_store_email() instead
    Dispatches an email sending task to Celery for background processing.
    """
    try:
        task_result = send_email_task.delay(
            recipient_email=recipientEmail,
            template_name=template_name,
            context=context,
            subject=subject,
            tags=tags
        )
        logger.info(f"Email task {task_result.id} dispatched for {recipientEmail}: {subject}")
        return task_result.id
    except Exception as e:
        logger.error(f"Failed to dispatch email task for {recipientEmail}: {e}")
        return None