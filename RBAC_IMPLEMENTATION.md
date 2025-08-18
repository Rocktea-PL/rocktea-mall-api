# Role-Based Access Control (RBAC) Implementation

## System Architecture

### 1. Multi-Role Hierarchy
```
Super Admin (is_superuser=True)
├── Full system access
├── Can assign/remove any roles
└── Creates all admin users

Multi-Role Admin (is_active_admin=True)
├── Can have multiple roles simultaneously
├── Product Admin + Order Admin + Analytics Admin
├── Permissions aggregated from all assigned roles
└── Custom permissions can grant/revoke specific access

Regular User (unchanged)
├── Dropshippers, consumers unaffected
└── Existing functionality preserved
```

### 2. Permission System
- **Multi-Role Support**: Admins can have multiple roles simultaneously
- **Permission Aggregation**: Combines permissions from all assigned roles
- **Custom Permissions**: Fine-grained grants/revokes beyond roles
- **Super Admin Control**: Only super admin can assign/remove roles
- **Secure by Default**: Regular users unaffected by admin system

### 3. Security Features
- **Audit Logging**: All admin actions logged with IP, user agent, timestamp
- **Role Assignment Tracking**: Who assigned what role to whom
- **Super Admin Protection**: Cannot be restricted by permission system
- **Admin Isolation**: Admin endpoints separated from user endpoints

## API Endpoints

### Admin Management
```
GET    /api/admin-management/admin-users/           # List admin users
POST   /api/admin-management/admin-users/           # Create multi-role admin (super admin only)
GET    /api/admin-management/admin-users/{id}/      # Get admin user details
PUT    /api/admin-management/admin-users/{id}/      # Update admin user
DELETE /api/admin-management/admin-users/{id}/     # Delete admin user (super admin only)
GET    /api/admin-management/user-permissions/      # Get current user permissions
GET    /api/admin-management/available-roles/       # Get available roles
POST   /api/admin-management/assign-role/           # Assign role (super admin only)
DELETE /api/admin-management/remove-role/           # Remove role (super admin only)
```

### Product Management (Example)
```python
# In your product views, add decorators:
@require_permission(PermissionType.PRODUCT_VIEW)
def list_products(self, request):
    # Product listing logic

@require_permission(PermissionType.PRODUCT_ADD)
@log_admin_action('CREATE', 'PRODUCT')
def create_product(self, request):
    # Product creation logic
```

## Next.js Frontend Integration

### 1. Permission Context
```typescript
// contexts/PermissionContext.tsx
interface PermissionContextType {
  permissions: string[];
  role: string;
  canAccess: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

export const usePermissions = () => {
  const context = useContext(PermissionContext);
  return context;
};
```

### 2. Protected Components
```typescript
// components/ProtectedComponent.tsx
interface ProtectedComponentProps {
  permission: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const ProtectedComponent: React.FC<ProtectedComponentProps> = ({
  permission,
  fallback = <div>Access Denied</div>,
  children
}) => {
  const { canAccess } = usePermissions();
  
  if (!canAccess(permission)) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
};
```

### 3. Route Protection
```typescript
// middleware.ts
export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token');
  const permissions = getUserPermissions(token);
  
  // Check route permissions
  if (request.nextUrl.pathname.startsWith('/admin/products')) {
    if (!permissions.includes('product_view')) {
      return NextResponse.redirect('/unauthorized');
    }
  }
}
```

## Usage Examples

### 1. Create Product Admin
```bash
python manage.py create_admin_user \
  --email product@admin.com \
  --password secure123 \
  --role product_admin \
  --first-name Product \
  --last-name Admin
```

### 2. Frontend Permission Check
```typescript
// In your React component
const ProductManagement = () => {
  const { canAccess } = usePermissions();
  
  return (
    <div>
      <ProtectedComponent permission="product_view">
        <ProductList />
      </ProtectedComponent>
      
      <ProtectedComponent permission="product_add">
        <AddProductButton />
      </ProtectedComponent>
      
      <ProtectedComponent permission="product_delete">
        <DeleteProductButton />
      </ProtectedComponent>
    </div>
  );
};
```

### 3. API Call with Permission
```typescript
// utils/api.ts
export const createProduct = async (productData: ProductData) => {
  const response = await fetch('/api/products/', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${getToken()}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(productData)
  });
  
  if (response.status === 403) {
    throw new Error('Insufficient permissions');
  }
  
  return response.json();
};
```

## Security Benefits

1. **Principle of Least Privilege**: Users only get permissions they need
2. **Audit Trail**: Complete logging of admin actions
3. **Granular Control**: Fine-grained permissions for each operation
4. **Frontend Security**: UI elements hidden based on permissions
5. **API Security**: Backend endpoints protected by permission decorators
6. **Role Separation**: Clear separation of admin responsibilities

## Migration Required

```bash
# Create migrations for new models
python manage.py makemigrations mall
python manage.py migrate

# Update existing admins to have full privileges
python manage.py shell
>>> from django.contrib.auth import get_user_model
>>> from mall.admin_roles import AdminUserRole
>>> from mall.permissions import AdminRole
>>> User = get_user_model()
>>> 
>>> # Give existing staff users super admin role
>>> for user in User.objects.filter(is_staff=True, is_active_admin=False):
...     user.is_active_admin = True
...     user.save()
...     AdminUserRole.objects.create(
...         user=user,
...         role=AdminRole.SUPER_ADMIN,
...         assigned_by=None  # System migration
...     )
```

## Key Changes from Single-Role System

1. **Multiple Roles**: Admins can have multiple roles simultaneously
2. **Role Management**: Super admin assigns/removes roles via API
3. **Permission Aggregation**: Permissions combined from all assigned roles
4. **Custom Permissions**: Additional grants/revokes beyond roles
5. **Simplified Role State**: No active/inactive - roles are assigned or removed
6. **Enhanced Security**: Complete admin isolation from regular users

This multi-role RBAC system provides maximum flexibility while maintaining strict security controls.