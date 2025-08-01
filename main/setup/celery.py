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
   task_serializer='json',
   accept_content=['json'],
   result_serializer='json',
   task_track_started=True,
   task_time_limit=30 * 60,
   task_soft_time_limit=25 * 60,
   worker_prefetch_multiplier=1,
   worker_max_tasks_per_child=1000,  # Prevent memory leaks
   worker_disable_rate_limits=False,
   task_compression='gzip',
   result_compression='gzip',
   result_expires=3600,  # 1 hour
   task_ignore_result=True,  # Don't store results for fire-and-forget tasks
   beat_schedule={
      'check-shipping-status': {
         'task': 'mall.tasks.check_shipping_status',
         'schedule': timedelta(minutes=30),
         'options': {'queue': 'periodic', 'expires': 1800}
      },
      'cancel-unpaid-shipments': {
         'task': 'mall.tasks.cancel_unpaid_shipments', 
         'schedule': timedelta(hours=2),
         'options': {'queue': 'periodic', 'expires': 3600}
      },
   },
   timezone='UTC',
   task_routes={
      'mall.tasks.upload_image': {'queue': 'media'},
      'mall.tasks.check_shipping_status': {'queue': 'periodic'},
      'mall.tasks.cancel_unpaid_shipments': {'queue': 'periodic'},
   }
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()