"""
Books Models
============

This module defines the core data models for the library catalog:
- Author: who wrote the books
- Category: how books are organized (genre/subject)
- Book: the main catalog item

Teaching Notes:
- ForeignKey creates a many-to-one relationship (many books, one author)
- on_delete=models.CASCADE: deleting an Author deletes all their books
- on_delete=models.SET_NULL: deleting a Category sets the book's category to NULL
- related_name lets you do author.books.all() from the Author side
- SlugField is used for URL-friendly identifiers (e.g., "science-fiction")
- The __str__ method defines how the object appears in Django admin and debugging
"""

from django.db import models
from django.utils.text import slugify


class Author(models.Model):
    """
    Represents a book author.
    
    Simple model — authors just have a name and optional bio.
    In a real system you might add social links, nationality, etc.
    """
    name = models.CharField(max_length=200)
    bio = models.TextField(blank=True, default='', help_text='Author biography')
    birth_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Category(models.Model):
    """
    A book category/genre (e.g., Science Fiction, History, Programming).
    
    The slug field is a URL-safe version of the name:
    "Science Fiction" → "science-fiction"
    Useful for pretty URLs like /books/?category=science-fiction
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(
        max_length=100,
        unique=True,
        blank=True,
        help_text='URL-friendly version of the name, auto-generated if empty'
    )

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Auto-generate slug from name if not provided.
        
        Overriding save() is how you add pre-save logic in Django.
        slugify('Science Fiction') → 'science-fiction'
        """
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class Book(models.Model):
    """
    The main catalog model — represents a physical or digital book.
    
    Key design decisions:
    - available_copies tracks how many can currently be borrowed
    - total_copies is the library's total stock
    - available_copies should never exceed total_copies
    - ISBN (International Standard Book Number) uniquely identifies a book edition
    """

    title = models.CharField(max_length=300)

    # ForeignKey = many books can have one author
    # null=True, blank=True allows books with unknown authors
    # related_name='books' lets us do: author.books.all()
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,
        related_name='books',
        help_text='Primary author of the book'
    )

    # SET_NULL means if a category is deleted, books aren't deleted —
    # their category field is just set to NULL
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='books',
    )

    # ISBN-13 format: 13 digits, globally unique book identifier
    isbn = models.CharField(
        max_length=13,
        unique=True,
        help_text='13-digit ISBN number'
    )

    description = models.TextField(blank=True, default='')
    published_date = models.DateField(null=True, blank=True)

    # Copy tracking — business logic lives in the model and serializer
    available_copies = models.PositiveIntegerField(default=1)
    total_copies = models.PositiveIntegerField(default=1)

    # ImageField stores the file path; actual file is saved to MEDIA_ROOT
    cover_image = models.ImageField(
        upload_to='book_covers/%Y/%m/',
        null=True,
        blank=True
    )

    # auto_now_add sets the timestamp when the object is first created
    # auto_now updates the timestamp every time the object is saved
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']  # Newest books first by default

    def __str__(self):
        return f'{self.title} by {self.author.name}'

    @property
    def is_available(self):
        """
        A model property that computes availability.
        Properties are not stored in the database — they're computed on access.
        We expose this in the API via SerializerMethodField.
        """
        return self.available_copies > 0

    def borrow(self):
        """
        Decrement available copies when a book is borrowed.
        Raises ValueError if no copies are available.
        Called by LoanViewSet.perform_create().
        """
        if self.available_copies <= 0:
            raise ValueError(f'No available copies of "{self.title}"')
        self.available_copies -= 1
        self.save(update_fields=['available_copies'])  # Only update this one field (efficient)

    def return_book(self):
        """
        Increment available copies when a book is returned.
        Called by LoanViewSet when processing a return.
        """
        if self.available_copies < self.total_copies:
            self.available_copies += 1
            self.save(update_fields=['available_copies'])
