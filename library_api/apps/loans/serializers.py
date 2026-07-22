"""
Loans Serializers
=================

This module shows more advanced serializer patterns:

1. LoanSerializer — full read representation with nested data
2. LoanCreateSerializer — write-optimized with custom validation and auto-fields
3. LoanReturnSerializer — minimal update serializer for the return action

Teaching Notes:
- Use CurrentUserDefault() to automatically set the user to the logged-in user
- validate() method can check external state (e.g., book availability)
- SerializerMethodField is great for computed state like is_overdue
- Keep create/update serializers simple — accept IDs, not nested objects
"""

from datetime import date, timedelta
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.books.serializers import BookListSerializer
from .models import Loan

User = get_user_model()


class LoanSerializer(serializers.ModelSerializer):
    """
    Full read serializer for Loan objects.
    
    Includes nested book and user data for rich API responses.
    Also computes is_overdue from the model property.
    """

    # Nested book data — the borrower needs to see which book this is
    book_detail = BookListSerializer(source='book', read_only=True)

    # Computed field from model property
    is_overdue = serializers.SerializerMethodField()

    # Show username without nesting the full user object
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Loan
        fields = [
            'id', 'username', 'book', 'book_detail', 'loan_date',
            'due_date', 'return_date', 'status', 'is_overdue', 'notes'
        ]
        read_only_fields = ['id', 'loan_date', 'return_date', 'status']

    def get_is_overdue(self, obj):
        """Return the overdue status from the model property."""
        return obj.is_overdue


class LoanCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a new loan.
    
    Key design choices:
    - user is set automatically from the JWT token (not from request body)
    - due_date is auto-calculated (14 days from today)
    - validate() checks that the book has available copies
    
    This prevents clients from:
    - Borrowing books that are out of stock
    - Setting their own due dates
    - Borrowing as another user
    """

    # HiddenField is not shown in the API schema and not accepted from input.
    # CurrentUserDefault() automatically sets it to request.user.
    # This is the DRF-recommended way to handle "created_by" / "user" fields.
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Loan
        fields = ['id', 'user', 'book', 'notes', 'due_date', 'loan_date']
        read_only_fields = ['id', 'loan_date', 'due_date']

    def validate_book(self, book):
        """
        Validate that the requested book has available copies.
        
        This is field-level validation for the 'book' field.
        Runs before the cross-field validate() method.
        """
        if book.available_copies <= 0:
            raise serializers.ValidationError(
                f'"{book.title}" has no available copies. Please check back later.'
            )
        return book

    def validate(self, attrs):
        """
        Check for existing active loans of the same book by the same user.
        Prevents a user from borrowing the same book twice simultaneously.
        """
        user = attrs['user']
        book = attrs['book']

        existing_loan = Loan.objects.filter(
            user=user,
            book=book,
            status=Loan.Status.ACTIVE
        ).first()

        if existing_loan:
            raise serializers.ValidationError(
                f'You already have an active loan for "{book.title}".'
            )
        return attrs

    def create(self, validated_data):
        """
        Override create to auto-set the due_date before saving.
        
        Due date = today + 14 days.
        We set it here (not in validate) because it's not validation logic —
        it's business logic that generates a derived field.
        """
        validated_data['due_date'] = date.today() + timedelta(days=14)
        loan = Loan.objects.create(**validated_data)
        # Decrement available copies
        loan.book.borrow()
        return loan


class LoanReturnSerializer(serializers.ModelSerializer):
    """
    Minimal serializer for the return_book action.
    
    When returning a book, the client only needs to optionally add notes.
    The actual status change and timestamps are handled in the view's action method.
    """

    class Meta:
        model = Loan
        fields = ['id', 'notes', 'status', 'return_date']
        read_only_fields = ['id', 'status', 'return_date']
