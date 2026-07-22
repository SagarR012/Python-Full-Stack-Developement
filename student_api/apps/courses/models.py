"""
Courses Models — Student Management API
=========================================

Models:
- Course: a course offering (e.g., CS101 Introduction to Programming)
- Enrollment: junction table linking students to courses (with extra data)

COMPARE WITH: library_api/apps/loans/models.py

The Enrollment model mirrors the Loan model:
- Both are junction tables (User-Book vs Student-Course)
- Both have a status field with TextChoices
- Both have date fields (loan_date vs enrollment_date)
- Both have business logic methods (process_return vs drop_course)

STUDENT EXERCISE:
1. Add a 'max_students' field to Course and validate in
   EnrollmentSerializer that the course isn't full
2. Add an 'is_full' @property to Course
3. Add a 'drop_course' method to Enrollment (mirrors loan.process_return)
4. Add a prerequisite ManyToManyField to Course (self-referential)
"""

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Course(models.Model):
    """
    A course offering.

    Course code is a unique identifier (e.g., "CS101", "MATH201").
    A course is taught by a teacher (ForeignKey to User with role='teacher').
    """

    class Status(models.TextChoices):
        ACTIVE    = 'active',    'Active'
        INACTIVE  = 'inactive',  'Inactive'
        COMPLETED = 'completed', 'Completed'

    course_code = models.CharField(
        max_length=20,
        unique=True,
        help_text='Unique course code (e.g., CS101)'
    )

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, default='')

    # The teacher who teaches this course
    # ForeignKey: one teacher → many courses
    # null=True: course can exist without a teacher assignment
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses_taught',
        help_text='Teacher assigned to this course'
    )

    # FK to department — same SET_NULL pattern as Book.category
    department = models.ForeignKey(
        'students.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='courses',
    )

    credits = models.PositiveSmallIntegerField(
        default=3,
        help_text='Number of credit hours'
    )

    max_students = models.PositiveIntegerField(
        default=30,
        help_text='Maximum number of students that can enroll'
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['course_code']

    def __str__(self):
        return f'{self.course_code}: {self.title}'

    @property
    def enrolled_count(self):
        """Number of currently enrolled students."""
        return self.enrollments.filter(status=Enrollment.Status.ENROLLED).count()

    @property
    def is_full(self):
        """Check if the course has reached its student capacity."""
        return self.enrolled_count >= self.max_students

    @property
    def is_active(self):
        return self.status == self.Status.ACTIVE


class Enrollment(models.Model):
    """
    Enrollment records track which students are in which courses.

    This is the junction/association table between StudentProfile and Course,
    with additional data (enrollment date, status, grade).

    MIRRORS: library_api/apps/loans/models.py Loan model
    - Loan: User ←→ Book (who borrowed what)
    - Enrollment: StudentProfile ←→ Course (who is enrolled where)
    """

    class Status(models.TextChoices):
        ENROLLED   = 'enrolled',   'Enrolled'
        DROPPED    = 'dropped',    'Dropped'
        COMPLETED  = 'completed',  'Completed'
        WAITLISTED = 'waitlisted', 'Waitlisted'

    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='enrollments',
    )

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='enrollments',
    )

    enrollment_date = models.DateTimeField(auto_now_add=True)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ENROLLED,
    )

    notes = models.TextField(blank=True, default='')

    class Meta:
        ordering = ['-enrollment_date']
        # A student can only be enrolled in a course once at a time
        unique_together = [['student', 'course']]

    def __str__(self):
        return f'{self.student} enrolled in {self.course}'

    def drop_course(self):
        """
        Process a course drop.
        Business logic in the model (Fat Model, Skinny View).
        """
        self.status = self.Status.DROPPED
        self.save(update_fields=['status'])
