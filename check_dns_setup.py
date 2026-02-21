#!/usr/bin/env python
"""
Quick diagnostic script to check DNS/Route53 setup
Run on server:
  cd /home/ubuntu/django-app/dev
  source venv/bin/activate
  python check_dns_setup.py
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, '/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.conf import settings
import boto3
from botocore.exceptions import ClientError

print("=" * 60)
print("DNS SETUP DIAGNOSTIC")
print("=" * 60)

# 1. Check environment variables
print("\n1. Environment Configuration:")
print(f"   ENVIRONMENT: {settings.ENVIRONMENT}")
print(f"   AWS_ACCESS_KEY_ID: {'✓ Set' if settings.AWS_ACCESS_KEY_ID else '✗ Missing'}")
print(f"   AWS_SECRET_ACCESS_KEY: {'✓ Set' if settings.AWS_SECRET_ACCESS_KEY else '✗ Missing'}")
print(f"   ROUTE53_PRODUCTION_HOSTED_ZONE_ID: {settings.ROUTE53_PRODUCTION_HOSTED_ZONE_ID or '✗ Missing'}")
print(f"   AWS_REGION_NAME: {settings.AWS_REGION_NAME}")

# 2. Test AWS credentials
print("\n2. Testing AWS Credentials:")
try:
    client = boto3.client(
        'route53',
        region_name=settings.AWS_REGION_NAME,
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    response = client.list_hosted_zones()
    print(f"   ✓ AWS credentials valid")
    print(f"   Found {len(response.get('HostedZones', []))} hosted zones")
    
    # Check if our zone exists
    zone_id = settings.ROUTE53_PRODUCTION_HOSTED_ZONE_ID
    if zone_id:
        for zone in response.get('HostedZones', []):
            if zone_id in zone['Id']:
                print(f"   ✓ Hosted zone {zone_id} found: {zone['Name']}")
                break
        else:
            print(f"   ✗ Hosted zone {zone_id} NOT found in your account")
    
except ClientError as e:
    print(f"   ✗ AWS Error: {e}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 3. Check Celery
print("\n3. Checking Celery:")
try:
    from setup.celery import app
    inspect = app.control.inspect()
    active = inspect.active()
    if active:
        print(f"   ✓ Celery workers active: {list(active.keys())}")
    else:
        print(f"   ✗ No active Celery workers found")
except Exception as e:
    print(f"   ✗ Celery check failed: {e}")

# 4. Check Redis
print("\n4. Checking Redis:")
try:
    import redis
    r = redis.from_url(settings.REDIS_URL)
    r.ping()
    queue_length = r.llen('celery')
    print(f"   ✓ Redis connected")
    print(f"   Celery queue length: {queue_length}")
except Exception as e:
    print(f"   ✗ Redis error: {e}")

# 5. Test DNS creation (dry run)
print("\n5. Testing DNS Creation Function:")
try:
    from workshop.route53 import create_cname_record
    print(f"   ✓ Route53 module imported successfully")
    print(f"   Function available: create_cname_record")
except Exception as e:
    print(f"   ✗ Import error: {e}")

# 6. Check recent stores and DNS status
print("\n6. Recent Stores DNS Status:")
try:
    from mall.models import Store
    recent_stores = Store.objects.filter(has_made_payment=True).order_by('-created_at')[:5]
    
    if recent_stores:
        for store in recent_stores:
            status = "✓" if store.dns_record_created else "✗"
            print(f"   {status} {store.name} (ID: {store.id})")
            print(f"      Payment: {store.has_made_payment}, DNS: {store.dns_record_created}")
            print(f"      Domain: {store.domain_name or 'Not set'}")
            print(f"      Slug: {store.slug}")
            print(f"      Created: {store.created_at}")
    else:
        print(f"   No stores with payment found")
except Exception as e:
    print(f"   ✗ Error: {e}")

# 7. Check Django logs for DNS errors
print("\n7. Checking Django Logs:")
try:
    import subprocess
    result = subprocess.run(
        ['tail', '-20', '/home/ubuntu/django-app/dev/main/logs/django.log'],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(f"   Last 20 lines of django.log:")
        for line in result.stdout.split('\n')[-10:]:
            if line.strip():
                print(f"   {line}")
    else:
        print(f"   ✗ Could not read django.log")
except Exception as e:
    print(f"   ✗ Error reading logs: {e}")

print("\n" + "=" * 60)
print("DIAGNOSTIC COMPLETE")
print("=" * 60)
print("\nNext Steps:")
print("1. Check if AWS credentials are set correctly on production server")
print("2. Review django.log for DNS creation errors")
print("3. Test DNS creation manually with a test store")
print("4. Verify Route53 hosted zone ID matches production zone")
