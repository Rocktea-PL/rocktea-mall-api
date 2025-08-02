#!/bin/bash

echo "Restarting services to apply email delivery fix..."

# Restart gunicorn to reload Python code
sudo systemctl restart gunicorn-rocktea.service
echo "✅ Gunicorn restarted"

# Restart celery to reload task definitions
sudo systemctl restart celery-worker-rocktea.service
echo "✅ Celery restarted"

# Check service status
echo "Checking service status..."
sudo systemctl status gunicorn-rocktea.service --no-pager -l
sudo systemctl status celery-worker-rocktea.service --no-pager -l

echo "✅ Services restarted. Email delivery should now work properly."