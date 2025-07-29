import threading

_thread_local = threading.local()

class RequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_local.request = request
        try:
            response = self.get_response(request)
        finally:
            # Clean up thread local data
            if hasattr(_thread_local, 'request'):
                delattr(_thread_local, 'request')
        return response

def get_current_request():
    """Get the current request from thread local storage."""
    return getattr(_thread_local, 'request', None)