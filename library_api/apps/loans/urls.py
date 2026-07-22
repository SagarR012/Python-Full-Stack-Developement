"""
Loans URL Configuration
========================

Teaching Notes:
- DefaultRouter generates all standard URLs plus the custom action URLs
- For LoanViewSet, the generated URLs include:
    GET    /api/v1/loans/               → list
    POST   /api/v1/loans/               → create (borrow a book)
    GET    /api/v1/loans/{id}/          → retrieve
    DELETE /api/v1/loans/{id}/          → destroy
    POST   /api/v1/loans/{id}/return/   → return_book custom action
    GET    /api/v1/loans/my-loans/      → my_loans custom action
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'loans'

router = DefaultRouter()
router.register(r'loans', views.LoanViewSet, basename='loan')

urlpatterns = [
    path('', include(router.urls)),
]
