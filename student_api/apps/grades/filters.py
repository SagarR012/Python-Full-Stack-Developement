"""
Grades Filters — Student Management API
"""

import django_filters
from .models import Grade


class GradeFilter(django_filters.FilterSet):
    """
    Filter grade records.

    Usage:
      ?student=1               → grades for student with DB id=1
      ?student_id=STU-2024-001 → grades for student with that student_id
      ?course=2                → grades for course with DB id=2
      ?course_code=CS101       → grades for that course code
      ?letter_grade=A          → only A grades
      ?min_score=80            → score >= 80
      ?max_score=100           → score <= 100
    """

    student = django_filters.NumberFilter(
        field_name='student__id',
        lookup_expr='exact',
    )
    student_id = django_filters.CharFilter(
        field_name='student__student_id',
        lookup_expr='exact',
    )
    course = django_filters.NumberFilter(
        field_name='course__id',
        lookup_expr='exact',
    )
    course_code = django_filters.CharFilter(
        field_name='course__course_code',
        lookup_expr='iexact',
    )
    letter_grade = django_filters.CharFilter(
        field_name='letter_grade',
        lookup_expr='exact',
    )
    min_score = django_filters.NumberFilter(
        field_name='score',
        lookup_expr='gte',
    )
    max_score = django_filters.NumberFilter(
        field_name='score',
        lookup_expr='lte',
    )

    class Meta:
        model = Grade
        fields = ['student', 'course', 'letter_grade']
