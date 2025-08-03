# Celery Email System Deployment Guide

## Overview
This guide will help you deploy the optimized Celery email system on your Ubuntu server with reliable email delivery and proper monitoring.

## Files Included
- `celery-worker-rocktea.service` - Optimized worker service
- `celery-beat-rocktea.service` - Beat scheduler service  
- `setup_celery_ubuntu.sh` - Automated setup script
- `monitor_email_queue.py` - Health monitoring script

## Quick Deployment

### 1. Upload Files to Server
```bash
# Upload all files to your server
scp celery-*.service setup_celery_ubuntu.sh monitor_email_queue.py ubuntu@your-server:/home/ubuntu/
```

### 2. Run Setup Script
```bash
# SSH into your server
ssh ubuntu@your-server

# Make setup script executable and run it
chmod +x setup_celery_ubuntu.sh
sudo ./setup_celery_ubuntu.sh
```

### 3. Verify Installation
```bash
# Check service status
sudo systemctl status celery-worker-rocktea
sudo systemctl status celery-beat-rocktea

# Check logs
sudo tail -f /var/log/celery/worker.log
```

## Manual Setup (Alternative)

If you prefer manual setup:

### 1. Stop Existing Services
```bash
sudo systemctl stop celery-worker-rocktea.service
sudo systemctl disable celery-worker-rocktea.service
```

### 2. Create Directories
```bash
sudo mkdir -p /var/log/celery /var/run/celery
sudo chown ubuntu:www-data /var/log/celery /var/run/celery
sudo chmod 755 /var/log/celery /var/run/celery
```

### 3. Install Service Files
```bash
sudo cp celery-worker-rocktea.service /etc/systemd/system/
sudo cp celery-beat-rocktea.service /etc/systemd/system/
sudo chmod 644 /etc/systemd/system/celery-*.service
```

### 4. Enable and Start Services
```bash
sudo systemctl daemon-reload
sudo systemctl enable celery-worker-rocktea celery-beat-rocktea
sudo systemctl start celery-worker-rocktea celery-beat-rocktea
```

## Key Improvements Made

### 1. Email Delivery Reliability
- **Transaction Safety**: Emails now send only after successful database commits
- **Better Retry Logic**: Exponential backoff with jitter for failed emails
- **Timeout Handling**: 30-second timeout with automatic retry
- **Error Classification**: Different handling for client vs server errors

### 2. Celery Worker Optimization
- **Resource Limits**: Memory limit of 512MB per worker
- **Task Limits**: Max 100 tasks per child process to prevent memory leaks
- **Prefetch Control**: Single task prefetch to prevent queue blocking
- **Health Checks**: Automatic restart on failure

### 3. Monitoring and Logging
- **Structured Logging**: Better log format with task IDs
- **Log Rotation**: Automatic log rotation to prevent disk space issues
- **Health Monitoring**: Script to check system health
- **Performance Metrics**: Track email delivery success rates

## Monitoring Commands

### Check System Health
```bash
# Run health check
python3 monitor_email_queue.py

# Check service status
sudo systemctl status celery-worker-rocktea
sudo systemctl status celery-beat-rocktea
```

### View Logs
```bash
# Worker logs
sudo tail -f /var/log/celery/worker.log

# Beat scheduler logs  
sudo tail -f /var/log/celery/beat.log

# Filter for email tasks only
sudo grep "send_email_task" /var/log/celery/worker.log
```

### Queue Management
```bash
# Check queue length
redis-cli -u $CELERY_BROKER_URL llen celery

# Clear failed tasks (if needed)
redis-cli -u $CELERY_BROKER_URL flushdb
```

## Troubleshooting

### Email Not Sending
1. Check worker is running: `sudo systemctl status celery-worker-rocktea`
2. Check Redis connection: `redis-cli ping`
3. Check logs for errors: `sudo tail -f /var/log/celery/worker.log`
4. Run health check: `python3 monitor_email_queue.py`

### High Memory Usage
1. Check worker memory: `ps aux | grep celery`
2. Restart worker: `sudo systemctl restart celery-worker-rocktea`
3. Check for memory leaks in logs

### Queue Backup
1. Check queue length: `redis-cli llen celery`
2. Increase worker concurrency (if needed)
3. Check for stuck tasks in logs

## Performance Tuning

### For High Email Volume
```bash
# Edit service file to increase concurrency
sudo systemctl edit celery-worker-rocktea.service

# Add override:
[Service]
ExecStart=
ExecStart=/home/ubuntu/django-app/dev/venv/bin/celery -A setup worker \
    --loglevel=info \
    --pool=prefork \
    --concurrency=4 \
    --events \
    --time-limit=600 \
    --soft-time-limit=540 \
    --max-tasks-per-child=50 \
    --prefetch-multiplier=1
```

### For Low Memory Servers
```bash
# Reduce memory limit and task count
[Service]
MemoryMax=256M
ExecStart=/home/ubuntu/django-app/dev/venv/bin/celery -A setup worker \
    --max-tasks-per-child=50
```

## Security Notes

- Services run as `ubuntu` user with `www-data` group
- `NoNewPrivileges=true` prevents privilege escalation
- `PrivateTmp=true` provides isolated temporary directories
- Log files have restricted permissions

## Maintenance

### Weekly Tasks
- Check log file sizes: `du -sh /var/log/celery/`
- Review failed task count: `python3 monitor_email_queue.py`
- Check system resources: `htop`

### Monthly Tasks
- Review and clean old logs
- Update dependencies if needed
- Check for Django/Celery updates

## Support

If you encounter issues:
1. Run the health check script
2. Check service logs
3. Verify Redis connectivity
4. Ensure environment variables are set correctly

The system is now optimized for reliable email delivery with proper error handling and monitoring.