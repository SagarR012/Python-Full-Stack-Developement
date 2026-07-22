"""
Books Views
===========

This module uses ViewSets — the most powerful view abstraction in DRF.

Teaching Notes:

ViewSet vs APIView:
- APIView: One class per HTTP method combination (ListBooks, CreateBook are separate)
- ViewSet: One class for all related operations on a resource

ModelViewSet provides all 5 standard actions:
  list()     → GET /books/         → returns list
  create()   → POST /books/        → creates object
  retrieve() → GET /books/{id}/    → returns one object
  update()   → PUT /books/{id}/    → full update
  partial_update() → PATCH /books/{id}/ → partial update
  destroy()  → DELETE /books/{id}/ → deletes object

Custom Actions:
- @action(detail=True) creates GET/POST /books/{id}/custom-action/
- @action(detail=False) creates GET/POST /books/custom-action/

Key ViewSet hooks:
- get_queryset(): customize what objects are returned
- get_serializer_class(): use different serializers per action
- perform_create(): customize object creation (e.g., set owner)
- get_permissions(): dynamic permissions based on action
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from .models import Author, Category, Book
from .serializers import (
    AuthorSerializer,
    CategorySerializer,
    BookListSerializer,
    BookDetailSerializer,
    BookCreateUpdateSerializer,
)
from .filters import BookFilter
from apps.accounts.permissions import IsLibrarianOrAdmin


@extend_schema_view(
    list=extend_schema(summary='List all authors', tags=['Authors & Categories']),
    create=extend_schema(summary='Create an author', tags=['Authors & Categories']),
    retrieve=extend_schema(summary='Get author details', tags=['Authors & Categories']),
    update=extend_schema(summary='Update an author', tags=['Authors & Categories']),
    partial_update=extend_schema(summary='Partially update an author', tags=['Authors & Categories']),
    destroy=extend_schema(summary='Delete an author', tags=['Authors & Categories']),
)
class AuthorViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Author CRUD operations.
    
    ModelViewSet is the "batteries included" option — it provides
    list, create, retrieve, update, partial_update, and destroy
    without writing any action methods.
    
    The router handles URL generation (see urls.py).
    """
    queryset = Author.objects.all()
    serializer_class = AuthorSerializer

    def get_permissions(self):
        """
        Dynamic permission assignment based on the action being performed.
        
        This is more flexible than setting permission_classes at class level
        because different operations can have different access requirements.
        
        - list/retrieve: Anyone can read author info
        - create/update/destroy: Only librarians or admins
        """
        if self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsLibrarianOrAdmin]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        """
        Optimize database queries with prefetch_related.
        
        Without prefetch_related, accessing author.books.count() for each
        author in a list would cause N+1 queries:
        - 1 query to get all authors
        - N queries to get books for each author (one per author)
        
        With prefetch_related('books'), Django fetches all books in 1 extra
        query and caches them — total 2 queries regardless of author count.
        """
        return Author.objects.prefetch_related('books').all()


@extend_schema_view(
    list=extend_schema(summary='List all categories', tags=['Authors & Categories']),
    create=extend_schema(summary='Create a category', tags=['Authors & Categories']),
    retrieve=extend_schema(summary='Get category details', tags=['Authors & Categories']),
    update=extend_schema(summary='Update a category', tags=['Authors & Categories']),
    partial_update=extend_schema(summary='Partially update a category', tags=['Authors & Categories']),
    destroy=extend_schema(summary='Delete a category', tags=['Authors & Categories']),
)
class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for Category CRUD operations."""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsLibrarianOrAdmin()]


@extend_schema_view(
    list=extend_schema(
        summary='List all books',
        tags=['Books'],
        parameters=[
            OpenApiParameter('search', description='Search by title, author, or ISBN', required=False, type=str),
            OpenApiParameter('category', description='Filter by category ID', required=False, type=int),
            OpenApiParameter('author', description='Filter by author ID', required=False, type=int),
            OpenApiParameter('available', description='Filter only available books', required=False, type=bool),
            OpenApiParameter('ordering', description='Order by: title, -title, published_date, -published_date', required=False, type=str),
        ]
    ),
    create=extend_schema(summary='Create a book (librarian/admin only)', tags=['Books']),
    retrieve=extend_schema(summary='Get book details', tags=['Books']),
    update=extend_schema(summary='Update a book (librarian/admin only)', tags=['Books']),
    partial_update=extend_schema(summary='Partially update a book (librarian/admin only)', tags=['Books']),
    destroy=extend_schema(summary='Delete a book (librarian/admin only)', tags=['Books']),
)
class BookViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Book CRUD + custom actions.
    
    This is the most feature-rich ViewSet in the project, demonstrating:
    - Dynamic serializer selection (get_serializer_class)
    - Dynamic permissions (get_permissions)
    - Custom filtering (filterset_class, search_fields, ordering_fields)
    - Custom actions (@action decorator)
    - Query optimization (select_related, prefetch_related)
    """

    # FilterSet class for field-specific filtering
    filterset_class = BookFilter

    # SearchFilter backend uses these fields for ?search= queries
    # '^' prefix = starts with; '=' = exact; '@' = full-text; '' = icontains
    search_fields = ['title', 'author__name', 'isbn', 'description']

    # OrderingFilter backend uses these fields for ?ordering= queries
    ordering_fields = ['title', 'published_date', 'created_at', 'available_copies']
    ordering = ['-created_at']  # Default ordering

    def get_queryset(self):
        """
        Optimize with select_related for FK relationships.
        
        select_related works for ForeignKey/OneToOne relationships.
        It performs a SQL JOIN, fetching related objects in the same query.
        
        Without this: accessing book.author.name for 100 books = 101 queries
        With this: 1 query with JOINed data
        """
        return Book.objects.select_related('author', 'category').all()

    def get_serializer_class(self):
        """
        Return different serializers based on the action.
        
        This is a powerful DRF pattern:
        - list action: lightweight serializer (many objects, want less data)
        - retrieve action: detailed serializer (one object, want full data)
        - create/update: input-optimized serializer (accept IDs, not nested objects)
        
        This avoids having one "god serializer" that tries to do everything.
        """
        if self.action == 'list':
            return BookListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return BookCreateUpdateSerializer
        else:
            # retrieve, destroy, and custom actions
            return BookDetailSerializer

    def get_permissions(self):
        """
        Permission strategy for Book endpoints:
        - Reading (list, retrieve, availability): open to everyone
        - Writing (create, update, delete): requires librarian or admin role
        """
        if self.action in ['list', 'retrieve', 'availability']:
            return [AllowAny()]
        return [IsLibrarianOrAdmin()]

    @extend_schema(
        summary='Check book availability',
        description='Returns availability status and copy counts for a specific book.',
        tags=['Books'],
    )
    @action(detail=True, methods=['get'], url_path='availability')
    def availability(self, request, pk=None):
        """
        Custom action: GET /api/v1/books/{id}/availability/
        
        The @action decorator creates a new URL for this ViewSet.
        detail=True means it operates on a single object (requires {pk} in URL).
        detail=False would mean it operates on the collection.
        
        url_path='availability' sets the URL segment (default would be 'availability'
        from the method name anyway, but being explicit is clearer).
        """
        book = self.get_object()  # Fetches book by pk, handles 404 automatically
        return Response({
            'id': book.id,
            'title': book.title,
            'is_available': book.is_available,
            'available_copies': book.available_copies,
            'total_copies': book.total_copies,
            'borrowed_copies': book.total_copies - book.available_copies,
        })
