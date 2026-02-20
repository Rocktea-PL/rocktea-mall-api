from django.http import HttpResponse

class BlockWebDAVMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.blocked_methods = [
            'PROPFIND', 'PROPPATCH', 'MKCOL', 'COPY', 'MOVE', 
            'LOCK', 'UNLOCK', 'TRACE'
        ]

    def __call__(self, request):
        if request.method in self.blocked_methods:
            return HttpResponse('Method not allowed', status=405)
        return self.get_response(request)