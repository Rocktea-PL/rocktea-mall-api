#!/usr/bin/env python
"""
Test script to validate email templates and context variables
Run this to check if templates render correctly with provided context
"""

import os
import sys
import django
from django.template.loader import render_to_string
from django.utils import timezone

# Add the project path
sys.path.append('/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

def test_store_welcome_template():
    """Test store welcome success template"""
    context = {
        "full_name": "John Doe",
        "store_name": "Test Store",
        "store_domain": "https://test-store.yourockteamall.com",
        "environment": "DEV",
        "store_id": "12345",
        "current_year": timezone.now().year,
        "owner_email": "test@example.com",
        "is_local": False,
    }
    
    try:
        html_content = render_to_string('emails/store_welcome_success.html', context)
        print("✅ store_welcome_success.html renders successfully")
        return True
    except Exception as e:
        print(f"❌ store_welcome_success.html failed: {e}")
        return False

def test_store_deletion_template():
    """Test store deletion success template"""
    context = {
        "full_name": "John Doe",
        "store_name": "Test Store",
        "store_domain": "https://test-store.yourockteamall.com",
        "deletion_date": timezone.now().strftime("%B %d, %Y at %I:%M %p"),
        "current_year": timezone.now().year,
        "support_email": "support@yourockteamall.com",
    }
    
    try:
        html_content = render_to_string('emails/store_deletion_success.html', context)
        print("✅ store_deletion_success.html renders successfully")
        return True
    except Exception as e:
        print(f"❌ store_deletion_success.html failed: {e}")
        return False

def test_dns_failure_template():
    """Test DNS failure template"""
    context = {
        "full_name": "John Doe",
        "store_name": "Test Store",
        "attempted_domain": "test-store.yourockteamall.com",
        "store_id": "12345",
        "current_year": timezone.now().year,
        "support_email": "support@yourockteamall.com",
    }
    
    try:
        html_content = render_to_string('emails/store_dns_failure.html', context)
        print("✅ store_dns_failure.html renders successfully")
        return True
    except Exception as e:
        print(f"❌ store_dns_failure.html failed: {e}")
        return False

def test_dns_error_template():
    """Test DNS error template"""
    context = {
        "full_name": "John Doe",
        "store_name": "Test Store",
        "store_id": "12345",
        "error_reference": "DNS_ERROR_12345_20250802_1600",
        "current_year": timezone.now().year,
        "support_email": "support@yourockteamall.com",
    }
    
    try:
        html_content = render_to_string('emails/store_dns_error.html', context)
        print("✅ store_dns_error.html renders successfully")
        return True
    except Exception as e:
        print(f"❌ store_dns_error.html failed: {e}")
        return False

def test_deletion_failure_template():
    """Test store deletion failure template"""
    context = {
        "full_name": "John Doe",
        "store_name": "Test Store",
        "store_domain": "https://test-store.yourockteamall.com",
        "current_year": timezone.now().year,
        "support_email": "support@yourockteamall.com",
    }
    
    try:
        html_content = render_to_string('emails/store_deletion_failure.html', context)
        print("✅ store_deletion_failure.html renders successfully")
        return True
    except Exception as e:
        print(f"❌ store_deletion_failure.html failed: {e}")
        return False

if __name__ == "__main__":
    print("Testing email templates...")
    print("=" * 50)
    
    tests = [
        test_store_welcome_template,
        test_store_deletion_template,
        test_dns_failure_template,
        test_dns_error_template,
        test_deletion_failure_template,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print("=" * 50)
    print(f"Results: {passed}/{total} templates passed")
    
    if passed == total:
        print("🎉 All email templates are working correctly!")
    else:
        print("⚠️ Some templates have issues. Check the errors above.")