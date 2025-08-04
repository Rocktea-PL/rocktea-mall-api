#!/bin/bash
# Production setup script for RockTea Mall

echo "Setting up production environment..."

# 1. Create log directories
sudo mkdir -p /var/log/gunicorn
sudo mkdir -p /var/run/gunicorn
sudo chown ubuntu:www-data /var/log/gunicorn
sudo chown ubuntu:www-data /var/run/gunicorn

# 2. Set production environment variables
echo "PRODUCTION=true" >> /home/ubuntu/django-app/dev/main/setup/.env
echo "DEBUG=false" >> /home/ubuntu/django-app/dev/main/setup/.env

# 3. Copy optimized service files
sudo cp optimized-gunicorn-rocktea.service /etc/systemd/system/
sudo cp gunicorn.conf.py /home/ubuntu/django-app/dev/

# 4. Reload systemd and restart services
sudo systemctl daemon-reload
sudo systemctl stop gunicorn-rocktea
sudo systemctl start gunicorn-rocktea
sudo systemctl enable gunicorn-rocktea

# 5. Check status
sudo systemctl status gunicorn-rocktea

echo "Production setup complete!"
echo "Monitor with: sudo journalctl -u gunicorn-rocktea -f"