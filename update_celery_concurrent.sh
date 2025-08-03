#!/bin/bash

echo "Updating Celery to support concurrent email processing..."

# Stop current service
sudo systemctl stop celery-worker-rocktea.service

# Install new concurrent service
sudo cp celery-worker-concurrent.service /etc/systemd/system/celery-worker-rocktea.service
sudo chmod 644 /etc/systemd/system/celery-worker-rocktea.service

# Reload and restart
sudo systemctl daemon-reload
sudo systemctl start celery-worker-rocktea.service

echo "Celery updated for concurrent processing. Checking status..."
sleep 3
sudo systemctl status celery-worker-rocktea.service --no-pager

echo ""
echo "Email processing is now concurrent - multiple emails can be sent simultaneously!"