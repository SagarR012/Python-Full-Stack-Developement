"""
Courses Views — Student Management API
========================================

COMPARE WITH: library_api/apps/loans/views.py + books/views.py

Patterns demonstrated:
- get_queryset() with data scoping (students see only their enrolled courses)
- get_serializer_class() per action
- get_permissions() per action
- @action(detail=True) for drop_course (mirrors loan return_book)
- @action(detail=False) for my_courses (mirrors loans my_loans)
- select_related for query optimization

STUDENT EXERCISE:
1. Add an @action to CourseViewSet:
   GET /api/v1/courses/{id}/students/
   Returns all enrolled students in a course (teacher/admin only).

2. Modify EnrollmentViewSet.get_queryset() so that:
   - Students see only their own enrollments
   - Teachers see enrollments for courses they teach
   - Admins see all enrollments

3. Add an @action: POST /api/v1/enrollments/{id}/complete/
   Marks the enrollment as 'completed' (teacher/admin only).
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Course, Enrollment
from .serializers import (
    CourseListSerializer,
    CourseDetailSerializer,
    CourseCreateUpdateSerializer,
    EnrollmentListSerializer,
    EnrollmentDetailSerializer,
    EnrollmentCreateSerializer,
)
from .filters import CourseFilter, EnrollmentFilter
from apps.accounts.permissions import IsTeacherOrAdmin, IsAdminUser, IsOwnerOrAdmin


@extend_schema_view(
    list=extend_schema(
        summary='List all courses',
        tags=['Courses'],
        parameters=[
            OpenApiParameter('search', description='Search by code or title', required=False, type=str),
            OpenApiParameter('department', description='Filter by department ID', required=False, type=int),
            OpenApiParameter('status', description='Filter by status', required=False, type=str),
            OpenApiParameter('available', description='Only courses with open seats', required=False, type=bool),
        ]
    ),
    create=extend_schema(summary='Create a course (teacher/admin)', tags=['Courses']),
    retrieve=extend_schema(summary='Get course details', tags=['Courses']),
    update=extend_schema(summary='Update a course (teacher/admin)', tags=['Courses']),
    partial_update=extend_schema(summary='Partially update a course (teacher/admin)', tags=['Courses']),
    destroy=extend_schema(summary='Delete a course (admin)', tags=['Courses']),
)
class CourseViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Course CRUD + custom actions.

    Access control:
    - List/Retrieve: anyone (public course catalog)
    - Create/Update: teacher or admin
    - Delete: admin only
    """

    filterset_class = CourseFilter
    search_fields = ['course_code', 'title', 'description', 'teacher__first_name',
                     'teacher__last_name']
    ordering_fields = ['course_code', 'title', 'credits', 'start_date', 'enrolled_count']
    ordering = ['course_code']

    def get_queryset(self):
        return Course.objects.select_related('teacher', 'department').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return CourseListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_courses']:
            return [AllowAny()]
        elif self.action == 'destroy':
            return [IsAdminUser()]
        return [IsTeacherOrAdmin()]

    @extend_schema(
        summary='List courses I am enrolled in (or teaching)',
        tags=['Courses'],
    )
    @action(detail=False, methods=['get'], url_path='my-courses',
            permission_classes=[IsAuthenticated])
    def my_courses(self, request):
        """
        GET /api/v1/courses/my-courses/

        For students: courses they are enrolled in.
        For teachers: courses they are teaching.
        For admins: all courses.
        """
        user = request.user

        if user.is_admin:
            courses = Course.objects.select_related('teacher', 'department').all()

        elif user.is_teacher:
            courses = Course.objects.select_related(
                'teacher', 'department'
            ).filter(teacher=user)

        else:
            # Student — courses they're actively enrolled in
            try:
                student_profile = user.student_profile
            except Exception:
                return Response(
                    {'error': 'No student profile found for your account.'},
                    status=status.HTTP_404_NOT_FOUND
                )
            enrolled_course_ids = Enrollment.objects.filter(
                student=student_profile,
                status=Enrollment.Status.ENROLLED,
            ).values_list('course_id', flat=True)
            courses = Course.objects.select_related(
                'teacher', 'department'
            ).filter(id__in=enrolled_course_ids)

        page = self.paginate_queryset(courses)
        if page is not None:
            serializer = CourseListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = CourseListSerializer(courses, many=True)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(
        summary='List enrollments',
        tags=['Enrollments'],
        parameters=[
            OpenApiParameter('student', description='Filter by student DB ID', required=False, type=int),
            OpenApiParameter('course', description='Filter by course ID', required=False, type=int),
            OpenApiParameter('status', description='Filter by status', required=False, type=str),
        ]
    ),
    create=extend_schema(summary='Enroll a student in a course', tags=['Enrollments']),
    retrieve=extend_schema(summary='Get enrollment details', tags=['Enrollments']),
    destroy=extend_schema(summary='Cancel enrollment (admin)', tags=['Enrollments']),
)
class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Enrollment CRUD.

    MIRRORS: library_api LoanViewSet

    Access control:
    - List/Retrieve: authenticated users (scoped to own enrollments for students)
    - Create: teacher or admin (enrolls specific students)
    - Delete: admin only
    - drop_course action: the student themselves or teacher/admin

    PUT/PATCH are disabled — use drop_course action for status changes.
    """

    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    filterset_class = EnrollmentFilter
    ordering_fields = ['enrollment_date', 'status']
    ordering = ['-enrollment_date']

    def get_queryset(self):
        """
        Data scoping — mirrors library API's LoanViewSet.get_queryset().

        Students see only their own enrollments.
        Teachers see enrollments in courses they teach.
        Admins see everything.
        """
        user = self.request.user

        if user.is_admin:
            return Enrollment.objects.select_related(
                'student__user', 'course', 'course__teacher'
            ).all()

        if user.is_teacher:
            # Teachers see enrollments for their courses
            return Enrollment.objects.select_related(
                'student__user', 'course'
            ).filter(course__teacher=user)

        # Students see only their own enrollments
        try:
            student_profile = user.student_profile
            return Enrollment.objects.select_related(
                'student__user', 'course', 'course__teacher'
            ).filter(student=student_profile)
        except Exception:
            return Enrollment.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return EnrollmentCreateSerializer
        elif self.action == 'list':
            return EnrollmentListSerializer
        return EnrollmentDetailSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        elif self.action in ['list', 'retrieve', 'my_enrollments']:
            return [IsAuthenticated()]
        return [IsTeacherOrAdmin()]

    @extend_schema(
        summary='Drop a course (withdraw from enrollment)',
        description='Sets enrollment status to "dropped".',
        tags=['Enrollments'],
    )
    @action(detail=True, methods=['post'], url_path='drop',
            permission_classes=[IsAuthenticated])
    def drop_course(self, request, pk=None):
        """
        POST /api/v1/enrollments/{id}/drop/

        MIRRORS: library_api LoanViewSet.return_book

        Students can drop their own enrollments.
        Teachers/Admins can drop any enrollment.
        """
        enrollment = self.get_object()

        # Students can only drop their own enrollments
        if not (request.user.is_teacher_or_admin):
            try:
                if enrollment.student != request.user.student_profile:
                    return Response(
                        {'error': 'You can only drop your own enrollments.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
            except Exception:
                return Response(
                    {'error': 'No student profile for your account.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        if enrollment.status == Enrollment.Status.DROPPED:
            return Response(
                {'error': 'This enrollment has already been dropped.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        enrollment.drop_course()
        return Response(
            EnrollmentDetailSerializer(enrollment).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary='List current user\'s enrollments',
        tags=['Enrollments'],
    )
    @action(detail=False, methods=['get'], url_path='my-enrollments',
            permission_classes=[IsAuthenticated])
    def my_enrollments(self, request):
        """
        GET /api/v1/enrollments/my-enrollments/

        MIRRORS: library_api LoanViewSet.my_loans

        Returns the current student's enrollments.
        Supports ?status=enrolled filter.
        """
        try:
            student_profile = request.user.student_profile
        except Exception:
            return Response(
                {'error': 'No student profile for your account.'},
                status=status.HTTP_404_NOT_FOUND
            )

        enrollments = Enrollment.objects.filter(
            student=student_profile
        ).select_related('course', 'course__teacher')

        status_filter = request.query_params.get('status')
        if status_filter:
            enrollments = enrollments.filter(status=status_filter)

        page = self.paginate_queryset(enrollments)
        if page is not None:
            serializer = EnrollmentListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = EnrollmentListSerializer(enrollments, many=True)
        return Response(serializer.data)
