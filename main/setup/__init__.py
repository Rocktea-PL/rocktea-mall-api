# Only import celery in non-CI environments
import os

if not os.environ.get('CI'):
    from .celery import app as celery_app
    __all__ = ('celery_app',)
else:
    __all__ = ()