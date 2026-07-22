# Lesson 02: Models & Serializers

## Overview

Models define your database structure. Serializers convert between
Python objects and JSON (and handle validation). Together, they form
the data layer of your API.

---

## 1. Django Models — Database Tables in Python

A Django model is a Python class that maps to a database table.
Each attribute is a column.

```python
from django.db import models

class Author(models.Model):
    name       = models.CharField(max_length=200)     # VARCHAR(200)
    bio        = models.TextField(blank=True)          # TEXT
    birth_date = models.DateField(null=True, blank=True)  # DATE

    def __str__(self):
        return self.name
```

After writing this, run:
```bash
python manage.py makemigrations   # creates migration file
python manage.py migrate          # applies it to the database
```

---

## 2. Field Types — The Important Ones

| Field | SQL Type | Notes |
|-------|----------|-------|
| `CharField(max_length=N)` | VARCHAR(N) | Short strings, max_length required |
| `TextField()` | TEXT | Long text, no limit |
| `IntegerField()` | INTEGER | Whole numbers |
| `PositiveIntegerField()` | INTEGER | Only 0 and above |
| `FloatField()` | REAL | Decimal numbers |
| `BooleanField()` | BOOLEAN | True / False |
| `DateField()` | DATE | Date only (2024-01-15) |
| `DateTimeField()` | DATETIME | Date + time |
| `EmailField()` | VARCHAR | Validates email format |
| `SlugField()` | VARCHAR | URL-safe strings |
| `ImageField()` | VARCHAR | Stores file path, needs Pillow |
| `ForeignKey()` | INTEGER (FK) | Many-to-one relationship |

### Key field options

```python
name = models.CharField(
    max_length=200,
    blank=True,      # Allows empty string in forms/serializers
    null=True,       # Allows NULL in the database
    default='',      # Default value
    unique=True,     # Unique constraint in DB
    help_text='...'  # Appears in admin and Swagger docs
)
```

**Rule of thumb:**
- `null=True` on string fields is usually wrong — use `default=''` instead
- `null=True` is correct for `DateField`, `ForeignKey`, etc.
- `blank=True` means "not required in form/serializer validation"

---

## 3. Relationships

### ForeignKey (Many-to-One)

```python
class Book(models.Model):
    # Many books → one author
    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE,     # Delete books if author is deleted
        related_name='books',         # Lets you do: author.books.all()
    )
```

**on_delete options:**
- `CASCADE` — delete related objects too
- `SET_NULL` — set FK to NULL (requires `null=True`)
- `PROTECT` — raise error, prevent deletion
- `DO_NOTHING` — do nothing (dangerous, use carefully)

### ManyToManyField

```python
class Book(models.Model):
    # A book can have many tags; a tag can be on many books
    tags = models.ManyToManyField('Tag', blank=True)
```

### Reverse Relations

```python
author = Author.objects.get(id=1)
author.books.all()       # All books by this author (via related_name)
author.books.count()     # Count without loading all
author.books.filter(available_copies__gt=0)  # Available books
```

---

## 4. Model Methods and Properties

```python
class Book(models.Model):
    available_copies = models.PositiveIntegerField(default=1)
    total_copies     = models.PositiveIntegerField(default=1)

    @property
    def is_available(self):
        """Properties are computed, not stored in DB."""
        return self.available_copies > 0

    def borrow(self):
        """Business logic lives in the model (Fat Model, Skinny View)."""
        if self.available_copies <= 0:
            raise ValueError('No available copies')
        self.available_copies -= 1
        # update_fields is efficient: only UPDATE that one column
        self.save(update_fields=['available_copies'])

    def __str__(self):
        # Defines how the object appears in admin and debug output
        return f'{self.title} by {self.author.name}'
```

---

## 5. The TextChoices Pattern

```python
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN     = 'admin',     'Admin'
        LIBRARIAN = 'librarian', 'Librarian'
        MEMBER    = 'member',    'Member'
        #           ↑ DB value    ↑ Human label

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
    )
```

- `user.role` → `'member'` (the database value)
- `user.get_role_display()` → `'Member'` (the human label)
- `User.Role.ADMIN` → `'admin'`

---

## 6. Meta Class

```python
class Book(models.Model):
    title = models.CharField(max_length=300)

    class Meta:
        ordering = ['-created_at']    # Default sort: newest first
        verbose_name = 'Book'
        verbose_name_plural = 'Books'
        # unique_together = [['author', 'isbn']]  # Composite unique constraint
```

---

## 7. Serializers — The Bridge Between Python and JSON

A serializer converts:
- **Python objects → JSON** (serialization): when returning data
- **JSON → Python objects** (deserialization): when receiving data + validating

### ModelSerializer (most common)

```python
from rest_framework import serializers
from .models import Author

class AuthorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Author
        fields = ['id', 'name', 'bio', 'birth_date']
        read_only_fields = ['id']
```

This auto-generates fields from the model. Equivalent to writing all the
field declarations manually, but much shorter.

### Using a Serializer

```python
# Serializing (Python → JSON dict)
author = Author.objects.get(id=1)
serializer = AuthorSerializer(author)
serializer.data   # → {'id': 1, 'name': 'J.R.R. Tolkien', ...}

# Deserializing + validation (JSON → Python, with validation)
serializer = AuthorSerializer(data={'name': 'Tolkien', 'bio': '...'})
serializer.is_valid()   # → True or False
serializer.errors       # → validation error details
serializer.save()       # → calls create() or update()

# Serializing many objects
authors = Author.objects.all()
serializer = AuthorSerializer(authors, many=True)
serializer.data   # → [{'id': 1, ...}, {'id': 2, ...}, ...]
```

---

## 8. Field-Level Validation

```python
class AuthorSerializer(serializers.ModelSerializer):

    def validate_name(self, value):
        """Called automatically for the 'name' field."""
        if len(value) < 2:
            raise serializers.ValidationError('Name must be at least 2 characters.')
        return value.strip()   # Return the (possibly cleaned) value
```

Pattern: `validate_<fieldname>(self, value)` — DRF calls this automatically.

---

## 9. Object-Level Validation

```python
class BookSerializer(serializers.ModelSerializer):

    def validate(self, attrs):
        """Cross-field validation — called after field-level validation."""
        available = attrs.get('available_copies')
        total = attrs.get('total_copies')

        if available is not None and total is not None:
            if available > total:
                raise serializers.ValidationError(
                    'available_copies cannot exceed total_copies.'
                )
        return attrs
```

---

## 10. Custom Fields

### SerializerMethodField — computed/read-only values

```python
class AuthorSerializer(serializers.ModelSerializer):
    book_count = serializers.SerializerMethodField()

    class Meta:
        model = Author
        fields = ['id', 'name', 'book_count']

    def get_book_count(self, obj):
        """get_<field_name> — DRF calls this automatically."""
        return obj.books.count()
```

### source= — map to a different field or traversal

```python
class LoanSerializer(serializers.ModelSerializer):
    # Read username from related User object
    username = serializers.CharField(source='user.username', read_only=True)
```

### write_only — accepted in input, never returned in output

```python
password = serializers.CharField(write_only=True)
```

### read_only — returned in output, not accepted in input

```python
created_at = serializers.DateTimeField(read_only=True)
```

---

## 11. Nested Serializers

```python
class BookListSerializer(serializers.ModelSerializer):
    # Embed the full Author object in the response
    author = AuthorSerializer(read_only=True)
    category = CategorySerializer(read_only=True)

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'category', 'isbn']
```

**Result:**
```json
{
  "id": 1,
  "title": "The Hobbit",
  "author": {
    "id": 3,
    "name": "J.R.R. Tolkien",
    "book_count": 5
  },
  "category": {
    "id": 2,
    "name": "Fantasy",
    "slug": "fantasy"
  }
}
```

**Tradeoff:** More data per response, but the client doesn't need to make extra requests for author/category details.

---

## 12. Multiple Serializers Per Model

A single model often needs different serializers for different purposes:

| Serializer | Used For | Why Different |
|------------|----------|---------------|
| `BookListSerializer` | GET /books/ | Nested author/category for readability |
| `BookDetailSerializer` | GET /books/{id}/ | All fields including description |
| `BookCreateUpdateSerializer` | POST/PUT/PATCH | Accepts IDs, not nested objects |
| `UserRegistrationSerializer` | POST /register/ | Includes password confirmation |
| `UserProfileSerializer` | GET/PATCH /profile/ | Excludes sensitive fields |

---

## 13. The create() and update() Hooks

```python
class UserRegistrationSerializer(serializers.ModelSerializer):

    def create(self, validated_data):
        """
        Called when serializer.save() is called with no instance.
        Override to customize how objects are created.
        """
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)   # Hash the password!
        user.save()
        return user

    def update(self, instance, validated_data):
        """
        Called when serializer.save() is called with an instance.
        Override to customize how objects are updated.
        """
        instance.name = validated_data.get('name', instance.name)
        instance.save()
        return instance
```

---

## 14. HiddenField — Auto-Set Fields

```python
class LoanCreateSerializer(serializers.ModelSerializer):
    # Auto-set to the currently authenticated user
    # Not visible in API schema, not accepted from client
    user = serializers.HiddenField(
        default=serializers.CurrentUserDefault()
    )
```

This is the DRF-recommended way to set "who created this" without
trusting the client to send the correct user ID.

---

## 15. N+1 Query Problem

**The Problem:**
```python
# 1 query to get 100 authors...
authors = Author.objects.all()

for author in authors:
    # ...then 100 queries for books (one per author) = 101 total!
    print(author.books.count())
```

**The Fix — prefetch_related for reverse FK/M2M:**
```python
# 2 queries total, regardless of author count
authors = Author.objects.prefetch_related('books').all()
```

**The Fix — select_related for FK/O2O:**
```python
# 1 query using SQL JOIN
books = Book.objects.select_related('author', 'category').all()
```

| Method | Use For | How |
|--------|---------|-----|
| `select_related` | ForeignKey, OneToOneField | SQL JOIN (1 query) |
| `prefetch_related` | ManyToMany, reverse FK | 2 queries, Python join |

Always add these in `get_queryset()` on your ViewSets.

---

## Key Points to Remember

- Models = Python classes → database tables
- `makemigrations` + `migrate` after every model change
- Use `null=True` for optional FK/Date fields; use `default=''` for optional text
- Serializers validate input AND format output
- `validate_<field>` for single field, `validate()` for cross-field
- `write_only=True` on passwords, `read_only=True` on computed fields
- Use multiple serializers per model for different operations
- Fix N+1 queries with `select_related` and `prefetch_related`
