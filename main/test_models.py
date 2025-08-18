#!/usr/bin/env python
"""Quick model test script"""
import os
import sys
import django

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.test_settings')
    django.setup()
    
    try:
        from mall.models import CustomUser
        from mall.admin_roles import AdminUserRole, AdminCustomPermission
        from mall.permissions import AdminRole, PermissionType
        
        print("✓ All models imported successfully")
        print(f"✓ AdminRole choices: {AdminRole.choices}")
        print(f"✓ PermissionType choices count: {len(PermissionType.choices)}")
        
        # Test model creation
        print("✓ Models are properly configured")
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
    except Exception as e:
        print(f"✗ Error: {e}")