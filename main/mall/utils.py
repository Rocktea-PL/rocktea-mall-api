from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings
import re
from django.utils.text import slugify
from .models import Store

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

def get_store_from_request(request):
    """
    Get store from request based on subdomain or mallcli parameter.
    """
    # First check if middleware already found the store
    if hasattr(request, 'store') and request.store:
        return request.store
    
    # Fallback: try to find by mallcli parameter
    mall_id = request.GET.get('mallcli')
    if mall_id:
        try:
            return Store.objects.get(id=mall_id)
        except Store.DoesNotExist:
            pass
    
    # Fallback: try to find by host
    host = request.get_host()
    try:
        return Store.objects.filter(domain_name__icontains=host).first()
    except:
        pass
    
    return None

def determine_environment_config(request=None):
    """
    Determine the environment configuration based on request or settings.
    Updated for your specific setup.
    """
    
    # Try to get environment from request first
    if request and hasattr(request, 'environment'):
        if request.environment == 'dev':
            return {
                'target_domain': 'user-dev.yourockteamall.com',
                'hosted_zone_id': settings.ROUTE53_DEV_HOSTED_ZONE_ID,
                'environment': 'dev'
            }
        elif request.environment == 'prod':
            return {
                'target_domain': 'yourockteamall.com',
                'hosted_zone_id': settings.ROUTE53_PRODUCTION_HOSTED_ZONE_ID,
                'environment': 'prod'
            }
    
    # Try to get environment from request host
    if request:
        current_domain = request.get_host()
        if "user-dev.yourockteamall.com" in current_domain or "dropshippers-dev.yourockteamall.com" in current_domain:
            return {
                'target_domain': 'user-dev.yourockteamall.com',
                'hosted_zone_id': settings.ROUTE53_DEV_HOSTED_ZONE_ID,
                'environment': 'dev'
            }
        elif "yourockteamall.com" in current_domain:
            return {
                'target_domain': 'yourockteamall.com',
                'hosted_zone_id': settings.ROUTE53_PRODUCTION_HOSTED_ZONE_ID,
                'environment': 'prod'
            }
    
    # Fallback to settings-based determination
    if hasattr(settings, 'PRODUCTION') and settings.PRODUCTION:
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