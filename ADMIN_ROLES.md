# Admin Roles & Permissions

## Product Manager vs Product Admin

### Product Manager
**Purpose**: Limited product management role for staff who only handle product data entry

**Permissions**:
- ✅ Can VIEW products (only their own)
- ✅ Can ADD new products
- ✅ Can EDIT products (only ones they created)
- ❌ Cannot DELETE any products
- ❌ Cannot see other users' products

**Access**:
- Dashboard (read-only overview)
- Warehouse > Products (limited to their own)

**Use Case**: Data entry staff, product catalogers, inventory clerks

---

### Product Admin
**Purpose**: Full product management with all permissions

**Permissions**:
- ✅ Can VIEW all products
- ✅ Can ADD new products
- ✅ Can EDIT any product
- ✅ Can DELETE any product
- ✅ Can see all products from all users

**Access**:
- Dashboard
- Warehouse (all sections: Products, Brands, Categories, SubCategories, Types)

**Use Case**: Product managers, inventory managers, catalog administrators

---

## All Available Roles

### 1. Super Admin
- **Access**: Everything
- **Permissions**: All permissions across the system
- **Can**: Create users, manage all data, configure system

### 2. Product Admin
- **Access**: Dashboard, Warehouse (all)
- **Permissions**: Full product management
- **Can**: CRUD all products, brands, categories

### 3. Product Manager
- **Access**: Dashboard, Warehouse > Products (own only)
- **Permissions**: Add/Edit own products only
- **Can**: Create and update their own products

### 4. Store Admin
- **Access**: Dashboard, Dropshippers, Orders
- **Permissions**: Manage stores and dropshippers
- **Can**: View/edit stores, manage dropshippers, view orders

### 5. Order Admin
- **Access**: Dashboard, Orders, Transactions
- **Permissions**: Full order management
- **Can**: View/edit orders, manage transactions

### 6. User Admin
- **Access**: Dashboard, Dropshippers, Users
- **Permissions**: User management
- **Can**: Create/edit users, manage dropshippers

### 7. Analytics Admin
- **Access**: Dashboard, Transactions
- **Permissions**: View analytics and reports
- **Can**: View all analytics, transactions, reports

---

## Testing Roles

### Test Product Manager
1. Create user with "Product Manager" role
2. Login with that user
3. Should only see: Dashboard, Warehouse > Products
4. Create a product - should succeed
5. Try to edit own product - should succeed
6. Try to delete product - should fail (403)
7. Try to access /orders - should redirect to /dashboard
8. Try to access /users - should redirect to /dashboard

### Test Product Admin
1. Create user with "Product Admin" role
2. Login with that user
3. Should see: Dashboard, Warehouse (all sections)
4. Can view all products from all users
5. Can edit any product
6. Can delete any product
7. Try to access /orders - should redirect to /dashboard
8. Try to access /users - should redirect to /dashboard

---

## Key Differences Summary

| Feature | Product Manager | Product Admin |
|---------|----------------|---------------|
| View all products | ❌ (own only) | ✅ |
| Add products | ✅ | ✅ |
| Edit own products | ✅ | ✅ |
| Edit others' products | ❌ | ✅ |
| Delete products | ❌ | ✅ |
| Manage brands | ❌ | ✅ |
| Manage categories | ❌ | ✅ |
| Access other sections | ❌ | ❌ |

---

## Implementation Notes

- Product Manager is designed for data entry staff with limited permissions
- Product Admin has full control over product catalog
- Both roles are restricted to product-related functions only
- Neither can access orders, users, or transactions
- Super Admin can do everything
