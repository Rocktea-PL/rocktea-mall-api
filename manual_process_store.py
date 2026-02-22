#!/usr/bin/env python
"""
Manually mark stores as paid and trigger DNS creation
Use this ONLY if you've verified payment was received outside the webhook
"""
import os
import sys
import django

sys.path.insert(0, '/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from mall.models import Store
from mall.signals import create_store_domain_after_payment

def manually_process_store(store_id):
    """Manually mark store as paid and create DNS"""
    try:
        store = Store.objects.get(id=store_id)
        
        print(f"\n{'='*80}")
        print(f"Store: {store.name}")
        print(f"Owner: {store.owner.email}")
        print(f"Current Status:")
        print(f"  Payment: {store.has_made_payment}")
        print(f"  Completed: {store.completed}")
        print(f"  DNS Created: {store.dns_record_created}")
        print(f"  Domain: {store.domain_name or 'Not set'}")
        print(f"  User completed_steps: {store.owner.completed_steps}")
        print(f"{'='*80}\n")
        
        # Check if already processed
        if store.has_made_payment and store.completed and store.owner.completed_steps == 3:
            print("⚠️  Store already marked as paid with completed_steps = 3")
            if store.dns_record_created and store.domain_name:
                print("✅ Store is fully processed. Nothing to do.")
                return
            else:
                print("⚠️  DNS not created yet. Will attempt DNS creation only.")
                confirm = input("Create DNS for this store? (yes/no): ")
                if confirm.lower() != 'yes':
                    print("Cancelled.")
                    return
                print("\n🚀 Creating DNS record...")
                create_store_domain_after_payment(store)
                store.refresh_from_db()
                if store.dns_record_created:
                    print(f"✅ DNS created: {store.domain_name}")
                else:
                    print("❌ DNS creation failed")
                return
        
        # Confirm before proceeding with full update
        confirm = input("Mark this store as PAID and create DNS? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Update store payment status (matching webhook behavior)
        if not store.has_made_payment or not store.completed:
            store.has_made_payment = True
            store.completed = True
            store.save(update_fields=['has_made_payment', 'completed'])
            print("✓ Store marked as paid and completed")
        
        # Update user completed_steps to 3 (matching webhook behavior)
        user = store.owner
        if user.completed_steps != 3:
            user.completed_steps = 3
            user.save(update_fields=['completed_steps'])
            print("✓ User completed_steps updated to 3")
        
        # Create notification only if not already exists
        from mall.models import Notification
        existing_notification = Notification.objects.filter(
            store=store,
            notification_type='payment',
            message__icontains='payment has been successfully processed'
        ).exists()
        
        if not existing_notification:
            notification_message = f"Your dropshipping payment has been successfully processed. Your store is now active!"
            Notification.objects.create(
                store=store,
                message=notification_message, 
                notification_type='payment'
            )
            print("✓ Notification created")
        else:
            print("⚠️  Payment notification already exists, skipped")
        
        # Trigger DNS creation only if not already created
        if not store.dns_record_created or not store.domain_name:
            print("\n🚀 Creating DNS record...")
            create_store_domain_after_payment(store)
        else:
            print("⚠️  DNS already created, skipped")
        
        # Refresh and show result
        store.refresh_from_db()
        user.refresh_from_db()
        print(f"\n{'='*80}")
        print(f"RESULT:")
        print(f"  Payment: {store.has_made_payment}")
        print(f"  Completed: {store.completed}")
        print(f"  User completed_steps: {user.completed_steps}")
        print(f"  DNS Created: {store.dns_record_created}")
        print(f"  Domain: {store.domain_name or 'Not set'}")
        print(f"{'='*80}\n")
        
        if store.dns_record_created:
            print("✅ SUCCESS! Store is now active with DNS")
        else:
            print("❌ DNS creation failed - check logs above")
            
    except Store.DoesNotExist:
        print(f"❌ Store {store_id} not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python manual_process_store.py <store_id>")
        print("\nStores without payment:")
        stores = Store.objects.filter(has_made_payment=False).order_by('-created_at')
        for store in stores:
            print(f"  ID: {store.id} - {store.name} ({store.owner.email})")
        sys.exit(1)
    
    store_id = sys.argv[1]
    manually_process_store(store_id)
