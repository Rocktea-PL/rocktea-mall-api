from .models import MainUser 

class TenantMiddleware:
   def __init__(self, get_response):
      self.get_response=get_response
      
   def __call__(self, request):
        # Extract the tenant identifier from the request, e.g., from the domain name
        # Logic here to identify the tenant
        domain = request.get_host()
        
        