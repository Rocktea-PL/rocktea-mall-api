# Admin System Usage Guide

## Key Changes Made

### 1. Existing Admins Keep Full Access
- All existing `is_staff=True` users automatically get SUPER_ADMIN role
- `create_superuser` now creates admins with full privileges
- No disruption to existing admin functionality

### 2. User/Dropshipper Protection
- Permission system only applies to admin users
- Regular users and dropshippers keep all existing functionality
- No changes to existing user workflows

### 3. Admin-Only Endpoints
- All admin management endpoints require `has_admin_access()`
- Regular users cannot access admin management features
- Proper separation between admin and user functionality

## URL Structure

### Admin Management URLs (Admin Only)
```
/api/admin-management/admin-users/           # List/Create admin users
/api/admin-management/admin-users/{id}/      # Admin user details
/api/admin-management/user-permissions/      # Current user permissions
/api/admin-management/available-roles/       # Available roles
```

## Creating New Admin Users

### 1. Create True Superuser (System Admin)
```bash
python manage.py create_true_superuser \
  --email superadmin@example.com \
  --password secure123
```

### 2. Create Role-Based Admin (API)
```python
# Only existing superusers can create new admins via API
POST /api/admin-management/admin-users/
{
  "email": "product@admin.com",
  "password": "secure123",
  "first_name": "Product",
  "last_name": "Admin",
  "admin_role": "product_admin",
  "is_active_admin": true
}
```

## Permission Checking

### Backend (Only for Admin Endpoints)
```python
from mall.decorators import require_admin_access, require_permission
from mall.permissions import PermissionType

# Restrict to admin users only
@require_admin_access
def admin_only_view(request):
    pass

# Restrict to specific admin permission
@require_permission(PermissionType.PRODUCT_DELETE)
def delete_product(request):
    pass
```

### Frontend (Admin Panel Only)
```typescript
// Check if user is admin
const { user } = useAuth();
if (!user.has_admin_access) {
  return <AccessDenied />;
}

// Check specific permission
<ProtectedComponent permission="product_add">
  <AddProductButton />
</ProtectedComponent>
```

## Migration Required

```bash
python manage.py makemigrations mall
python manage.py migrate

# Update existing admins to have full privileges
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> User.objects.filter(is_staff=True, is_active_admin=False).update(
...     is_active_admin=True, 
...     admin_role='super_admin'
... )
```

## Security Features

1. **Admin Isolation**: Admin endpoints completely separated from user endpoints
2. **Existing Admin Protection**: All current admins keep full access
3. **User Functionality Preserved**: No impact on dropshippers/consumers
4. **Audit Logging**: All admin actions logged for security
5. **Role-Based Restrictions**: New admins can be limited to specific functions

## Example Usage

### Regular User (Unchanged)
```python
# Dropshippers and consumers work exactly as before
user.is_store_owner  # Still works
user.create_store()  # Still works
user.place_order()  # Still works
```

### Admin User
```python
# Existing admins
user.is_staff = True  # Keeps all access
user.has_permission('product_delete')  # Returns True

# New role-based admin
user.admin_role = 'product_admin'
user.has_permission('product_delete')  # Returns True
user.has_permission('user_delete')     # Returns False
```

This system maintains backward compatibility while adding granular admin controls.