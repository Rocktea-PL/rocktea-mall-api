#!/usr/bin/env python
import os
import sys
import django
import json

sys.path.insert(0, '/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from order.models import PaystackWebhook

print("\n" + "="*80)
print("WEBHOOK DATA INSPECTION")
print("="*80)

webhooks = PaystackWebhook.objects.filter(purpose='dropshipping_payment').order_by('-created_at')[:3]

for wh in webhooks:
    print(f"\n{'='*80}")
    print(f"Reference: {wh.reference}")
    print(f"Status: {wh.status}")
    print(f"Created: {wh.created_at}")
    print(f"User: {wh.user.email if wh.user else 'None'}")
    print(f"Store: {wh.store.name if wh.store else 'None'}")
    print(f"\nData field content:")
    if wh.data:
        print(json.dumps(wh.data, indent=2))
    else:
        print("  Data is NULL/empty")
    print("="*80)
