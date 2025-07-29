from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
import re
from django.utils.text import slugify

class EmailVerificationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        return f"{user.pk}{timestamp}{user.is_verified}"

    @property
    def timeout(self):
        return settings.EMAIL_VERIFICATION_TIMEOUT
    
def generate_store_slug(store_name):
    """
    Generate a clean, DNS-safe slug from store name.
    """
    # Remove special characters and convert to lowercase
    slug = slugify(store_name).replace('_', '-').lower()
    
    # Ensure it starts and ends with alphanumeric characters
    slug = re.sub(r'^[^a-z0-9]+|[^a-z0-9]+$', '', slug)
    
    # Replace multiple consecutive hyphens with single hyphen
    slug = re.sub(r'-+', '-', slug)
    
    # Ensure minimum length and maximum length for DNS
    if len(slug) < 3:
        slug = f"store-{slug}"
    if len(slug) > 63:  # DNS label limit
        slug = slug[:63].rstrip('-')
    
    return slug

def determine_environment_config(request=None):
    """
    Determine the environment configuration based on request or settings.
    """
    from django.conf import settings
    
    # Try to get environment from request first
    if request:
        current_domain = request.get_host()
        if "dropshippers-dev.yourockteamall.com" in current_domain:
            return {
                'target_domain': 'user-dev.yourockteamall.com',
                'hosted_zone_id': settings.ROUTE53_DEV_HOSTED_ZONE_ID,
                'environment': 'dev'
            }
        elif "dropshippers.yourockteamall.com" in current_domain:
            return {
                'target_domain': 'yourockteamall.com',
                'hosted_zone_id': settings.ROUTE53_PRODUCTION_HOSTED_ZONE_ID,
                'environment': 'prod'
            }
    
    # Fallback to settings-based determination
    if hasattr(settings, 'ENVIRONMENT'):
        if settings.ENVIRONMENT == 'production':
            return {
                'target_domain': 'yourockteamall.com',
                'hosted_zone_id': settings.ROUTE53_PRODUCTION_HOSTED_ZONE_ID,
                'environment': 'prod'
            }
    
    # Default to dev
    return {
        'target_domain': 'user-dev.yourockteamall.com',
        'hosted_zone_id': settings.ROUTE53_DEV_HOSTED_ZONE_ID,
        'environment': 'dev'
    }