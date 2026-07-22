"""
Accounts URL Configuration
===========================

Teaching Notes:
- app_name enables URL namespacing: reverse('accounts:register')
- SimpleJWT provides ready-made views for token operations
- TokenObtainPairView: POST with credentials → returns access + refresh tokens
- TokenRefreshView: POST with refresh token → returns new access token
- TokenBlacklistView: POST with refresh token → blacklists it (logout)
"""

from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,    # Login: username+password → access+refresh tokens
    TokenRefreshView,        # Refresh: refresh token → new access token
    TokenBlacklistView,      # Logout: blacklists the refresh token
)
from . import views

app_name = 'accounts'

urlpatterns = [
    # --- Registration ---
    path('auth/register/', views.UserRegistrationView.as_view(), name='register'),

    # --- JWT Authentication ---
    # Login: POST with {"username": "...", "password": "..."}
    # Returns: {"access": "...", "refresh": "..."}
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),

    # Refresh: POST with {"refresh": "..."} 
    # Returns: {"access": "...", "refresh": "..."} (new tokens if ROTATE_REFRESH_TOKENS=True)
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),

    # Logout: POST with {"refresh": "..."}
    # Blacklists the refresh token, preventing future use
    path('auth/logout/', TokenBlacklistView.as_view(), name='logout'),

    # --- User Profile ---
    path('auth/profile/', views.UserProfileView.as_view(), name='profile'),
    path('auth/change-password/', views.ChangePasswordView.as_view(), name='change-password'),

    # --- Admin ---
    path('auth/users/', views.UserListView.as_view(), name='user-list'),
]
