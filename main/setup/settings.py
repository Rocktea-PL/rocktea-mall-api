from pathlib import Path
import environ
import datetime
import os
from datetime import timedelta
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
import cloudinary

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env()

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'staticfiles/'),
    # Add other paths to app-specific static directories if needed
]

# Static Files
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ["*"]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "mall.apps.MallConfig",
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third-parties
    "django_phonenumbers",
    "cloudinary_storage",
    'multiselectfield',
    'rest_framework_simplejwt',
    'rest_framework',
    'django_filters',

    # Caution
    'django_extensions',

    # Security
    "corsheaders",
    "order",
    "services",

    # API Documentation
    'drf_yasg',

    # Storage
    "whitenoise.runserver_nostatic",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # 'mall.middleware.DomainNameMiddleware',
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


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': env('PGDATABASE'),
        'USER': env('PGUSER'),
        'PASSWORD': env('PGPASSWORD'),
        'HOST': env('PGHOST'),
        'PORT': env('PGPORT'),


    },

    #     'production': {
    #         'ENGINE': 'django.db.backends.postgresql_psycopg2',
    #         'NAME': env('DB_NAME'),
    #         'USER': env('DB_USER'),
    #         'PASSWORD': env('DB_PASSWORD'),
    #         'HOST': env('DB_HOST'),
    #         'PORT': env('DB_PORT'),
    #     },
    # }
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
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}

REDIS_HOST = env("REDISHOST")
REDIS_PORT = env("REDISPORT")
REDIS_PASSWORD = env("REDISPASSWORD")
REDIS_URL = env("REDIS_URL")

# settings.py
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
    traces_sample_rate=100,
    profiles_sample_rate=100,
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
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# AbstractUser
AUTH_USER_MODEL = "mall.CustomUser"

# Paystack
TEST_PUBLIC_KEY = env("TEST_PUBLIC_KEY")
TEST_SECRET_KEY = env("TEST_SECRET_KEY")

TEST_KEY = env("TEST_KEY")

cloudinary.config(
  cloud_name = env("CLOUDINARY_NAME"),
  api_key = env("CLOUDINARY_API_KEY"),
  api_secret = env("CLOUDINARY_SECRET")
)