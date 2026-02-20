from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .admin_serializers import AdminUserSerializer, CreateAdminUserSerializer, UserPermissionsSerializer
from .decorators import require_permission, log_admin_action, require_admin_access
from .permissions import PermissionType

User = get_user_model()

class AdminUserListCreateView(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateAdminUserSerializer
        return AdminUserSerializer
    
    def get_queryset(self):
        return User.objects.filter(is_active_admin=True).prefetch_related(
            'admin_roles', 'custom_permissions'
        ).order_by('-date_joined')
    
    @require_permission(PermissionType.USER_VIEW)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @require_permission(PermissionType.USER_CREATE)
    @log_admin_action('CREATE', 'USER')
    def post(self, request, *args, **kwargs):
        # Only superusers can create admin users
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can create admin users'}, 
                          status=status.HTTP_403_FORBIDDEN)
        return super().post(request, *args, **kwargs)

class AdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminUserSerializer
    
    def get_queryset(self):
        return User.objects.filter(is_active_admin=True)
    
    @require_permission(PermissionType.USER_VIEW)
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @require_permission(PermissionType.USER_EDIT)
    @log_admin_action('UPDATE', 'USER')
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)
    
    @require_permission(PermissionType.USER_EDIT)
    @log_admin_action('UPDATE', 'USER')
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    
    @require_permission(PermissionType.USER_DELETE)
    @log_admin_action('DELETE', 'USER')
    def delete(self, request, *args, **kwargs):
        # Only superusers can delete admin users
        if not request.user.is_superuser:
            return Response({'error': 'Only super admins can delete admin users'}, 
                          status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin_access
def user_permissions(request):
    """Get current user's permissions - admin only"""
    serializer = UserPermissionsSerializer(request.user)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@require_admin_access
@require_permission(PermissionType.USER_VIEW)
def available_roles(request):
    """Get available admin roles and their permissions - admin only"""
    from .permissions import AdminRole, ROLE_PERMISSIONS
    
    roles_data = []
    for role_key, role_name in AdminRole.choices:
        roles_data.append({
            'key': role_key,
            'name': role_name,
            'permissions': ROLE_PERMISSIONS.get(role_key, [])
        })
    
    return Response({'roles': roles_data})