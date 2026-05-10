from datetime import timedelta
from pathlib import Path
from decouple import config
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_rq',
    'accounts',
    'sites',
    'analytics',
    'tracking',
    'email_service',
]

MIDDLEWARE = [
    'common.middleware.MetricsMiddleware',
    'common.cors.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'EXCEPTION_HANDLER': 'common.exceptions.custom_exception_handler',
    'DEFAULT_SCHEMA_CLASS': 'common.openapi.EnvelopeAutoSchema',
}

SIMPLE_JWT = {

    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=10),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
}


SPECTACULAR_SETTINGS = {
    'TITLE': 'Metrika API',
    'DESCRIPTION': 'API documentation for Metrika analytics platform',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
}

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

AUTHENTICATION_BACKENDS = ['accounts.backends.CustomModelBackend']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': config('DB_NAME'),
        'USER': config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST'),
        'PORT': config('DB_PORT'),
    }
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": config("REDIS_URI"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher",
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.ScryptPasswordHasher",
]


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8},
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'common.validators.SymbolPasswordValidator',
    },
]

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

STATIC_URL = 'static/'

STATICFILES_DIRS = BASE_DIR / 'static'

AUTH_USER_MODEL = 'accounts.User'

FRONTEND_BASE_URL = config('FRONTEND_BASE_URL')

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

CSRF_COOKIE_HTTPONLY = False
CSRF_TRUSTED_ORIGINS = [FRONTEND_BASE_URL]

REFRESH_TOKEN_COOKIE_NAME = 'refresh_token'
REFRESH_TOKEN_COOKIE_HTTPONLY = True
REFRESH_TOKEN_COOKIE_SAMESITE = 'Strict' if not DEBUG else 'Lax'
REFRESH_TOKEN_MAX_AGE = int(timedelta(days=1).total_seconds())


SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict' if not DEBUG else 'Lax'
SESSION_COOKIE_MAX_AGE = int(timedelta(hours=1).total_seconds())

CORS_ALLOWED_METHODS = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
CORS_ALLOWED_HEADERS = 'Authorization, Content-Type, X-CSRFToken, X-Correlation-ID, X-Tracking-Token'
CORS_MAX_AGE = 86400

EMAIL_CHANGE_TIMEOUT = int(timedelta(hours=24).total_seconds())

GEOIP_PATH = BASE_DIR / 'geoip' / 'GeoLite2-City.mmdb'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'common.logging.JSONFormatter',
        },
        'rq_console': {
            'format': '%(asctime)s %(message)s',
            'datefmt': '%H:%M:%S',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
        'rq_console': {
            'level': 'DEBUG',
            'class': 'rq.logutils.ColorizingStreamHandler',
            'formatter': 'rq_console',
            'exclude': ['%(asctime)s'],
        }
    },
    'root': {
        'level': 'INFO',
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.request': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'accounts': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'analytics': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'sites': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'tracking': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'email_service': {
            'level': 'DEBUG',
            'handlers': ['console'],
            'propagate': False,
        },
        'rq.worker': {
            'handlers': ['rq_console'],
            'level': 'DEBUG',
        }
    },
}

RQ_QUEUES = {
    'default': {
        'USE_REDIS_CACHE': 'default',
        'DEFAULT_TIMEOUT': 360,
        'DEFAULT_RESULT_TTL': 800,
        'REDIS_CLIENT_KWARGS': {    # Eventual additional Redis connection arguments
            'ssl_cert_reqs': None,
        },
    },
    'high': {
        'URL': config('REDISTOGO_URL', 'redis://localhost:6379/1'),  # If you're on Heroku
        'DEFAULT_TIMEOUT': 500,
    },
}

RQ_EXCEPTION_HANDLERS = ['email_service.rq_handlers.email_exception_handler']
