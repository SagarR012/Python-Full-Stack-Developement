"""
Custom Permissions — Student Management API
============================================

COMPARE WITH: library_api/apps/accounts/permissions.py

Same architecture, different role names.

Permission Classes:
- IsAdminUser       → only admins
- IsTeacherOrAdmin  → teachers and admins (manage courses, grades)
- IsOwnerOrAdmin    → users can access their own data; admins can access anything

STUDENT EXERCISE:
After studying this file:
1. Write a new permission: IsTeacher (only teachers, not admins)
2. Write a new permission: IsStudentOrTeacher (students and teachers, no admin required)
3. When would you use has_object_permission vs has_permission?
"""

from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminUser(BasePermission):
    """
    Only users with role='admin' can access.

    Note: This checks our custom role field, NOT Django's built-in is_staff.
    """
    message = 'Only administrators can perform this action.'

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_admin
        )


class IsTeacherOrAdmin(BasePermission):
    """
    Teachers and admins can write; anyone can read.

    This is the same pattern as IsLibrarianOrAdmin in the library API —
    just with different role names.

    Applied to:
    - Course creation/update/deletion
    - Grade entry
    - Enrollment management
    """
    message = 'Only teachers and administrators can perform this action.'

    def has_permission(self, request, view):
        # Safe methods (GET, HEAD, OPTIONS) — allow everyone
        if request.method in SAFE_METHODS:
            return True
        # Writes require teacher or admin role
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_teacher_or_admin
        )


class IsOwnerOrAdmin(BasePermission):
    """
    Users can access their own data. Admins can access anything.

    This covers:
    - Students viewing their own profile
    - Students viewing their own grades
    - Teachers can't read other teachers' private data
    """
    message = 'You can only access your own data.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        obj = the model instance being accessed.

        Supports:
        - User objects (profile access)
        - Objects with a .user FK (Grade, Enrollment)
        - Objects with a .student FK (GradeRecord.student)
        """
        if request.user.is_admin:
            return True

        # For objects with a direct user FK
        if hasattr(obj, 'user'):
            return obj.user == request.user

        # For objects with a student FK (grade records, enrollments)
        if hasattr(obj, 'student'):
            return obj.student.user == request.user

        # The object IS the user (profile endpoint)
        return obj == request.user


class IsTeacherOwnerOrAdmin(BasePermission):
    """
    For grade records:
    - The teacher who created the grade can edit it
    - Admins can edit any grade
    - Students can only read their own grades (use with AllowAny or IsOwnerOrAdmin)
    """
    message = 'Only the teacher who created this grade or an admin can modify it.'

    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_admin:
            return True

        # Safe methods for any authenticated user (restrict further in view)
        if request.method in SAFE_METHODS:
            return True

        # Write access: only the teacher who created this record
        if hasattr(obj, 'teacher'):
            return obj.teacher == request.user

        return False
