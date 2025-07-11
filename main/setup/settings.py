from pathlib import Path
import environ
import os
from datetime import timedelta
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import cloudinary
import socket
import sys  # Added for sys.stderr output
from django.core.management.utils import get_random_secret_key  # For generating secure keys
from .config import load_env

# Build paths inside the project like this: BASE_DIR / 'subdir'.
# BASE_DIR = Path(__file__).resolve().parent.parent

# env = environ.Env()
# environ.Env.read_env(os.path.join(BASE_DIR, 'setup/.env'))

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# env = environ.Env()
# # Path to .env file - adjust to your structure
# env_path = BASE_DIR / 'main' / 'setup' / '.env'
# environ.Env.read_env(env_path)

env = load_env()


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# Generate new secret key if current one is insecure
current_secret = env('SECRET_KEY')
if len(current_secret) < 50 or 'django-insecure' in current_secret:
    print("WARNING: Generating new secure SECRET_KEY", file=sys.stderr)
    new_secret = get_random_secret_key()
    os.environ['SECRET_KEY'] = new_secret
    SECRET_KEY = new_secret
else:
    SECRET_KEY = current_secret

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles/'),
]

# Static Files
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', default=False)  # Use boolean conversion

# After BASE_DIR definition
print(f"\n\n=== PATH DEBUGGING ===", file=sys.stderr)
print(f"Settings file: {__file__}", file=sys.stderr)
print(f"BASE_DIR: {BASE_DIR}", file=sys.stderr)
print(f"Static files dir: {os.path.join(BASE_DIR, 'staticfiles/')}", file=sys.stderr)

# After env loading
print(f"\nEnvironment Variables:", file=sys.stderr)
print(f"DEBUG: {DEBUG}", file=sys.stderr)
print(f"SECRET_KEY: {SECRET_KEY[:5]}...{SECRET_KEY[-5:]}", file=sys.stderr)
print(f"PGHOST: {env('PGHOST')}", file=sys.stderr)

# Security Settings
if DEBUG:
    ALLOWED_HOSTS = ["*", "localhost"]
    # Debug-specific security settings
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
else:
    ALLOWED_HOSTS = [
        "12.0.0.1",
        "rocktea-mall-api-test.up.railway.app",
        "rocktea-mall-api-production.up.railway.app",
        "rocktea-mall.vercel.app",
        "localhost",
        "18.217.233.199",
        socket.gethostname()
    ]
    # Production security settings
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# Security headers - apply regardless of DEBUG mode
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin-allow-popups"
X_FRAME_OPTIONS = "DENY"

# Application definition
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

ROOT_URLCONF = 'setup.urls'

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

# Storage
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "media": {
        "BACKEND": "storages.backends.cloudinary.MediaCloudinaryStorage",
    }
}

WHITENOISE_ALLOW_ALL_ORIGINS = True
WHITENOISE_AUTOREFRESH = True

WSGI_APPLICATION = 'setup.wsgi.application'

# Database configuration
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

CORS_ALLOW_ALL_ORIGINS = True

CSRF_TRUSTED_ORIGINS = [
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

# File Storage
CLOUDINARY_STORAGE = {
    "CLOUDINARY_URL": env("CLOUDINARY_URL")
}

SIMPLE_JWT = {
    'USER_ID_FIELD': 'id',
    "ACCESS_TOKEN_LIFETIME": timedelta(days=14),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=14),
}

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

REDIS_HOST = env("REDISHOST")
REDIS_PORT = env("REDISPORT")
REDIS_PASSWORD = env("REDISPASSWORD")
REDIS_URL = env("REDIS_URL")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"redis://{REDIS_HOST}:{REDIS_PORT}/0",
        "OPTIONS": {
            "PASSWORD": REDIS_PASSWORD,
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

sentry_sdk.init(
    dsn=env("DSN"),
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

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files
STATIC_URL = 'static/'

# Default primary key field type
DEFAULT_AUTO_FIELD  = 'django.db.models.BigAutoField'

# AbstractUser
AUTH_USER_MODEL     = "mall.CustomUser"

# Paystack
TEST_PUBLIC_KEY = env("TEST_PUBLIC_KEY")
TEST_SECRET_KEY = env("TEST_SECRET_KEY")
TEST_KEY = env("TEST_KEY")

cloudinary.config(
  cloud_name    = env("CLOUDINARY_NAME"),
  api_key       = env("CLOUDINARY_API_KEY"),
  api_secret    = env("CLOUDINARY_SECRET")
)

# Email configuration
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')

# Shipbubble API keys
SHIPBUBBLE_API_KEY = env("SHIPBUBBLE_API_KEY")
SHIPBUBBLE_API_URL = env("SHIPBUBBLE_API_URL")

# Brevo email service
SENDER_NAME = env("SENDER_NAME")
SENDER_EMAIL = env("SENDER_EMAIL")
BREVO_API_KEY = env("BREVO_API_KEY")

# Print security status for verification
print(f"\nSecurity Configuration Summary:", file=sys.stderr)
print(f"DEBUG: {DEBUG}", file=sys.stderr)
print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}", file=sys.stderr)
print(f"SECURE_HSTS_SECONDS: {SECURE_HSTS_SECONDS}", file=sys.stderr)
print(f"X_FRAME_OPTIONS: {X_FRAME_OPTIONS}", file=sys.stderr)
print(f"SECRET_KEY length: {len(SECRET_KEY)} characters", file=sys.stderr)