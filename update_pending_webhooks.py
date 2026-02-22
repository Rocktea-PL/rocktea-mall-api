#!/usr/bin/env python
"""
Update PaystackWebhook records from Pending to Success for stores that have been paid
"""
import os
import sys
import django

sys.path.insert(0, '/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from order.models import PaystackWebhook
from mall.models import Store

def update_pending_webhooks():
    """Update pending webhook records for paid stores"""
    
    # Find all pending webhooks
    pending_webhooks = PaystackWebhook.objects.filter(status='Pending')
    
    print(f"\n{'='*80}")
    print(f"Found {pending_webhooks.count()} pending webhook records")
    print(f"{'='*80}\n")
    
    if pending_webhooks.count() == 0:
        print("✅ No pending webhooks to update")
        return
    
    updated_count = 0
    skipped_count = 0
    
    for webhook in pending_webhooks:
        email = webhook.email
        
        try:
            # Find the store for this email
            from mall.models import CustomUser
            user = CustomUser.objects.get(email=email)
            store = Store.objects.get(owner=user)
            
            # Check if store has been paid
            if store.has_made_payment and store.completed:
                print(f"📧 {email}")
                print(f"   Store: {store.name}")
                print(f"   Status: Paid ✅")
                print(f"   Updating webhook to Success...")
                
                webhook.status = 'Success'
                webhook.store = store
                webhook.save(update_fields=['status', 'store'])
                
                updated_count += 1
                print(f"   ✓ Updated\n")
            else:
                print(f"📧 {email}")
                print(f"   Store: {store.name}")
                print(f"   Status: Not paid yet ⏳")
                print(f"   Skipping...\n")
                skipped_count += 1
                
        except Exception as e:
            print(f"📧 {email}")
            print(f"   ❌ Error: {e}\n")
            skipped_count += 1
    
    print(f"{'='*80}")
    print(f"SUMMARY:")
    print(f"  Updated: {updated_count}")
    print(f"  Skipped: {skipped_count}")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    confirm = input("Update all pending webhooks for paid stores? (yes/no): ")
    if confirm.lower() == 'yes':
        update_pending_webhooks()
    else:
        print("Cancelled.")
