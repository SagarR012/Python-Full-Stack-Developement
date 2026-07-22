"""
Accounts Views — Student Management API
=========================================

COMPARE WITH: library_api/apps/accounts/views.py

Identical view patterns:
- UserRegistrationView → CreateAPIView, AllowAny
- UserProfileView → RetrieveUpdateAPIView, overrides get_object() to return request.user
- ChangePasswordView → APIView, manual validation flow
- UserListView → ListAPIView, admin-only

STUDENT EXERCISE:
1. Add a UserDetailView (admin only) that can fetch any user by ID
2. Add a DeactivateUserView (admin only): sets is_active=False
3. Add an endpoint to get all users with role='teacher'
"""

from django.contrib.auth import get_user_model
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .serializers import (
    UserRegistrationSerializer,
    UserProfileSerializer,
    ChangePasswordSerializer,
    UserListSerializer,
)
from .permissions import IsAdminUser

User = get_user_model()


class UserRegistrationView(generics.CreateAPIView):
    """
    POST /api/v1/auth/register/

    Register a new user account.
    AllowAny — registration must be publicly accessible.
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Register a new user',
        description='Create a new user account. Default role is student.',
        tags=['Authentication'],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {
                'message': 'User registered successfully.',
                'user': UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET    /api/v1/auth/profile/   — View your profile
    PUT    /api/v1/auth/profile/   — Full profile update
    PATCH  /api/v1/auth/profile/   — Partial profile update

    get_object() is overridden to always return request.user,
    so the URL doesn't need a user ID.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(summary='Get current user profile', tags=['Authentication'])
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(summary='Update current user profile', tags=['Authentication'])
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(summary='Partially update current user profile', tags=['Authentication'])
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        """Always return the currently authenticated user."""
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/

    Change the current user's password.
    We use APIView here because password changing doesn't fit the CRUD pattern.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        summary='Change user password',
        description='Requires old password verification.',
        tags=['Authentication'],
    )
    def post(self, request):
        # Pass request in context so the serializer can access request.user
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'message': 'Password changed successfully.'},
            status=status.HTTP_200_OK
        )


class UserListView(generics.ListAPIView):
    """
    GET /api/v1/auth/users/

    List all users — admin only.
    Demonstrates role-based access control.
    """
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='List all users (admin only)',
        tags=['Authentication'],
        parameters=[
            OpenApiParameter('search', description='Search by username or email', required=False, type=str),
            OpenApiParameter('role', description='Filter by role', required=False, type=str, enum=['admin', 'teacher', 'student']),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        queryset = User.objects.all()

        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                username__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )

        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)

        return queryset
