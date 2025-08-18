// Next.js Frontend Integration Examples

// 1. Permission Context
import React, { createContext, useContext, useEffect, useState } from 'react';

interface Permission {
  permissions: string[];
  role: string;
  canAccess: (permission: string) => boolean;
  hasRole: (role: string) => boolean;
}

const PermissionContext = createContext<Permission | null>(null);

export const PermissionProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [permissions, setPermissions] = useState<string[]>([]);
  const [role, setRole] = useState<string>('');

  useEffect(() => {
    // Fetch user permissions on mount
    fetchUserPermissions();
  }, []);

  const fetchUserPermissions = async () => {
    try {
      const response = await fetch('/api/user-permissions/', {
        headers: { 'Authorization': `Bearer ${getToken()}` }
      });
      const data = await response.json();
      setPermissions(data.permissions);
      setRole(data.role);
    } catch (error) {
      console.error('Failed to fetch permissions:', error);
    }
  };

  const canAccess = (permission: string): boolean => {
    return permissions.includes(permission);
  };

  const hasRole = (userRole: string): boolean => {
    return role === userRole;
  };

  return (
    <PermissionContext.Provider value={{ permissions, role, canAccess, hasRole }}>
      {children}
    </PermissionContext.Provider>
  );
};

export const usePermissions = () => {
  const context = useContext(PermissionContext);
  if (!context) {
    throw new Error('usePermissions must be used within PermissionProvider');
  }
  return context;
};

// 2. Protected Component
interface ProtectedComponentProps {
  permission: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const ProtectedComponent: React.FC<ProtectedComponentProps> = ({
  permission,
  fallback = <div className="text-red-500">Access Denied</div>,
  children
}) => {
  const { canAccess } = usePermissions();
  
  if (!canAccess(permission)) {
    return <>{fallback}</>;
  }
  
  return <>{children}</>;
};

// 3. Product Management Page Example
const ProductManagement: React.FC = () => {
  const { canAccess } = usePermissions();
  const [products, setProducts] = useState([]);

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-6">Product Management</h1>
      
      {/* View Products */}
      <ProtectedComponent permission="product_view">
        <div className="mb-6">
          <h2 className="text-xl mb-4">Products</h2>
          <ProductList products={products} />
        </div>
      </ProtectedComponent>

      {/* Add Product */}
      <ProtectedComponent permission="product_add">
        <div className="mb-6">
          <button 
            className="bg-blue-500 text-white px-4 py-2 rounded"
            onClick={() => setShowAddForm(true)}
          >
            Add New Product
          </button>
        </div>
      </ProtectedComponent>

      {/* Admin Actions */}
      <ProtectedComponent permission="product_delete">
        <div className="bg-red-50 p-4 rounded">
          <h3 className="text-red-700 font-semibold">Danger Zone</h3>
          <p className="text-red-600">Delete products permanently</p>
        </div>
      </ProtectedComponent>
    </div>
  );
};

// 4. API Utilities with Permission Handling
class ApiClient {
  private baseUrl = '/api';
  
  private async request(endpoint: string, options: RequestInit = {}) {
    const token = localStorage.getItem('auth-token');
    
    const response = await fetch(`${this.baseUrl}${endpoint}`, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (response.status === 403) {
      throw new Error('Insufficient permissions for this action');
    }

    if (response.status === 401) {
      // Redirect to login
      window.location.href = '/login';
      throw new Error('Authentication required');
    }

    return response.json();
  }

  // Product API methods
  async getProducts() {
    return this.request('/products/');
  }

  async createProduct(productData: any) {
    return this.request('/products/', {
      method: 'POST',
      body: JSON.stringify(productData),
    });
  }

  async deleteProduct(productId: string) {
    return this.request(`/products/${productId}/`, {
      method: 'DELETE',
    });
  }

  // Admin API methods
  async getAdminUsers() {
    return this.request('/admin-users/');
  }

  async createAdminUser(userData: any) {
    return this.request('/admin-users/', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }
}

export const apiClient = new ApiClient();

// 5. Middleware for Route Protection
import { NextRequest, NextResponse } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('auth-token')?.value;
  
  if (!token) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  // Decode token to get permissions (implement based on your JWT structure)
  const permissions = getUserPermissionsFromToken(token);
  
  // Route-based permission checking
  const pathname = request.nextUrl.pathname;
  
  if (pathname.startsWith('/admin/products')) {
    if (!permissions.includes('product_view')) {
      return NextResponse.redirect(new URL('/unauthorized', request.url));
    }
  }
  
  if (pathname.startsWith('/admin/users')) {
    if (!permissions.includes('user_view')) {
      return NextResponse.redirect(new URL('/unauthorized', request.url));
    }
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/admin/:path*']
};

// 6. Permission-based Navigation
const AdminNavigation: React.FC = () => {
  const { canAccess } = usePermissions();

  const navItems = [
    { 
      name: 'Products', 
      href: '/admin/products', 
      permission: 'product_view',
      icon: '📦'
    },
    { 
      name: 'Orders', 
      href: '/admin/orders', 
      permission: 'order_view',
      icon: '📋'
    },
    { 
      name: 'Stores', 
      href: '/admin/stores', 
      permission: 'store_view',
      icon: '🏪'
    },
    { 
      name: 'Users', 
      href: '/admin/users', 
      permission: 'user_view',
      icon: '👥'
    },
    { 
      name: 'Analytics', 
      href: '/admin/analytics', 
      permission: 'analytics_view',
      icon: '📊'
    },
  ];

  return (
    <nav className="bg-gray-800 text-white p-4">
      <ul className="space-y-2">
        {navItems.map((item) => (
          canAccess(item.permission) && (
            <li key={item.name}>
              <a 
                href={item.href}
                className="flex items-center space-x-2 p-2 rounded hover:bg-gray-700"
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </a>
            </li>
          )
        ))}
      </ul>
    </nav>
  );
};

// Helper function to get token
function getToken(): string | null {
  return localStorage.getItem('auth-token');
}

// Helper function to decode permissions from JWT (implement based on your JWT structure)
function getUserPermissionsFromToken(token: string): string[] {
  try {
    const payload = JSON.parse(atob(token.split('.')[1]));
    return payload.permissions || [];
  } catch {
    return [];
  }
}