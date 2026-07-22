"""
Courses Serializers — Student Management API
=============================================

COMPARE WITH: library_api/apps/loans/serializers.py

Same patterns:
- HiddenField(CurrentUserDefault()) — auto-set the enrolling student
- validate_course() — check capacity before enrollment
- validate() — prevent duplicate enrollments (like duplicate loans)
- create() — custom logic beyond simple model.save()
- Multiple serializers per model (List, Detail, Create)

STUDENT EXERCISE:
1. Add validate() to EnrollmentCreateSerializer that checks
   the course is 'active' (not completed or inactive)
2. Add an EnrollmentUpdateSerializer with only 'notes' editable
3. In CourseListSerializer, add 'available_seats' as a SerializerMethodField
   = max_students - enrolled_count
"""

from rest_framework import serializers
from apps.students.serializers import (
    StudentProfileListSerializer,
    DepartmentMinimalSerializer,
)
from .models import Course, Enrollment


# =============================================================================
# COURSE SERIALIZERS
# =============================================================================

class CourseListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for course list view."""
    teacher_name = serializers.SerializerMethodField()
    department_name = serializers.CharField(source='department.name', read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'title', 'teacher_name',
            'department_name', 'credits', 'max_students',
            'enrolled_count', 'is_full', 'status', 'start_date',
        ]

    def get_teacher_name(self, obj):
        """SerializerMethodField — compute teacher's full name."""
        if not obj.teacher:
            return None
        return obj.teacher.get_full_name() or obj.teacher.username


class CourseDetailSerializer(serializers.ModelSerializer):
    """Full serializer for a single course."""
    teacher_name = serializers.SerializerMethodField()
    department = DepartmentMinimalSerializer(read_only=True)
    enrolled_count = serializers.IntegerField(read_only=True)
    is_full = serializers.BooleanField(read_only=True)
    is_active = serializers.BooleanField(read_only=True)

    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'title', 'description',
            'teacher_name', 'department', 'credits',
            'max_students', 'enrolled_count', 'is_full', 'is_active',
            'status', 'start_date', 'end_date', 'created_at',
        ]

    def get_teacher_name(self, obj):
        if not obj.teacher:
            return None
        return obj.teacher.get_full_name() or obj.teacher.username


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """
    For creating and updating courses.
    Accepts teacher FK ID and department FK ID — not nested objects.
    """

    class Meta:
        model = Course
        fields = [
            'id', 'course_code', 'title', 'description',
            'teacher', 'department', 'credits', 'max_students',
            'status', 'start_date', 'end_date',
        ]
        read_only_fields = ['id']

    def validate_teacher(self, user):
        """Ensure the assigned teacher has role='teacher' or 'admin'."""
        if user and not user.is_teacher_or_admin:
            raise serializers.ValidationError(
                f'User "{user.username}" is not a teacher or admin.'
            )
        return user

    def validate(self, attrs):
        """start_date must be before end_date."""
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start and end and start > end:
            raise serializers.ValidationError(
                {'end_date': 'end_date must be after start_date.'}
            )
        return attrs


# =============================================================================
# ENROLLMENT SERIALIZERS
# =============================================================================

class EnrollmentListSerializer(serializers.ModelSerializer):
    """
    Read serializer for enrollment list.
    Shows student and course summary without deep nesting.
    """
    student_id = serializers.CharField(source='student.student_id', read_only=True)
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    course_code = serializers.CharField(source='course.course_code', read_only=True)
    course_title = serializers.CharField(source='course.title', read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student_id', 'student_name',
            'course_code', 'course_title',
            'status', 'enrollment_date',
        ]


class EnrollmentDetailSerializer(serializers.ModelSerializer):
    """Full enrollment detail with nested student and course objects."""
    student = StudentProfileListSerializer(read_only=True)
    course = CourseListSerializer(read_only=True)

    class Meta:
        model = Enrollment
        fields = [
            'id', 'student', 'course',
            'status', 'enrollment_date', 'notes',
        ]


class EnrollmentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating enrollments (enrolling a student in a course).

    MIRRORS: library_api LoanCreateSerializer

    - student is NOT a HiddenField here (teachers enroll specific students)
    - validate_course() checks capacity (mirrors validate_book() for availability)
    - validate() prevents duplicate enrollments (mirrors duplicate loan check)
    """

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'notes']
        read_only_fields = ['id']

    def validate_course(self, course):
        """
        Ensure the course is active and has available capacity.
        Mirrors library API's validate_book() which checks available_copies.
        """
        if not course.is_active:
            raise serializers.ValidationError(
                f'Course "{course.course_code}" is not currently active.'
            )
        if course.is_full:
            raise serializers.ValidationError(
                f'Course "{course.course_code}" is full '
                f'({course.enrolled_count}/{course.max_students} students).'
            )
        return course

    def validate(self, attrs):
        """
        Prevent duplicate enrollments.
        Mirrors library API's duplicate loan check.
        """
        student = attrs['student']
        course = attrs['course']

        existing = Enrollment.objects.filter(
            student=student,
            course=course,
            status=Enrollment.Status.ENROLLED,
        ).first()

        if existing:
            raise serializers.ValidationError(
                f'Student "{student.student_id}" is already enrolled in '
                f'"{course.course_code}".'
            )
        return attrs
