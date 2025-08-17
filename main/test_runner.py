#!/usr/bin/env python
"""
Fast test runner for CI/CD pipelines
"""
import os
import sys
import django
from django.conf import settings
from django.test.utils import get_runner

if __name__ == "__main__":
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
    
    # Override settings for faster tests
    settings.configure(
        **{
            **settings.__dict__,
            'DATABASES': {
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            'MIGRATION_MODULES': {
                'mall': None,
                'order': None,
                'services': None,
                'accounts': None,
                'dropshippers': None,
                'products': None,
                'admin_orders': None,
                'dashboards': None,
                'tenants': None,
            },
            'LOGGING_CONFIG': None,
            'CELERY_TASK_ALWAYS_EAGER': True,
            'CELERY_TASK_EAGER_PROPAGATES': True,
            'PASSWORD_HASHERS': [
                'django.contrib.auth.hashers.MD5PasswordHasher',
            ],
        }
    )
    
    django.setup()
    TestRunner = get_runner(settings)
    test_runner = TestRunner(verbosity=1, interactive=False, keepdb=False)
    failures = test_runner.run_tests([])
    
    if failures:
        sys.exit(1)