from django.utils.functional import SimpleLazyObject
from mall.models import Store

def get_current_store(request):
    user_data = getattr(request, 'user_data', None)
    
    if user_data and 'store_id' in user_data:
        store_id = user_data['store_id']
        try:
            return Store.objects.get(id=store_id)
        except Store.DoesNotExist:
            pass
    return None


class StoreMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # print(request.user_data)  # Debugging output
        request.store = SimpleLazyObject(lambda: get_current_store(request))
        response = self.get_response(request)
        return response
