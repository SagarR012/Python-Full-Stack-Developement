"""
Books Serializers
=================

This module demonstrates several serializer patterns:

1. Simple ModelSerializer (Author, Category)
2. Nested serializers — embedding related objects instead of just IDs
3. Multiple serializers per model — different shapes for different actions
4. SerializerMethodField — computed/read-only fields
5. Custom validation at the field and object level

Teaching Notes:
- Using nested serializers in LIST views improves API usability
  (clients get author name, not just author ID)
- But nested writes are complex — for CREATE/UPDATE use flat IDs
- This is why BookListSerializer (nested) differs from BookCreateUpdateSerializer (flat IDs)
"""

from rest_framework import serializers
from .models import Author, Category, Book


class AuthorSerializer(serializers.ModelSerializer):
    """
    Full serializer for Author — used for CRUD operations.
    book_count is a computed field showing how many books this author has.
    """

    # SerializerMethodField is for read-only computed values
    book_count = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'birth_date', 'book_count']
        read_only_fields = ['id']

    def get_book_count(self, obj):
        """
        Count the books for this author.
        obj.books is the reverse relation defined by related_name='books' on the FK.
        
        Note: This causes N+1 queries if not careful — see books/views.py
        for how we use select_related/prefetch_related to avoid this.
        """
        return obj.books.count()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    book_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'book_count']
        # slug is auto-generated — don't require it from the client
        read_only_fields = ['id', 'slug']

    def get_book_count(self, obj):
        return obj.books.count()


class BookListSerializer(serializers.ModelSerializer):
    """
    Used for GET /books/ (list view) — returns many books.
    
    We NEST the author and category objects here so the client gets
    full details without making extra requests. This is called "eager loading"
    in API design.
    
    Tradeoff: More data per response, but fewer total requests.
    """

    # Nested serializers — the author object is embedded in the book JSON
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    # is_available is a property on the model, exposed here as a read-only field
    is_available = serializers.BooleanField(read_only=True)

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'category', 'isbn',
            'published_date', 'available_copies', 'total_copies',
            'is_available', 'cover_image', 'created_at'
        ]


class BookDetailSerializer(serializers.ModelSerializer):
    """
    Used for GET /books/{id}/ (detail view) — returns one book with full info.
    
    Includes all fields including description and the computed is_available.
    """

    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)
    is_available = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'category', 'isbn', 'description',
            'published_date', 'available_copies', 'total_copies',
            'is_available', 'cover_image', 'created_at', 'updated_at'
        ]

    def get_is_available(self, obj):
        """
        Using SerializerMethodField here instead of the model property
        to show both approaches. Both work fine — the method approach
        gives you more control over computation.
        """
        return obj.available_copies > 0


class BookCreateUpdateSerializer(serializers.ModelSerializer):
    """
    Used for POST/PUT/PATCH (create and update operations).
    
    Why not use the nested serializer for writes?
    - Nested creates/updates require complex logic
    - For writes, we just need the foreign key IDs (author_id, category_id)
    - Keep writes simple: accept IDs, return full nested objects separately
    
    This is a common API pattern: input accepts IDs, output returns objects.
    """

    class Meta:
        model = Book
        fields = [
            'id', 'title', 'author', 'category', 'isbn', 'description',
            'published_date', 'available_copies', 'total_copies', 'cover_image'
        ]
        read_only_fields = ['id']

    def validate_isbn(self, value):
        """
        Validate ISBN format: must be exactly 13 digits.
        """
        # Remove hyphens that users might include: 978-0-7432-7356-5
        isbn_clean = value.replace('-', '').replace(' ', '')
        if not isbn_clean.isdigit():
            raise serializers.ValidationError('ISBN must contain only digits (and optional hyphens).')
        if len(isbn_clean) not in (10, 13):
            raise serializers.ValidationError('ISBN must be 10 or 13 digits long.')
        return isbn_clean

    def validate(self, attrs):
        """
        Cross-field validation: available_copies must not exceed total_copies.
        """
        available = attrs.get('available_copies')
        total = attrs.get('total_copies')

        # On partial update (PATCH), these fields might not be in attrs
        if available is not None and total is not None:
            if available > total:
                raise serializers.ValidationError(
                    'available_copies cannot exceed total_copies.'
                )
        return attrs
