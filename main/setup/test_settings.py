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

# Use PostgreSQL for CI tests (compatible with production)
if 'CI' in os.environ:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('PGDATABASE', 'test_db'),
            'USER': os.environ.get('PGUSER', 'postgres'),
            'PASSWORD': os.environ.get('PGPASSWORD', 'postgres'),
            'HOST': os.environ.get('PGHOST', 'localhost'),
            'PORT': os.environ.get('PGPORT', '5432'),
        }
    }
else:
    # Use existing settings for local testing
    pass

# Keep migrations enabled
MIGRATION_MODULES = {}

# Disable logging during tests
LOGGING_CONFIG = None

# Make Celery synchronous for tests
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Disable database connection pooling for tests
DATABASES['default']['CONN_MAX_AGE'] = 0

# Use locmem cache for tests (supports delete_pattern)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'test-cache',
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