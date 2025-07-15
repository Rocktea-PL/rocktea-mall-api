import requests
from django.conf import settings
import logging
logger = logging.getLogger(__name__)

def sendEmail(recipientEmail, content, subject):
    try:
        url = "https://api.brevo.com/v3/smtp/email"

        payload = {
            "sender": {
                "name": settings.SENDER_NAME,
                "email": settings.SENDER_EMAIL,
            },
            "to": [
                {
                    "email": recipientEmail
                }
            ],
            "subject": subject,
            "htmlContent": content,
            "tags": ["welcome-email", "dropshipper-onboarding"]
        }
        headers = {
            "accept": "application/json",
            'api-key': settings.BREVO_API_KEY,
            "content-type": "application/json",

        }

        response = requests.post(url, json=payload, headers=headers)

        logger.info(f"Email sent to {recipientEmail}: {response.status_code}")

        print(response.text)
    except Exception as e:
        logger.error(f"Email sending failed: {str(e)}")
        return None