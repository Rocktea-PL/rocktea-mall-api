from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .admin_roles import AdminUserRole
from .permissions import AdminRole
from .decorators import require_admin_access

User = get_user_model()

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@require_admin_access
def assign_role(request):
    """Assign role to admin user - super admin only"""
    if not request.user.is_superuser:
        return Response({'error': 'Only super admin can assign roles'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    user_id = request.data.get('user_id')
    role = request.data.get('role')
    
    if not user_id or not role:
        return Response({'error': 'user_id and role required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    if role not in [choice[0] for choice in AdminRole.choices]:
        return Response({'error': 'Invalid role'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id, is_active_admin=True)
    except User.DoesNotExist:
        return Response({'error': 'Admin user not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    
    # Create role assignment
    role_obj, created = AdminUserRole.objects.get_or_create(
        user=user,
        role=role,
        defaults={'assigned_by': request.user}
    )
    
    if created:
        return Response({'message': f'Role {role} assigned to {user.email}'})
    else:
        return Response({'message': f'Role {role} already assigned to {user.email}'})

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
@require_admin_access
def remove_role(request):
    """Remove role from admin user - super admin only"""
    if not request.user.is_superuser:
        return Response({'error': 'Only super admin can remove roles'}, 
                       status=status.HTTP_403_FORBIDDEN)
    
    user_id = request.data.get('user_id')
    role = request.data.get('role')
    
    if not user_id or not role:
        return Response({'error': 'user_id and role required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(id=user_id, is_active_admin=True)
        role_obj = AdminUserRole.objects.get(user=user, role=role)
        role_obj.delete()
        return Response({'message': f'Role {role} removed from {user.email}'})
    except User.DoesNotExist:
        return Response({'error': 'Admin user not found'}, 
                       status=status.HTTP_404_NOT_FOUND)
    except AdminUserRole.DoesNotExist:
        return Response({'error': 'Role assignment not found'}, 
                       status=status.HTTP_404_NOT_FOUND)