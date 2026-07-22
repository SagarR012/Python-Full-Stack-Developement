"""
Root URL Configuration — Student Management API
================================================

Mirrors the structure of library_api/library_api/urls.py intentionally.
Compare the two to see how the same patterns apply to a different domain.

URL versioning (/api/v1/) is best practice:
- Allows breaking changes in /api/v2/ without breaking existing clients
- Easy to deprecate old versions
"""

from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('swagger-ui', permanent=False)),
    path('admin/', admin.site.urls),

    # App API endpoints — all under /api/v1/
    path('api/v1/', include('apps.accounts.urls', namespace='accounts')),
    path('api/v1/', include('apps.students.urls', namespace='students')),
    path('api/v1/', include('apps.courses.urls', namespace='courses')),
    path('api/v1/', include('apps.grades.urls', namespace='grades')),

    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
