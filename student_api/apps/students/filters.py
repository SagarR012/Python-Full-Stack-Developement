"""
Students Filters — Student Management API
==========================================

COMPARE WITH: library_api/apps/books/filters.py

Same patterns:
- NumberFilter for ID lookups
- CharFilter for text fields
- BooleanFilter with custom method
- DateFilter for date ranges

STUDENT EXERCISE:
1. Add a GPA range filter to StudentProfileFilter (min_gpa, max_gpa)
   This will require importing Grade and doing an annotation in the filterset
2. Add a 'graduated_in_year' filter using DateFilter on enrollment_date__year
"""

import django_filters
from .models import StudentProfile, TeacherProfile


class StudentProfileFilter(django_filters.FilterSet):
    """
    Custom FilterSet for StudentProfile.

    Supported query params:
      ?department=1           → filter by department ID
      ?department_slug=cs     → filter by department slug
      ?year_level=2           → filter second-year students
      ?status=active          → filter by enrollment status
      ?active=true            → shortcut for status=active
      ?enrolled_after=2024-01-01
    """

    department = django_filters.NumberFilter(
        field_name='department__id',
        lookup_expr='exact',
        label='Department ID'
    )

    department_slug = django_filters.CharFilter(
        field_name='department__slug',
        lookup_expr='exact',
        label='Department slug'
    )

    year_level = django_filters.CharFilter(
        field_name='year_level',
        lookup_expr='exact',
        label='Year level (1-5)'
    )

    status = django_filters.CharFilter(
        field_name='status',
        lookup_expr='exact',
        label='Enrollment status'
    )

    # Boolean filter: ?active=true → active students only
    active = django_filters.BooleanFilter(
        method='filter_active',
        label='Active students only'
    )

    enrolled_after = django_filters.DateFilter(
        field_name='enrollment_date',
        lookup_expr='gte',
        label='Enrolled on or after (YYYY-MM-DD)'
    )

    enrolled_before = django_filters.DateFilter(
        field_name='enrollment_date',
        lookup_expr='lte',
        label='Enrolled on or before (YYYY-MM-DD)'
    )

    class Meta:
        model = StudentProfile
        fields = ['department', 'year_level', 'status']

    def filter_active(self, queryset, name, value):
        """Custom method: filter by active status."""
        if value:
            return queryset.filter(status='active')
        return queryset.exclude(status='active')


class TeacherProfileFilter(django_filters.FilterSet):
    """FilterSet for TeacherProfile."""

    department = django_filters.NumberFilter(
        field_name='department__id',
        lookup_expr='exact',
    )

    department_slug = django_filters.CharFilter(
        field_name='department__slug',
        lookup_expr='exact',
    )

    employment_type = django_filters.CharFilter(
        field_name='employment_type',
        lookup_expr='exact',
    )

    class Meta:
        model = TeacherProfile
        fields = ['department', 'employment_type']
