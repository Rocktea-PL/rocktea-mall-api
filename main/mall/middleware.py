import threading
import logging

_thread_local = threading.local()
logger = logging.getLogger(__name__)

class RequestMiddleware:
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
    """
    Middleware to handle subdomain routing and store identification.
    Updated for your specific domain structure.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract subdomain information
        host = request.get_host()
        
        # Parse the host to extract subdomain
        subdomain_info = self.parse_subdomain(host)
        
        # Add subdomain info to request
        request.subdomain = subdomain_info['subdomain']
        request.domain = subdomain_info['domain']
        request.is_subdomain = subdomain_info['is_subdomain']
        request.environment = subdomain_info['environment']
        
        logger.info(f"Request host: {host}, subdomain: {request.subdomain}, environment: {request.environment}")
        
        # If it's a store subdomain, try to find the store
        if request.is_subdomain and request.subdomain:
            try:
                from .models import Store
                
                # Look for store by domain name (contains the full URL)
                full_domain_https = f"https://{host}"
                store = Store.objects.filter(
                    domain_name__icontains=host
                ).first()
                
                if not store:
                    # Try to find by mallcli parameter if present
                    mall_id = request.GET.get('mallcli')
                    if mall_id:
                        store = Store.objects.filter(id=mall_id).first()
                        logger.info(f"Found store by mallcli parameter: {store}")
                
                request.store = store
                if store:
                    logger.info(f"Found store: {store.name} (ID: {store.id})")
                else:
                    logger.warning(f"No store found for host: {host}")
                
            except Exception as e:
                logger.error(f"Error finding store for host {host}: {e}")
                request.store = None
        else:
            request.store = None
        
        response = self.get_response(request)
        return response
    
    def parse_subdomain(self, host):
        """
        Parse the host to extract subdomain information.
        Updated for your specific domain structure.
        """
        # Remove port if present
        host = host.split(':')[0]
        
        # Define your base domains based on your setup
        domain_configs = [
            {
                'domain': 'user-dev.yourockteamall.com',
                'environment': 'dev',
                'is_store_domain': True
            },
            {
                'domain': 'yourockteamall.com', 
                'environment': 'prod',
                'is_store_domain': True
            },
            {
                'domain': 'dropshippers.yourockteamall.com',
                'environment': 'prod',
                'is_store_domain': False
            },
            {
                'domain': 'dropshippers-dev.yourockteamall.com',
                'environment': 'dev', 
                'is_store_domain': False
            }
        ]
        
        for config in domain_configs:
            base_domain = config['domain']
            
            if host == base_domain:
                # This is the main domain, no subdomain
                return {
                    'subdomain': None,
                    'domain': base_domain,
                    'is_subdomain': False,
                    'environment': config['environment'],
                    'is_store_domain': config['is_store_domain']
                }
            elif host.endswith('.' + base_domain):
                # This is a subdomain
                subdomain = host[:-len('.' + base_domain)]
                return {
                    'subdomain': subdomain,
                    'domain': base_domain,
                    'is_subdomain': True,
                    'environment': config['environment'],
                    'is_store_domain': config['is_store_domain']
                }
        
        # If no match found, treat as unknown
        return {
            'subdomain': None,
            'domain': host,
            'is_subdomain': False,
            'environment': 'unknown',
            'is_store_domain': False
        }