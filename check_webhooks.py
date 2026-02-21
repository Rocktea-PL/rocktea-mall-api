#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, '/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from order.models import PaystackWebhook
from mall.models import Store

print("\n" + "="*80)
print("PAYSTACK WEBHOOK RECORDS")
print("="*80)

webhooks = PaystackWebhook.objects.filter(purpose='dropshipping_payment').order_by('-created_at')[:10]

if not webhooks:
    print("No dropshipping payment webhooks found")
else:
    for wh in webhooks:
        email = wh.data.get('customer', {}).get('email') if wh.data else 'N/A'
        print(f"\nReference: {wh.reference}")
        print(f"Email: {email}")
        print(f"Purpose: {wh.purpose}")
        print(f"Status: {wh.status}")
        print(f"Store: {wh.store.name if wh.store else 'Not linked'}")
        print(f"Created: {wh.created_at}")
        print("-" * 80)

print(f"\nTotal webhooks: {PaystackWebhook.objects.count()}")
print(f"Dropshipping webhooks: {PaystackWebhook.objects.filter(purpose='dropshipping_payment').count()}")
print(f"Successful webhooks: {PaystackWebhook.objects.filter(status='Success').count()}")

# Check if any stores should have payment
print("\n" + "="*80)
print("CHECKING STORE-WEBHOOK MATCH")
print("="*80)

for store in Store.objects.all():
    # Try to find webhook by checking data field
    webhooks = PaystackWebhook.objects.filter(purpose='dropshipping_payment')
    
    matching_webhook = None
    for wh in webhooks:
        if wh.data:
            email = wh.data.get('customer', {}).get('email') or wh.data.get('email')
            if email == store.owner.email:
                matching_webhook = wh
                break
    
    if matching_webhook:
        print(f"\nStore: {store.name}")
        print(f"  Owner: {store.owner.email}")
        print(f"  Payment Status: {store.has_made_payment}")
        print(f"  Webhook Status: {matching_webhook.status}")
        print(f"  Webhook Reference: {matching_webhook.reference}")
        if matching_webhook.status == 'Success' and not store.has_made_payment:
            print(f"  ⚠️  MISMATCH: Webhook successful but store payment is False!")
