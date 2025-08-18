"""
Fast test settings for CI/CD and local testing
"""
import os

# Set CI environment before importing settings
os.environ['CI'] = 'true'
os.environ['SECRET_KEY'] = 'test-secret-key-for-ci-environment-only'
os.environ['REDIS_URL'] = 'redis://dummy:6379/0'
# Mock Cloudinary settings for CI
os.environ['CLOUDINARY_URL'] = 'cloudinary://dummy:dummy@dummy'
os.environ['CLOUDINARY_NAME'] = 'dummy'
os.environ['CLOUDINARY_API_KEY'] = 'dummy'
os.environ['CLOUDINARY_SECRET'] = 'dummy'

from .settings import *

# CI database is set above
if not os.environ.get('CI'):
    # Use existing PostgreSQL settings from main settings for local testing
    pass

# Use faster password hasher for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Use in-memory database for faster tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
        'OPTIONS': {
            'timeout': 20,
        },
    }
}

# Keep migrations enabled but optimize
MIGRATION_MODULES = {}

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
CLOUDINARY_STORAGE = {
    'CLOUDINARY_URL': 'cloudinary://dummy:dummy@dummy',
    'CLOUD_NAME': 'dummy',
    'API_KEY': 'dummy', 
    'API_SECRET': 'dummy'
}
BREVO_API_KEY = 'test_key'
TEST_SECRET_KEY = 'test_secret'