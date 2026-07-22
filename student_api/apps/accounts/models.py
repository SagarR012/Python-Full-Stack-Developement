"""
Accounts Models — Student Management API
=========================================

COMPARE WITH: library_api/apps/accounts/models.py

The pattern is identical:
- Extend AbstractUser (not AbstractBaseUser)
- Add a role field using TextChoices
- Add convenience properties for role checks

DIFFERENCES FROM LIBRARY API:
- Roles: Admin, Teacher, Student (instead of Admin, Librarian, Member)
- Added phone_number field
- Added department field (teachers/students belong to departments)
- Added employee_id / student_id for institutional identifiers

STUDENT EXERCISE:
After studying this file, try to answer:
1. Why do we use get_user_model() instead of importing User directly?
2. What would happen if we used AbstractBaseUser instead of AbstractUser?
3. Why are is_admin, is_teacher, is_student defined as @property?
"""

from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """
    Custom User model for the student management system.

    Roles:
    - ADMIN: Full access — can manage everything
    - TEACHER: Can manage courses, create assignments, enter grades
    - STUDENT: Can view their own profile, courses they're enrolled in, their grades
    """

    class Role(models.TextChoices):
        ADMIN   = 'admin',   'Admin'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'

    # Custom profile fields
    phone_number = models.CharField(
        max_length=20,
        blank=True,
        default='',
        help_text='Contact phone number'
    )

    bio = models.TextField(
        blank=True,
        default='',
        help_text='Short biography or description'
    )

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,   # New users default to student
        help_text='Determines what actions the user can perform'
    )

    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_joined']

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'

    # -------------------------------------------------------------------------
    # Convenience properties — use these in permissions and views
    # if request.user.is_teacher:  ← much more readable than role == 'teacher'
    # -------------------------------------------------------------------------

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_teacher_or_admin(self):
        """Check if user can perform teacher-level operations."""
        return self.role in [self.Role.ADMIN, self.Role.TEACHER]
