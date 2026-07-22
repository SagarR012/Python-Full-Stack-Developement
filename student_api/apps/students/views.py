"""
Students Views — Student Management API
=========================================

COMPARE WITH: library_api/apps/books/views.py

Same patterns:
- ModelViewSet for full CRUD
- get_serializer_class() for different serializers per action
- get_permissions() for dynamic permissions
- @action for custom endpoints
- select_related/prefetch_related for query optimization

STUDENT EXERCISE:
1. Add a custom action to StudentProfileViewSet:
   GET /api/v1/students/{id}/grades/
   Returns all grades for a specific student.

2. Add a custom action to DepartmentViewSet:
   GET /api/v1/departments/{id}/students/
   Returns all students in a department.
   (detail=True, paginate the results)

3. Add a my_profile action to StudentProfileViewSet:
   GET /api/v1/students/my-profile/
   Returns the current user's student profile without needing the ID.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Department, StudentProfile, TeacherProfile
from .serializers import (
    DepartmentSerializer,
    StudentProfileListSerializer,
    StudentProfileDetailSerializer,
    StudentProfileCreateUpdateSerializer,
    TeacherProfileListSerializer,
    TeacherProfileDetailSerializer,
    TeacherProfileCreateUpdateSerializer,
)
from .filters import StudentProfileFilter, TeacherProfileFilter
from apps.accounts.permissions import IsTeacherOrAdmin, IsAdminUser, IsOwnerOrAdmin


@extend_schema_view(
    list=extend_schema(summary='List all departments', tags=['Departments']),
    create=extend_schema(summary='Create a department', tags=['Departments']),
    retrieve=extend_schema(summary='Get department details', tags=['Departments']),
    update=extend_schema(summary='Update a department', tags=['Departments']),
    partial_update=extend_schema(summary='Partially update a department', tags=['Departments']),
    destroy=extend_schema(summary='Delete a department', tags=['Departments']),
)
class DepartmentViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Department CRUD.

    - Reading: open to everyone
    - Writing: teacher or admin only
    """
    queryset = Department.objects.prefetch_related('students', 'teachers').all()
    serializer_class = DepartmentSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsTeacherOrAdmin()]


@extend_schema_view(
    list=extend_schema(
        summary='List all students',
        tags=['Students'],
        parameters=[
            OpenApiParameter('search', description='Search by student ID, name', required=False, type=str),
            OpenApiParameter('department', description='Filter by department ID', required=False, type=int),
            OpenApiParameter('year_level', description='Filter by year (1-5)', required=False, type=str),
            OpenApiParameter('status', description='Filter by status', required=False, type=str),
            OpenApiParameter('active', description='Only active students', required=False, type=bool),
        ]
    ),
    create=extend_schema(summary='Create a student profile', tags=['Students']),
    retrieve=extend_schema(summary='Get student details', tags=['Students']),
    update=extend_schema(summary='Update a student profile', tags=['Students']),
    partial_update=extend_schema(summary='Partially update a student profile', tags=['Students']),
    destroy=extend_schema(summary='Delete a student profile', tags=['Students']),
)
class StudentProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for StudentProfile CRUD.

    Access control:
    - List/Retrieve: authenticated users (teachers see all, students see own)
    - Create/Update/Delete: teacher or admin
    """

    filterset_class = StudentProfileFilter
    search_fields = [
        'student_id',
        'user__username',
        'user__first_name',
        'user__last_name',
        'user__email',
    ]
    ordering_fields = ['student_id', 'enrollment_date', 'year_level']
    ordering = ['student_id']

    def get_queryset(self):
        """
        Optimize with select_related for FK and OneToOne relationships.

        Without select_related:
        - Accessing student.user.username for 100 students = 101 queries
        With select_related:
        - 1 query with JOINs for user + department
        """
        return StudentProfile.objects.select_related(
            'user', 'department'
        ).all()

    def get_serializer_class(self):
        """Different serializers for list, detail, and write operations."""
        if self.action == 'list':
            return StudentProfileListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return StudentProfileCreateUpdateSerializer
        return StudentProfileDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve', 'my_profile']:
            return [IsAuthenticated()]
        return [IsTeacherOrAdmin()]

    @extend_schema(
        summary='Get current user\'s student profile',
        description='Returns the student profile of the currently authenticated user.',
        tags=['Students'],
    )
    @action(detail=False, methods=['get'], url_path='my-profile')
    def my_profile(self, request):
        """
        GET /api/v1/students/my-profile/

        Custom action — same pattern as my_loans in the library API.
        detail=False: operates on the collection, no {pk} in URL.
        """
        try:
            profile = StudentProfile.objects.select_related(
                'user', 'department'
            ).get(user=request.user)
        except StudentProfile.DoesNotExist:
            return Response(
                {'error': 'You do not have a student profile.'},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = StudentProfileDetailSerializer(profile)
        return Response(serializer.data)


@extend_schema_view(
    list=extend_schema(summary='List all teachers', tags=['Teachers']),
    create=extend_schema(summary='Create a teacher profile', tags=['Teachers']),
    retrieve=extend_schema(summary='Get teacher details', tags=['Teachers']),
    update=extend_schema(summary='Update a teacher profile', tags=['Teachers']),
    partial_update=extend_schema(summary='Partially update a teacher profile', tags=['Teachers']),
    destroy=extend_schema(summary='Delete a teacher profile', tags=['Teachers']),
)
class TeacherProfileViewSet(viewsets.ModelViewSet):
    """
    ViewSet for TeacherProfile CRUD.

    - Reading: open to authenticated users
    - Writing: admin only (managing teacher records is admin-level)
    """

    filterset_class = TeacherProfileFilter
    search_fields = ['employee_id', 'user__username', 'user__first_name',
                     'user__last_name', 'specialization']
    ordering_fields = ['employee_id', 'hire_date']
    ordering = ['employee_id']

    def get_queryset(self):
        return TeacherProfile.objects.select_related('user', 'department').all()

    def get_serializer_class(self):
        if self.action == 'list':
            return TeacherProfileListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return TeacherProfileCreateUpdateSerializer
        return TeacherProfileDetailSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAdminUser()]
