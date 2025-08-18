# Multi-Role Admin System Design

## Architecture Overview

### 1. Database Schema
```
CustomUser
├── is_superuser (Boolean) - Full system access
├── is_active_admin (Boolean) - Can access admin functions
└── Relationships:
    ├── admin_roles (Many-to-Many via AdminUserRole)
    └── custom_permissions (One-to-Many via AdminCustomPermission)

AdminUserRole
├── user (FK to CustomUser)
├── role (Choice: product_admin, store_admin, etc.)
├── assigned_by (FK to CustomUser - who assigned this role)
└── assigned_at (DateTime)

AdminCustomPermission
├── user (FK to CustomUser)
├── permission (Choice: product_view, product_add, etc.)
├── granted (Boolean) - True=grant, False=revoke
├── assigned_by (FK to CustomUser)
└── assigned_at (DateTime)
```

### 2. Permission Resolution Logic
```python
def get_permissions(user):
    if user.is_superuser:
        return ALL_PERMISSIONS
    
    permissions = set()
    
    # 1. Aggregate from all assigned roles
    for role in user.admin_roles.all():
        permissions.update(ROLE_PERMISSIONS[role.role])
    
    # 2. Apply custom permissions (grants/revokes)
    for custom in user.custom_permissions.all():
        if custom.granted:
            permissions.add(custom.permission)
        else:
            permissions.discard(custom.permission)
    
    return list(permissions)
```

## API Design

### Create Admin with Multiple Roles
```json
POST /api/admin-management/admin-users/
{
  "email": "admin@example.com",
  "password": "secure123",
  "first_name": "Multi",
  "last_name": "Admin",
  "roles": ["product_admin", "order_admin"],
  "custom_permissions": ["analytics_view", "store_view"]
}
```

### Response
```json
{
  "id": "uuid",
  "email": "admin@example.com",
  "role_display": "Product Admin, Order Admin",
  "assigned_roles": ["product_admin", "order_admin"],
  "permissions": [
    "product_view", "product_add", "product_edit", "product_delete",
    "order_view", "order_edit", "analytics_view", "store_view"
  ]
}
```

## Security Features

### 1. Super Admin Control
- Only `is_superuser=True` users can create/modify admin users
- All role assignments tracked with `assigned_by` field
- Audit trail for all admin actions

### 2. Permission Hierarchy
```
Super Admin (is_superuser=True)
├── All permissions automatically
├── Can create/delete any admin
└── Cannot be restricted

Multi-Role Admin (is_active_admin=True)
├── Permissions from assigned roles
├── Custom permissions (grants/revokes)
├── Can be restricted by super admin
└── Cannot create other admins

Regular User (is_active_admin=False)
├── Existing functionality preserved
├── Not affected by admin permission system
└── Cannot access admin endpoints
```

### 3. Permission Examples

**Product + Order Admin:**
```python
user.admin_roles = ["product_admin", "order_admin"]
user.permissions = [
    "product_view", "product_add", "product_edit", "product_delete",
    "order_view", "order_edit", "product_view"  # from order_admin
]
```

**Custom Permission Override:**
```python
# Grant additional permission
AdminCustomPermission(user=user, permission="analytics_view", granted=True)

# Revoke role permission
AdminCustomPermission(user=user, permission="product_delete", granted=False)

# Final permissions: product_view, product_add, product_edit, order_view, order_edit, analytics_view
```

## Usage Examples

### 1. Create Specialized Admin
```python
# Super admin creates product manager with analytics access
POST /api/admin-management/admin-users/
{
  "email": "product.manager@company.com",
  "roles": ["product_admin"],
  "custom_permissions": ["analytics_view", "store_view"]
}
```

### 2. Create Multi-Department Admin
```python
# Admin handling both products and orders
POST /api/admin-management/admin-users/
{
  "email": "operations@company.com", 
  "roles": ["product_admin", "order_admin", "store_admin"]
}
```

### 3. Assign/Remove Roles
```python
# Assign additional role
POST /api/admin-management/assign-role/
{
  "user_id": "admin-user-id",
  "role": "analytics_admin"
}

# Remove role
DELETE /api/admin-management/remove-role/
{
  "user_id": "admin-user-id",
  "role": "product_admin"
}
```

## Migration Strategy

### 1. Database Migration
```python
# Add new models
python manage.py makemigrations mall
python manage.py migrate

# Migrate existing single-role admins
python manage.py shell
>>> from mall.models import CustomUser
>>> from mall.admin_roles import AdminUserRole
>>> 
>>> # Convert existing admin_role to AdminUserRole
>>> for user in CustomUser.objects.filter(admin_role__isnull=False):
>>>     AdminUserRole.objects.create(
>>>         user=user,
>>>         role=user.admin_role,
>>>         assigned_by=None  # System migration
>>>     )
```

### 2. API Compatibility
- Old single-role APIs still work
- New multi-role APIs available
- Gradual migration path

## Testing Strategy

### 1. Unit Tests
- Permission aggregation logic
- Role assignment/removal
- Custom permission grants/revokes
- Super admin privilege preservation

### 2. Integration Tests
- API endpoint security
- Multi-role admin creation
- Permission-based access control
- Regular user functionality preservation

### 3. Security Tests
- Unauthorized admin creation attempts
- Permission escalation prevention
- Audit trail verification

This design provides maximum flexibility while maintaining security and backward compatibility.