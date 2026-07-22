"""
Loans Views
===========

The LoanViewSet demonstrates several important DRF concepts:

1. Queryset filtering based on user identity (users see their own loans)
2. Staff override (staff/admin can see all loans)
3. Custom actions with @action (return_book, my_loans)
4. Automatic user assignment via perform_create()
5. Business logic in views (decrement book copies)

Teaching Notes:
- get_queryset() is where you scope data to the current user
- perform_create() is where you inject non-user-submitted data before saving
- @action(detail=True) for single-object operations
- @action(detail=False) for collection-level operations
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Loan
from .serializers import LoanSerializer, LoanCreateSerializer, LoanReturnSerializer
from apps.accounts.permissions import IsAdminUser


@extend_schema_view(
    list=extend_schema(summary='List loans (own loans for members, all for staff)', tags=['Loans']),
    create=extend_schema(summary='Borrow a book', tags=['Loans']),
    retrieve=extend_schema(summary='Get loan details', tags=['Loans']),
    destroy=extend_schema(summary='Cancel a loan (admin only)', tags=['Loans']),
)
class LoanViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing book loans.
    
    Access control:
    - Regular members see only their own loans
    - Staff (is_staff=True) and admins see all loans
    - Only staff/admins can list all loans via the main list endpoint
    
    Note: We disable PUT/PATCH — loans aren't updated directly.
    Returns are handled via the return_book custom action.
    """

    # Disable full update (PUT) — use return_book action instead
    http_method_names = ['get', 'post', 'delete', 'head', 'options']

    def get_queryset(self):
        """
        Data isolation: users only see their own loans.
        
        This is a critical security pattern — without this, any authenticated
        user could GET /loans/ and see everyone's borrowing history.
        
        Staff and admins bypass this filter to see all loans.
        """
        user = self.request.user

        # Staff and admin users can see all loans
        if user.is_staff or user.is_admin:
            return Loan.objects.select_related('user', 'book', 'book__author').all()

        # Regular users only see their own loans
        return Loan.objects.select_related(
            'user', 'book', 'book__author'
        ).filter(user=user)

    def get_serializer_class(self):
        """
        Use different serializers for reading vs. creating.
        
        - list/retrieve: LoanSerializer (rich, nested data)
        - create: LoanCreateSerializer (validates book availability, sets user)
        """
        if self.action == 'create':
            return LoanCreateSerializer
        elif self.action == 'return_book':
            return LoanReturnSerializer
        return LoanSerializer

    def get_permissions(self):
        """
        All loan operations require authentication.
        Admin-only for viewing all loans and deletion.
        """
        if self.action == 'destroy':
            return [IsAdminUser()]
        return [IsAuthenticated()]

    @extend_schema(
        summary='Return a borrowed book',
        description='Mark a loan as returned. Updates loan status and increments book available copies.',
        tags=['Loans'],
    )
    @action(detail=True, methods=['post'], url_path='return')
    def return_book(self, request, pk=None):
        """
        Custom action: POST /api/v1/loans/{id}/return/
        
        Processes a book return:
        1. Verify the loan belongs to the requesting user
        2. Verify the loan is still active (not already returned)
        3. Call loan.process_return() which updates status and book copies
        
        Why a custom action instead of PATCH?
        - The return process involves multiple model changes atomically
        - A custom action makes the intent explicit in the URL
        - It allows us to enforce business rules cleanly
        """
        loan = self.get_object()  # get_object() also enforces object-level permissions

        # Check that this loan belongs to the current user (unless staff)
        if not (request.user.is_staff or request.user.is_admin):
            if loan.user != request.user:
                return Response(
                    {'error': 'You can only return your own loans.'},
                    status=status.HTTP_403_FORBIDDEN
                )

        # Prevent returning a book that was already returned
        if loan.status == Loan.Status.RETURNED:
            return Response(
                {'error': 'This book has already been returned.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Optional notes from the return request
        notes = request.data.get('notes', '')
        if notes:
            loan.notes = notes

        # This method handles all the return logic atomically
        loan.process_return()

        return Response(
            LoanSerializer(loan).data,
            status=status.HTTP_200_OK
        )

    @extend_schema(
        summary='List current user\'s loans',
        description='Returns only the loans belonging to the currently authenticated user.',
        tags=['Loans'],
    )
    @action(detail=False, methods=['get'], url_path='my-loans')
    def my_loans(self, request):
        """
        Custom action: GET /api/v1/loans/my-loans/
        
        Returns the current user's loans regardless of whether they're staff.
        This is useful for staff members who want to see their personal loans
        without seeing everyone else's.
        
        detail=False means this action works on the collection, not a single object.
        No {pk} in the URL.
        """
        loans = Loan.objects.filter(
            user=request.user
        ).select_related('book', 'book__author')

        # Filter by status if provided: ?status=active
        status_filter = request.query_params.get('status')
        if status_filter:
            loans = loans.filter(status=status_filter)

        # Use DRF's pagination from settings
        page = self.paginate_queryset(loans)
        if page is not None:
            serializer = LoanSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = LoanSerializer(loans, many=True)
        return Response(serializer.data)
