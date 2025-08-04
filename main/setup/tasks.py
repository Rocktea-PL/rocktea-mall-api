# This file is deprecated - email functionality moved to setup/email_service.py
# Import the new email service for backward compatibility
from .email_service import send_email_task

# Re-export for backward compatibility
__all__ = ['send_email_task']