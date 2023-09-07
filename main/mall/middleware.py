# middleware.py

class DomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Extract the domain from the request (you may need to adjust this logic)
        domain = request.get_host()

        # Check if the user is authenticated (assuming you're using Django's authentication system)
        if request.user.is_authenticated and not request.user.associated_domain:
            # Associate the domain with the user
            request.user.associated_domain = domain
            request.user.save()

        response = self.get_response(request)
        return response

        