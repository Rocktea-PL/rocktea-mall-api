from celery import Celery
import os
from datetime import timedelta
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')

app = Celery('setup',
   broker=settings.REDIS_URL,
   backend=settings.REDIS_URL)

app.config_from_object('django.conf:settings', namespace='CELERY')

app.conf.update(
   broker_connection_retry_on_startup=True,
   worker_cancel_long_running_tasks_on_connection_loss=True,
   worker_timeout=300,
)
worker_timeout = timedelta(minutes=5)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()