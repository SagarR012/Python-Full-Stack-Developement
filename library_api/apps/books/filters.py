"""
Books Filters
=============

django-filter provides declarative filter definitions that integrate
automatically with DRF's DjangoFilterBackend.

Teaching Notes:
- FilterSet is similar to Django's ModelForm — it maps filter params to queryset filters
- NumberFilter, CharFilter, DateFilter etc. define the filter type
- lookup_expr defines how the filter compares: 'exact', 'icontains', 'gte', 'lte', etc.
- field_name is the model field to filter on
- The filterset_class = BookFilter on the ViewSet activates these filters

Usage examples:
  GET /api/v1/books/?category=1
  GET /api/v1/books/?author=2&available=true
  GET /api/v1/books/?published_after=2020-01-01&published_before=2023-12-31
  GET /api/v1/books/?min_copies=2
"""

import django_filters
from .models import Book


class BookFilter(django_filters.FilterSet):
    """
    Custom FilterSet for the Book model.
    
    Provides fine-grained filtering beyond what DRF's SearchFilter offers.
    SearchFilter does full-text search; FilterSet does field-specific filtering.
    """

    # Filter by exact category ID
    # ?category=3
    category = django_filters.NumberFilter(
        field_name='category__id',
        lookup_expr='exact',
        label='Category ID'
    )

    # Filter by category slug (URL-friendly)
    # ?category_slug=science-fiction
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact',
        label='Category slug'
    )

    # Filter by exact author ID
    # ?author=5
    author = django_filters.NumberFilter(
        field_name='author__id',
        lookup_expr='exact',
        label='Author ID'
    )

    # Filter by author name (partial, case-insensitive)
    # ?author_name=tolkien
    author_name = django_filters.CharFilter(
        field_name='author__name',
        lookup_expr='icontains',
        label='Author name (partial)'
    )

    # Filter books by availability
    # ?available=true
    available = django_filters.BooleanFilter(
        field_name='available_copies',
        method='filter_available',
        label='Only available books'
    )

    # Range filters for available_copies
    # ?min_copies=2
    min_copies = django_filters.NumberFilter(
        field_name='available_copies',
        lookup_expr='gte',  # gte = greater than or equal
        label='Minimum available copies'
    )
    max_copies = django_filters.NumberFilter(
        field_name='available_copies',
        lookup_expr='lte',  # lte = less than or equal
        label='Maximum available copies'
    )

    # Date range filters for published_date
    # ?published_after=2020-01-01&published_before=2023-12-31
    published_after = django_filters.DateFilter(
        field_name='published_date',
        lookup_expr='gte',
        label='Published on or after (YYYY-MM-DD)'
    )
    published_before = django_filters.DateFilter(
        field_name='published_date',
        lookup_expr='lte',
        label='Published on or before (YYYY-MM-DD)'
    )

    class Meta:
        model = Book
        # These are the default filterable fields (exact match)
        fields = ['category', 'author', 'isbn']

    def filter_available(self, queryset, name, value):
        """
        Custom filter method for boolean availability check.
        
        When value=True: return books with at least 1 available copy
        When value=False: return books with 0 available copies (all borrowed)
        
        Custom filter methods have the signature: (self, queryset, name, value)
        'name' is the filter field name, 'value' is the cleaned filter value.
        """
        if value:
            return queryset.filter(available_copies__gt=0)
        return queryset.filter(available_copies=0)
