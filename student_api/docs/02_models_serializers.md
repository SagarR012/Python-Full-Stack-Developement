# Lesson 2 — Models & Serializers

## Models: The Database Layer

Models define the shape of your database tables. Each class = one table.

### Custom User Model (apps/accounts/models.py)

```python
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN   = 'admin',   'Admin'
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER
```

**Why extend AbstractUser?**
- AbstractUser already has username, password, email, first_name, last_name
- You add only what you need (role, phone_number, bio)
- You DON'T rewrite authentication from scratch

**Why TextChoices?**
```python
# Without TextChoices — magic strings, easy to make typos
role = 'teacherrr'  # Bug! No error raised

# With TextChoices — IDE autocomplete + validation
role = User.Role.TEACHER  # Always correct
```

**Why @property for role checks?**
```python
# Without property — verbose and tied to implementation detail
if user.role == 'teacher':  ...

# With property — readable, and you can change the implementation later
if user.is_teacher:  ...
```

> In settings.py: `AUTH_USER_MODEL = 'accounts.User'`
> This MUST be set before the first migration. It tells Django to use your
> custom User model everywhere.

---

### ForeignKey vs OneToOneField

```python
# ForeignKey: ONE department → MANY students
department = models.ForeignKey(
    Department,
    on_delete=models.SET_NULL,  # If dept deleted, set this field to NULL
    null=True,
    related_name='students',    # dept.students.all() — reverse access
)

# OneToOneField: ONE user → ONE student profile (not many)
user = models.OneToOneField(
    User,
    on_delete=models.CASCADE,   # If user deleted, delete the profile too
    related_name='student_profile',
)
```

**on_delete options:**
| Option | Meaning |
|--------|---------|
| `CASCADE` | Delete child records when parent is deleted |
| `SET_NULL` | Set FK to NULL when parent is deleted (requires `null=True`) |
| `PROTECT` | Raise an error — prevent parent deletion |

**Rule of thumb:**
- Use CASCADE for tightly coupled data (profile belongs to user — no user, no profile)
- Use SET_NULL for loosely coupled data (student can exist without a department)

---

### Model with Business Logic (apps/grades/models.py)

```python
class Grade(models.Model):
    score = models.DecimalField(max_digits=5, decimal_places=2)
    letter_grade = models.CharField(max_length=2, blank=True)

    def save(self, *args, **kwargs):
        """Auto-compute letter_grade from score before saving."""
        if self.score is not None and self.letter_grade not in ('I', 'W'):
            self.letter_grade = self.compute_letter_grade(self.score)
        super().save(*args, **kwargs)  # Always call super()!

    @staticmethod
    def compute_letter_grade(score):
        score = float(score)
        if score >= 97: return 'A+'
        if score >= 93: return 'A'
        # ...
        return 'F'
```

**Fat Model, Skinny View principle:**
- Put business logic in the model (where data lives), not the view
- `Grade.save()` auto-computes letter grade — the view doesn't need to know how
- `Enrollment.drop_course()` sets status to 'dropped' — one place to change

---

## Serializers: The Conversion Layer

Serializers do two things:
1. **Serialize**: Python object → JSON (for API responses)
2. **Deserialize**: JSON → Python (for API requests + validation)

### Multiple Serializers Per Model

This project uses 3 serializers per model (a common pattern):

```python
# apps/students/serializers.py

# 1. List — lightweight, for showing many records
class StudentProfileListSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(read_only=True)  # from @property

    class Meta:
        model = StudentProfile
        fields = ['id', 'student_id', 'full_name', 'department_name', 'year_level']

# 2. Detail — full data, for showing one record
class StudentProfileDetailSerializer(serializers.ModelSerializer):
    department = DepartmentMinimalSerializer(read_only=True)  # nested object
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = StudentProfile
        fields = ['id', 'student_id', 'email', 'department', ...]

# 3. Create/Update — for write operations (accepts IDs, not nested objects)
class StudentProfileCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = ['id', 'user', 'student_id', 'department', ...]  # FKs as IDs
```

**Why separate list vs detail?**
- List returns 50 students — you don't want 50 deeply nested objects
- Detail returns 1 student — nested objects are fine and useful

**Why separate read vs write?**
- Read serializers use nested objects for rich output
- Write serializers use FK IDs (easier for API clients to send)

---

### source= Parameter

```python
# Read a field from a related object
department_name = serializers.CharField(source='department.name', read_only=True)
# This calls: student.department.name

email = serializers.EmailField(source='user.email', read_only=True)
# This traverses the OneToOneField: student.user.email
```

---

### SerializerMethodField

When you need computed data that doesn't map directly to a model field:

```python
class CourseListSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()

    def get_teacher_name(self, obj):
        # 'obj' is the Course instance
        if not obj.teacher:
            return None
        return obj.teacher.get_full_name() or obj.teacher.username
```

The method name must be `get_<field_name>`.

---

### Serializer Validation

```python
class StudentProfileCreateUpdateSerializer(serializers.ModelSerializer):

    def validate_user(self, user):
        """Single-field validation: runs for the 'user' field."""
        if not user.is_student:
            raise serializers.ValidationError(
                f'User "{user.username}" is not a student.'
            )
        return user  # Always return the value

    def validate(self, attrs):
        """Cross-field validation: runs after all individual fields pass."""
        start = attrs.get('start_date')
        end = attrs.get('end_date')
        if start and end and start > end:
            raise serializers.ValidationError(
                {'end_date': 'end_date must be after start_date.'}
            )
        return attrs  # Always return attrs
```

**Validation order:**
1. Field-level type checking (is it an integer? a date?)
2. `validate_<field>()` for each field
3. `validate()` for cross-field checks

---

### HiddenField — Auto-set from Request

```python
# apps/grades/serializers.py
class GradeCreateSerializer(serializers.ModelSerializer):
    teacher = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
    # teacher is NOT in the request JSON — set automatically from request.user
    # The client never sends it, so they can't fake it
```

---

## Try It

Open Swagger at http://127.0.0.1:8000/api/docs/ and look at the request/response
schemas for `POST /api/v1/grades/`. Notice:
- `teacher` is not in the request body (HiddenField)
- `letter_grade` is read-only (computed by the model)

---

## Key Takeaways

1. `AbstractUser` lets you add fields to Django's User model without rewriting auth
2. `@property` on models makes permission checks and views more readable
3. `on_delete=CASCADE` vs `SET_NULL` controls what happens when a parent is deleted
4. Use 3 serializers per model: List (lightweight), Detail (nested), Write (IDs)
5. `source=` traverses FK/OneToOne relationships
6. `validate_<field>` for single-field validation, `validate()` for cross-field
7. `HiddenField` auto-sets values from the request context (like current user)
