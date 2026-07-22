"""
Loans Models
============

The Loan model tracks book borrowing activity — who borrowed what and when.

Teaching Notes:
- This is a junction/association table between User and Book
- It adds extra data to the relationship: loan_date, due_date, status
- Django's get_user_model() is used instead of a direct import to avoid
  coupling to a specific User class
- The status field uses choices to enforce valid state transitions
- auto_now_add captures the exact moment of loan creation
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Loan(models.Model):
    """
    Represents a book loan transaction.
    
    Lifecycle:
    1. Created with status=ACTIVE when a member borrows a book
    2. Updated to status=RETURNED when the book is brought back
    3. A background job (or manual process) marks overdue loans as OVERDUE
    """

    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'        # Book currently borrowed
        RETURNED = 'returned', 'Returned'  # Book has been returned
        OVERDUE = 'overdue', 'Overdue'     # Past due date, not returned

    # Who borrowed the book
    # on_delete=CASCADE: if the user is deleted, their loan records are also deleted
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='loans',
        help_text='The user who borrowed the book'
    )

    # Which book was borrowed
    book = models.ForeignKey(
        'books.Book',
        on_delete=models.CASCADE,
        related_name='loans',
        help_text='The book being borrowed'
    )

    # Timestamps
    # auto_now_add: set once when the record is created, never updated
    loan_date = models.DateTimeField(
        auto_now_add=True,
        help_text='When the book was borrowed'
    )

    # Due date is set by the serializer (14 days from loan_date)
    due_date = models.DateField(
        help_text='When the book must be returned'
    )

    # return_date is NULL until the book is actually returned
    return_date = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the book was actually returned (null if not yet returned)'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    notes = models.TextField(
        blank=True,
        default='',
        help_text='Optional notes about this loan (damage, special circumstances, etc.)'
    )

    class Meta:
        ordering = ['-loan_date']

    def __str__(self):
        return f'{self.user.username} → {self.book.title} ({self.status})'

    @property
    def is_overdue(self):
        """
        Check if this loan is overdue.
        Uses timezone.now().date() to compare dates correctly,
        regardless of time zone settings.
        """
        if self.status == self.Status.RETURNED:
            return False
        return timezone.now().date() > self.due_date

    def process_return(self):
        """
        Process a book return:
        1. Set return_date to now
        2. Update status to RETURNED
        3. Call book.return_book() to increment available_copies
        
        This method encapsulates the return business logic in one place,
        following the "Fat Model, Skinny View" principle.
        """
        self.return_date = timezone.now()
        self.status = self.Status.RETURNED
        self.save(update_fields=['return_date', 'status'])
        self.book.return_book()
