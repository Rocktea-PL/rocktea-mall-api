"""
Domain utilities for multi-domain support
"""
import logging
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site

logger = logging.getLogger(__name__)

def extract_primary_domain(current_domain):
    """
    Extract primary domain from current site domain
    Examples:
        api.staging.rockteapl.com -> rockteapl.com
        api.yourockteamall.com -> yourockteamall.com
        localhost -> yourockteamall.com (default)
    """
    if 'localhost' in current_domain or '127.0.0.1' in current_domain:
        return 'yourockteamall.com'  # Default for local
    
    # Remove api. and staging. prefixes
    domain_parts = current_domain.replace('api.', '').replace('staging.', '').split('.')
    
    # Get last two parts (domain.com)
    if len(domain_parts) >= 2:
        return '.'.join(domain_parts[-2:])
    
    return 'yourockteamall.com'  # Fallback


def get_store_frontend_url(store, subdomain_type='user', request=None):
    """
    Get the correct frontend URL for a store based on multi-domain configuration
    
    Args:
        store: Store instance
        subdomain_type: 'user', 'dropshipper', or 'admin'
        request: Django request object (optional, used to detect domain)
    
    Returns:
        str: Full frontend URL (e.g., https://store-name.staging.rockteapl.com)
    """
    # Determine environment
    environment = getattr(settings, 'ENVIRONMENT', 'local')
    
    # Get primary domain from current site
    if request:
        current_site = get_current_site(request).domain
        primary_domain = extract_primary_domain(current_site)
        is_staging = 'staging' in current_site
    else:
        primary_domain = 'yourockteamall.com'
        is_staging = environment == 'dev'
    
    if environment == 'local':
        # Local development
        if subdomain_type == 'user':
            return f"http://localhost:3000"
        elif subdomain_type == 'dropshipper':
            return f"http://localhost:3002"
        elif subdomain_type == 'admin':
            return f"http://localhost:3005"
    
    # Build production/staging URL
    protocol = 'https'
    staging_prefix = 'staging.' if is_staging else ''
    
    if subdomain_type == 'user':
        base_url = f"{protocol}://{store.domain_name}.{staging_prefix}{primary_domain}"
    elif subdomain_type == 'dropshipper':
        base_url = f"{protocol}://dropshippers.{staging_prefix}{primary_domain}"
    elif subdomain_type == 'admin':
        base_url = f"{protocol}://admin.{staging_prefix}{primary_domain}"
    
    return base_url


def get_verification_url(user, token, request=None):
    """
    Get the correct verification URL based on user type and domain
    
    Args:
        user: CustomUser instance
        token: Verification token
        request: Django request object (optional)
    
    Returns:
        str: Full verification URL
    """
    environment = getattr(settings, 'ENVIRONMENT', 'local')
    
    # Get primary domain from current site
    if request:
        current_site = get_current_site(request).domain
        primary_domain = extract_primary_domain(current_site)
        is_staging = 'staging' in current_site
    else:
        primary_domain = 'yourockteamall.com'
        is_staging = environment == 'dev'
    
    # Determine subdomain based on user type
    if user.is_store_owner:
        subdomain = 'dropshippers'
    elif user.is_admin or user.is_superuser:
        subdomain = 'admin'
    else:
        subdomain = 'user'
    
    if environment == 'local':
        if subdomain == 'dropshippers':
            base_url = "http://localhost:3002"
        elif subdomain == 'admin':
            base_url = "http://localhost:3005"
        else:
            base_url = "http://localhost:3000"
    else:
        staging_prefix = 'staging.' if is_staging else ''
        base_url = f"https://{subdomain}.{staging_prefix}{primary_domain}"
    
    return f"{base_url}/verify-email?token={token}"
