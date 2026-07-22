"""
Grades URLs — Student Management API
======================================

Generated URLs:
  GET    /api/v1/grades/                    → list
  POST   /api/v1/grades/                    → create (enter grade)
  GET    /api/v1/grades/{id}/               → retrieve
  PUT    /api/v1/grades/{id}/               → update
  PATCH  /api/v1/grades/{id}/               → partial_update
  DELETE /api/v1/grades/{id}/               → destroy
  GET    /api/v1/grades/my-grades/          → my_grades (custom action)
  GET    /api/v1/grades/transcript/         → transcript (custom action)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'grades'

router = DefaultRouter()
router.register(r'grades', views.GradeViewSet, basename='grade')

urlpatterns = [
    path('', include(router.urls)),
]
