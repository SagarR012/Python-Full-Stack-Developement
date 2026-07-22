"""
Students URLs — Student Management API
========================================

COMPARE WITH: library_api/apps/books/urls.py

Identical Router pattern — register ViewSets, get URLs for free.

Generated URLs:
  GET    /api/v1/departments/                → list
  POST   /api/v1/departments/                → create
  GET    /api/v1/departments/{id}/           → retrieve
  PUT    /api/v1/departments/{id}/           → update
  PATCH  /api/v1/departments/{id}/           → partial_update
  DELETE /api/v1/departments/{id}/           → destroy
  GET    /api/v1/students/                   → list
  POST   /api/v1/students/                   → create
  GET    /api/v1/students/{id}/              → retrieve
  PUT    /api/v1/students/{id}/              → update
  PATCH  /api/v1/students/{id}/              → partial_update
  DELETE /api/v1/students/{id}/              → destroy
  GET    /api/v1/students/my-profile/        → my_profile (custom action)
  GET    /api/v1/teachers/                   → list
  ...
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'students'

router = DefaultRouter()
router.register(r'departments', views.DepartmentViewSet, basename='department')
router.register(r'students', views.StudentProfileViewSet, basename='student')
router.register(r'teachers', views.TeacherProfileViewSet, basename='teacher')

urlpatterns = [
    path('', include(router.urls)),
]
