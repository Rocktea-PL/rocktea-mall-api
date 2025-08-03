from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.conf import settings

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
    Determine the environment configuration based on request or settings.
    """
    # Check ENVIRONMENT setting first
    environment = getattr(settings, 'ENVIRONMENT', 'local')
    
    # Handle local environment - no AWS DNS creation
    if environment in ['local', 'localhost']:
        return {
            'environment': 'local',
            'target_domain': None,
            'hosted_zone_id': '',
            'is_local': True
        }
    
    # Try to get environment from request first
    if request:
        current_domain = request.get_host()
        if "dropshippers-dev.yourockteamall.com" in current_domain:
            return {
                'target_domain': 'user-dev.yourockteamall.com',
                'hosted_zone_id': getattr(settings, 'ROUTE53_PRODUCTION_HOSTED_ZONE_ID', ''),
                'environment': 'dev',
                'is_local': False
            }
        elif "dropshippers.yourockteamall.com" in current_domain:
            return {
                'target_domain': 'yourockteamall.com',
                'hosted_zone_id': getattr(settings, 'ROUTE53_PRODUCTION_HOSTED_ZONE_ID', ''),
                'environment': 'prod',
                'is_local': False
            }
    
    # Fallback to settings-based determination
    if environment in ['prod', 'production']:
        return {
            'target_domain': 'yourockteamall.com',
            'hosted_zone_id': getattr(settings, 'ROUTE53_PRODUCTION_HOSTED_ZONE_ID', ''),
            'environment': 'prod',
            'is_local': False
        }
    
    # Default to dev
    return {
        'target_domain': 'user-dev.yourockteamall.com',
        'hosted_zone_id': getattr(settings, 'ROUTE53_PRODUCTION_HOSTED_ZONE_ID', ''),
        'environment': 'dev',
        'is_local': False
    }

def generate_store_domain(store_slug, environment='dev'):
    """Generate full domain name for a store"""
    if environment == 'local':
        return "http://localhost:8000"
    elif environment == 'prod':
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
