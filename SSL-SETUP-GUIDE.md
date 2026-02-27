# SSL Certificate Setup for rockteapl.com

Complete guide to obtain SSL certificates for all rockteapl.com subdomains.

## Prerequisites

- DNS records must be pointing to your server (34.244.101.132)
- Nginx configs deployed to sites-available
- Port 80 and 443 open

## Step 1: Enable Nginx Configs

```bash
ssh ubuntu@34.244.101.132

# Enable all rockteapl.com configs
sudo ln -sf /etc/nginx/sites-available/api.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/api.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/admin.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/admin.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/dropshippers.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/dropshippers.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/user.staging.rockteapl.com /etc/nginx/sites-enabled/
sudo ln -sf /etc/nginx/sites-available/user.rockteapl.com /etc/nginx/sites-enabled/

# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## Step 2: Install Certbot (if not already installed)

```bash
ssh ubuntu@34.244.101.132

sudo apt update
sudo apt install certbot python3-certbot-nginx -y
```

## Step 3: Obtain SSL Certificates (Non-Interactive)

### API Staging
```bash
sudo certbot --nginx -d api.staging.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com
```

### API Production
```bash
sudo certbot --nginx -d api.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com
```

### Admin Staging
```bash
sudo certbot --nginx -d admin.staging.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com
```

### Admin Production
```bash
sudo certbot --nginx -d admin.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com
```

### Dropshippers Staging
```bash
sudo certbot --nginx -d dropshippers.staging.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com
```

### Dropshippers Production
```bash
sudo certbot --nginx -d dropshippers.rockteapl.com --non-interactive --agree-tos --email rockteapl1@gmail.com
```

### User Stores - Staging (with wildcard using Route53)
```bash
sudo certbot certonly --dns-route53 \
  -d staging.rockteapl.com \
  -d *.staging.rockteapl.com \
  --non-interactive \
  --agree-tos \
  --email rockteapl1@gmail.com
```

### User Stores - Production (with wildcard using Route53)
```bash
sudo certbot certonly --dns-route53 \
  -d rockteapl.com \
  -d *.rockteapl.com \
  --non-interactive \
  --agree-tos \
  --email rockteapl1@gmail.com
```

## Step 4: Configure AWS Credentials for Route53 (Wildcard Certs)

For wildcard certificates, certbot needs AWS credentials:

```bash
# Create AWS credentials file
sudo mkdir -p /root/.aws
sudo nano /root/.aws/credentials
```

Add:
```ini
[default]
aws_access_key_id = YOUR_AWS_ACCESS_KEY_ID
aws_secret_access_key = YOUR_AWS_SECRET_ACCESS_KEY
```

Set permissions:
```bash
sudo chmod 600 /root/.aws/credentials
```

## Step 5: Install Route53 Plugin

```bash
sudo apt install python3-certbot-dns-route53 -y
```

## Step 6: Update Nginx Configs for Wildcard Certs

After obtaining wildcard certificates with `certonly`, update nginx configs:

```bash
sudo nano /etc/nginx/sites-available/user.rockteapl.com
```

Ensure SSL paths point to the wildcard certificates (already configured in the provided config).

```bash
# Test and reload
sudo nginx -t
sudo systemctl reload nginx
```

## Step 7: Verify SSL Certificates

```bash
# List all certificates
sudo certbot certificates

# Test nginx configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

## Step 8: Test HTTPS Access

```bash
# Test each domain
curl -I https://api.staging.rockteapl.com
curl -I https://api.rockteapl.com
curl -I https://admin.staging.rockteapl.com
curl -I https://admin.rockteapl.com
curl -I https://dropshippers.staging.rockteapl.com
curl -I https://dropshippers.rockteapl.com
curl -I https://staging.rockteapl.com
curl -I https://rockteapl.com
```

## Auto-Renewal

Certbot automatically renews ALL certificates (including wildcards) using the same method they were obtained with.

### How It Works
- Certbot timer runs twice daily
- Renews certificates within 30 days of expiry
- Wildcard certs auto-renew via Route53 DNS validation
- Non-wildcard certs auto-renew via nginx plugin
- No manual intervention needed
- **--expand is NOT needed** - Your wildcard and non-wildcard certs are separate (correct setup)

### Verify Auto-Renewal Setup

```bash
# Test renewal (dry-run - doesn't actually renew)
sudo certbot renew --dry-run

# Check renewal timer is active
sudo systemctl status certbot.timer

# View renewal configuration for each cert
sudo certbot certificates
```

### Important for Wildcard Renewals

AWS credentials in `/root/.aws/credentials` must remain accessible:

```bash
# Verify credentials file exists and has correct permissions
sudo ls -la /root/.aws/credentials
# Should show: -rw------- (600 permissions)

# Test Route53 access for wildcard renewal
sudo certbot renew --cert-name rockteapl.com --dry-run
```

### Manual Renewal (if needed)

```bash
# Renew all certificates
sudo certbot renew

# Renew specific certificate
sudo certbot renew --cert-name rockteapl.com

# Force renewal (even if not due)
sudo certbot renew --force-renewal
```

## Troubleshooting

### Certificate Request Failed
```bash
# Check DNS propagation
dig api.staging.rockteapl.com +short

# Check nginx is running
sudo systemctl status nginx

# Check port 80 is accessible
sudo netstat -tlnp | grep :80
```

### Wildcard Certificate Issues
```bash
# Verify TXT record
dig _acme-challenge.staging.rockteapl.com TXT +short

# Wait longer for DNS propagation
sleep 120
```

### Certificate Not Applied
```bash
# Check nginx config
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx

# Check certificate paths
sudo ls -la /etc/letsencrypt/live/
```

## Certificate Locations

After successful setup:
- `/etc/letsencrypt/live/api.staging.rockteapl.com/`
- `/etc/letsencrypt/live/api.rockteapl.com/`
- `/etc/letsencrypt/live/admin.staging.rockteapl.com/`
- `/etc/letsencrypt/live/admin.rockteapl.com/`
- `/etc/letsencrypt/live/dropshippers.staging.rockteapl.com/`
- `/etc/letsencrypt/live/dropshippers.rockteapl.com/`
- `/etc/letsencrypt/live/staging.rockteapl.com/`
- `/etc/letsencrypt/live/rockteapl.com/`

## Timeline

- Non-wildcard certificates: 2-5 minutes each
- Wildcard certificates: 5-10 minutes each (DNS validation)
- Total time: ~30-45 minutes for all certificates
