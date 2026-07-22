"""
Django Settings for Library Management API
==========================================

This settings file is the central configuration for the Django project.
It controls everything from database connections to REST framework behavior.

Teaching Notes:
- We use python-dotenv to load sensitive values from a .env file
- Never commit real SECRET_KEY or credentials to version control
- DEBUG=True is fine for development but MUST be False in production
"""

import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
# This keeps secrets out of the codebase — a critical security practice
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# =============================================================================
# SECURITY SETTINGS
# =============================================================================

# SECURITY WARNING: keep the secret key used in production secret!
# We load it from the environment; fall back to a dev key for convenience
SECRET_KEY = os.getenv(
    'SECRET_KEY',
    'django-insecure-dev-key-change-this-in-production-12345'
)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')

# =============================================================================
# INSTALLED APPS
# =============================================================================
# Order matters: Django processes apps in this order for things like
# template discovery and management command registration.

INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party apps
    'rest_framework',                    # Django REST Framework — our API backbone
    'rest_framework_simplejwt',          # JWT authentication support
    'rest_framework_simplejwt.token_blacklist',  # Enables token invalidation on logout
    'drf_spectacular',                   # OpenAPI 3.0 schema generation (Swagger/ReDoc)
    'django_filters',                    # Powerful filtering for querysets

    # Our project apps
    'apps.accounts',                     # User management, auth
    'apps.books',                        # Book/Author/Category catalog
    'apps.loans',                        # Book lending system
]

# =============================================================================
# MIDDLEWARE
# =============================================================================
# Middleware processes every request/response — think of it as a pipeline.
# Each middleware can modify the request before the view or the response after.

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'library_api.urls'

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

WSGI_APPLICATION = 'library_api.wsgi.application'

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
# INTERNATIONALIZATION
# =============================================================================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# =============================================================================
# STATIC & MEDIA FILES
# =============================================================================
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Media files are user-uploaded files (book covers, avatars)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Point Django to our custom User model
# This must be set BEFORE the first migration — changing it later is painful
AUTH_USER_MODEL = 'accounts.User'

# =============================================================================
# DJANGO REST FRAMEWORK CONFIGURATION
# =============================================================================
# This is the main DRF config. Every key here affects how our API behaves.

REST_FRAMEWORK = {
    # --- Authentication ---
    # JWTAuthentication checks for a Bearer token in the Authorization header.
    # SessionAuthentication is kept for the browsable API and admin.
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],

    # --- Permissions ---
    # IsAuthenticated means every endpoint requires a valid JWT by default.
    # Individual views can override this (e.g., AllowAny for public endpoints).
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # --- Schema Generation ---
    # drf-spectacular generates OpenAPI 3.0 schemas from your code.
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # --- Pagination ---
    # PageNumberPagination adds ?page=N to list endpoints.
    # Without pagination, large datasets would be returned all at once — dangerous!
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

    # --- Filtering ---
    # These backends are applied globally to all ViewSets.
    # DjangoFilterBackend: exact field filtering (?category=fiction)
    # SearchFilter: full-text search (?search=tolkien)
    # OrderingFilter: sort results (?ordering=-published_date)
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],

    # --- Throttling ---
    # Rate limiting protects the API from abuse and DDoS attacks.
    # Anonymous users get fewer requests than authenticated ones.
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',   # For unauthenticated requests
        'rest_framework.throttling.UserRateThrottle',   # For authenticated requests
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',    # 100 requests per day for anonymous users
        'user': '1000/day',   # 1000 requests per day for authenticated users
    },
}

# =============================================================================
# SIMPLE JWT CONFIGURATION
# =============================================================================
# JWT (JSON Web Tokens) are self-contained authentication tokens.
# They don't require server-side session storage — scalable and stateless.

SIMPLE_JWT = {
    # Access token expires quickly — if stolen, damage is limited
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),

    # Refresh token lives longer — used only to get new access tokens
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # ROTATE_REFRESH_TOKENS: each time a refresh token is used,
    # a NEW refresh token is issued. This is called "refresh token rotation"
    # and limits the window of exposure for a stolen refresh token.
    'ROTATE_REFRESH_TOKENS': True,

    # BLACKLIST_AFTER_ROTATION: the old refresh token is blacklisted
    # after rotation, preventing its reuse even if it was stolen.
    # Requires 'rest_framework_simplejwt.token_blacklist' in INSTALLED_APPS
    'BLACKLIST_AFTER_ROTATION': True,

    # Update the user's last_login field every time they get a new token
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
}

# =============================================================================
# DRF SPECTACULAR (Swagger/OpenAPI) CONFIGURATION
# =============================================================================
SPECTACULAR_SETTINGS = {
    'TITLE': 'Library Management API',
    'DESCRIPTION': (
        'A comprehensive RESTful API for managing a library system. '
        'Supports book catalog management, user accounts with JWT authentication, '
        'and a book loan tracking system. '
        'Built with Django REST Framework as a teaching project.'
    ),
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,      # Don't include the schema endpoint in itself
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,   # Keep auth token in Swagger UI across page refreshes
    },
    'COMPONENT_SPLIT_REQUEST': True,    # Separate request/response schemas for clarity
}
