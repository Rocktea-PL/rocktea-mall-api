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
    """Generate a URL-safe slug from store name"""
    from django.utils.text import slugify
    return slugify(store_name.lower())


def determine_environment_config(request=None):
    """
    Determine environment configuration based on request or settings
    """
    # Default to development
    environment = 'dev'
    
    if request and hasattr(request, 'get_host'):
        host = request.get_host()
        if 'yourockteamall.com' in host and 'dev' not in host:
            environment = 'prod'
    
    # You can also check Django settings
    if settings.ENVIRONMENT == 'production':
        environment = 'prod'
    
    configs = {
        'dev': {
            'environment': 'dev',
            'target_domain': 'user-dev.yourockteamall.com',
            'hosted_zone_id': getattr(settings, 'ROUTE53_PRODUCTION_HOSTED_ZONE_ID', ''),
            'base_url': 'https://user-dev.yourockteamall.com'
        },
        'prod': {
            'environment': 'prod', 
            'target_domain': 'yourockteamall.com',
            'hosted_zone_id': getattr(settings, 'ROUTE53_PRODUCTION_HOSTED_ZONE_ID', ''),
            'base_url': 'https://yourockteamall.com'
        }
    }
    
    return configs.get(environment, configs['dev'])


def generate_store_domain(store_slug, environment='dev'):
    """Generate full domain name for a store"""
    config = determine_environment_config()
    if environment == 'prod':
        return f"{store_slug}.yourockteamall.com"
    else:
        return f"{store_slug}.user-dev.yourockteamall.com"


def get_store_from_request(request):
    """
    Helper function to get store from request
    """
    if hasattr(request, 'store') and request.store:
        return request.store
    
    # Fallback: try to get from user
    if hasattr(request, 'user') and request.user.is_authenticated:
        try:
            from .models import Store
            return Store.objects.get(owner=request.user)
        except Store.DoesNotExist:
            pass
    
    return None