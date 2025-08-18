"""
Fast test settings for CI/CD and local testing
"""
import os

# Set CI environment before importing settings
os.environ['CI'] = 'true'
os.environ['SECRET_KEY'] = 'test-secret-key-for-ci-environment-only'
os.environ['REDIS_URL'] = 'redis://dummy:6379/0'

from .settings import *

# Use SQLite for CI tests (faster and no version issues)
if 'CI' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
else:
    # Use existing PostgreSQL settings from main settings
    pass

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Keep migrations enabled for proper database setup
# MIGRATION_MODULES = {
#     'mall': None,
#     'order': None,
#     'services': None,
#     'accounts': None,
#     'dropshippers': None,
#     'products': None,
#     'admin_orders': None,
#     'dashboards': None,
#     'tenants': None,
# }

# Disable logging during tests
LOGGING_CONFIG = None

# Make Celery synchronous for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Use dummy cache for tests
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

# Use dummy email backend
EMAIL_BACKEND = 'django.core.mail.backends.dummy.EmailBackend'

# Disable file storage for tests
STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.InMemoryStorage"
    }
}

# Disable external services
CLOUDINARY_STORAGE = {}
BREVO_API_KEY = 'test_key'
TEST_SECRET_KEY = 'test_secret'