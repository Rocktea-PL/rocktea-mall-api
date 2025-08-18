from django.db import models
from django.conf import settings
from .permissions import AdminRole, PermissionType

class AdminUserRole(models.Model):
    """Many-to-many relationship for admin users and their roles"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_roles')
    role = models.CharField(max_length=20, choices=AdminRole.choices)
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='assigned_roles')
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'role']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return f"{self.user.email} - {self.role}"

class AdminCustomPermission(models.Model):
    """Custom permissions for admin users beyond their roles"""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='custom_permissions')
    permission = models.CharField(max_length=20, choices=PermissionType.choices)
    granted = models.BooleanField(default=True)  # True=grant, False=revoke
    assigned_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    assigned_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'permission']
        indexes = [
            models.Index(fields=['user', 'granted']),
        ]
    
    def __str__(self):
        action = "Grant" if self.granted else "Revoke"
        return f"{action} {self.permission} for {self.user.email}"