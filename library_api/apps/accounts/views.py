"""
Accounts Views
==============

Views handle the business logic of processing HTTP requests and returning responses.

Teaching Notes:
- Generic views (CreateAPIView, RetrieveUpdateAPIView) do 90% of the work for you
- Override methods like get_object(), get_queryset(), perform_create() for customization
- request.user gives you the currently authenticated user (from JWT token)
- self.get_serializer(data=request.data) creates a serializer with the request data
- serializer.is_valid(raise_exception=True) validates and raises 400 if invalid

View Types in DRF:
- APIView: Lowest level, most control
- GenericAPIView + Mixins: Middle ground
- ListAPIView, CreateAPIView, etc.: Convenience classes with specific mixins
- ViewSet: Groups related views together (pairs with Routers)
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
    
    Why AllowAny?
    - Registration must be accessible without authentication
    - Otherwise new users could never sign up!
    - AllowAny overrides the global IsAuthenticated default from settings
    """
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]  # Override global default — public endpoint

    @extend_schema(
        summary='Register a new user',
        description='Create a new user account. Returns the created user data.',
        tags=['Authentication'],
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Override create() to return a custom success message alongside user data.
        The default CreateAPIView.create() just returns the serialized data.
        """
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
    GET /api/v1/auth/profile/  — View your profile
    PUT /api/v1/auth/profile/  — Full profile update
    PATCH /api/v1/auth/profile/ — Partial profile update
    
    RetrieveUpdateAPIView combines:
    - RetrieveModelMixin (GET)
    - UpdateModelMixin (PUT/PATCH)
    
    We override get_object() to always return the current user,
    so the URL doesn't need a user ID — /profile/ just works.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get current user profile',
        tags=['Authentication'],
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @extend_schema(
        summary='Update current user profile',
        tags=['Authentication'],
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @extend_schema(
        summary='Partially update current user profile',
        tags=['Authentication'],
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)

    def get_object(self):
        """
        Always return the currently authenticated user.
        
        Normally get_object() fetches a model from the DB based on URL kwargs.
        We override this to make /profile/ always refer to "me".
        """
        return self.request.user


class ChangePasswordView(APIView):
    """
    POST /api/v1/auth/change-password/
    
    Change the current user's password.
    
    We use APIView here (not a generic view) because password changing
    doesn't fit neatly into the CRUD pattern — it has its own validation
    logic and response format.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=ChangePasswordSerializer,
        summary='Change user password',
        description='Change the authenticated user\'s password. Requires old password verification.',
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
    
    This demonstrates role-based access control:
    only users with is_admin=True can reach this endpoint.
    """
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='List all users (admin only)',
        tags=['Authentication'],
        parameters=[
            OpenApiParameter(name='search', description='Search by username or email', required=False, type=str),
        ]
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    def get_queryset(self):
        """
        Return all users, with optional search filtering.
        
        We manually implement search here to show how it works under the hood.
        The global SearchFilter backend doesn't apply because we'd need to set
        search_fields on the view.
        """
        queryset = User.objects.all()
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                username__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )
        return queryset
