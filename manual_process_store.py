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
        print(f"{'='*80}\n")
        
        # Confirm before proceeding
        confirm = input("Mark this store as PAID and create DNS? (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("Cancelled.")
            return
        
        # Update store payment status
        store.has_made_payment = True
        store.completed = True
        store.save(update_fields=['has_made_payment', 'completed'])
        print("✓ Store marked as paid")
        
        # Update user completed_steps
        user = store.owner
        user.completed_steps = 3
        user.save(update_fields=['completed_steps'])
        print("✓ User completed_steps updated")
        
        # Trigger DNS creation
        print("\n🚀 Creating DNS record...")
        create_store_domain_after_payment(store)
        
        # Refresh and show result
        store.refresh_from_db()
        print(f"\n{'='*80}")
        print(f"RESULT:")
        print(f"  Payment: {store.has_made_payment}")
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
