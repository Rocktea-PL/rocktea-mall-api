#!/usr/bin/env python
import os
import sys
import django

# Add the main directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'main'))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from mall.models import Notification, Store

# Test creating a withdrawal notification
try:
    store = Store.objects.get(id='54146bcb-94e8-4ff1-a41b-f8f122ddbf6f')
    
    # Create a test withdrawal notification
    notification = Notification.objects.create(
        store=store,
        message="Test withdrawal of 5000 has been successfully processed.",
        notification_type='withdrawal'
    )
    
    print(f"Created notification: {notification.id}")
    print(f"Store: {notification.store.id}")
    print(f"Type: {notification.notification_type}")
    print(f"Recipient: {notification.recipient}")
    
    # Test filtering
    withdrawal_notifications = Notification.objects.filter(
        store=store,
        recipient__isnull=True,
        notification_type='withdrawal'
    )
    
    print(f"Found {withdrawal_notifications.count()} withdrawal notifications")
    for notif in withdrawal_notifications:
        print(f"- ID: {notif.id}, Message: {notif.message}")
        
except Exception as e:
    print(f"Error: {e}")