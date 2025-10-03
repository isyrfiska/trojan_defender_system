# Configuration Guide

This guide covers all configuration options for Trojan Defender, including environment variables, settings files, and deployment-specific configurations.

## Table of Contents

- [Environment Variables](#environment-variables)
- [Django Settings](#django-settings)
- [Database Configuration](#database-configuration)
- [Redis Configuration](#redis-configuration)
- [Email Configuration](#email-configuration)
- [File Storage Configuration](#file-storage-configuration)
- [Security Configuration](#security-configuration)
- [Logging Configuration](#logging-configuration)
- [Celery Configuration](#celery-configuration)
- [Frontend Configuration](#frontend-configuration)
- [Docker Configuration](#docker-configuration)
- [Production Settings](#production-settings)
- [Development Settings](#development-settings)

## Environment Variables

### Core Application Settings

#### Required Variables

```bash
# Django Secret Key (REQUIRED)
# Generate with: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY=your_very_long_secret_key_here_at_least_50_characters_long

# Debug Mode (REQUIRED)
# Set to False in production
DEBUG=True

# Allowed Hosts (REQUIRED for production)
# Comma-separated list of allowed hostnames
ALLOWED_HOSTS=localhost,127.0.0.1,yourdomain.com,www.yourdomain.com

# Database URL (REQUIRED)
# Format: postgresql://user:password@host:port/database
DATABASE_URL=postgresql://trojan_defender:password@localhost:5432/trojan_defender

# Redis URL (REQUIRED)
# Format: redis://[:password]@host:port/database
REDIS_URL=redis://:password@localhost:6379/0
```

#### Optional Variables

```bash
# Application Name
APP_NAME=Trojan Defender

# Application Version
APP_VERSION=1.0.0

# Time Zone
TIME_ZONE=UTC

# Language Code
LANGUAGE_CODE=en-us

# Site ID (for Django sites framework)
SITE_ID=1

# Admin URL Path (security through obscurity)
ADMIN_URL=admin/
```

### Security Settings

```bash
# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,https://yourdomain.com
CORS_ALLOW_CREDENTIALS=True
CORS_ALLOW_ALL_ORIGINS=False

# CSRF Settings
CSRF_TRUSTED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CSRF_COOKIE_SECURE=True
CSRF_COOKIE_HTTPONLY=True
CSRF_COOKIE_SAMESITE=Strict

# Session Settings
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Strict
SESSION_COOKIE_AGE=86400

# Security Headers
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_BROWSER_XSS_FILTER=True
X_FRAME_OPTIONS=DENY

# Content Security Policy
CSP_DEFAULT_SRC="'self'"
CSP_SCRIPT_SRC="'self' 'unsafe-inline' https://cdn.jsdelivr.net"
CSP_STYLE_SRC="'self' 'unsafe-inline' https://fonts.googleapis.com"
CSP_FONT_SRC="'self' https://fonts.gstatic.com"
CSP_IMG_SRC="'self' data: https:"
CSP_CONNECT_SRC="'self' wss: ws:"
```

### Database Configuration

```bash
# PostgreSQL Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=trojan_defender
DB_USER=trojan_defender
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Database Connection Pool
DB_CONN_MAX_AGE=600
DB_CONN_HEALTH_CHECKS=True

# Database Options
DB_OPTIONS_SSLMODE=prefer
DB_OPTIONS_CONNECT_TIMEOUT=10
DB_OPTIONS_OPTIONS=-c default_transaction_isolation=read committed
```

### Redis Configuration

```bash
# Redis Connection
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_redis_password
REDIS_DB=0

# Redis SSL
REDIS_SSL=False
REDIS_SSL_CERT_REQS=required

# Cache Configuration
CACHE_TTL=300
CACHE_KEY_PREFIX=trojan_defender
CACHE_VERSION=1
```

### Email Configuration

```bash
# Email Backend
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

# SMTP Settings
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Email Addresses
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
SERVER_EMAIL=server@yourdomain.com
ADMINS_EMAIL=admin@yourdomain.com

# Email Templates
EMAIL_SUBJECT_PREFIX=[Trojan Defender]
EMAIL_TIMEOUT=30
```

### File Storage Configuration

```bash
# Local Storage
MEDIA_ROOT=/app/media
MEDIA_URL=/media/
STATIC_ROOT=/app/static
STATIC_URL=/static/

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE=10485760  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE=10485760  # 10MB
FILE_UPLOAD_PERMISSIONS=0o644
FILE_UPLOAD_DIRECTORY_PERMISSIONS=0o755

# AWS S3 Storage (Optional)
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_STORAGE_BUCKET_NAME=your-bucket-name
AWS_S3_REGION_NAME=us-west-2
AWS_S3_CUSTOM_DOMAIN=your-bucket-name.s3.amazonaws.com
AWS_DEFAULT_ACL=private
AWS_S3_OBJECT_PARAMETERS={'CacheControl': 'max-age=86400'}

# Google Cloud Storage (Optional)
GS_BUCKET_NAME=your-bucket-name
GS_PROJECT_ID=your-project-id
GS_CREDENTIALS_FILE=/path/to/credentials.json
GS_DEFAULT_ACL=private
```

### Logging Configuration

```bash
# Log Level
LOG_LEVEL=INFO

# Log Directory
LOG_DIR=/app/logs

# Log File Names
DJANGO_LOG_FILE=django.log
APP_LOG_FILE=app.log
CELERY_LOG_FILE=celery.log
SECURITY_LOG_FILE=security.log

# Log Rotation
LOG_MAX_SIZE=10485760  # 10MB
LOG_BACKUP_COUNT=5

# Sentry Configuration (Optional)
SENTRY_DSN=https://your-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=production
SENTRY_RELEASE=1.0.0
SENTRY_TRACES_SAMPLE_RATE=0.1
```

### Celery Configuration

```bash
# Celery Broker
CELERY_BROKER_URL=redis://:password@localhost:6379/1
CELERY_RESULT_BACKEND=redis://:password@localhost:6379/2

# Celery Settings
CELERY_TASK_SERIALIZER=json
CELERY_RESULT_SERIALIZER=json
CELERY_ACCEPT_CONTENT=json
CELERY_TIMEZONE=UTC
CELERY_ENABLE_UTC=True

# Worker Settings
CELERY_WORKER_CONCURRENCY=4
CELERY_WORKER_PREFETCH_MULTIPLIER=1
CELERY_TASK_ACKS_LATE=True
CELERY_WORKER_MAX_TASKS_PER_CHILD=1000

# Task Settings
CELERY_TASK_SOFT_TIME_LIMIT=300
CELERY_TASK_TIME_LIMIT=600
CELERY_TASK_MAX_RETRIES=3
CELERY_TASK_DEFAULT_RETRY_DELAY=60

# Beat Settings
CELERY_BEAT_SCHEDULE_FILENAME=celerybeat-schedule
CELERY_BEAT_SCHEDULER=django_celery_beat.schedulers:DatabaseScheduler
```

### API Configuration

```bash
# API Settings
API_VERSION=v1
API_TITLE=Trojan Defender API
API_DESCRIPTION=Cybersecurity platform API

# Rate Limiting
API_RATE_LIMIT=1000/hour
API_BURST_RATE=100/minute
API_ANON_RATE_LIMIT=100/hour

# Pagination
API_PAGE_SIZE=20
API_MAX_PAGE_SIZE=100

# Authentication
JWT_ACCESS_TOKEN_LIFETIME=3600  # 1 hour
JWT_REFRESH_TOKEN_LIFETIME=604800  # 7 days
JWT_ALGORITHM=HS256
JWT_SIGNING_KEY=${SECRET_KEY}

# API Keys
API_KEY_HEADER=X-API-Key
API_KEY_PREFIX=td_
```

### Monitoring Configuration

```bash
# Health Check
HEALTH_CHECK_URL=/health/
HEALTH_CHECK_TIMEOUT=30

# Metrics
METRICS_ENABLED=True
METRICS_URL=/metrics/
PROMETHEUS_METRICS_EXPORT_PORT=8001

# Performance Monitoring
APM_ENABLED=False
APM_SERVICE_NAME=trojan-defender
APM_ENVIRONMENT=production
```

## Django Settings

### Base Settings (`settings/base.py`)

```python
import os
from pathlib import Path
from decouple import config, Csv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=False, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost', cast=Csv())

# Application definition
DJANGO_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    'channels',
    'drf_spectacular',
]

LOCAL_APPS = [
    'accounts',
    'scanner',
    'threats',
    'chatbot',
    'reports',
    'notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'trojan_defender.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
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
DATABASES = {
    'default': {
        'ENGINE': config('DB_ENGINE', default='django.db.backends.postgresql'),
        'NAME': config('DB_NAME', default='trojan_defender'),
        'USER': config('DB_USER', default='trojan_defender'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST': config('DB_HOST', default='localhost'),
        'PORT': config('DB_PORT', default='5432'),
        'CONN_MAX_AGE': config('DB_CONN_MAX_AGE', default=600, cast=int),
        'CONN_HEALTH_CHECKS': config('DB_CONN_HEALTH_CHECKS', default=True, cast=bool),
        'OPTIONS': {
            'sslmode': config('DB_OPTIONS_SSLMODE', default='prefer'),
            'connect_timeout': config('DB_OPTIONS_CONNECT_TIMEOUT', default=10, cast=int),
        },
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 8,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = config('LANGUAGE_CODE', default='en-us')
TIME_ZONE = config('TIME_ZONE', default='UTC')
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = config('STATIC_URL', default='/static/')
STATIC_ROOT = config('STATIC_ROOT', default=BASE_DIR / 'staticfiles')
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Media files
MEDIA_URL = config('MEDIA_URL', default='/media/')
MEDIA_ROOT = config('MEDIA_ROOT', default=BASE_DIR / 'media')

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Site ID
SITE_ID = config('SITE_ID', default=1, cast=int)
```

### Production Settings (`settings/production.py`)

```python
from .base import *
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration

# Security Settings
SECURE_SSL_REDIRECT = config('SECURE_SSL_REDIRECT', default=True, cast=bool)
SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=31536000, cast=int)
SECURE_HSTS_INCLUDE_SUBDOMAINS = config('SECURE_HSTS_INCLUDE_SUBDOMAINS', default=True, cast=bool)
SECURE_HSTS_PRELOAD = config('SECURE_HSTS_PRELOAD', default=True, cast=bool)
SECURE_CONTENT_TYPE_NOSNIFF = config('SECURE_CONTENT_TYPE_NOSNIFF', default=True, cast=bool)
SECURE_BROWSER_XSS_FILTER = config('SECURE_BROWSER_XSS_FILTER', default=True, cast=bool)
X_FRAME_OPTIONS = config('X_FRAME_OPTIONS', default='DENY')

# Session Security
SESSION_COOKIE_SECURE = config('SESSION_COOKIE_SECURE', default=True, cast=bool)
SESSION_COOKIE_HTTPONLY = config('SESSION_COOKIE_HTTPONLY', default=True, cast=bool)
SESSION_COOKIE_SAMESITE = config('SESSION_COOKIE_SAMESITE', default='Strict')
SESSION_COOKIE_AGE = config('SESSION_COOKIE_AGE', default=86400, cast=int)

# CSRF Security
CSRF_COOKIE_SECURE = config('CSRF_COOKIE_SECURE', default=True, cast=bool)
CSRF_COOKIE_HTTPONLY = config('CSRF_COOKIE_HTTPONLY', default=True, cast=bool)
CSRF_COOKIE_SAMESITE = config('CSRF_COOKIE_SAMESITE', default='Strict')
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='', cast=Csv())

# CORS Settings
CORS_ALLOWED_ORIGINS = config('CORS_ALLOWED_ORIGINS', default='', cast=Csv())
CORS_ALLOW_CREDENTIALS = config('CORS_ALLOW_CREDENTIALS', default=True, cast=bool)
CORS_ALLOW_ALL_ORIGINS = config('CORS_ALLOW_ALL_ORIGINS', default=False, cast=bool)

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': config('LOG_DIR', default='/app/logs') + '/django.log',
            'maxBytes': config('LOG_MAX_SIZE', default=10485760, cast=int),
            'backupCount': config('LOG_BACKUP_COUNT', default=5, cast=int),
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'root': {
        'handlers': ['file', 'console'],
        'level': config('LOG_LEVEL', default='INFO'),
    },
    'loggers': {
        'django': {
            'handlers': ['file', 'console'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
        'trojan_defender': {
            'handlers': ['file', 'console'],
            'level': config('LOG_LEVEL', default='INFO'),
            'propagate': False,
        },
    },
}

# Sentry Configuration
SENTRY_DSN = config('SENTRY_DSN', default='')
if SENTRY_DSN:
    sentry_sdk.init(
        dsn=SENTRY_DSN,
        integrations=[
            DjangoIntegration(auto_enabling=True),
            CeleryIntegration(auto_enabling=True),
        ],
        traces_sample_rate=config('SENTRY_TRACES_SAMPLE_RATE', default=0.1, cast=float),
        send_default_pii=False,
        environment=config('SENTRY_ENVIRONMENT', default='production'),
        release=config('SENTRY_RELEASE', default='1.0.0'),
    )

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': config('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': config('CACHE_KEY_PREFIX', default='trojan_defender'),
        'VERSION': config('CACHE_VERSION', default=1, cast=int),
        'TIMEOUT': config('CACHE_TTL', default=300, cast=int),
    }
}

# Email Configuration
EMAIL_BACKEND = config('EMAIL_BACKEND', default='django.core.mail.backends.smtp.EmailBackend')
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_USE_SSL = config('EMAIL_USE_SSL', default=False, cast=bool)
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='noreply@example.com')
SERVER_EMAIL = config('SERVER_EMAIL', default='server@example.com')
EMAIL_SUBJECT_PREFIX = config('EMAIL_SUBJECT_PREFIX', default='[Trojan Defender] ')
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=30, cast=int)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = config('FILE_UPLOAD_MAX_MEMORY_SIZE', default=10485760, cast=int)
DATA_UPLOAD_MAX_MEMORY_SIZE = config('DATA_UPLOAD_MAX_MEMORY_SIZE', default=10485760, cast=int)
FILE_UPLOAD_PERMISSIONS = config('FILE_UPLOAD_PERMISSIONS', default=0o644, cast=int)
FILE_UPLOAD_DIRECTORY_PERMISSIONS = config('FILE_UPLOAD_DIRECTORY_PERMISSIONS', default=0o755, cast=int)
```

### Development Settings (`settings/development.py`)

```python
from .base import *

# Debug Settings
DEBUG = True
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Development Apps
INSTALLED_APPS += [
    'debug_toolbar',
    'django_extensions',
]

# Development Middleware
MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
] + MIDDLEWARE

# Debug Toolbar Configuration
INTERNAL_IPS = [
    '127.0.0.1',
    'localhost',
]

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}

# Database (SQLite for development)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Cache (Local memory for development)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Email (Console backend for development)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# CORS (Allow all origins in development)
CORS_ALLOW_ALL_ORIGINS = True

# Security (Relaxed for development)
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# Logging (Console only for development)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}
```

## Frontend Configuration

### Environment Variables (`.env`)

```bash
# API Configuration
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws

# Application Settings
REACT_APP_NAME=Trojan Defender
REACT_APP_VERSION=1.0.0
REACT_APP_DESCRIPTION=Advanced Cybersecurity Platform

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=false
REACT_APP_ENABLE_CHAT=true
REACT_APP_ENABLE_THREAT_MAP=true
REACT_APP_ENABLE_REPORTS=true

# Third-party Services
REACT_APP_GOOGLE_ANALYTICS_ID=
REACT_APP_SENTRY_DSN=
REACT_APP_MAPBOX_TOKEN=

# Development Settings
REACT_APP_DEBUG=true
GENERATE_SOURCEMAP=true
ESLINT_NO_DEV_ERRORS=true
FAST_REFRESH=true
```

### Production Environment (`.env.production`)

```bash
# API Configuration
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_WS_URL=wss://yourdomain.com/ws

# Application Settings
REACT_APP_NAME=Trojan Defender
REACT_APP_VERSION=1.0.0
REACT_APP_DESCRIPTION=Advanced Cybersecurity Platform

# Feature Flags
REACT_APP_ENABLE_ANALYTICS=true
REACT_APP_ENABLE_CHAT=true
REACT_APP_ENABLE_THREAT_MAP=true
REACT_APP_ENABLE_REPORTS=true

# Third-party Services
REACT_APP_GOOGLE_ANALYTICS_ID=GA_MEASUREMENT_ID
REACT_APP_SENTRY_DSN=https://your-dsn@sentry.io/project-id
REACT_APP_MAPBOX_TOKEN=your_mapbox_token

# Production Settings
REACT_APP_DEBUG=false
GENERATE_SOURCEMAP=false
ESLINT_NO_DEV_ERRORS=false
FAST_REFRESH=false
```

### Build Configuration (`package.json`)

```json
{
  "name": "trojan-defender-frontend",
  "version": "1.0.0",
  "private": true,
  "homepage": ".",
  "dependencies": {
    "@testing-library/jest-dom": "^5.16.4",
    "@testing-library/react": "^13.3.0",
    "@testing-library/user-event": "^13.5.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-scripts": "5.0.1",
    "web-vitals": "^2.1.4"
  },
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "build:prod": "REACT_APP_ENV=production npm run build",
    "build:staging": "REACT_APP_ENV=staging npm run build",
    "analyze": "npm run build && npx webpack-bundle-analyzer build/static/js/*.js"
  },
  "eslintConfig": {
    "extends": [
      "react-app",
      "react-app/jest"
    ]
  },
  "browserslist": {
    "production": [
      ">0.2%",
      "not dead",
      "not op_mini all"
    ],
    "development": [
      "last 1 chrome version",
      "last 1 firefox version",
      "last 1 safari version"
    ]
  },
  "proxy": "http://localhost:8000"
}
```

## Docker Configuration

### Backend Dockerfile

```dockerfile
# Dockerfile.prod
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    clamav \
    clamav-daemon \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Start application
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "trojan_defender.wsgi:application"]
```

### Frontend Dockerfile

```dockerfile
# Dockerfile.prod
# Build stage
FROM node:18-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
```

### Docker Compose Override

```yaml
# docker-compose.override.yml (for development)
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile.dev
    volumes:
      - ./backend:/app
      - /app/venv
    environment:
      - DEBUG=True
      - DJANGO_SETTINGS_MODULE=trojan_defender.settings.development
    command: python manage.py runserver 0.0.0.0:8000

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.dev
    volumes:
      - ./frontend:/app
      - /app/node_modules
    environment:
      - REACT_APP_API_URL=http://localhost:8000/api
      - REACT_APP_WS_URL=ws://localhost:8000/ws
    command: npm start

  db:
    ports:
      - "5432:5432"

  redis:
    ports:
      - "6379:6379"
```

## Configuration Validation

### Environment Validation Script

```python
#!/usr/bin/env python
# validate_config.py

import os
import sys
from urllib.parse import urlparse

def validate_required_vars():
    """Validate required environment variables."""
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'ALLOWED_HOSTS',
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing required environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ All required environment variables are set")
    return True

def validate_database_url():
    """Validate database URL format."""
    db_url = os.getenv('DATABASE_URL')
    if not db_url:
        return False
    
    try:
        parsed = urlparse(db_url)
        if not all([parsed.scheme, parsed.hostname, parsed.username, parsed.password]):
            print("❌ Invalid database URL format")
            return False
        
        print(f"✅ Database URL is valid (host: {parsed.hostname})")
        return True
    except Exception as e:
        print(f"❌ Error parsing database URL: {e}")
        return False

def validate_redis_url():
    """Validate Redis URL format."""
    redis_url = os.getenv('REDIS_URL')
    if not redis_url:
        return False
    
    try:
        parsed = urlparse(redis_url)
        if parsed.scheme != 'redis':
            print("❌ Redis URL must use redis:// scheme")
            return False
        
        print(f"✅ Redis URL is valid (host: {parsed.hostname or 'localhost'})")
        return True
    except Exception as e:
        print(f"❌ Error parsing Redis URL: {e}")
        return False

def validate_security_settings():
    """Validate security settings for production."""
    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    
    if debug:
        print("⚠️  DEBUG is enabled - ensure this is not production")
        return True
    
    security_vars = {
        'SECURE_SSL_REDIRECT': 'True',
        'SESSION_COOKIE_SECURE': 'True',
        'CSRF_COOKIE_SECURE': 'True',
    }
    
    issues = []
    for var, expected in security_vars.items():
        value = os.getenv(var, 'False')
        if value.lower() != expected.lower():
            issues.append(f"{var} should be {expected} in production")
    
    if issues:
        print(f"⚠️  Security issues: {'; '.join(issues)}")
        return False
    
    print("✅ Security settings are properly configured")
    return True

def main():
    """Run all validation checks."""
    print("🔍 Validating Trojan Defender configuration...\n")
    
    checks = [
        validate_required_vars,
        validate_database_url,
        validate_redis_url,
        validate_security_settings,
    ]
    
    results = [check() for check in checks]
    
    if all(results):
        print("\n🎉 Configuration validation passed!")
        sys.exit(0)
    else:
        print("\n❌ Configuration validation failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### Configuration Templates

#### Development Template (`.env.development.template`)

```bash
# Copy this file to .env and fill in the values

# Django Settings
SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (SQLite for development)
DATABASE_URL=sqlite:///db.sqlite3

# Redis (optional for development)
REDIS_URL=redis://localhost:6379/0

# Email (console backend for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# CORS (allow all origins in development)
CORS_ALLOW_ALL_ORIGINS=True

# Frontend URLs
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_WS_URL=ws://localhost:8000/ws
```

#### Production Template (`.env.production.template`)

```bash
# Copy this file to .env.prod and fill in the values

# Django Settings
SECRET_KEY=CHANGE_ME_TO_A_VERY_LONG_RANDOM_STRING
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Database
DATABASE_URL=postgresql://username:password@localhost:5432/trojan_defender

# Redis
REDIS_URL=redis://:password@localhost:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@yourdomain.com

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
CORS_ALLOWED_ORIGINS=https://yourdomain.com
CSRF_TRUSTED_ORIGINS=https://yourdomain.com

# Frontend URLs
REACT_APP_API_URL=https://yourdomain.com/api
REACT_APP_WS_URL=wss://yourdomain.com/ws

# Monitoring (optional)
SENTRY_DSN=https://your-dsn@sentry.io/project-id
```

---

*This configuration guide covers all aspects of setting up Trojan Defender. Always validate your configuration before deploying to production.*