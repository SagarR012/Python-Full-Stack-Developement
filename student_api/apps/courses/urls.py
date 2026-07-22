"""
Courses URLs — Student Management API
=======================================

Generated URLs:
  GET    /api/v1/courses/                        → list
  POST   /api/v1/courses/                        → create
  GET    /api/v1/courses/{id}/                   → retrieve
  PUT    /api/v1/courses/{id}/                   → update
  PATCH  /api/v1/courses/{id}/                   → partial_update
  DELETE /api/v1/courses/{id}/                   → destroy
  GET    /api/v1/courses/my-courses/             → my_courses (custom action)

  GET    /api/v1/enrollments/                    → list
  POST   /api/v1/enrollments/                    → create (enroll)
  GET    /api/v1/enrollments/{id}/               → retrieve
  DELETE /api/v1/enrollments/{id}/               → destroy
  POST   /api/v1/enrollments/{id}/drop/          → drop_course (custom action)
  GET    /api/v1/enrollments/my-enrollments/     → my_enrollments (custom action)
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'courses'

router = DefaultRouter()
router.register(r'courses', views.CourseViewSet, basename='course')
router.register(r'enrollments', views.EnrollmentViewSet, basename='enrollment')

urlpatterns = [
    path('', include(router.urls)),
]
