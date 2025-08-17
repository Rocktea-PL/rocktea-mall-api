#!/usr/bin/env python
"""
Fast test runner for CI/CD pipelines
Uses SQLite in-memory database and optimized settings
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.test_settings')
    django.setup()
    
    from django.core.management import execute_from_command_line
    
    try:
        execute_from_command_line(['manage.py', 'test', '--verbosity=1'])
        print(f"\n✅ All tests passed! Database: {settings.DATABASES['default']['ENGINE']}")
    except SystemExit as e:
        if e.code != 0:
            print(f"\n❌ Tests failed with exit code: {e.code}")
            sys.exit(e.code)
        else:
            print(f"\n✅ All tests passed! Database: {settings.DATABASES['default']['ENGINE']}")
            sys.exit(0)