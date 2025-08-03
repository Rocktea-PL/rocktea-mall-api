import os
import sys

# FORCE DEBUG FROM ENVIRONMENT FIRST
os.environ['DJANGO_DEBUG'] = 'True'  # Add this line
from pathlib import Path
import environ
from datetime import timedelta
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import socket
from django.core.management.utils import get_random_secret_key  # For generating secure keys
from .config import load_env

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Check if we're in a CI environment
CI_ENVIRONMENT = os.environ.get('CI', False)

if CI_ENVIRONMENT:
    # Create a mock environment for CI
    env = environ.Env()
    print("CI environment detected - using mock settings", file=sys.stderr)
else:
    # Load real environment
    env = load_env()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# =====================
# SECURITY CONFIGURATION
# =====================
# Safely get SECRET_KEY without causing recursion
try:
    SECRET_KEY = env('SECRET_KEY')
    if len(SECRET_KEY) < 50 or 'django-insecure' in SECRET_KEY:
        raise ValueError("Invalid SECRET_KEY")
except (KeyError, ValueError):
    SECRET_KEY = get_random_secret_key()
    os.environ['SECRET_KEY'] = SECRET_KEY
    print("WARNING: Generated new secure SECRET_KEY", file=sys.stderr)

# Environment detection
PRODUCTION = env('ENV', default='development') == 'production'
ENVIRONMENT = env('ENVIRONMENT', default='development')
ENV = env('ENV', default='development')
# Debug settings
DEBUG = env.bool('DJANGO_DEBUG', default=not PRODUCTION)
os.environ['DJANGO_DEBUG'] = str(DEBUG)


# Security settings
if PRODUCTION:
    ALLOWED_HOSTS = [
        "rocktea-mall.vercel.app",
        "rocktea-dropshippers.vercel.app",
        "rocktea-users.vercel.app",

        # API Domains
        "api-dev.yourockteamall.com",
        "api.yourockteamall.com",
        "rocktea-mall-api-production.up.railway.app",
        "rocktea-mall-api-test.up.railway.app", # Keep test API if it's still used

        # Frontend Domains (if they hit this Django app directly for any reason, e.g., static files)
        '.yourockteamall.com',  # Allows any subdomain of yourockteamall.com
        '.user-dev.yourockteamall.com',
        "user-dev.yourockteamall.com",
        "www.user-dev.yourockteamall.com",
        "yourockteamall.com",
        "www.yourockteamall.com",
        "dropshippers.yourockteamall.com",
        "www.dropshippers.yourockteamall.com",
        "dropshippers-dev.yourockteamall.com",
        "www.dropshippers-dev.yourockteamall.com",
        "admin.yourockteamall.com",
        "www.admin.yourockteamall.com",
        "admin-dev.yourockteamall.com",
        "www.admin-dev.yourockteamall.com",
        
        # Direct IP access
        "18.217.233.199",
        
        # Internal hostname resolution
        socket.gethostname()
    ]
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_BROWSER_XSS_FILTER = True
else:
    ALLOWED_HOSTS = ["*"]
    SECURE_SSL_REDIRECT = False

# Security headers
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
X_FRAME_OPTIONS = "DENY"


# =====================
# APPLICATION CONFIG
# =====================
INSTALLED_APPS = [
    "django.contrib.admin",
    "mall.apps.MallConfig",
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    "django_phonenumbers",
    # "cloudinary_storage",
    'multiselectfield',
    'rest_framework_simplejwt',
    'rest_framework',
    'django_rest_passwordreset',
    'django_filters',
    'django_extensions',
    "corsheaders",
    'drf_yasg',
    "whitenoise.runserver_nostatic",

    'django_celery_beat',

    # Your apps
    "order",
    "services",
    "dropshippers",
    "accounts",
    "dashboards",
    "products",
    "admin_orders",
]

# Conditionally add Cloudinary only in non-CI environments
if not CI_ENVIRONMENT:
    INSTALLED_APPS.append("cloudinary_storage")
    # INSTALLED_APPS.append("cloudinary")
    print("Added Cloudinary to INSTALLED_APPS", file=sys.stderr)

# Corrected middleware order with all security middleware
MIDDLEWARE = [
    # Security middleware must come first
    'django.middleware.security.SecurityMiddleware',
    
    # Performance monitoring (disabled for now)
    # 'mall.performance_middleware.PerformanceMonitoringMiddleware',
    # 'mall.performance_middleware.CacheHitRateMiddleware',
    
    # File validation (simple version without python-magic)
    'mall.simple_file_validation.SimpleFileUploadMiddleware',
    
    # Other middleware
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    
    # CSRF protection
    'django.middleware.csrf.CsrfViewMiddleware',
    
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Clickjacking protection
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'mall.middleware.RequestMiddleware',
    'mall.middleware.SubdomainMiddleware',
]

# Set debug environment variable
os.environ['DJANGO_DEBUG'] = str(DEBUG)

ROOT_URLCONF = 'setup.urls'
WSGI_APPLICATION = 'setup.wsgi.application'

# =====================
# DATABASE & CACHE
# =====================
# =====================
# DATABASE & CACHE - WITH CI DEFAULTS
# =====================
if CI_ENVIRONMENT:
    # Use SQLite for CI tests
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
    
    # Mock cache for CI
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }

    REDIS_URL = "redis://dummy:6379/0" 
else:
    # Real database configuration
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': env('PGDATABASE'),
            'USER': env('PGUSER'),
            'PASSWORD': env('PGPASSWORD'),
            'HOST': env('PGHOST'),
            'PORT': env('PGPORT'),
            'CONN_MAX_AGE': 600,
        }
    }

    REDIS_HOST = env("REDISHOST", default='localhost')
    REDIS_PORT = env("REDISPORT", default='6379')
    REDIS_PASSWORD = env("REDISPASSWORD", default=None)
    REDIS_URL = env("REDIS_URL", default=f"redis://{REDIS_HOST}:{REDIS_PORT}/0")
    
    # Enhanced cache configuration with memory management
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
            "OPTIONS": {
                "PASSWORD": REDIS_PASSWORD,
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
                "CONNECTION_POOL_KWARGS": {
                    "max_connections": 50,
                    "retry_on_timeout": True,
                    "health_check_interval": 30,
                },
                "COMPRESSOR": "django_redis.compressors.zlib.ZlibCompressor",
                "IGNORE_EXCEPTIONS": True,
                "REDIS_CLIENT_KWARGS": {
                    "health_check_interval": 30,
                },
            },
            "KEY_PREFIX": "rocktea",
            "TIMEOUT": 300,  # 5 minutes default
        }
    }

# Redis memory optimization
REDIS_MAX_MEMORY = "256mb"  # Adjust based on your server
REDIS_EVICTION_POLICY = "allkeys-lru"  # Evict least recently used keys

# Database query optimizations
DATABASE_ROUTERS = []

# Cache timeouts for different data types
CACHE_TIMEOUTS = {
    'products': 60 * 15,      # 15 minutes
    'categories': 60 * 60,    # 1 hour  
    'stores': 60 * 30,        # 30 minutes
    'orders': 60 * 5,         # 5 minutes
    'marketplace': 60 * 10,   # 10 minutes
}

# File upload limits (5MB)
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024  # 5MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Session optimization using Redis
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_SAVE_EVERY_REQUEST = False
SESSION_EXPIRE_AT_BROWSER_CLOSE = False

# Optimized logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'django.log',
            'maxBytes': 1024*1024*5,  # 5MB
            'backupCount': 3,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': 'WARNING',
            'propagate': True,
        },
        'mall': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# =====================
# REST FRAMEWORK
# =====================
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.BasicAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else None,
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/hour',
        'user': '1000/hour'
    }
}

SIMPLE_JWT = {
    'USER_ID_FIELD': 'id',
    "ACCESS_TOKEN_LIFETIME": timedelta(days=14),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
}


# =====================
# STATIC & MEDIA FILES
# =====================
# =====================
# STATIC FILES - WHITENOISE ONLY
# =====================
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'main', 'static'),
]

# Static file finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Storage configuration - WhiteNoise for static, Cloudinary for media
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage" if CI_ENVIRONMENT 
                  else "cloudinary_storage.storage.MediaCloudinaryStorage"
    }
}

# WhiteNoise configuration for static files
WHITENOISE_USE_FINDERS = True
WHITENOISE_AUTOREFRESH = DEBUG
WHITENOISE_MAX_AGE = 31536000 if PRODUCTION else 0  # 1 year cache in production
WHITENOISE_SKIP_COMPRESS_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'zip', 'gz', 'tgz', 'bz2', 'tbz', 'xz', 'br']
WHITENOISE_MIMETYPES = {
    '.js': 'application/javascript',
    '.css': 'text/css',
    '.woff': 'font/woff',
    '.woff2': 'font/woff2',
}
WHITENOISE_STATIC_PREFIX = '/static/'

if not CI_ENVIRONMENT:
    CLOUDINARY_STORAGE = {"CLOUDINARY_URL": env("CLOUDINARY_URL", default="")}
    try:
        import cloudinary
        cloudinary.config(
            cloud_name=env("CLOUDINARY_NAME", default=""),
            api_key=env("CLOUDINARY_API_KEY", default=""),
            api_secret=env("CLOUDINARY_SECRET", default="")
        )
        print("Cloudinary configured", file=sys.stderr)
    except ImportError:
        pass

# =====================
# INTERNATIONALIZATION
# =====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# =====================
# CUSTOM CONFIG
# =====================
# AbstractUser
AUTH_USER_MODEL     = "mall.CustomUser"
# Default primary key field type
DEFAULT_AUTO_FIELD  = 'django.db.models.BigAutoField'

# =====================
# EXTERNAL SERVICES
# =====================
# Sentry - only initialize if DSN is provided
if sentry_dsn := env("DSN", default=""):
    sentry_sdk.init(
        dsn=env("DSN", default=""),
        traces_sample_rate=1.0,  # Reduced from 100 to 1.0 (0-1 range)
        profiles_sample_rate=1.0,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=True,
                cache_spans=True,
            ),
        ],
    )
else:
    print("Sentry not initialized - DSN not set", file=sys.stderr)

# Email
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
# EMAIL_HOST_USER     = env('EMAIL_HOST_USER')
# EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Paystack
# =====================
# EXTERNAL SERVICES
# =====================
# Payment and shipping
TEST_PUBLIC_KEY = env("TEST_PUBLIC_KEY", default="ci_dummy_public_key")
TEST_SECRET_KEY = env("TEST_SECRET_KEY", default="ci_dummy_secret_key")
TEST_KEY = env("TEST_KEY", default="ci_dummy_key")

# ... rest of the settings ...

# Shipbubble API keys
SHIPBUBBLE_API_KEY = env("SHIPBUBBLE_API_KEY", default="")
SHIPBUBBLE_API_URL = env("SHIPBUBBLE_API_URL", default="")

# Brevo email service
SENDER_NAME = env("SENDER_NAME", default="")
SENDER_EMAIL = env("SENDER_EMAIL", default="")
BREVO_API_KEY = env("BREVO_API_KEY", default="")

# =====================
# CELERY CONFIGURATION WITH REDIS
# =====================
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = True
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes
CELERY_WORKER_PREFETCH_MULTIPLIER = 4
CELERY_TASK_ACKS_LATE = True
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000
CELERY_WORKER_CONCURRENCY = 4
CELERY_TASK_ROUTES = {
    'setup.tasks.send_email_task': {'queue': 'emails'},
}
CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_FLOWER_BROKER_URL = REDIS_URL

# 24 hours expiration
EMAIL_VERIFICATION_TIMEOUT = 86400

# AWS Route 53 DNS Configuration
# IMPORTANT: Replace with the actual Hosted Zone IDs you copied from Route 53
ROUTE53_PRODUCTION_HOSTED_ZONE_ID = env('ROUTE53_PRODUCTION_HOSTED_ZONE_ID', default='')

# AWS Region for Route 53 API calls (e.g., 'us-east-1', 'eu-west-2')
AWS_REGION_NAME = env('AWS_REGION_NAME', default='us-east-1')
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default='')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default='')

# Domain Configuration
STORE_DOMAINS = {
    'dev': 'user-dev.yourockteamall.com',
    'prod': 'yourockteamall.com'
}

# APPEND_SLASH = False

# CORS
if not PRODUCTION:
    CORS_ALLOW_ALL_ORIGINS = True
else:
    CORS_ALLOWED_ORIGINS = [
        # Local development origins
        "http://localhost:5174",
        "http://localhost:5173",
        "http://127.0.0.1:8000", # If your frontend runs here during dev

        # Your production/staging frontend origins
        "https://user-dev.yourockteamall.com",
        "https://www.user-dev.yourockteamall.com",
        "https://yourockteamall.com",
        "https://www.yourockteamall.com",
        "https://dropshippers.yourockteamall.com",
        "https://www.dropshippers.yourockteamall.com",
        "https://dropshippers-dev.yourockteamall.com",
        "https://www.dropshippers-dev.yourockteamall.com",
        "https://admin.yourockteamall.com",
        "https://www.admin.yourockteamall.com",
        "https://admin-dev.yourockteamall.com",
        "https://www.admin-dev.yourockteamall.com",
    ]

CSRF_TRUSTED_ORIGINS = [
    "https://rocktea-mall.vercel.app",
    "https://rocktea-mall-api-test.up.railway.app",
    "https://rocktea-dropshippers.vercel.app",
    "https://rocktea-users.vercel.app",

    # Local development origins
    "http://localhost:5174",
    "http://localhost:5173",
    "http://127.0.0.1:8000",

    # Your production/staging frontend origins
    "https://user-dev.yourockteamall.com",
    "https://www.user-dev.yourockteamall.com",
    "https://yourockteamall.com",
    "https://www.yourockteamall.com",
    "https://dropshippers.yourockteamall.com",
    "https://www.dropshippers.yourockteamall.com",
    "https://dropshippers-dev.yourockteamall.com",
    "https://www.dropshippers-dev.yourockteamall.com",
    "https://admin.yourockteamall.com",
    "https://www.admin.yourockteamall.com",
    "https://admin-dev.yourockteamall.com",
    "https://www.admin-dev.yourockteamall.com",
]

CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]

# import cloudinary
# import cloudinary.uploader
# import cloudinary.api

# cloudinary.config(
#     cloud_name='your_cloud_name',  # Replace with your cloud name
#     api_key='your_api_key',         # Replace with your API key
#     api_secret='your_api_secret'    # Replace with your API secret
# )

# Use cloudinary_storage for media file uploads
# DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# =====================
# TEMPLATES (Minimal)
# =====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'main/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Remove duplicate WhiteNoise settings

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Remove debug override that causes circular imports
