"""
Django Settings for Student Management API
==========================================

PRACTICE PROJECT — Student Management REST API

This project is your hands-on practice for:
  - Custom User model with roles (Admin, Teacher, Student)
  - JWT authentication (access/refresh tokens, rotation, blacklisting)
  - ModelViewSets with Routers
  - Custom permissions (IsTeacherOrAdmin, IsOwnerOrAdmin)
  - Throttling and pagination
  - Custom FilterSets (filter by department, year, GPA range)
  - Swagger/ReDoc documentation
  - Postman collection with automated tests

Compare every decision here to the Library API (library_api/settings.py).
The patterns are intentionally identical so the comparison reinforces learning.
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY
# =============================================================================
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-student-api-dev-key-change-this-in-production'
)

DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# =============================================================================
# INSTALLED APPS
# =============================================================================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'drf_spectacular',
    'django_filters',

    # Our apps
    'apps.accounts',     # User management + JWT auth
    'apps.students',     # Student profiles and department data
    'apps.courses',      # Course catalog and enrollments
    'apps.grades',       # Grade records
]

# =============================================================================
# MIDDLEWARE
# =============================================================================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'student_api.urls'

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

WSGI_APPLICATION = 'student_api.wsgi.application'

# =============================================================================
# DATABASE — PostgreSQL
# =============================================================================
# psycopg2-binary is the PostgreSQL driver for Django.
# Install it: pip install psycopg2-binary
#
# Credentials are loaded from the .env file — never hardcode them here.
# Add these to your .env file:
#   DB_NAME=bookshelf
#   DB_USER=postgres
#   DB_PASSWORD=Root@123
#   DB_HOST=localhost
#   DB_PORT=5432

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     os.getenv('DB_NAME',     'bookshelf'),
        'USER':     os.getenv('DB_USER',     'postgres'),
        'PASSWORD': os.getenv('DB_PASSWORD', 'Root@123'),
        'HOST':     os.getenv('DB_HOST',     'localhost'),
        'PORT':     os.getenv('DB_PORT',     '5432'),
    }
}

# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# =============================================================================
# I18N
# =============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC FILES
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ⭐ Custom User model — must be set BEFORE the first migration
AUTH_USER_MODEL = 'accounts.User'

# =============================================================================
# DJANGO REST FRAMEWORK
# =============================================================================
REST_FRAMEWORK = {
    # JWT authentication + session for browsable API
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],

    # Every endpoint requires a valid JWT by default
    # Individual views override with AllowAny for public endpoints
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Auto-schema generation for Swagger
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Pagination: return 10 items per page
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

    # Filtering backends: field filter + search + ordering
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # Throttling: rate limit to protect from abuse
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}

# =============================================================================
# SIMPLE JWT
# =============================================================================
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# =============================================================================
# DRF SPECTACULAR (Swagger)
# =============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Student Management API',
    'DESCRIPTION': (
        'A REST API for managing students, courses, enrollments, and grades. '
        'Practice project for learning Django REST Framework and JWT authentication.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,
    },
    'COMPONENT_SPLIT_REQUEST': True,
}
