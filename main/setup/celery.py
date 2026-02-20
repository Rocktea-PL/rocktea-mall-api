from celery import Celery
import os
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')

# Import settings after environment is set
from django.conf import settings

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
   task_ignore_result=False,  # Store results for debugging
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
      'update-shipment-status': {
         'task': 'order.tasks.update_shipment_status',
         'schedule': timedelta(minutes=15),
         'options': {'queue': 'periodic', 'expires': 900}
      },
      'check-withdrawal-status': {
         'task': 'order.tasks.check_withdrawal_status',
         'schedule': timedelta(minutes=15),  # Reduced frequency
         'options': {'queue': 'periodic', 'expires': 900, 'retry': False}
      },
   },
   timezone='UTC',
   task_routes={
      'setup.tasks.send_email_task': {'queue': 'emails'},
      'setup.tasks.create_store_domain_task': {'queue': 'default'},
      'setup.tasks.send_order_completion_email_task': {'queue': 'emails'},
      'mall.tasks.upload_image': {'queue': 'media'},
      'mall.tasks.check_shipping_status': {'queue': 'periodic'},
      'mall.tasks.cancel_unpaid_shipments': {'queue': 'periodic'},
      'order.tasks.update_shipment_status': {'queue': 'periodic'},
      'order.tasks.check_withdrawal_status': {'queue': 'periodic'},
      'tenants.tasks.upload_profile_image': {'queue': 'media'},
   }
)

# Load task modules from all registered Django apps.
app.autodiscover_tasks()