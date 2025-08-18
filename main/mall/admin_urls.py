from django.urls import path
from .admin_views import (
    AdminUserListCreateView, AdminUserDetailView, 
    user_permissions, available_roles
)
from .admin_role_management import assign_role, remove_role

urlpatterns = [
    path('admin-users/', AdminUserListCreateView.as_view(), name='admin-users-list'),
    path('admin-users/<str:pk>/', AdminUserDetailView.as_view(), name='admin-user-detail'),
    path('user-permissions/', user_permissions, name='user-permissions'),
    path('available-roles/', available_roles, name='available-roles'),
    path('assign-role/', assign_role, name='assign-role'),
    path('remove-role/', remove_role, name='remove-role'),
]