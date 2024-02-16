"""
    Middleware to get host name from server.
"""
from .models import Store

class DomainNameMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extracting the domain name from the request
        domain_name = request.META.get('HTTP_ORIGIN', None)

        # Storing the domain name in request object for further use
        request.domain_name = domain_name

        response = self.get_response(request)

        return response