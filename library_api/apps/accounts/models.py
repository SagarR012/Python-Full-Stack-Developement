"""
Accounts Models
===============

This module defines the custom User model for the library system.

Teaching Notes:
- Always use a custom User model from the start of a project.
  Changing AUTH_USER_MODEL after migrations have been run is extremely painful.
- Extending AbstractUser is the simplest approach: you keep all built-in
  fields (username, email, password, is_staff, etc.) and just add your own.
- The 'role' field demonstrates a common pattern: using choices to create
  a type/role system without a separate Role table.
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model for the library system.

    We extend AbstractUser (not AbstractBaseUser) because:
    - AbstractUser already has username, email, password, first_name, etc.
    - AbstractBaseUser requires you to implement everything from scratch
    - AbstractUser is the right choice when you just want to add fields

    Role System:
    - ADMIN: Full access to everything
    - LIBRARIAN: Can manage books and loans
    - MEMBER: Regular library member, can borrow books
    """

    class Role(models.TextChoices):
        """
        TextChoices creates an enum-like class for string choices.
        Each entry is (database_value, human_readable_label).
        Using a nested class keeps choices close to the field that uses them.
        """
        ADMIN = 'admin', 'Admin'
        LIBRARIAN = 'librarian', 'Librarian'
        MEMBER = 'member', 'Member'

    # Additional profile fields beyond the AbstractUser defaults
    bio = models.TextField(
        blank=True,
        default='',
        help_text='A short biography of the user'
    )

    avatar = models.ImageField(
        upload_to='avatars/%Y/%m/',  # Organizes files by year/month to avoid huge directories
        null=True,
        blank=True,
        help_text='Profile picture'
    )

    date_of_birth = models.DateField(
        null=True,
        blank=True,
        help_text='User date of birth'
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,  # New users are regular members by default
        help_text='User role determines what actions they can perform'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    # -------------------------------------------------------------------------
    # Convenience properties — makes permission checking readable in views
    # e.g., if request.user.is_admin: ...
    # -------------------------------------------------------------------------

    @property
    def is_admin(self):
        """Check if user has admin role."""
        return self.role == self.Role.ADMIN

    @property
    def is_librarian(self):
        """Check if user has librarian role."""
        return self.role == self.Role.LIBRARIAN

    @property
    def is_member(self):
        """Check if user has member role."""
        return self.role == self.Role.MEMBER

    @property
    def is_librarian_or_admin(self):
        """Check if user can manage library resources."""
        return self.role in [self.Role.ADMIN, self.Role.LIBRARIAN]
