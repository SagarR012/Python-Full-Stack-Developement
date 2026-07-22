"""
Grades Views — Student Management API
========================================

Patterns demonstrated:
- Data scoping in get_queryset() (students see only their own grades)
- perform_create() / perform_update() are NOT needed because teacher
  is set via HiddenField in the serializer
- @action(detail=False) for transcript — a computed resource
- @action(detail=False) for my_grades — scoped to the current user
- Custom action that returns non-model response data

STUDENT EXERCISE:
1. Add an @action: GET /api/v1/grades/course-summary/?course=CS101
   Returns: { course, average_score, grade_distribution: {A: 5, B: 8, ...} }
   Use Django's aggregation: Grade.objects.aggregate(avg=Avg('score'))

2. Add validation in get_permissions(): a teacher can only enter/edit grades
   for courses they teach. Implement this with IsTeacherOwnerOrAdmin.

3. The transcript action currently only works for the current user.
   Add an admin override: if the request user is admin, accept a
   ?student_id= query param to get any student's transcript.
"""

from decimal import Decimal
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Grade
from .serializers import (
    GradeListSerializer,
    GradeDetailSerializer,
    GradeCreateSerializer,
    GradeUpdateSerializer,
    StudentTranscriptSerializer,
)
from .filters import GradeFilter
from apps.accounts.permissions import IsTeacherOrAdmin, IsAdminUser


@extend_schema_view(
    list=extend_schema(
        summary='List grade records',
        tags=['Grades'],
        parameters=[
            OpenApiParameter('student_id', description='Filter by student ID string', required=False, type=str),
            OpenApiParameter('course_code', description='Filter by course code', required=False, type=str),
            OpenApiParameter('min_score', description='Minimum score', required=False, type=float),
            OpenApiParameter('max_score', description='Maximum score', required=False, type=float),
        ]
    ),
    create=extend_schema(summary='Enter a grade (teacher/admin)', tags=['Grades']),
    retrieve=extend_schema(summary='Get grade details', tags=['Grades']),
    update=extend_schema(summary='Update a grade (teacher/admin)', tags=['Grades']),
    partial_update=extend_schema(summary='Partially update a grade (teacher/admin)', tags=['Grades']),
    destroy=extend_schema(summary='Delete a grade record (admin)', tags=['Grades']),
)
class GradeViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Grade CRUD.

    Access control:
    - List/Retrieve: students see own grades, teachers see grades for their courses
    - Create/Update: teacher or admin
    - Delete: admin only
    """

    filterset_class = GradeFilter
    search_fields = ['student__student_id', 'student__user__first_name',
                     'course__course_code', 'course__title']
    ordering_fields = ['score', 'letter_grade', 'graded_at']
    ordering = ['-graded_at']

    def get_queryset(self):
        """
        Scope grade records to the requesting user.

        - Admins: see everything
        - Teachers: see grades for courses they teach
        - Students: see only their own grades
        """
        user = self.request.user

        base_qs = Grade.objects.select_related(
            'student__user', 'course', 'teacher'
        )

        if user.is_admin:
            return base_qs.all()

        if user.is_teacher:
            return base_qs.filter(course__teacher=user)

        # Student — only their own grades
        try:
            return base_qs.filter(student=user.student_profile)
        except Exception:
            return Grade.objects.none()

    def get_serializer_class(self):
        if self.action == 'create':
            return GradeCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return GradeUpdateSerializer
        elif self.action == 'list':
            return GradeListSerializer
        return GradeDetailSerializer

    def get_permissions(self):
        if self.action == 'destroy':
            return [IsAdminUser()]
        elif self.action in ['list', 'retrieve', 'my_grades', 'transcript']:
            return [IsAuthenticated()]
        return [IsTeacherOrAdmin()]

    @extend_schema(
        summary='Get my grades',
        description='Returns all grades for the currently authenticated student.',
        tags=['Grades'],
    )
    @action(detail=False, methods=['get'], url_path='my-grades',
            permission_classes=[IsAuthenticated])
    def my_grades(self, request):
        """
        GET /api/v1/grades/my-grades/

        Returns the current student's grades.
        Supports ?course_code= and ?letter_grade= filters.
        """
        try:
            student_profile = request.user.student_profile
        except Exception:
            return Response(
                {'error': 'No student profile for your account.'},
                status=status.HTTP_404_NOT_FOUND
            )

        grades = Grade.objects.filter(
            student=student_profile
        ).select_related('course', 'teacher')

        # Optional filters
        course_code = request.query_params.get('course_code')
        if course_code:
            grades = grades.filter(course__course_code__iexact=course_code)

        letter = request.query_params.get('letter_grade')
        if letter:
            grades = grades.filter(letter_grade=letter)

        page = self.paginate_queryset(grades)
        if page is not None:
            serializer = GradeListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = GradeListSerializer(grades, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Get my academic transcript',
        description=(
            'Returns a complete transcript for the current student: '
            'all grades with GPA calculation.'
        ),
        tags=['Grades'],
    )
    @action(detail=False, methods=['get'], url_path='transcript',
            permission_classes=[IsAuthenticated])
    def transcript(self, request):
        """
        GET /api/v1/grades/transcript/

        Returns a computed transcript for the current student.
        This demonstrates returning structured non-model data from a custom action.
        """
        try:
            student_profile = request.user.student_profile
        except Exception:
            return Response(
                {'error': 'No student profile for your account.'},
                status=status.HTTP_404_NOT_FOUND
            )

        grades = Grade.objects.filter(
            student=student_profile
        ).select_related('course')

        # Calculate GPA
        gpa = self._calculate_gpa(grades)

        data = {
            'student_id': student_profile.student_id,
            'full_name': student_profile.full_name,
            'department': (
                student_profile.department.name
                if student_profile.department else 'Unassigned'
            ),
            'total_courses': grades.count(),
            'gpa': round(gpa, 2),
            'grades': grades,
        }

        serializer = StudentTranscriptSerializer(data)
        return Response(serializer.data)

    @staticmethod
    def _calculate_gpa(grades):
        """
        Calculate GPA from a queryset of Grade objects.
        Uses a weighted average based on course credits.
        """
        grade_points_scale = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D': 1.0, 'F': 0.0,
        }
        total_points = Decimal('0.0')
        total_credits = 0

        for grade in grades:
            points = grade_points_scale.get(grade.letter_grade)
            if points is not None:
                credits = grade.course.credits
                total_points += Decimal(str(points)) * credits
                total_credits += credits

        if total_credits == 0:
            return 0.0
        return float(total_points / total_credits)
