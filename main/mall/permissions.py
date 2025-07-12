from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to only allow admin users to create objects.
    """

    def has_permission(self, request, view):
        # Allow read-only access for any request
        if request.method in SAFE_METHODS:
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

class IsStoreOwnerOrAdminDelete(BasePermission):
    """
    Custom permission to only allow store owners and admin users to delete objects.
    """

    def has_permission(self, request, view):
        # Allow delete access only for store owners and admin users
        if request.method == 'DELETE':
            return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_store_owner)
        # Allow read-only access for any request
        if request.method in SAFE_METHODS:
            return True
        return False

class IsStoreOwnerOrAdminViewAdd(BasePermission):
    """
    Custom permission to only allow store owners and admin users to view and add objects.
    """

    def has_permission(self, request, view):
        # Allow view and add access only for store owners and admin users
        if request.method in ('GET', 'POST'):
            return request.user and request.user.is_authenticated and (request.user.is_staff or request.user.is_store_owner)
        # Allow read-only access for any request
        if request.method in SAFE_METHODS:
            return True
        return False