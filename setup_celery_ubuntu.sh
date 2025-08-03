#!/bin/bash

# Setup script for Celery services on Ubuntu server
# Run this script as root: sudo bash setup_celery_ubuntu.sh

set -e

echo "Setting up Celery services for Rocktea Mall..."

# Create necessary directories
echo "Creating directories..."
mkdir -p /var/log/celery
mkdir -p /var/run/celery

# Set proper ownership
chown ubuntu:www-data /var/log/celery
chown ubuntu:www-data /var/run/celery

# Set proper permissions
chmod 755 /var/log/celery
chmod 755 /var/run/celery

# Stop existing services if running
echo "Stopping existing services..."
systemctl stop celery-worker-rocktea.service 2>/dev/null || true
systemctl stop celery-beat-rocktea.service 2>/dev/null || true

# Copy service files
echo "Installing service files..."
cp celery-worker-rocktea.service /etc/systemd/system/
cp celery-beat-rocktea.service /etc/systemd/system/

# Set proper permissions on service files
chmod 644 /etc/systemd/system/celery-worker-rocktea.service
chmod 644 /etc/systemd/system/celery-beat-rocktea.service

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Enable services
echo "Enabling services..."
systemctl enable celery-worker-rocktea.service
systemctl enable celery-beat-rocktea.service

# Start services
echo "Starting services..."
systemctl start celery-worker-rocktea.service
systemctl start celery-beat-rocktea.service

# Check status
echo "Checking service status..."
systemctl status celery-worker-rocktea.service --no-pager
systemctl status celery-beat-rocktea.service --no-pager

# Create logrotate configuration
echo "Setting up log rotation..."
cat > /etc/logrotate.d/celery-rocktea << 'EOF'
/var/log/celery/*.log {
    daily
    missingok
    rotate 52
    compress
    delaycompress
    notifempty
    create 644 ubuntu www-data
    postrotate
        systemctl reload celery-worker-rocktea.service
    endscript
}
EOF

echo "Setup complete!"
echo ""
echo "Useful commands:"
echo "  Check worker status: sudo systemctl status celery-worker-rocktea"
echo "  Check beat status:   sudo systemctl status celery-beat-rocktea"
echo "  View worker logs:    sudo tail -f /var/log/celery/worker.log"
echo "  View beat logs:      sudo tail -f /var/log/celery/beat.log"
echo "  Restart worker:      sudo systemctl restart celery-worker-rocktea"
echo "  Restart beat:        sudo systemctl restart celery-beat-rocktea"