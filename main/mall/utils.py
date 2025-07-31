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
    Determine environment configuration based on request or settings
    """
    # Default to development
    environment = 'dev'
    
    # Check for localhost/development indicators first
    if _is_server_running_locally():
        return {
            'environment': 'local',
            'target_domain': None,
            'hosted_zone_id': '',
            'base_url': 'http://localhost:8000'
        }
    
    # If server is not local, determine environment from request or settings
    if request and hasattr(request, 'get_host'):
        host = request.get_host()
        
        # Check for dev environment
        if 'dev.yourockteamall.com' in host or 'dropshippers-dev.yourockteamall.com' in host:
            environment = 'dev'
        # Check for production domain  
        elif 'yourockteamall.com' in host and 'dev' not in host:
            environment = 'prod'
    
    # Also check Django settings as fallback
    if hasattr(settings, 'ENVIRONMENT'):
        if settings.ENVIRONMENT == 'production':
            environment = 'prod'
        elif settings.ENVIRONMENT == 'development':
            environment = 'dev'
    
    configs = {
        'local': {
            'environment': 'local',
            'target_domain': None,
            'hosted_zone_id': '',
            'base_url': 'http://localhost:8000'
        },
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

def _is_server_running_locally():
    """
    Check if the Django server itself is running locally
    """

    # Check for development-specific settings
    if hasattr(settings, 'ENVIRONMENT'):
        if settings.ENVIRONMENT == 'local':
            return True
    
    return False

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