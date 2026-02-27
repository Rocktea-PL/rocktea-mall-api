#!/bin/bash

# Cleanup and regenerate SSL certificates for rockteapl.com domains

echo "=== Cleaning up rockteapl.com SSL certificates ==="

# Delete rockteapl.com certificates
sudo certbot delete --cert-name api.staging.rockteapl.com --non-interactive
sudo certbot delete --cert-name api.rockteapl.com --non-interactive
sudo certbot delete --cert-name admin.staging.rockteapl.com --non-interactive
sudo certbot delete --cert-name admin.rockteapl.com --non-interactive
sudo certbot delete --cert-name dropshippers.staging.rockteapl.com --non-interactive
sudo certbot delete --cert-name dropshippers.rockteapl.com --non-interactive

echo "=== Removing rockteapl.com server blocks from rocktea-user ==="

# Backup original file
sudo cp /etc/nginx/sites-available/rocktea-user /etc/nginx/sites-available/rocktea-user.backup

# Remove rockteapl.com server blocks (keep only yourockteamall.com)
sudo sed -i '/server_name.*rockteapl\.com/,/^}/d' /etc/nginx/sites-available/rocktea-user

echo "=== Disabling rockteapl.com configs temporarily ==="

# Disable all rockteapl.com configs
sudo rm -f /etc/nginx/sites-enabled/api.staging.rockteapl.com
sudo rm -f /etc/nginx/sites-enabled/api.rockteapl.com
sudo rm -f /etc/nginx/sites-enabled/admin.staging.rockteapl.com
sudo rm -f /etc/nginx/sites-enabled/admin.rockteapl.com
sudo rm -f /etc/nginx/sites-enabled/dropshippers.staging.rockteapl.com
sudo rm -f /etc/nginx/sites-enabled/dropshippers.rockteapl.com
sudo rm -f /etc/nginx/sites-enabled/user.staging.rockteapl.com
sudo rm -f /etc/nginx/sites-enabled/user.rockteapl.com

echo "=== Testing nginx configuration ==="
sudo nginx -t

echo "=== Reloading nginx ==="
sudo systemctl reload nginx

echo "=== Regenerating SSL certificates ==="

# Re-enable configs before certbot
sudo ln -sf /etc/nginx/sites-available/api.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/api.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/admin.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/admin.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/dropshippers.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/dropshippers.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/user.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/user.rockteapl.com /etc/nginx/sites-enabled/

# API Staging
sudo certbot --nginx -d api.staging.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com

# API Production
sudo certbot --nginx -d api.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com

# Admin Staging
sudo certbot --nginx -d admin.staging.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com

# Admin Production
sudo certbot --nginx -d admin.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com

# Dropshippers Staging
sudo certbot --nginx -d dropshippers.staging.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com

# Dropshippers Production
sudo certbot --nginx -d dropshippers.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com

# User Stores - Staging (wildcard)
sudo certbot certonly --dns-route53 \
  -d staging.rockteapl.com \
  -d *.staging.rockteapl.com \
  --non-interactive \
  --agree-tos \
  --email rockteapl1@gmail.com

# User Stores - Production (wildcard)
sudo certbot certonly --dns-route53 \
  -d rockteapl.com \
  -d *.rockteapl.com \
  --non-interactive \
  --agree-tos \
  --email rockteapl1@gmail.com

echo "=== Final nginx test and reload ==="
sudo nginx -t
sudo systemctl reload nginx

echo "=== Done! Verify certificates ==="
sudo certbot certificates
