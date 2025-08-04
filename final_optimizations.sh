#!/bin/bash
# Final production optimizations for RockTea Mall

echo "Applying final optimizations..."

# 2. Health check endpoint already added to Django app

# 3. Setup log rotation
sudo tee /etc/logrotate.d/rocktea << 'EOF'
/var/log/gunicorn/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu www-data
    postrotate
        systemctl reload gunicorn-rocktea-prod
    endscript
}
EOF

# 4. Create backup scripts for both dev and prod
sudo tee /usr/local/bin/backup_rocktea_dev.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups/dev"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Load dev environment
source /home/ubuntu/django-app/dev/main/setup/.env

# EC2 PostgreSQL backup
pg_dump -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE > $BACKUP_DIR/dev_backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "dev_backup_*.sql" -mtime +7 -delete

echo "Dev backup completed: $BACKUP_DIR/dev_backup_$DATE.sql"
EOF

sudo tee /usr/local/bin/backup_rocktea_prod.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/home/ubuntu/backups/prod"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

# Load prod environment
source /home/ubuntu/django-app/prod/main/setup/.env

# RDS backup using pg_dump with full connection string
pg_dump -h $PGHOST -p $PGPORT -U $PGUSER -d $PGDATABASE > $BACKUP_DIR/prod_backup_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "prod_backup_*.sql" -mtime +7 -delete

# Upload to S3 for extra safety (optional)
# aws s3 cp $BACKUP_DIR/prod_backup_$DATE.sql s3://your-backup-bucket/

echo "Prod backup completed: $BACKUP_DIR/prod_backup_$DATE.sql"
EOF

sudo chmod +x /usr/local/bin/backup_rocktea_dev.sh
sudo chmod +x /usr/local/bin/backup_rocktea_prod.sh

# 5. Setup daily backup cron for both environments
(crontab -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup_rocktea_dev.sh >> /var/log/backup_dev.log 2>&1") | crontab -
(crontab -l 2>/dev/null; echo "0 3 * * * /usr/local/bin/backup_rocktea_prod.sh >> /var/log/backup_prod.log 2>&1") | crontab -

# 6. Collect static files
cd /home/ubuntu/django-app/prod/main
source ../venv/bin/activate
python manage.py collectstatic --noinput

# 7. Setup process monitoring
sudo tee /etc/systemd/system/rocktea-monitor.service << 'EOF'
[Unit]
Description=RockTea Mall Health Monitor
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/curl -f http://127.0.0.1:8001/health/ || systemctl restart gunicorn-rocktea-prod

[Install]
WantedBy=multi-user.target
EOF

sudo tee /etc/systemd/system/rocktea-monitor.timer << 'EOF'
[Unit]
Description=Run RockTea health check every 5 minutes
Requires=rocktea-monitor.service

[Timer]
OnCalendar=*:0/5
Persistent=true

[Install]
WantedBy=timers.target
EOF

sudo systemctl enable rocktea-monitor.timer
sudo systemctl start rocktea-monitor.timer

echo "Final optimizations complete!"
echo ""
echo "=== Health Monitoring ==="
echo "Health check: curl http://127.0.0.1:8001/health/"
echo "Monitor status: sudo systemctl status rocktea-monitor.timer"
echo ""
echo "=== Backup System ==="
echo "Dev backups: ls -la /home/ubuntu/backups/dev/"
echo "Prod backups: ls -la /home/ubuntu/backups/prod/"
echo "Backup logs: tail -f /var/log/backup_*.log"
echo ""
echo "=== Manual Testing ==="
echo "Test dev backup: sudo /usr/local/bin/backup_rocktea_dev.sh"
echo "Test prod backup: sudo /usr/local/bin/backup_rocktea_prod.sh"
echo "View cron jobs: crontab -l"