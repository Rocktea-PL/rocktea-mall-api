from typing import Optional
import hmac
import hashlib
import json
import logging
from dataclasses import dataclass

@dataclass
class WebhookPayload:
    """Data class to store parsed webhook payload data."""
    event: str
    data: dict
    raw_body: dict

class WebhookProcessor:
    """Process and validate Paystack webhook requests."""
    
    def __init__(self, payload: bytes, signature: str, secret: str):
        """
        Initialize the webhook processor.
        
        Args:
            payload (bytes): Raw webhook payload
            signature (str): Paystack signature header
            secret (str): Secret key for signature verification
        """
        self.payload = payload
        self.signature = signature
        self.secret = secret
        self._body: Optional[dict] = None
        self._event: Optional[str] = None

    @property
    def body(self) -> Optional[dict]:
        """Get the parsed webhook body."""
        return self._body

    @property
    def event(self) -> Optional[str]:
        """Get the webhook event type."""
        return self._event

    def verify_signature(self) -> bool:
        """
        Verify the Paystack signature.
        
        Returns:
            bool: True if signature is valid, False otherwise
        """
        try:
            calculated_hash = hmac.new(
                self.secret.encode('utf-8'),
                self.payload,
                digestmod=hashlib.sha512
            ).hexdigest()
            return hmac.compare_digest(calculated_hash, self.signature)
        except Exception as e:
            logging.error(f"Signature verification failed: {e}")
            return False

    def parse_payload(self) -> bool:
        """
        Parse the webhook payload.
        
        Returns:
            bool: True if payload was parsed successfully, False otherwise
        """
        try:
            body_unicode = self.payload.decode('utf-8')
            self._body = json.loads(body_unicode)
            self._event = self._body['event']
            return True
        except (ValueError, KeyError) as e:
            logging.error(f"Failed to parse payload: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error parsing payload: {e}")
            return False

    def get_parsed_payload(self) -> Optional[WebhookPayload]:
        """
        Get the parsed webhook payload as a structured object.
        
        Returns:
            Optional[WebhookPayload]: Parsed payload or None if parsing failed
        """
        if self._body and self._event:
            return WebhookPayload(
                event=self._event,
                data=self._body.get('data', {}),
                raw_body=self._body
            )
        return None