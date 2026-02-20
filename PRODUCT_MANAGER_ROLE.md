# Product Manager Role Implementation

## Overview
A new "Product Manager" role has been added to allow admins to create users who can:
- ✅ Add products to the system
- ✅ View only their own products
- ✅ Update only their own products
- ❌ Cannot delete any products
- 📝 All actions are logged with audit trail

## Changes Made

### 1. Database Changes

#### Migration File
- **File**: `mall/migrations/0063_product_created_by.py`
- **Change**: Added `created_by` field to Product model to track who created each product

#### Run Migration
```bash
python manage.py migrate
```

### 2. Permission System Updates

#### File: `mall/permissions.py`
- Added new role: `PRODUCT_MANAGER = 'product_manager', 'Product Manager'`
- Permissions for Product Manager:
  - `PRODUCT_VIEW` - Can view products
  - `PRODUCT_ADD` - Can add products
  - `PRODUCT_EDIT` - Can edit products
  - ❌ No `PRODUCT_DELETE` permission

### 3. Product Model Updates

#### File: `mall/models.py`
- Added `created_by` field to track product creator
- Field: `created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='created_products')`

### 4. Product Views Updates

#### File: `products/views.py`
- **get_queryset()**: Product Managers only see their own products
- **create()**: 
  - Checks `PRODUCT_ADD` permission
  - Sets `created_by` to current user
  - Logs creation in audit trail
- **update()**: 
  - Checks `PRODUCT_EDIT` permission
  - Product Managers can only edit their own products
  - Logs updates in audit trail
- **perform_destroy()**: 
  - Checks `PRODUCT_DELETE` permission (Product Managers don't have this)
  - Logs deletions in audit trail

## How to Use

### 1. Create a Product Manager User

**API Endpoint**: `POST /api/admin/users/`

**Request Body**:
```json
{
  "email": "productmanager@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepassword123",
  "roles": ["product_manager"]
}
```

**Note**: Only Super Admins can create admin users

### 2. Product Manager Login

Product Manager logs in with their credentials and receives a JWT token.

### 3. Product Manager Actions

#### Add Product
```bash
POST /api/admin/products/
Authorization: Bearer <token>

{
  "name": "New Product",
  "description": "Product description",
  "quantity": 100,
  "category": "category_id",
  "subcategory": "subcategory_id",
  "brand": "brand_id",
  ...
}
```

#### View Their Products
```bash
GET /api/admin/products/
Authorization: Bearer <token>
```
Returns only products created by this Product Manager.

#### Update Their Product
```bash
PATCH /api/admin/products/{product_id}/
Authorization: Bearer <token>

{
  "quantity": 150
}
```
Can only update products they created.

#### Try to Delete (Will Fail)
```bash
DELETE /api/admin/products/{product_id}/
Authorization: Bearer <token>
```
Returns: `403 Forbidden - You do not have permission to delete products`

### 4. View Audit Logs

All Product Manager actions are logged in the `AdminAuditLog` table:
- Product creation
- Product updates
- Failed permission attempts

**Query Logs**:
```python
from mall.admin_audit import AdminAuditLog

# Get all logs for a specific user
logs = AdminAuditLog.objects.filter(admin_user=user).order_by('-timestamp')

# Get product-related logs
product_logs = AdminAuditLog.objects.filter(
    resource_type='PRODUCT',
    action__in=['CREATE', 'UPDATE']
).order_by('-timestamp')
```

## Admin Dashboard Integration

### Frontend Implementation (Next.js)

#### 1. Create Product Manager User Form
```typescript
// pages/admin/users/create.tsx
const createProductManager = async (data) => {
  const response = await fetch(`${API_URL}/api/admin/users/`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      ...data,
      roles: ['product_manager']
    })
  });
  return response.json();
};
```

#### 2. View Audit Logs
```typescript
// pages/admin/audit-logs.tsx
const fetchAuditLogs = async (userId?: string) => {
  const url = userId 
    ? `${API_URL}/api/admin/audit-logs/?user=${userId}`
    : `${API_URL}/api/admin/audit-logs/`;
    
  const response = await fetch(url, {
    headers: {
      'Authorization': `Bearer ${token}`
    }
  });
  return response.json();
};
```

## Testing

### Test Scenarios

1. **Create Product Manager**
   - Super Admin creates Product Manager user
   - Verify user has `product_manager` role

2. **Product Manager Creates Product**
   - Product Manager logs in
   - Creates a product
   - Verify `created_by` is set correctly
   - Verify audit log entry exists

3. **Product Manager Views Products**
   - Product Manager can only see their own products
   - Cannot see products created by others

4. **Product Manager Updates Product**
   - Can update their own products
   - Cannot update products created by others (403 error)

5. **Product Manager Cannot Delete**
   - Attempt to delete returns 403 Forbidden
   - Audit log records the failed attempt

6. **Audit Trail**
   - All actions logged with timestamp
   - IP address and user agent captured
   - Details include product name and SKU

## Database Schema

### AdminAuditLog Table
```sql
- id (auto)
- admin_user_id (FK to CustomUser)
- action (CREATE, UPDATE, DELETE, VIEW)
- resource_type (PRODUCT, STORE, ORDER, USER, SYSTEM)
- resource_id (product ID)
- details (JSON: {product_name, sku})
- ip_address
- user_agent
- timestamp
```

### Product Table (Updated)
```sql
- id
- sku
- name
- description
- quantity
- category_id
- created_by_id (NEW - FK to CustomUser)
- created_at
- ...
```

## Security Features

1. **Permission-Based Access**: All actions check permissions before execution
2. **Ownership Validation**: Product Managers can only modify their own products
3. **Audit Trail**: Complete log of all actions with user, timestamp, and details
4. **No Delete Permission**: Product Managers cannot delete products
5. **IP Tracking**: All actions logged with IP address for security

## API Endpoints Summary

| Endpoint | Method | Permission | Product Manager Access |
|----------|--------|------------|----------------------|
| `/api/admin/products/` | GET | PRODUCT_VIEW | ✅ (own products only) |
| `/api/admin/products/` | POST | PRODUCT_ADD | ✅ |
| `/api/admin/products/{id}/` | GET | PRODUCT_VIEW | ✅ (if they created it) |
| `/api/admin/products/{id}/` | PATCH | PRODUCT_EDIT | ✅ (if they created it) |
| `/api/admin/products/{id}/` | DELETE | PRODUCT_DELETE | ❌ |
| `/api/admin/users/` | POST | USER_CREATE | ❌ (Super Admin only) |
| `/api/admin/audit-logs/` | GET | - | ✅ (admin access) |

## Next Steps

1. Run the migration: `python manage.py migrate`
2. Test creating a Product Manager user via API
3. Test Product Manager can add/edit products
4. Verify Product Manager cannot delete products
5. Check audit logs are being created
6. Update frontend admin dashboard to support Product Manager role
7. Add audit log viewer in admin dashboard

## Support

For issues or questions, check:
- Audit logs: `AdminAuditLog.objects.all()`
- User permissions: `user.get_permissions()`
- User roles: `user.get_assigned_roles()`
