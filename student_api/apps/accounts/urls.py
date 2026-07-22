"""
Accounts URLs — Student Management API
========================================

COMPARE WITH: library_api/apps/accounts/urls.py

Identical structure — the JWT endpoints (login, refresh, logout) are
provided by SimpleJWT. We just wire up the views.
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenBlacklistView,
)
from . import views

app_name = 'accounts'

urlpatterns = [
    # Registration
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),

    # JWT Authentication
    # POST {"username": "...", "password": "..."} → {"access": "...", "refresh": "..."}
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),

    # POST {"refresh": "..."} → {"access": "...", "refresh": "..."} (rotated)
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # POST {"refresh": "..."} → blacklists the token (logout)
    path('auth/logout/', TokenBlacklistView.as_view(), name='logout'),

    # Profile management
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # Admin
    path('auth/users/', views.UserListView.as_view(), name='user-list'),
]
