from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from mall.permissions import AdminRole, PermissionType
from mall.admin_roles import AdminUserRole, AdminCustomPermission

User = get_user_model()

class MultiRoleAdminSystemTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        
        # Create super admin
        self.super_admin = User.objects.create_true_superuser(
            email='super@admin.com',
            password='super123'
        )
        
        # Create regular admin with multiple roles
        self.multi_admin = User.objects.create_user(
            email='multi@admin.com',
            password='admin123',
            is_staff=True,
            is_active_admin=True
        )
        
        # Assign multiple roles
        AdminUserRole.objects.create(
            user=self.multi_admin,
            role=AdminRole.PRODUCT_ADMIN,
            assigned_by=self.super_admin
        )
        AdminUserRole.objects.create(
            user=self.multi_admin,
            role=AdminRole.ORDER_ADMIN,
            assigned_by=self.super_admin
        )
        
        # Add custom permission
        AdminCustomPermission.objects.create(
            user=self.multi_admin,
            permission=PermissionType.ANALYTICS_VIEW,
            granted=True,
            assigned_by=self.super_admin
        )

    def test_super_admin_has_all_permissions(self):
        """Super admin should have all permissions"""
        self.assertTrue(self.super_admin.has_permission(PermissionType.PRODUCT_DELETE))
        self.assertTrue(self.super_admin.has_permission(PermissionType.USER_CREATE))
        self.assertTrue(self.super_admin.has_permission(PermissionType.SYSTEM_CONFIG))
        
        all_permissions = [p[0] for p in PermissionType.choices]
        self.assertEqual(set(self.super_admin.get_permissions()), set(all_permissions))

    def test_multi_role_admin_permissions(self):
        """Admin with multiple roles should have combined permissions"""
        # Should have product permissions
        self.assertTrue(self.multi_admin.has_permission(PermissionType.PRODUCT_VIEW))
        self.assertTrue(self.multi_admin.has_permission(PermissionType.PRODUCT_ADD))
        self.assertTrue(self.multi_admin.has_permission(PermissionType.PRODUCT_DELETE))
        
        # Should have order permissions
        self.assertTrue(self.multi_admin.has_permission(PermissionType.ORDER_VIEW))
        self.assertTrue(self.multi_admin.has_permission(PermissionType.ORDER_EDIT))
        
        # Should have custom permission
        self.assertTrue(self.multi_admin.has_permission(PermissionType.ANALYTICS_VIEW))
        
        # Should NOT have user management permissions
        self.assertFalse(self.multi_admin.has_permission(PermissionType.USER_CREATE))
        self.assertFalse(self.multi_admin.has_permission(PermissionType.USER_DELETE))

    def test_role_display_multiple_roles(self):
        """Role display should show multiple roles"""
        role_display = self.multi_admin.role_display
        self.assertIn('Product Admin', role_display)
        self.assertIn('Order Admin', role_display)

    def test_super_admin_can_create_admin(self):
        """Only super admin can create new admin users"""
        self.client.force_authenticate(user=self.super_admin)
        
        data = {
            'email': 'new@admin.com',
            'password': 'secure123',
            'first_name': 'New',
            'last_name': 'Admin',
            'roles': [AdminRole.STORE_ADMIN, AdminRole.ANALYTICS_ADMIN],
            'custom_permissions': [PermissionType.PRODUCT_VIEW]
        }
        
        response = self.client.post('/api/admin-management/admin-users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify user was created with correct roles
        new_admin = User.objects.get(email='new@admin.com')
        self.assertTrue(new_admin.is_active_admin)
        self.assertEqual(new_admin.admin_roles.count(), 2)
        self.assertEqual(new_admin.custom_permissions.count(), 1)
        
        # Verify permissions
        self.assertTrue(new_admin.has_permission(PermissionType.STORE_VIEW))
        self.assertTrue(new_admin.has_permission(PermissionType.ANALYTICS_VIEW))
        self.assertTrue(new_admin.has_permission(PermissionType.PRODUCT_VIEW))

    def test_regular_admin_cannot_create_admin(self):
        """Regular admin cannot create other admin users"""
        self.client.force_authenticate(user=self.multi_admin)
        
        data = {
            'email': 'blocked@admin.com',
            'password': 'secure123',
            'roles': [AdminRole.PRODUCT_ADMIN]
        }
        
        response = self.client.post('/api/admin-management/admin-users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_custom_permission_revoke(self):
        """Custom permissions can revoke role permissions"""
        # Add revoke permission
        AdminCustomPermission.objects.create(
            user=self.multi_admin,
            permission=PermissionType.PRODUCT_DELETE,
            granted=False,  # Revoke
            assigned_by=self.super_admin
        )
        
        # Should still have other product permissions
        self.assertTrue(self.multi_admin.has_permission(PermissionType.PRODUCT_VIEW))
        self.assertTrue(self.multi_admin.has_permission(PermissionType.PRODUCT_ADD))
        
        # Should NOT have delete permission (revoked)
        self.assertFalse(self.multi_admin.has_permission(PermissionType.PRODUCT_DELETE))

    def test_role_removal(self):
        """Removed roles should not grant permissions"""
        # Remove product admin role
        product_role = self.multi_admin.admin_roles.get(role=AdminRole.PRODUCT_ADMIN)
        product_role.delete()
        
        # Should lose product permissions
        self.assertFalse(self.multi_admin.has_permission(PermissionType.PRODUCT_DELETE))
        
        # Should keep order permissions
        self.assertTrue(self.multi_admin.has_permission(PermissionType.ORDER_VIEW))

    def test_regular_user_unaffected(self):
        """Regular users should not be affected by admin permission system"""
        regular_user = User.objects.create_user(
            email='regular@user.com',
            password='user123',
            is_store_owner=True
        )
        
        # Regular users should have access (existing functionality preserved)
        self.assertTrue(regular_user.has_permission(PermissionType.PRODUCT_VIEW))
        self.assertTrue(regular_user.has_permission('any_permission'))
        self.assertFalse(regular_user.is_admin_user())

class AdminCreationAPITest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.super_admin = User.objects.create_true_superuser(
            email='super@admin.com',
            password='super123'
        )

    def test_create_admin_with_multiple_roles_api(self):
        """Test creating admin with multiple roles via API"""
        self.client.force_authenticate(user=self.super_admin)
        
        data = {
            'email': 'multi@role.com',
            'password': 'secure123',
            'first_name': 'Multi',
            'last_name': 'Role',
            'roles': [
                AdminRole.PRODUCT_ADMIN,
                AdminRole.ORDER_ADMIN,
                AdminRole.ANALYTICS_ADMIN
            ],
            'custom_permissions': [
                PermissionType.STORE_VIEW,
                PermissionType.USER_VIEW
            ]
        }
        
        response = self.client.post('/api/admin-management/admin-users/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify created admin
        admin = User.objects.get(email='multi@role.com')
        self.assertEqual(admin.admin_roles.count(), 3)
        self.assertEqual(admin.custom_permissions.count(), 2)
        
        # Test combined permissions
        expected_permissions = set()
        expected_permissions.update([
            PermissionType.PRODUCT_VIEW, PermissionType.PRODUCT_ADD, 
            PermissionType.PRODUCT_EDIT, PermissionType.PRODUCT_DELETE,
            PermissionType.ORDER_VIEW, PermissionType.ORDER_EDIT,
            PermissionType.ANALYTICS_VIEW,
            PermissionType.STORE_VIEW, PermissionType.USER_VIEW
        ])
        
        actual_permissions = set(admin.get_permissions())
        self.assertTrue(expected_permissions.issubset(actual_permissions))