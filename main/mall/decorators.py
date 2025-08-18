from functools import wraps
from rest_framework.response import Response
from rest_framework import status
from .permissions import PermissionType
from .admin_audit import AdminAuditLog

def require_admin_access(view_func):
    """Decorator to restrict access to admin users only"""
    @wraps(view_func)
    def wrapper(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, 
                          status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.has_admin_access():
            return Response({'error': 'Admin access required'}, 
                          status=status.HTTP_403_FORBIDDEN)
        
        return view_func(self, request, *args, **kwargs)
    return wrapper

def require_permission(permission):
    """Decorator to check if user has specific permission"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, 
                              status=status.HTTP_401_UNAUTHORIZED)
            
            # First check if user is admin
            if not request.user.has_admin_access():
                return Response({'error': 'Admin access required'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            if not request.user.has_permission(permission):
                # Log unauthorized access attempt
                AdminAuditLog.objects.create(
                    admin_user=request.user,
                    action='VIEW',
                    resource_type=permission.split('_')[0].upper(),
                    details={'permission_denied': permission, 'endpoint': request.path},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                return Response({'error': 'Insufficient permissions'}, 
                              status=status.HTTP_403_FORBIDDEN)
            
            return view_func(self, request, *args, **kwargs)
        return wrapper
    return decorator

def log_admin_action(action, resource_type):
    """Decorator to log admin actions"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            response = view_func(self, request, *args, **kwargs)
            
            if request.user.is_authenticated and request.user.has_admin_access():
                resource_id = kwargs.get('pk') or kwargs.get('id')
                AdminAuditLog.objects.create(
                    admin_user=request.user,
                    action=action,
                    resource_type=resource_type,
                    resource_id=str(resource_id) if resource_id else None,
                    details={'status_code': response.status_code},
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
            
            return response
        return wrapper
    return decorator