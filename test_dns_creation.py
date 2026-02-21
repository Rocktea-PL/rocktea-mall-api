#!/usr/bin/env python
"""
Test DNS creation for a specific store
Run on server: 
  cd /home/ubuntu/django-app/dev
  source venv/bin/activate
  python test_dns_creation.py <store_id>
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from mall.models import Store
from mall.signals import create_store_domain_after_payment
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_dns_creation(store_id):
    """Test DNS creation for a specific store"""
    try:
        store = Store.objects.get(id=store_id)
        print(f"\n{'='*60}")
        print(f"Testing DNS Creation for Store")
        print(f"{'='*60}")
        print(f"Store Name: {store.name}")
        print(f"Store ID: {store.id}")
        print(f"Owner: {store.owner.email}")
        print(f"Slug: {store.slug}")
        print(f"Payment Made: {store.has_made_payment}")
        print(f"DNS Created: {store.dns_record_created}")
        print(f"Current Domain: {store.domain_name or 'Not set'}")
        print(f"{'='*60}\n")
        
        if store.dns_record_created:
            print("⚠️  DNS already created for this store")
            print(f"Domain: {store.domain_name}")
            return
        
        if not store.has_made_payment:
            print("⚠️  Store has not made payment yet")
            return
        
        print("🚀 Starting DNS creation...")
        create_store_domain_after_payment(store)
        
        # Refresh from database
        store.refresh_from_db()
        
        print(f"\n{'='*60}")
        print(f"DNS Creation Result")
        print(f"{'='*60}")
        print(f"DNS Created: {store.dns_record_created}")
        print(f"Domain Name: {store.domain_name or 'Not set'}")
        print(f"{'='*60}\n")
        
        if store.dns_record_created:
            print("✅ DNS creation successful!")
        else:
            print("❌ DNS creation failed - check logs above")
            
    except Store.DoesNotExist:
        print(f"❌ Store with ID {store_id} not found")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_dns_creation.py <store_id>")
        print("\nRecent stores with payment:")
        try:
            stores = Store.objects.filter(has_made_payment=True).order_by('-created_at')[:5]
            for store in stores:
                status = "✓" if store.dns_record_created else "✗"
                print(f"  {status} ID: {store.id} - {store.name} ({store.owner.email})")
        except Exception as e:
            print(f"Error listing stores: {e}")
        sys.exit(1)
    
    store_id = sys.argv[1]
    test_dns_creation(store_id)
