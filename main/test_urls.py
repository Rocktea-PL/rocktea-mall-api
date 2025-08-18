#!/usr/bin/env python
"""Quick URL test script"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.test_settings')
    django.setup()
    
    from django.urls import reverse, NoReverseMatch
    
    # Test admin management URLs
    try:
        admin_users_url = reverse('admin-users-list')
        print(f"✓ admin-users-list URL: {admin_users_url}")
    except NoReverseMatch as e:
        print(f"✗ admin-users-list URL failed: {e}")
    
    try:
        user_permissions_url = reverse('user-permissions')
        print(f"✓ user-permissions URL: {user_permissions_url}")
    except NoReverseMatch as e:
        print(f"✗ user-permissions URL failed: {e}")
    
    # Test other URLs from failing tests
    from django.urls import resolve
    from django.http import Http404
    
    test_urls = [
        '/api/admin-management/admin-users/',
        '/mall/best_selling',
        '/rocktea/categories/',
        '/rocktea/products/',
        '/rocktea/create/store/',
        '/rocktea/wishlist/',
    ]
    
    for url in test_urls:
        try:
            resolved = resolve(url)
            print(f"✓ {url} -> {resolved.view_name}")
        except Http404:
            print(f"✗ {url} -> 404 Not Found")
        except Exception as e:
            print(f"✗ {url} -> Error: {e}")