# 🚀 RockTea PL API

**Your Complete Dropshipping Platform** - Custom domains, product selection, and seamless e-commerce. Start your business effortlessly.

![Django](https://img.shields.io/badge/django-%23092E20.svg?style=for-the-badge&logo=django&logoColor=white)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Redis](https://img.shields.io/badge/redis-%23DD0031.svg?style=for-the-badge&logo=redis&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/postgresql-%23316192.svg?style=for-the-badge&logo=postgresql&logoColor=white)

## 🌟 Features

- **Multi-tenant Dropshipping Platform** - Custom domains for each store
- **Automated DNS Management** - AWS Route53 integration
- **Real-time Email Notifications** - Celery + Redis background processing
- **Payment Integration** - Paystack payment gateway
- **Shipping Management** - Shipbubble API integration
- **Media Management** - Cloudinary integration
- **Admin Dashboard** - Store management and analytics
- **RESTful API** - Complete API for frontend integration

## 🛠️ Tech Stack

- **Backend**: Django 4.2+ with Django REST Framework
- **Database**: PostgreSQL with connection pooling
- **Cache/Queue**: Redis for caching and Celery task queue
- **Email**: Brevo API with background processing
- **Storage**: Cloudinary for media files, WhiteNoise for static files
- **DNS**: AWS Route53 for custom domain management
- **Monitoring**: Sentry for error tracking

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 12+
- Redis 6+
- Node.js (for frontend assets)

### Development Setup

```bash
# Clone repository
git clone https://github.com/yourusername/rocktea-mall-api.git
cd rocktea-mall-api

# Create virtual environment
py -3 -m venv .venv                    # Windows
python3 -m venv venv                   # Linux/macOS

# Activate environment
.\venv\Scripts\activate                 # Windows
source venv/bin/activate               # Linux/macOS

# Install dependencies
pip install -r ./main/requirements.txt

# Setup environment variables
cp main/setup/.env.example main/setup/.env
# Edit .env with your configuration

# Run migrations
python ./main/manage.py makemigrations
python ./main/manage.py migrate

# Create superuser
python ./main/manage.py createsuperuser

# Start development server
python ./main/manage.py runserver
```

### Environment Variables

Create `main/setup/.env` with:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/rocktea_mall
REDIS_URL=redis://localhost:6379/0

# AWS Configuration
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
ROUTE53_PRODUCTION_HOSTED_ZONE_ID=your_hosted_zone_id

# Email Service (Brevo)
BREVO_API_KEY=your_brevo_api_key
SENDER_NAME=RockTea PL
SENDER_EMAIL=noreply@yourockteamall.com

# Payment (Paystack)
TEST_PUBLIC_KEY=pk_test_your_paystack_public_key
TEST_SECRET_KEY=sk_test_your_paystack_secret_key

# Shipping (Shipbubble)
SHIPBUBBLE_API_KEY=your_shipbubble_api_key
SHIPBUBBLE_API_URL=https://api.shipbubble.com

# Media Storage (Cloudinary)
CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name

# Environment
ENVIRONMENT=local  # local, dev, prod
DEBUG=True
```

## 📦 Production Deployment

### Ubuntu Server Setup

1. **Upload service files to server:**
```bash
scp celery-worker-concurrent.service fix_celery_service.sh ubuntu@your-server:/home/ubuntu/
```

2. **Install and configure services:**
```bash
ssh ubuntu@your-server
chmod +x fix_celery_service.sh
sudo ./fix_celery_service.sh
```

3. **Verify deployment:**
```bash
# Check services
sudo systemctl status celery-worker-rocktea
python3 monitor_email_queue.py

# View logs
sudo tail -f /var/log/celery/worker.log
```

## 🔧 Development Commands

### Database Management
```bash
# Create migrations
python ./main/manage.py makemigrations

# Apply migrations
python ./main/manage.py migrate

# Show migration status
python ./main/manage.py showmigrations mall

# Rollback migration
python ./main/manage.py migrate mall 0049_customuser_is_verified

# Reset database (careful!)
python ./main/manage.py flush
```

### Package Management
```bash
# Upgrade pip
python -m pip install --upgrade pip

# Install new package
pip install package_name
pip freeze > ./main/requirements.txt

# Leave virtual environment
deactivate
```

## 📧 Email System Management

### Development
```bash
# Start Celery worker locally
celery -A setup worker --loglevel=info

# Start Celery beat scheduler
celery -A setup beat --loglevel=info

# Monitor tasks
celery -A setup flower
```

### Production
```bash
# Check email system health
python3 monitor_email_queue.py

# Manage Celery services
sudo systemctl status celery-worker-rocktea    # Check status
sudo systemctl restart celery-worker-rocktea   # Restart worker
sudo systemctl stop celery-worker-rocktea      # Stop worker
sudo systemctl start celery-worker-rocktea     # Start worker

# View email processing logs
sudo tail -f /var/log/celery/worker.log

# Check email queue length
redis-cli llen celery

# Clear failed tasks (if needed)
redis-cli flushdb
```

### Fix Permissions (if needed)
```bash
chmod +x fix_celery_permissions.sh
sudo ./fix_celery_permissions.sh
```

## 🏗️ Project Structure

```
rocktea-mall-api/
├── main/
│   ├── setup/                 # Django settings and configuration
│   │   ├── settings.py        # Main settings
│   │   ├── celery.py         # Celery configuration
│   │   ├── tasks.py          # Background tasks
│   │   └── utils.py          # Utility functions
│   ├── mall/                 # Core application
│   │   ├── models.py         # Database models
│   │   ├── views.py          # API views
│   │   ├── serializers.py    # DRF serializers
│   │   ├── signals.py        # Django signals
│   │   └── utils.py          # Helper functions
│   ├── order/                # Order management
│   ├── dropshippers/         # Dropshipper management
│   ├── workshop/             # AWS Route53 integration
│   ├── templates/            # Email templates
│   └── static/               # Static files
├── requirements.txt          # Python dependencies
├── celery-worker-concurrent.service  # Production Celery config
├── monitor_email_queue.py    # Health monitoring script
└── README.md                # This file
```

## 🔍 API Endpoints

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/register/` - User registration
- `POST /api/auth/refresh/` - Token refresh

### Stores
- `GET /api/stores/` - List stores
- `POST /api/stores/` - Create store
- `GET /api/stores/{id}/` - Store details
- `PUT /api/stores/{id}/` - Update store
- `DELETE /api/stores/{id}/` - Delete store

### Products
- `GET /api/products/` - List products
- `POST /api/products/` - Add product
- `GET /api/products/{id}/` - Product details

### Orders
- `GET /api/orders/` - List orders
- `POST /api/orders/` - Create order
- `POST /api/webhooks/paystack/` - Payment webhook

## 🧪 Testing

```bash
# Run all tests
python ./main/manage.py test

# Run specific app tests
python ./main/manage.py test mall

# Run with coverage
coverage run --source='.' ./main/manage.py test
coverage report
```

## 🚨 Troubleshooting

### Email Issues
1. Check Celery worker: `sudo systemctl status celery-worker-rocktea`
2. Check Redis: `redis-cli ping`
3. View logs: `sudo tail -f /var/log/celery/worker.log`
4. Run health check: `python3 monitor_email_queue.py`

### Database Issues
1. Check connection: `python ./main/manage.py dbshell`
2. Reset migrations: `python ./main/manage.py migrate --fake-initial`
3. Check migration status: `python ./main/manage.py showmigrations`

### DNS Issues
1. Verify AWS credentials in `.env`
2. Check Route53 hosted zone ID
3. Review DNS creation logs in Celery worker logs

## 📊 Monitoring

### Health Checks
```bash
# System health
python3 monitor_email_queue.py

# Service status
sudo systemctl status celery-worker-rocktea
sudo systemctl status postgresql
sudo systemctl status redis-server

# Resource usage
htop
df -h
```

### Log Files
- **Application**: `./main/logs/django.log`
- **Celery Worker**: `/var/log/celery/worker.log`
- **Celery Beat**: `/var/log/celery/beat.log`
- **System**: `/var/log/syslog`

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: [Wiki](https://github.com/yourusername/rocktea-mall-api/wiki)
- **Issues**: [GitHub Issues](https://github.com/yourusername/rocktea-mall-api/issues)
- **Email**: support@yourockteamall.com

---

**Built with ❤️ by the RockTea PL Team**