from functools import wraps

def store_domain_required(view_func):
   @wraps(view_func)
   def wrapper(request, *args, **kwargs):
      request.store_domain = request.META.get("HTTP_HOST", None)
      return view_func(request, *args, **kwargs)
   return wrapper

# https://rocktea-users.vercel.app
