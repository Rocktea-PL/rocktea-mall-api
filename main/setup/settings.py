import os
import sys

# FORCE DEBUG FROM ENVIRONMENT FIRST
os.environ['DJANGO_DEBUG'] = 'True'  # Add this line
from pathlib import Path
import environ
from datetime import timedelta
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import cloudinary
import socket
from django.core.management.utils import get_random_secret_key  # For generating secure keys
from .config import load_env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent

# env = environ.Env()
# environ.Env.read_env(os.path.join(BASE_DIR, 'setup/.env'))

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
SECRET_KEY = env('SECRET_KEY')
if len(SECRET_KEY) < 50 or 'django-insecure' in SECRET_KEY:
    print("WARNING: Generating new secure SECRET_KEY", file=sys.stderr)
    SECRET_KEY = get_random_secret_key()
    os.environ['SECRET_KEY'] = SECRET_KEY

# Environment detection
PRODUCTION = env('ENV', default='development') == 'production'
DEBUG = not PRODUCTION
os.environ['DJANGO_DEBUG'] = str(DEBUG)

# # SECURITY WARNING: don't run with debug turned on in production!
# DEBUG = os.environ.get('DJANGO_DEBUG', 'False') == 'True'
# # Immediately re-set environment variable to prevent override
# os.environ['DJANGO_DEBUG'] = str(DEBUG)


# Security settings
if PRODUCTION:
    ALLOWED_HOSTS = [
        "api-dev.yourockteamall.com",
        "rocktea-mall-api-production.up.railway.app",
        "18.217.233.199",
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
    "cloudinary_storage",
    'multiselectfield',
    'rest_framework_simplejwt',
    'rest_framework',
    'django_rest_passwordreset',
    'django_filters',
    'django_extensions',
    "corsheaders",
    'drf_yasg',
    "whitenoise.runserver_nostatic",

    # Your apps
    "order",
    "services",
    "dropshippers",
    "accounts",
    "dashboards",
    "products",
    "admin_orders",
]

# Corrected middleware order with all security middleware
MIDDLEWARE = [
    # Security middleware must come first
    'django.middleware.security.SecurityMiddleware',
    
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
]

# Immediately set environment variable to prevent override
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
        }
    }
    
    # Real cache configuration
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": f"redis://{env('REDISHOST', default='localhost')}:{env('REDISPORT', default='6379')}/0",
            "OPTIONS": {
                "PASSWORD": env('REDISPASSWORD', default=''),
                "CLIENT_CLASS": "django_redis.client.DefaultClient",
            },
        }
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
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ]
}

SIMPLE_JWT = {
    'USER_ID_FIELD': 'id',
    "ACCESS_TOKEN_LIFETIME": timedelta(days=14),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
}


# =====================
# STATIC & MEDIA FILES
# =====================
# Static files
STATIC_URL = 'static/'
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles/'),
]

# Static Files
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Storage
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "media": {
        "BACKEND": "storages.backends.cloudinary.MediaCloudinaryStorage",
    }
}

# Cloudinary with safe defaults
CLOUDINARY_STORAGE = {
    "CLOUDINARY_URL": env("CLOUDINARY_URL", default="cloudinary://dummy:dummy@dummy")
}

cloudinary.config(
  cloud_name=env("CLOUDINARY_NAME", default="dummy"),
  api_key=env("CLOUDINARY_API_KEY", default="dummy"),
  api_secret=env("CLOUDINARY_SECRET", default="dummy")
)

# =====================
# INTERNATIONALIZATION
# =====================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
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
sentry_dsn = env("DSN", default="")
if sentry_dsn:
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
TEST_PUBLIC_KEY = env("TEST_PUBLIC_KEY", default="")
TEST_SECRET_KEY = env("TEST_SECRET_KEY", default="")
TEST_KEY = env("TEST_KEY", default="")

# Shipbubble API keys
SHIPBUBBLE_API_KEY = env("SHIPBUBBLE_API_KEY", default="")
SHIPBUBBLE_API_URL = env("SHIPBUBBLE_API_URL", default="")

# Brevo email service
SENDER_NAME = env("SENDER_NAME", default="")
SENDER_EMAIL = env("SENDER_EMAIL", default="")
BREVO_API_KEY = env("BREVO_API_KEY", default="")

# CORS
CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
    "https://api-dev.yourockteamall.com",
    "https://rocktea-mall.vercel.app",
    "https://rocktea-mall-api-test.up.railway.app",
    "http://localhost:5174",
    "http://localhost:5173",
    "http://127.0.0.1:8000",
    "https://rocktea-dropshippers.vercel.app",
    "https://rocktea-users.vercel.app"
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

# =====================
# TEMPLATES (Minimal)
# =====================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WHITENOISE_ALLOW_ALL_ORIGINS = True
WHITENOISE_AUTOREFRESH = True

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

# ULTIMATE DEBUG OVERRIDE
DEBUG = True
os.environ['DJANGO_DEBUG'] = 'True'


# Add this at the VERY BOTTOM of settings.py
# --------------------------------------------------
# DEBUG OVERRIDE - FORCE PROPER VALUE
# --------------------------------------------------
import sys
from django.conf import settings

# Check if DEBUG was changed by Django internals
if settings.DEBUG != DEBUG:
    print(f"\nWARNING: DEBUG was changed from {DEBUG} to {settings.DEBUG}!", file=sys.stderr)
    print("Forcing DEBUG to original value...", file=sys.stderr)
    settings.DEBUG = DEBUG
