from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admin users to create objects.
    """

    def has_permission(self, request, view):
        # Allow read-only access for any request
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        # Allow create access only for admin users
        return request.user and request.user.is_staff

class IsAuthenticatedOrReadOnly(BasePermission):
    """
    Custom permission to only allow authenticated users to create objects.
    """

    def has_permission(self, request, view):
        # Allow read-only access for any request
        if request.method in SAFE_METHODS:
            return True
        # Allow create access only for authenticated users
        return request.user and request.user.is_authenticated