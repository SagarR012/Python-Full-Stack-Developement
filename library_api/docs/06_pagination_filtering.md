# Lesson 06: Pagination, Filtering & Search

## Overview

Without pagination, a request for `/api/v1/books/` could return
thousands of records and crash the client's browser. Without filtering,
clients have to download everything and filter on their end.
These features make your API practical at scale.

---

## 1. Why Pagination?

```
Database: 50,000 books
GET /api/v1/books/  → sends all 50,000 records → ❌ slow, crashes clients

GET /api/v1/books/?page=1  → sends records 1-10  → ✅ fast
GET /api/v1/books/?page=2  → sends records 11-20 → ✅ fast
```

---

## 2. PageNumberPagination (default in this project)

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,
}
```

**Response format:**
```json
{
  "count": 47,
  "next": "http://localhost:8000/api/v1/books/?page=2",
  "previous": null,
  "results": [
    { "id": 1, "title": "..." },
    ...
  ]
}
```

- `count` — total number of records
- `next` — URL for the next page (null if on last page)
- `previous` — URL for the previous page (null if on first page)
- `results` — the actual data for this page

**Usage:**
```
GET /api/v1/books/        → page 1 (records 1-10)
GET /api/v1/books/?page=2 → page 2 (records 11-20)
GET /api/v1/books/?page=5 → page 5 (records 41-50)
```

---

## 3. Custom Pagination Class

```python
# In any app or a shared pagination.py file
from rest_framework.pagination import PageNumberPagination

class StandardPagination(PageNumberPagination):
    page_size = 10            # Default page size
    page_size_query_param = 'page_size'   # Allow client to set: ?page_size=25
    max_page_size = 100       # Prevent abuse: can't request more than 100
    page_query_param = 'page' # The query param name (default is 'page')

class LargePagination(PageNumberPagination):
    page_size = 50

# Apply to a specific ViewSet
class BookViewSet(viewsets.ModelViewSet):
    pagination_class = StandardPagination
```

---

## 4. CursorPagination (for large, real-time data)

```python
from rest_framework.pagination import CursorPagination

class BookCursorPagination(CursorPagination):
    page_size = 10
    ordering = '-created_at'  # Must specify ordering
```

Cursor pagination is more efficient for large datasets because it uses
a cursor (bookmark) instead of counting records.
Use it for feeds, logs, or any dataset that updates frequently.

---

## 5. Turning Off Pagination for a View

```python
class BookViewSet(viewsets.ModelViewSet):
    pagination_class = None  # Returns all records without pagination
```

Use sparingly — only for small datasets or internal APIs.

---

## 6. Using Pagination in Custom Actions

```python
@action(detail=False, methods=['get'], url_path='my-loans')
def my_loans(self, request):
    loans = Loan.objects.filter(user=request.user)

    # Use the ViewSet's paginator
    page = self.paginate_queryset(loans)
    if page is not None:
        serializer = LoanSerializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    # Fallback if pagination is disabled
    serializer = LoanSerializer(loans, many=True)
    return Response(serializer.data)
```

---

## 7. Filtering with DjangoFilterBackend

DjangoFilterBackend enables exact-match filtering via query params.

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

### Simple filtering with filterset_fields

```python
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    # Auto-generates exact-match filters for these fields
    filterset_fields = ['category', 'author', 'isbn']
```

Usage:
```
GET /api/v1/books/?category=1         → books in category 1
GET /api/v1/books/?author=3           → books by author 3
GET /api/v1/books/?category=1&author=3 → both filters (AND)
```

---

## 8. Custom FilterSet (advanced filtering)

```python
# books/filters.py
import django_filters
from .models import Book

class BookFilter(django_filters.FilterSet):
    # Filter by category ID
    category = django_filters.NumberFilter(
        field_name='category__id',
        lookup_expr='exact'
    )

    # Filter by category slug
    category_slug = django_filters.CharFilter(
        field_name='category__slug',
        lookup_expr='exact'
    )

    # Filter by author name (partial match)
    author_name = django_filters.CharFilter(
        field_name='author__name',
        lookup_expr='icontains'  # case-insensitive contains
    )

    # Boolean filter (custom method)
    available = django_filters.BooleanFilter(
        field_name='available_copies',
        method='filter_available'
    )

    # Date range
    published_after = django_filters.DateFilter(
        field_name='published_date',
        lookup_expr='gte'   # greater than or equal
    )
    published_before = django_filters.DateFilter(
        field_name='published_date',
        lookup_expr='lte'   # less than or equal
    )

    class Meta:
        model = Book
        fields = ['category', 'author', 'isbn']

    def filter_available(self, queryset, name, value):
        """Custom filter method."""
        if value:
            return queryset.filter(available_copies__gt=0)
        return queryset.filter(available_copies=0)
```

```python
# books/views.py
class BookViewSet(viewsets.ModelViewSet):
    filterset_class = BookFilter   # Use the custom FilterSet
```

---

## 9. lookup_expr Reference

| lookup_expr | SQL | Example |
|-------------|-----|---------|
| `exact` | `= value` | `?isbn=9780743273565` |
| `iexact` | `= LOWER(value)` | Case-insensitive exact |
| `contains` | `LIKE %value%` | `?title=ring` |
| `icontains` | `ILIKE %value%` | `?author_name=tolkien` |
| `startswith` | `LIKE value%` | Starts with |
| `istartswith` | Case-insensitive starts with | |
| `gt` | `> value` | Greater than |
| `gte` | `>= value` | Greater than or equal |
| `lt` | `< value` | Less than |
| `lte` | `<= value` | Less than or equal |
| `in` | `IN (...)` | `?status__in=active,overdue` |
| `range` | `BETWEEN` | Date ranges |

---

## 10. SearchFilter — Full-Text Search

```python
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        ...
        'rest_framework.filters.SearchFilter',
    ],
}

class BookViewSet(viewsets.ModelViewSet):
    # Fields to search across with ?search=
    search_fields = [
        'title',          # icontains by default
        'author__name',   # Follow FK relationships with __
        'isbn',
        'description',
        '^title',         # ^ = starts with
        '=isbn',          # = = exact match
        '@description',   # @ = full-text search (PostgreSQL only)
    ]
```

Usage:
```
GET /api/v1/books/?search=tolkien
→ Searches title, author.name, isbn, description for "tolkien"
```

---

## 11. OrderingFilter — Sorting Results

```python
class BookViewSet(viewsets.ModelViewSet):
    ordering_fields = ['title', 'published_date', 'created_at', 'available_copies']
    ordering = ['-created_at']   # Default ordering if no ?ordering= param
```

Usage:
```
GET /api/v1/books/?ordering=title          → A-Z by title
GET /api/v1/books/?ordering=-title         → Z-A by title (- = descending)
GET /api/v1/books/?ordering=published_date → oldest first
GET /api/v1/books/?ordering=-published_date → newest first
GET /api/v1/books/?ordering=title,-published_date  → multiple fields
```

---

## 12. Combining All Three

```
GET /api/v1/books/?
    search=tolkien           ← SearchFilter
    &category=2              ← DjangoFilterBackend
    &available=true          ← DjangoFilterBackend (custom)
    &published_after=2000-01-01   ← DjangoFilterBackend
    &ordering=-published_date     ← OrderingFilter
    &page=2                  ← Pagination
    &page_size=20            ← Custom page size
```

These filters stack — they're all AND conditions.

---

## 13. Manual Filtering in get_queryset()

For complex filtering that doesn't fit FilterSet, do it in `get_queryset()`:

```python
class BookViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        queryset = Book.objects.select_related('author', 'category')

        # Manual filter from query params
        author_id = self.request.query_params.get('author_id')
        if author_id:
            queryset = queryset.filter(author_id=author_id)

        # Availability filter
        available = self.request.query_params.get('available')
        if available == 'true':
            queryset = queryset.filter(available_copies__gt=0)

        return queryset
```

---

## 14. Swagger Filter Documentation

With drf-spectacular, add `@extend_schema` to document filter params:

```python
@extend_schema(
    parameters=[
        OpenApiParameter('search', description='Search by title or author', required=False, type=str),
        OpenApiParameter('category', description='Filter by category ID', required=False, type=int),
        OpenApiParameter('available', description='Only available books', required=False, type=bool),
        OpenApiParameter('ordering', description='Sort: title, -title, published_date', required=False, type=str),
    ]
)
def list(self, request, *args, **kwargs):
    return super().list(request, *args, **kwargs)
```

---

## Key Points to Remember

- Pagination prevents sending thousands of records at once
- `count`, `next`, `previous`, `results` are the standard pagination response fields
- `DjangoFilterBackend` for exact/range field filtering
- `SearchFilter` for full-text search across multiple fields
- `OrderingFilter` for client-controlled sorting (use `-field` for descending)
- Custom `FilterSet` classes give you full control over filter logic
- All three backends stack: filters are AND conditions
- Use `select_related` and `prefetch_related` in `get_queryset()` for efficiency
