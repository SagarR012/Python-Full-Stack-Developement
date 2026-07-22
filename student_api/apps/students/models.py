"""
Students Models — Student Management API
==========================================

Models in this app:
- Department: academic departments (Computer Science, Mathematics, etc.)
- StudentProfile: extended profile linked to a User with role='student'
- TeacherProfile: extended profile linked to a User with role='teacher'

COMPARE WITH: library_api/apps/books/models.py

Patterns used here that you saw in the library API:
- TextChoices for enrollment year
- SlugField with auto-generation in save()
- @property for computed values (full_name, is_active_student)
- related_name for reverse FK access
- ForeignKey with on_delete options

STUDENT EXERCISE:
1. Add a 'gpa' property to StudentProfile that calculates GPA from grades
   (Hint: you'll need to import Grade from apps.grades.models later)
2. Add a 'course_count' property to TeacherProfile
3. What is the difference between on_delete=CASCADE and on_delete=SET_NULL?
   When would you use each for StudentProfile.department?
"""

from django.db import models
from django.utils.text import slugify
from django.contrib.auth import get_user_model

User = get_user_model()


class Department(models.Model):
    """
    An academic department (e.g., Computer Science, Mathematics).

    Uses a slug for URL-friendly department identifiers.
    Slug is auto-generated from name if not provided (same as Category in library API).
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(
        max_length=200,
        unique=True,
        blank=True,
        help_text='URL-friendly version of the name, auto-generated if empty'
    )
    description = models.TextField(blank=True, default='')
    head_of_department = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Name of the department head'
    )

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """Auto-generate slug from name if not provided."""
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class StudentProfile(models.Model):
    """
    Extended profile for students (users with role='student').

    OneToOneField means one User → one StudentProfile (not many).
    This is different from ForeignKey (one User → many objects).

    Why separate StudentProfile from User?
    - Keeps the User model clean and generic
    - Student-specific fields don't pollute the base user
    - Follows the open/closed principle
    """

    class YearLevel(models.TextChoices):
        FIRST  = '1', 'First Year'
        SECOND = '2', 'Second Year'
        THIRD  = '3', 'Third Year'
        FOURTH = '4', 'Fourth Year'
        FIFTH  = '5', 'Fifth Year'

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        INACTIVE  = 'inactive',  'Inactive'
        GRADUATED = 'graduated', 'Graduated'
        SUSPENDED = 'suspended', 'Suspended'

    # OneToOneField: each user has exactly one student profile
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='student_profile',
        help_text='The user account this profile belongs to'
    )

    student_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='Institutional student ID (e.g., STU-2024-001)'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,   # If department is deleted, don't delete student
        null=True,
        blank=True,
        related_name='students',
        help_text='The department this student belongs to'
    )

    year_level = models.CharField(
        max_length=1,
        choices=YearLevel.choices,
        default=YearLevel.FIRST,
    )

    date_of_birth = models.DateField(null=True, blank=True)
    enrollment_date = models.DateField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    address = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['student_id']

    def __str__(self):
        return f'{self.student_id} — {self.user.get_full_name() or self.user.username}'

    @property
    def full_name(self):
        """Computed from the linked User object."""
        return self.user.get_full_name() or self.user.username

    @property
    def is_active_student(self):
        return self.status == self.Status.ACTIVE


class TeacherProfile(models.Model):
    """
    Extended profile for teachers (users with role='teacher').
    """

    class EmploymentType(models.TextChoices):
        FULL_TIME  = 'full_time',  'Full Time'
        PART_TIME  = 'part_time',  'Part Time'
        ADJUNCT    = 'adjunct',    'Adjunct'

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='teacher_profile',
    )

    employee_id = models.CharField(
        max_length=20,
        unique=True,
        help_text='Institutional employee ID (e.g., TCH-001)'
    )

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='teachers',
    )

    specialization = models.CharField(
        max_length=200,
        blank=True,
        default='',
        help_text='Area of expertise or teaching specialization'
    )

    employment_type = models.CharField(
        max_length=20,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME,
    )

    hire_date = models.DateField(null=True, blank=True)

    class Meta:
        ordering = ['employee_id']

    def __str__(self):
        return f'{self.employee_id} — {self.user.get_full_name() or self.user.username}'

    @property
    def full_name(self):
        return self.user.get_full_name() or self.user.username
