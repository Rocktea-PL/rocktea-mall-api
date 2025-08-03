#!/usr/bin/env python3
"""
Email Queue Monitoring Script for Rocktea Mall
Run this script to check the health of your email processing system.

Usage: python monitor_email_queue.py
"""

import os
import sys
import django
import redis
from datetime import datetime, timedelta

# Setup Django
sys.path.append('/home/ubuntu/django-app/dev/main')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'setup.settings')
django.setup()

from django.conf import settings
from celery import Celery
import logging

logger = logging.getLogger(__name__)

def check_redis_connection():
    """Check if Redis is accessible"""
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        r.ping()
        return True, "Redis connection successful"
    except Exception as e:
        return False, f"Redis connection failed: {e}"

def check_celery_workers():
    """Check if Celery workers are running"""
    try:
        app = Celery('setup')
        app.config_from_object('django.conf:settings', namespace='CELERY')
        
        # Get active workers
        inspect = app.control.inspect()
        active_workers = inspect.active()
        
        if active_workers:
            worker_count = len(active_workers)
            return True, f"Found {worker_count} active worker(s)"
        else:
            return False, "No active workers found"
    except Exception as e:
        return False, f"Failed to check workers: {e}"

def check_queue_length():
    """Check email queue length"""
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        queue_length = r.llen('celery')
        
        if queue_length == 0:
            return True, "Email queue is empty"
        elif queue_length < 10:
            return True, f"Email queue has {queue_length} pending tasks"
        elif queue_length < 50:
            return False, f"Email queue is getting full: {queue_length} pending tasks"
        else:
            return False, f"Email queue is overloaded: {queue_length} pending tasks"
    except Exception as e:
        return False, f"Failed to check queue: {e}"

def check_failed_tasks():
    """Check for failed tasks in the last hour"""
    try:
        r = redis.Redis.from_url(settings.CELERY_BROKER_URL)
        
        # Check for failed tasks (this is a simplified check)
        failed_key = 'celery-task-meta-*'
        failed_count = 0
        
        for key in r.scan_iter(match=failed_key):
            task_data = r.get(key)
            if task_data and b'"FAILURE"' in task_data:
                failed_count += 1
        
        if failed_count == 0:
            return True, "No failed tasks found"
        elif failed_count < 5:
            return True, f"Found {failed_count} failed tasks (acceptable)"
        else:
            return False, f"Found {failed_count} failed tasks (needs attention)"
    except Exception as e:
        return False, f"Failed to check failed tasks: {e}"

def main():
    """Main monitoring function"""
    print("=" * 60)
    print("ROCKTEA MALL EMAIL QUEUE HEALTH CHECK")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    checks = [
        ("Redis Connection", check_redis_connection),
        ("Celery Workers", check_celery_workers),
        ("Queue Length", check_queue_length),
        ("Failed Tasks", check_failed_tasks),
    ]
    
    all_healthy = True
    
    for check_name, check_func in checks:
        try:
            is_healthy, message = check_func()
            status = "✅ HEALTHY" if is_healthy else "❌ ISSUE"
            print(f"{check_name:20} {status:12} {message}")
            
            if not is_healthy:
                all_healthy = False
        except Exception as e:
            print(f"{check_name:20} {'❌ ERROR':12} {e}")
            all_healthy = False
    
    print()
    print("=" * 60)
    
    if all_healthy:
        print("🎉 ALL SYSTEMS HEALTHY - Email processing is working normally")
        sys.exit(0)
    else:
        print("⚠️  ISSUES DETECTED - Check the problems above")
        sys.exit(1)

if __name__ == "__main__":
    main()