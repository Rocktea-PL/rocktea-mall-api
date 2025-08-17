import pytest
from django.test import override_settings

# Speed up tests by using in-memory database and disabling migrations
@pytest.fixture(scope='session')
def django_db_setup():
    pass

# Disable migrations for faster tests
@override_settings(
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    },
    MIGRATION_MODULES={
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
    # Disable logging during tests
    LOGGING_CONFIG=None,
    # Disable Celery during tests
    CELERY_TASK_ALWAYS_EAGER=True,
    CELERY_TASK_EAGER_PROPAGATES=True,
)