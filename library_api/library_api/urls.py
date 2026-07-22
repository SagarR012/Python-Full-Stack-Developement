"""
Root URL Configuration
======================

This is the central URL dispatcher for the entire project.
Django uses this file to route incoming HTTP requests to the right app.

Teaching Notes:
- include() delegates URL matching to another urls.py file
- namespace= helps reverse URLs without ambiguity (e.g., reverse('books:book-list'))
- The API schema endpoints are added here since they're project-wide, not app-specific
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,       # Serves the raw OpenAPI schema (YAML/JSON)
    SpectacularSwaggerView,   # Interactive Swagger UI
    SpectacularRedocView,     # Alternative clean ReDoc UI
)

urlpatterns = [
    # Django admin — useful during development
    path('admin/', admin.site.urls),

    # -------------------------------------------------------------------------
    # API Endpoints — all under /api/v1/ prefix
    # Versioning your API (/v1/) is best practice: it lets you ship breaking
    # changes in /v2/ without breaking existing clients.
    # -------------------------------------------------------------------------
    path('api/v1/', include('apps.accounts.urls', namespace='accounts')),
    path('api/v1/', include('apps.books.urls', namespace='books')),
    path('api/v1/', include('apps.loans.urls', namespace='loans')),

    # -------------------------------------------------------------------------
    # API Documentation Endpoints
    # -------------------------------------------------------------------------

    # Raw OpenAPI 3.0 schema — machine-readable, used by tools like Postman
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),

    # Swagger UI — interactive browser-based API explorer
    # Great for manual testing and sharing with frontend developers
    path(
        'api/docs/',
        SpectacularSwaggerView.as_view(url_name='schema'),
        name='swagger-ui',
    ),

    # ReDoc — a cleaner, read-only alternative to Swagger UI
    path(
        'api/redoc/',
        SpectacularRedocView.as_view(url_name='schema'),
        name='redoc',
    ),
]

# Serve media files (uploaded images) during development
# In production, use a web server (Nginx) or cloud storage (S3) for this
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
