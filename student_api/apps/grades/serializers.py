"""
Grades Serializers — Student Management API
=============================================

Patterns covered:
- read_only computed fields (letter_grade, grade_points)
- Teacher is set from request.user (via HiddenField)
- validate() that checks the student is enrolled in the course
- Multiple serializers: List (minimal), Detail (nested), Create/Update
"""

from rest_framework import serializers
from apps.students.serializers import StudentProfileListSerializer
from apps.courses.serializers import CourseListSerializer
from .models import Grade


class GradeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for grade list view."""
    student_id    = serializers.CharField(source='student.student_id', read_only=True)
    student_name  = serializers.CharField(source='student.full_name', read_only=True)
    course_code   = serializers.CharField(source='course.course_code', read_only=True)
    course_title  = serializers.CharField(source='course.title', read_only=True)
    grade_points  = serializers.FloatField(read_only=True)  # from @property

    class Meta:
        model = Grade
        fields = [
            'id', 'student_id', 'student_name',
            'course_code', 'course_title',
            'score', 'letter_grade', 'grade_points',
            'graded_at',
        ]


class GradeDetailSerializer(serializers.ModelSerializer):
    """Full grade detail with nested student and course objects."""
    student      = StudentProfileListSerializer(read_only=True)
    course       = CourseListSerializer(read_only=True)
    teacher_name = serializers.SerializerMethodField()
    grade_points = serializers.FloatField(read_only=True)

    class Meta:
        model = Grade
        fields = [
            'id', 'student', 'course', 'teacher_name',
            'score', 'letter_grade', 'grade_points',
            'remarks', 'graded_at', 'updated_at',
        ]

    def get_teacher_name(self, obj):
        if not obj.teacher:
            return None
        return obj.teacher.get_full_name() or obj.teacher.username


class GradeCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating a grade record.

    Key design:
    - teacher is auto-set to request.user (HiddenField + CurrentUserDefault)
    - letter_grade is read_only — auto-computed from score in model.save()
    - validate() checks the student is actually enrolled in the course
    """
    teacher = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )

    class Meta:
        model = Grade
        fields = ['id', 'student', 'course', 'teacher', 'score', 'letter_grade', 'remarks']
        read_only_fields = ['id', 'letter_grade']

    def validate(self, attrs):
        """
        Ensure the student is enrolled (and active) in the course before grading.
        A teacher shouldn't be able to enter a grade for a student not in their course.
        """
        from apps.courses.models import Enrollment
        student = attrs['student']
        course = attrs['course']

        is_enrolled = Enrollment.objects.filter(
            student=student,
            course=course,
            status=Enrollment.Status.ENROLLED,
        ).exists()

        if not is_enrolled:
            raise serializers.ValidationError(
                f'Student "{student.student_id}" is not enrolled in '
                f'course "{course.course_code}".'
            )

        # Prevent duplicate grade records (unique_together enforces this in DB too,
        # but raising it here gives a cleaner error message)
        if self.instance is None:  # Only on create, not update
            if Grade.objects.filter(student=student, course=course).exists():
                raise serializers.ValidationError(
                    f'A grade record already exists for student "{student.student_id}" '
                    f'in course "{course.course_code}". Use PATCH to update it.'
                )
        return attrs


class GradeUpdateSerializer(serializers.ModelSerializer):
    """
    For updating an existing grade (score and remarks only).
    letter_grade is auto-recomputed by the model's save() method.
    """

    class Meta:
        model = Grade
        fields = ['score', 'letter_grade', 'remarks']
        read_only_fields = ['letter_grade']


class StudentTranscriptSerializer(serializers.Serializer):
    """
    Non-model serializer for the transcript endpoint.
    Returns a summary of a student's academic record.
    """
    student_id  = serializers.CharField()
    full_name   = serializers.CharField()
    department  = serializers.CharField()
    total_courses = serializers.IntegerField()
    gpa         = serializers.FloatField()
    grades      = GradeListSerializer(many=True)
