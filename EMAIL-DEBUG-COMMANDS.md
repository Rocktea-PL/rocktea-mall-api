# EMAIL DEBUGGING COMMANDS

## 1. Check Celery Worker Logs
```bash
sudo tail -f /var/log/celery/worker.log
```

## 2. Test Email Templates
```bash
cd /home/ubuntu/django-app/dev/main
python manage.py shell
```

Then in Django shell:
```python
from django.template.loader import render_to_string
from django.utils import timezone

# Test store welcome template
context = {
    "full_name": "Test User",
    "store_name": "Test Store", 
    "store_domain": "https://test.yourockteamall.com",
    "environment": "DEV",
    "store_id": "123",
    "current_year": timezone.now().year,
    "owner_email": "test@example.com",
    "is_local": False,
}

try:
    html = render_to_string('emails/store_welcome_success.html', context)
    print("✅ Template renders successfully")
except Exception as e:
    print(f"❌ Template error: {e}")
```

## 3. Test Celery Task Directly
```python
from setup.tasks import send_email_task

# Test email task
result = send_email_task.delay(
    recipient_email="your-test-email@gmail.com",
    template_name='emails/store_welcome_success.html',
    context=context,
    subject="Test Email",
    tags=["test"]
)

print(f"Task ID: {result.id}")
```

## 4. Check Brevo API Settings
```bash
cd /home/ubuntu/django-app/dev/main
python manage.py shell
```

```python
from django.conf import settings
print(f"BREVO_API_KEY: {settings.BREVO_API_KEY[:10]}...")
print(f"SENDER_EMAIL: {settings.SENDER_EMAIL}")
print(f"SENDER_NAME: {settings.SENDER_NAME}")
```

## 5. Monitor Email Delivery
```bash
# Watch for email tasks
sudo journalctl -u celery-worker-rocktea.service -f | grep "send_email_task"

# Check for any email errors
sudo journalctl -u celery-worker-rocktea.service -f | grep -i "email\|error"
```

## 6. Common Issues to Check:
- ✅ Template files exist in correct location
- ✅ Context variables match template requirements  
- ✅ Brevo API key is valid
- ✅ Celery worker is running
- ✅ Redis connection is working
- ✅ No syntax errors in templates