"""
Students Serializers — Student Management API
==============================================

COMPARE WITH: library_api/apps/books/serializers.py

Same patterns:
- Multiple serializers per model (List vs Detail vs Create)
- SerializerMethodField for computed values
- Nested serializers for rich read responses
- Flat IDs for write operations

NEW PATTERNS HERE:
- validate() that checks the linked User's role
- source= traversing a OneToOneField (user.email)
- Nested OneToOneField serialization

STUDENT EXERCISE:
1. In StudentProfileCreateSerializer, add a validate() that checks
   the referenced user has role='student'
2. Add a validate_student_id to enforce the format "STU-YYYY-NNN"
3. Create a DepartmentDetailSerializer that includes lists of
   students and teachers in that department
"""

from rest_framework import serializers
from .models import Department, StudentProfile, TeacherProfile


# =============================================================================
# DEPARTMENT SERIALIZERS
# =============================================================================

class DepartmentSerializer(serializers.ModelSerializer):
    """Full serializer for Department — used for CRUD."""
    student_count = serializers.SerializerMethodField()
    teacher_count = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ['id', 'name', 'slug', 'description', 'head_of_department',
                  'student_count', 'teacher_count']
        read_only_fields = ['id', 'slug']

    def get_student_count(self, obj):
        return obj.students.count()

    def get_teacher_count(self, obj):
        return obj.teachers.count()


class DepartmentMinimalSerializer(serializers.ModelSerializer):
    """Minimal serializer — used when embedding department in other serializers."""
    class Meta:
        model = Department
        fields = ['id', 'name', 'slug']


# =============================================================================
# STUDENT PROFILE SERIALIZERS
# =============================================================================

class StudentProfileListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for student list view.
    Embeds department name and username from related objects.

    source= traverses the FK:
    - 'department' is a FK, so 'department.name' reads the name field
    - 'user' is a OneToOneField, so 'user.username' reads the username
    """
    department_name = serializers.CharField(source='department.name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(read_only=True)  # From @property on model

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'student_id', 'username', 'full_name', 'department_name',
            'year_level', 'status', 'enrollment_date'
        ]


class StudentProfileDetailSerializer(serializers.ModelSerializer):
    """
    Full serializer for student detail view.
    Uses nested DepartmentMinimalSerializer for the department.
    """
    department = DepartmentMinimalSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    # Traverse the OneToOneField to get user fields
    username  = serializers.CharField(source='user.username', read_only=True)
    email     = serializers.EmailField(source='user.email', read_only=True)
    phone     = serializers.CharField(source='user.phone_number', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'student_id', 'username', 'email', 'phone', 'full_name',
            'department', 'year_level', 'status', 'date_of_birth',
            'enrollment_date', 'address'
        ]


class StudentProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating and updating student profiles.
    Accepts user ID and department ID (not nested objects).
    """

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'user', 'student_id', 'department', 'year_level',
            'date_of_birth', 'status', 'address'
        ]
        read_only_fields = ['id']

    def validate_user(self, user):
        """
        Ensure the linked user has role='student'.
        You can't create a student profile for a teacher or admin.
        """
        if not user.is_student:
            raise serializers.ValidationError(
                f'User "{user.username}" has role "{user.role}". '
                'Only users with role=student can have a student profile.'
            )
        # Check they don't already have a profile
        if hasattr(user, 'student_profile') and self.instance is None:
            raise serializers.ValidationError(
                f'User "{user.username}" already has a student profile.'
            )
        return user


# =============================================================================
# TEACHER PROFILE SERIALIZERS
# =============================================================================

class TeacherProfileListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for teacher list view."""
    department_name = serializers.CharField(source='department.name', read_only=True)
    username  = serializers.CharField(source='user.username', read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'employee_id', 'username', 'full_name',
            'department_name', 'specialization', 'employment_type'
        ]


class TeacherProfileDetailSerializer(serializers.ModelSerializer):
    """Full serializer for teacher detail view."""
    department = DepartmentMinimalSerializer(read_only=True)
    full_name = serializers.CharField(read_only=True)
    username  = serializers.CharField(source='user.username', read_only=True)
    email     = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'employee_id', 'username', 'email', 'full_name',
            'department', 'specialization', 'employment_type', 'hire_date'
        ]


class TeacherProfileCreateUpdateSerializer(serializers.ModelSerializer):
    """For creating and updating teacher profiles."""

    class Meta:
        model = TeacherProfile
        fields = [
            'id', 'user', 'employee_id', 'department',
            'specialization', 'employment_type', 'hire_date'
        ]
        read_only_fields = ['id']

    def validate_user(self, user):
        """Ensure the linked user has role='teacher'."""
        if not user.is_teacher:
            raise serializers.ValidationError(
                f'User "{user.username}" is not a teacher.'
            )
        if hasattr(user, 'teacher_profile') and self.instance is None:
            raise serializers.ValidationError(
                f'User "{user.username}" already has a teacher profile.'
            )
        return user
