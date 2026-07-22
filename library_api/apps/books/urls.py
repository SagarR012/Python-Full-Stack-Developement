"""
Books URL Configuration
========================

Teaching Notes:
- DefaultRouter automatically generates URL patterns from ViewSets
- It creates all standard CRUD URLs plus an API root endpoint
- router.register(prefix, viewset, basename) is all you need

Generated URLs for BookViewSet:
  GET    /api/v1/books/                  → BookViewSet.list()
  POST   /api/v1/books/                  → BookViewSet.create()
  GET    /api/v1/books/{id}/             → BookViewSet.retrieve()
  PUT    /api/v1/books/{id}/             → BookViewSet.update()
  PATCH  /api/v1/books/{id}/             → BookViewSet.partial_update()
  DELETE /api/v1/books/{id}/             → BookViewSet.destroy()
  GET    /api/v1/books/{id}/availability/ → BookViewSet.availability()

The router handles ALL of this from a single register() call!
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'books'

# DefaultRouter also creates an API root at /api/v1/ that lists all endpoints
router = DefaultRouter()
router.register(r'authors', views.AuthorViewSet, basename='author')
router.register(r'categories', views.CategoryViewSet, basename='category')
router.register(r'books', views.BookViewSet, basename='book')

urlpatterns = [
    path('', include(router.urls)),
]
