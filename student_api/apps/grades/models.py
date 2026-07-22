"""
Grades Models — Student Management API
========================================

Models:
- Grade: a grade record linking a student, course, and score

This model ties together everything:
- ForeignKey to StudentProfile (from students app)
- ForeignKey to Course (from courses app)
- ForeignKey to User (the teacher who entered the grade)

Key patterns:
- TextChoices for letter grades
- @property for computed letter_grade
- save() override to auto-compute letter grade from score
- unique_together to prevent duplicate grade records

STUDENT EXERCISE:
1. Add a GPA calculation method to StudentProfile that averages
   all grade records (import this model there using
   'from apps.grades.models import Grade')
2. Add a 'grade_distribution' @action to the GradeViewSet that returns
   a count of A/B/C/D/F grades for a given course
3. Add a 'transcript' custom action to the student endpoint that returns
   all of a student's grades grouped by semester
"""

from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Grade(models.Model):
    """
    A grade record for a student in a specific course.

    Constraints:
    - One grade record per student per course (unique_together)
    - Score must be 0.00 – 100.00
    - Letter grade is auto-computed from the score
    """

    class LetterGrade(models.TextChoices):
        A_PLUS  = 'A+', 'A+ (97-100)'
        A       = 'A',  'A  (93-96)'
        A_MINUS = 'A-', 'A- (90-92)'
        B_PLUS  = 'B+', 'B+ (87-89)'
        B       = 'B',  'B  (83-86)'
        B_MINUS = 'B-', 'B- (80-82)'
        C_PLUS  = 'C+', 'C+ (77-79)'
        C       = 'C',  'C  (73-76)'
        C_MINUS = 'C-', 'C- (70-72)'
        D       = 'D',  'D  (60-69)'
        F       = 'F',  'F  (0-59)'
        INCOMPLETE = 'I', 'Incomplete'
        WITHDRAWN  = 'W', 'Withdrawn'

    student = models.ForeignKey(
        'students.StudentProfile',
        on_delete=models.CASCADE,
        related_name='grades',
    )

    course = models.ForeignKey(
        'courses.Course',
        on_delete=models.CASCADE,
        related_name='grades',
    )

    # The teacher who entered this grade
    teacher = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='grades_entered',
        help_text='Teacher who entered this grade'
    )

    # Numeric score 0.00 – 100.00
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(0.00),
            MaxValueValidator(100.00),
        ],
        help_text='Numeric score (0.00 – 100.00)'
    )

    # Auto-computed from score — set in save()
    letter_grade = models.CharField(
        max_length=2,
        choices=LetterGrade.choices,
        blank=True,
        default='',
    )

    remarks = models.TextField(
        blank=True,
        default='',
        help_text='Optional remarks from the teacher'
    )

    graded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-graded_at']
        # One grade record per student per course
        unique_together = [['student', 'course']]

    def __str__(self):
        return (
            f'{self.student.student_id} | {self.course.course_code} | '
            f'{self.score} ({self.letter_grade})'
        )

    @staticmethod
    def compute_letter_grade(score):
        """
        Compute letter grade from a numeric score.
        Static method — doesn't need 'self', but belongs to this class.
        """
        score = float(score)
        if score >= 97:  return 'A+'
        if score >= 93:  return 'A'
        if score >= 90:  return 'A-'
        if score >= 87:  return 'B+'
        if score >= 83:  return 'B'
        if score >= 80:  return 'B-'
        if score >= 77:  return 'C+'
        if score >= 73:  return 'C'
        if score >= 70:  return 'C-'
        if score >= 60:  return 'D'
        return 'F'

    def save(self, *args, **kwargs):
        """
        Auto-compute letter_grade from score before saving.

        Overriding save() is the Django way to add pre-save logic.
        Only compute if score is set and grade isn't a special value (I, W).
        """
        if self.score is not None and self.letter_grade not in ('I', 'W'):
            self.letter_grade = self.compute_letter_grade(self.score)
        super().save(*args, **kwargs)

    @property
    def grade_points(self):
        """
        Convert letter grade to GPA grade points (4.0 scale).
        Used for calculating overall GPA.
        """
        scale = {
            'A+': 4.0, 'A': 4.0, 'A-': 3.7,
            'B+': 3.3, 'B': 3.0, 'B-': 2.7,
            'C+': 2.3, 'C': 2.0, 'C-': 1.7,
            'D': 1.0,  'F': 0.0,
        }
        return scale.get(self.letter_grade, None)
