"""
Custom Permissions
==================

DRF permissions control who can access what. They are the gatekeepers
of your API endpoints.

Teaching Notes:
- BasePermission requires implementing has_permission() and/or has_object_permission()
- has_permission() is called on every request to the view
- has_object_permission() is called only when accessing a specific object
  (e.g., GET /api/books/5/ — the 5 is the object)
- Permissions are AND-ed together when listed: all must pass
- Return True to allow, False to deny (DRF returns 403 Forbidden)

Best Practice:
- Keep permissions small and composable
- Name them descriptively (IsOwnerOrAdmin reads like English)
- Always check request.user.is_authenticated first for safety
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """
    Allows access only to users with the 'admin' role.

    Note: This is different from Django's built-in IsAdminUser which checks
    is_staff. Our version checks the custom role field on our User model.
    """

    message = 'Only administrators can perform this action.'

    def has_permission(self, request, view):
        # First check: is the user even authenticated?
        # Without this check, AnonymousUser would fail on .is_admin access
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsLibrarianOrAdmin(BasePermission):
    """
    Allows access to librarians and admins.
    Used for book/loan management operations.

    SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS') — read-only methods.
    We allow anyone to read, but only librarians/admins to write.
    """

    message = 'Only librarians and administrators can perform this action.'

    def has_permission(self, request, view):
        # Allow anyone to use safe (read-only) methods
        if request.method in SAFE_METHODS:
            return True

        # For write operations, require librarian or admin role
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_librarian_or_admin
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Object-level permission: only the owner of an object or an admin can access it.

    This is a classic pattern for user-owned resources:
    - A user can view/edit their own profile
    - An admin can view/edit any profile
    - A user cannot access another user's data

    has_object_permission() receives the specific database object being accessed.
    """

    message = 'You can only access your own data.'

    def has_permission(self, request, view):
        # User must be authenticated for any access
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        obj is the model instance being accessed (e.g., a User or Loan instance).
        
        We check if the object belongs to the requesting user,
        OR if the user is an admin (who can access anything).
        """
        # Admins can access any object
        if request.user.is_admin:
            return True

        # For User objects, compare the user to the object itself
        if hasattr(obj, 'user'):
            # For objects with a 'user' FK (like Loan), compare to that FK
            return obj.user == request.user

        # The object IS the user (e.g., accessing User profile)
        return obj == request.user


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission: the owner can edit; everyone else can only read.
    
    Useful for public resources where reading is open but editing is restricted.
    """

    def has_object_permission(self, request, view, obj):
        # Allow read-only access to everyone
        if request.method in SAFE_METHODS:
            return True

        # Write access only for the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
        return obj == request.user
