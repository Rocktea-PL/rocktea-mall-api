from rest_framework import serializers
from django.contrib.auth import get_user_model
from .permissions import AdminRole, PermissionType, ROLE_PERMISSIONS
from .admin_roles import AdminUserRole, AdminCustomPermission

User = get_user_model()

class AdminUserSerializer(serializers.ModelSerializer):
    permissions = serializers.SerializerMethodField()
    role_display = serializers.ReadOnlyField()
    assigned_roles = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'is_active_admin', 
            'is_staff', 'is_superuser', 'permissions', 'role_display', 
            'assigned_roles', 'last_login', 'date_joined'
        ]
        read_only_fields = ['id', 'last_login', 'date_joined']
    
    def get_permissions(self, obj):
        return obj.get_permissions()
    
    def get_assigned_roles(self, obj):
        return obj.get_assigned_roles()

class CreateAdminUserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    roles = serializers.ListField(
        child=serializers.ChoiceField(choices=AdminRole.choices),
        write_only=True,
        required=True
    )
    custom_permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=PermissionType.choices),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'first_name', 'last_name', 
            'is_active_admin', 'roles', 'custom_permissions'
        ]
    
    def create(self, validated_data):
        roles = validated_data.pop('roles', [])
        custom_permissions = validated_data.pop('custom_permissions', [])
        password = validated_data.pop('password')
        
        # Create user
        validated_data['is_staff'] = True
        validated_data['is_active_admin'] = True
        user = User.objects.create_user(password=password, **validated_data)
        
        # Assign roles
        request_user = self.context['request'].user
        for role in roles:
            AdminUserRole.objects.create(
                user=user,
                role=role,
                assigned_by=request_user
            )
        
        # Assign custom permissions
        for permission in custom_permissions:
            AdminCustomPermission.objects.create(
                user=user,
                permission=permission,
                granted=True,
                assigned_by=request_user
            )
        
        return user

class UserPermissionsSerializer(serializers.Serializer):
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=PermissionType.choices),
        read_only=True
    )
    role = serializers.CharField(read_only=True)
    can_access_admin = serializers.BooleanField(read_only=True)
    
    def to_representation(self, instance):
        return {
            'permissions': instance.get_permissions(),
            'role': instance.role_display,
            'can_access_admin': instance.has_admin_access()
        }