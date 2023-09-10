# middleware.py
from django.conf import settings
from django.contrib.sessions.models import Session
from django.utils import timezone

class DomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if the user is authenticated
        if request.user.is_authenticated:
            
            # Get the user's associated domain (assuming it's stored in the session)
            user_domain = request.session.get('user_domain', None)
            
            # If the associated domain is not in the session, fetch it from the user object
            if not user_domain:
                user = request.user
                if user.is_store_owner and user.associated_domain:
                    user_domain = user.associated_domain.domain_name
                    
                    # Store the domain name in the session for future requests
                    request.session['user_domain'] = user_domain
                    
            # Set the domain_name attribute on the request object
            request.domain_name = user_domain

        response = self.get_response(request)
        return response
    
    
# class DomainMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Extract the domain from the request (you may need to adjust this logic)
#         domain = request.get_host()

#         # Check if the user is authenticated (assuming you're using Django's authentication system)
#         if request.user.is_authenticated and not request.user.associated_domain:
#             # Associate the domain with the user
#             request.user.associated_domain = domain
#             request.user.save()

#         response = self.get_response(request)
#         return response

        