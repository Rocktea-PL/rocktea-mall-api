import threading
import logging

_thread_local = threading.local()
logger = logging.getLogger(__name__)


class RequestMiddleware:
    """Store request in thread local storage for signals"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.request = request
        try:
            response = self.get_response(request)
        finally:
            if hasattr(_thread_local, 'request'):
                delattr(_thread_local, 'request')
        return response


def get_current_request():
    """Get the current request from thread local storage."""
    return getattr(_thread_local, 'request', None)


class SubdomainMiddleware:
    """Simple subdomain middleware for store identification"""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract host information
        host = request.get_host().split(':')[0]  # Remove port if present
        
        # Initialize request attributes
        request.store = None
        request.subdomain = None
        request.is_store_subdomain = False
        
        # Check if this is a store subdomain
        if self._is_store_subdomain(host):
            subdomain = self._extract_subdomain(host)
            request.subdomain = subdomain
            request.is_store_subdomain = True
            
            # Try to find the store
            store = self._find_store_by_subdomain(subdomain, request)
            request.store = store
            
            if store:
                logger.info(f"Found store: {store.name} for subdomain: {subdomain}")
            # Remove warning log for missing stores - it's normal for API endpoints
        
        response = self.get_response(request)
        return response
    
    def _is_store_subdomain(self, host):
        """Check if host is a store subdomain"""
        # Skip API domains and dropshipper admin domains
        api_domains = [
            'api.yourockteamall.com',
            'api-dev.yourockteamall.com',
            'dropshippers.yourockteamall.com',
            'dropshippers-dev.yourockteamall.com'
        ]
        
        if host in api_domains:
            return False
            
        store_domains = [
            'yourockteamall.com',
            'user-dev.yourockteamall.com'
        ]
        
        for domain in store_domains:
            if host.endswith('.' + domain) and host != domain:
                return True
        return False
    
    def _extract_subdomain(self, host):
        """Extract subdomain from host"""
        if host.endswith('.user-dev.yourockteamall.com'):
            return host.replace('.user-dev.yourockteamall.com', '')
        elif host.endswith('.yourockteamall.com'):
            return host.replace('.yourockteamall.com', '')
        return None
    
    def _find_store_by_subdomain(self, subdomain, request):
        """Find store by subdomain or mallcli parameter"""
        if not subdomain:
            return None
            
        try:
            from .models import Store
            
            # First try to find by slug
            store = Store.objects.filter(slug=subdomain).first()
            
            if not store:
                # Try to find by mallcli parameter
                mall_id = request.GET.get('mallcli')
                if mall_id:
                    store = Store.objects.filter(id=mall_id).first()
            
            return store
            
        except Exception as e:
            # Don't log errors for API endpoints - they're expected to not have stores
            return None