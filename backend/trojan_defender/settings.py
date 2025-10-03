import os
import logging
from datetime import timedelta
from pathlib import Path
from dotenv import load_dotenv
import re

# Load environment variables from .env file
# Load from .env.local first (for development with real credentials)
load_dotenv('.env.local')
# Then load from .env (for defaults and placeholders)
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is required")

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get('DEBUG', 0))

# Configure error handlers for production
if not DEBUG:
    HANDLER400 = 'trojan_defender.production_error_handlers.handle_400'
    HANDLER403 = 'trojan_defender.production_error_handlers.handle_403'
    HANDLER404 = 'trojan_defender.production_error_handlers.handle_404'
    HANDLER500 = 'trojan_defender.production_error_handlers.handle_500'

# Parse ALLOWED_HOSTS allowing comma or whitespace separators
_allowed_hosts_env = os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]')
ALLOWED_HOSTS = [h.strip() for h in re.split(r"[\s,]+", _allowed_hosts_env) if h.strip()]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'drf_yasg',  # Added for Swagger/OpenAPI documentation
    'corsheaders',
    'channels',
    'api',
    'users',
    'scanner',
    'threatmap',
    'notifications',
    'threat_intelligence',
    'reports',
    'threat_map',
]

MIDDLEWARE = [
    # Core Django security and session middleware (must be early)
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    # Ensure responses are processed correctly by CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    
    # Custom security middleware (after authentication)
    'trojan_defender.middleware.SecurityHeadersMiddleware',
    'trojan_defender.middleware.RequestSizeMiddleware',
    'trojan_defender.ip_security.IPSecurityMiddleware',
    'trojan_defender.rate_limiting.RateLimitMiddleware',
    'trojan_defender.content_security.ContentSecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'trojan_defender.middleware.SessionSecurityMiddleware',
    'trojan_defender.middleware.SecurityLoggingMiddleware',
    'trojan_defender.middleware.BruteForceProtectionMiddleware',
    
    # Cache middleware (after authentication and security) - DISABLED due to conflicts
    # 'trojan_defender.cache_middleware.CacheControlMiddleware',
    # 'trojan_defender.cache_middleware.CacheInvalidationMiddleware',
    # 'trojan_defender.cache_middleware.CacheWarmupMiddleware',
    
    # Final security middleware
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trojan_defender.urls'

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

WSGI_APPLICATION = 'trojan_defender.wsgi.application'
ASGI_APPLICATION = 'trojan_defender.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3'),
        'NAME': os.environ.get('DB_NAME', BASE_DIR / 'db.sqlite3'),
        'USER': os.environ.get('DB_USER', ''),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', ''),
        'PORT': os.environ.get('DB_PORT', ''),
        # Connection pooling settings
        'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', 600)),  # Keep connections alive for 10 minutes
        'CONN_HEALTH_CHECKS': True,  # Enable connection health checks
        'OPTIONS': {
            # Only add sslmode for PostgreSQL
            **(
                {'sslmode': 'disable', 'options': '-c statement_timeout=5000'}
                if os.environ.get('DB_ENGINE', 'django.db.backends.sqlite3') == 'django.db.backends.postgresql'
                else {}
            ),
        },
        'ATOMIC_REQUESTS': False,  # Set to True to wrap each request in a transaction
        'AUTOCOMMIT': True,
        'TIME_ZONE': 'UTC',
    }
}

# Database connection pooling with django-db-connection-pool
if not DEBUG and os.environ.get('USE_DB_POOL', 'False').lower() == 'true':
    DATABASES['default']['ENGINE'] = 'django_db_connection_pool.backends.postgresql'
    DATABASES['default']['POOL_OPTIONS'] = {
        'POOL_SIZE': int(os.environ.get('DB_POOL_SIZE', 20)),
        'MAX_OVERFLOW': int(os.environ.get('DB_MAX_OVERFLOW', 10)),
        'RECYCLE': int(os.environ.get('DB_RECYCLE', 300)),  # Recycle connections after 5 minutes
        'TIMEOUT': int(os.environ.get('DB_TIMEOUT', 30)),  # Connection timeout in seconds
    }

# Database router settings
DATABASE_ROUTERS = ['trojan_defender.db_router.DatabaseRouter']
DATABASE_APPS_MAPPING = {}  # Example: {'analytics': 'analytics_db'}
DATABASE_READ_REPLICAS = []  # Example: ['replica1', 'replica2']

# Validate database credentials - only for non-SQLite databases
if not DEBUG and DATABASES['default']['ENGINE'] != 'django.db.backends.sqlite3' and 'sqlite3' not in DATABASES['default']['ENGINE']:
    if not DATABASES['default']['USER'] or not DATABASES['default']['PASSWORD']:
        raise ValueError("DB_USER and DB_PASSWORD environment variables are required in production")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Custom user model
AUTH_USER_MODEL = 'users.User'

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Caches (define required aliases for tests and middleware)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'td-default',
        'TIMEOUT': 300,
        'OPTIONS': {
            'MAX_ENTRIES': 1000,
        }
    },
    'sessions': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'td-sessions',
        'TIMEOUT': 86400,
    },
    'rate_limit': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'td-rate-limit',
        'TIMEOUT': 3600,
    },
}

# Use cache-backed sessions pointing to the 'sessions' cache
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'sessions'

# REST framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.AllowAny',
    ),
    'EXCEPTION_HANDLER': 'trojan_defender.exceptions.custom_exception_handler',
}

# SIMPLE JWT configuration
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=int(os.environ.get('JWT_ACCESS_TOKEN_LIFETIME', 15))),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=int(os.environ.get('JWT_REFRESH_TOKEN_LIFETIME', 7))),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'ALGORITHM': 'HS512',
    'SIGNING_KEY': os.environ.get('JWT_SECRET_KEY', SECRET_KEY),
}

# CORS settings - Environment-based secure configuration
CORS_ALLOW_ALL_ORIGINS = False  # Never allow all origins in production
# Split env by commas or whitespace to avoid invalid combined origins
_cors_env = os.environ.get('CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000')
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in re.split(r"[\s,]+", _cors_env)
    if origin.strip()
]

# Additional CORS security settings
CORS_ALLOW_CREDENTIALS = os.environ.get('CORS_ALLOW_CREDENTIALS', 'True').lower() == 'true'
CORS_ALLOWED_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_ALLOWED_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

# Security: Only allow CORS in development or with explicit configuration
if not DEBUG and not os.environ.get('CORS_ALLOWED_ORIGINS'):
    CORS_ALLOWED_ORIGINS = []  # No CORS in production without explicit configuration

# Channels settings
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}