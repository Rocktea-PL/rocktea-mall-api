#!/usr/bin/env python
import os
import sys
import django

sys.path.insert(0, '/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from mall.models import Store

print("\n" + "="*80)
print("ALL STORES IN DATABASE")
print("="*80)

stores = Store.objects.all().order_by('-created_at')[:10]

if not stores:
    print("No stores found in database")
else:
    for store in stores:
        print(f"\nID: {store.id}")
        print(f"Name: {store.name}")
        print(f"Owner: {store.owner.email}")
        print(f"Slug: {store.slug}")
        print(f"Payment: {store.has_made_payment}")
        print(f"Completed: {store.completed}")
        print(f"DNS Created: {store.dns_record_created}")
        print(f"Domain: {store.domain_name or 'Not set'}")
        print(f"Created: {store.created_at}")
        print("-" * 80)

print(f"\nTotal stores: {Store.objects.count()}")
print(f"Stores with payment: {Store.objects.filter(has_made_payment=True).count()}")
print(f"Stores with DNS: {Store.objects.filter(dns_record_created=True).count()}")
