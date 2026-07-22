"""
Courses Filters — Student Management API
==========================================

COMPARE WITH: library_api/apps/books/filters.py

Same pattern — FilterSet with NumberFilter, CharFilter, BooleanFilter.
"""

import django_filters
from .models import Course, Enrollment


class CourseFilter(django_filters.FilterSet):
    """
    Filter courses by department, teacher, status, and date ranges.

    Usage:
      ?department=1
      ?department_slug=computer-science
      ?teacher=3
      ?status=active
      ?available=true         → courses with open seats
      ?credits=3
    """

    department = django_filters.NumberFilter(
        field_name='department__id',
        lookup_expr='exact',
    )
    department_slug = django_filters.CharFilter(
        field_name='department__slug',
        lookup_expr='exact',
    )
    teacher = django_filters.NumberFilter(
        field_name='teacher__id',
        lookup_expr='exact',
    )
    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='exact',
    )
    credits = django_filters.NumberFilter(
        field_name='credits',
        lookup_expr='exact',
    )
    # ?available=true → courses that are not full
    available = django_filters.BooleanFilter(
        method='filter_available',
        label='Courses with open seats',
    )
    starts_after = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='gte',
    )
    starts_before = django_filters.DateFilter(
        field_name='start_date',
        lookup_expr='lte',
    )

    class Meta:
        model = Course
        fields = ['department', 'teacher', 'status', 'credits']

    def filter_available(self, queryset, name, value):
        """Filter to courses that have available capacity."""
        from django.db.models import Count, F
        # Annotate with enrolled count, filter where it's less than max
        queryset = queryset.annotate(
            enrolled=Count(
                'enrollments',
                filter=__import__('django.db.models', fromlist=['Q']).Q(
                    enrollments__status='enrolled'
                )
            )
        )
        if value:
            return queryset.filter(enrolled__lt=F('max_students'))
        return queryset.filter(enrolled__gte=F('max_students'))


class EnrollmentFilter(django_filters.FilterSet):
    """Filter enrollments by student, course, and status."""

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
    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='exact',
    )

    class Meta:
        model = Enrollment
        fields = ['student', 'course', 'status']
