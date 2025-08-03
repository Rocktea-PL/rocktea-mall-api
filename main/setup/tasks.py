from .celery import app
import logging

import requests
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags

logger = logging.getLogger(__name__)

@app.task(bind=True, default_retry_delay=300, max_retries=3) # bind=True allows task to access self (for retries)
def send_email_task(self, recipient_email: str, template_name: str, context: dict, subject: str, tags: list = None):
   """
   Celery task to send an email using Brevo API, rendering content from a Django template.
   This task will be run in the background.
   """
   try:
      url = "https://api.brevo.com/v3/smtp/email"

      html_content = render_to_string(template_name, context)
      plain_text_content = strip_tags(html_content)

      payload = {
         "sender": {
               "name": settings.SENDER_NAME,
               "email": settings.SENDER_EMAIL,
         },
         "to": [
               {
                  "email": recipient_email
               }
         ],
         "subject": subject,
         "htmlContent": html_content,
         "textContent": plain_text_content
      }
      if tags:                     
         payload["tags"] = tags
      headers = {
         "accept": "application/json",
         'api-key': settings.BREVO_API_KEY,
         "content-type": "application/json",
      }

      response = requests.post(url, json=payload, headers=headers)
      response.raise_for_status()

      logger.info(f"Email sent successfully to {recipient_email} for subject '{subject}' (Status: {response.status_code})")
      return response.json()
   except requests.exceptions.RequestException as e:
      logger.error(f"Email sending failed to {recipient_email} via Brevo API: {e}")
      if hasattr(e, 'response') and e.response is not None:
         logger.error(f"Brevo API error response: {e.response.text}")
      # Retry the task on request failures
      try:
         self.retry(exc=e)
      except self.MaxRetriesExceededError:
         logger.error(f"Max retries exceeded for email to {recipient_email}. Task failed permanently.")
         # Optionally, send an alert to an admin here
      return None
   except Exception as e:
      logger.error(f"An unexpected error occurred during email sending to {recipient_email}: {str(e)}")
      # Do not retry for unexpected errors unless specifically needed
      return None