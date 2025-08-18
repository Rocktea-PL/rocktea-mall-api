from enum import Enum
from django.db import models
from rest_framework import permissions

class PermissionType(models.TextChoices):
    # Product permissions
    PRODUCT_VIEW = 'product_view', 'Can view products'
    PRODUCT_ADD = 'product_add', 'Can add products'
    PRODUCT_EDIT = 'product_edit', 'Can edit products'
    PRODUCT_DELETE = 'product_delete', 'Can delete products'
    
    # Store permissions
    STORE_VIEW = 'store_view', 'Can view stores'
    STORE_EDIT = 'store_edit', 'Can edit stores'
    STORE_DELETE = 'store_delete', 'Can delete stores'
    
    # Order permissions
    ORDER_VIEW = 'order_view', 'Can view orders'
    ORDER_EDIT = 'order_edit', 'Can edit orders'
    ORDER_DELETE = 'order_delete', 'Can delete orders'
    
    # User permissions
    USER_VIEW = 'user_view', 'Can view users'
    USER_CREATE = 'user_create', 'Can create users'
    USER_EDIT = 'user_edit', 'Can edit users'
    USER_DELETE = 'user_delete', 'Can delete users'
    
    # Analytics permissions
    ANALYTICS_VIEW = 'analytics_view', 'Can view analytics'
    
    # System permissions
    SYSTEM_CONFIG = 'system_config', 'Can configure system'

class AdminRole(models.TextChoices):
    SUPER_ADMIN = 'super_admin', 'Super Admin'
    PRODUCT_ADMIN = 'product_admin', 'Product Admin'
    STORE_ADMIN = 'store_admin', 'Store Admin'
    ORDER_ADMIN = 'order_admin', 'Order Admin'
    USER_ADMIN = 'user_admin', 'User Admin'
    ANALYTICS_ADMIN = 'analytics_admin', 'Analytics Admin'

# Role-Permission mapping
ROLE_PERMISSIONS = {
    AdminRole.SUPER_ADMIN: [p[0] for p in PermissionType.choices],  # All permissions
    AdminRole.PRODUCT_ADMIN: [
        PermissionType.PRODUCT_VIEW,
        PermissionType.PRODUCT_ADD,
        PermissionType.PRODUCT_EDIT,
        PermissionType.PRODUCT_DELETE,
    ],
    AdminRole.STORE_ADMIN: [
        PermissionType.STORE_VIEW,
        PermissionType.STORE_EDIT,
        PermissionType.ORDER_VIEW,
    ],
    AdminRole.ORDER_ADMIN: [
        PermissionType.ORDER_VIEW,
        PermissionType.ORDER_EDIT,
        PermissionType.PRODUCT_VIEW,
    ],
    AdminRole.USER_ADMIN: [
        PermissionType.USER_VIEW,
        PermissionType.USER_CREATE,
        PermissionType.USER_EDIT,
    ],
    AdminRole.ANALYTICS_ADMIN: [
        PermissionType.ANALYTICS_VIEW,
        PermissionType.ORDER_VIEW,
        PermissionType.PRODUCT_VIEW,
        PermissionType.STORE_VIEW,
    ],
}

# DRF Permission Classes
class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow admin users to edit, others read-only"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.has_admin_access()

class IsAuthenticatedOrReadOnly(permissions.BasePermission):
    """Allow authenticated users to edit, others read-only"""
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated

class IsStoreOwnerOrAdminDelete(permissions.BasePermission):
    """Allow store owners or admins to delete"""
    def has_object_permission(self, request, view, obj):
        if request.method == 'DELETE':
            return (request.user.is_authenticated and 
                   (obj.owner == request.user or request.user.has_admin_access()))
        return True

class IsStoreOwnerOrAdminViewAdd(permissions.BasePermission):
    """Allow store owners or admins to view/add"""
    def has_permission(self, request, view):
        return request.user.is_authenticated and \
               (request.user.is_store_owner or request.user.has_admin_access())