# Lesson 01: Project Setup & Django Fundamentals

## Overview

This lesson covers setting up the Library Management API project from scratch
and explains the key Django concepts you need before diving into REST APIs.

---

## 1. Why Django for APIs?

Django is a "batteries included" web framework. It provides:
- ORM (Object-Relational Mapping) — write Python, get SQL
- Authentication system built-in
- Admin interface for free
- Migrations system for database schema changes

Django REST Framework (DRF) sits on top of Django and adds:
- Serializers — convert models to/from JSON
- ViewSets — organize API logic
- Routers — auto-generate URLs
- Authentication backends (JWT, Session, Token)
- Built-in browsable API for development

---

## 2. Project Setup Steps

### Step 1: Virtual Environment

Always use a virtual environment to isolate project dependencies:

```bash
python -m venv venv
venv\Scripts\activate      # Windows
source venv/bin/activate   # macOS/Linux
```

**Why?** Different projects may need different versions of the same package.
Virtual environments prevent conflicts.

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

Our key dependencies:
- `Django==4.2.7` — web framework
- `djangorestframework==3.14.0` — REST API toolkit
- `djangorestframework-simplejwt==5.3.0` — JWT authentication
- `drf-spectacular==0.26.5` — OpenAPI schema generation
- `django-filter==23.3` — advanced filtering
- `Pillow==10.1.0` — image handling (book covers, avatars)
- `python-dotenv==1.0.0` — load .env files

### Step 3: Environment Variables

Create a `.env` file from the example:

```bash
cp .env.example .env
```

Generate a secure SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

**Key Rule:** Never commit `.env` to version control. Add it to `.gitignore`.

### Step 4: Run Migrations

```bash
python manage.py migrate
```

Migrations are Django's way of tracking and applying database schema changes.
Every time you change a model, you create a migration file:

```bash
python manage.py makemigrations   # Create migration files from model changes
python manage.py migrate          # Apply migration files to the database
```

### Step 5: Create Admin User

```bash
python manage.py createsuperuser
```

Then set the role via the Django shell:
```python
python manage.py shell
>>> from apps.accounts.models import User
>>> u = User.objects.get(username='admin')
>>> u.role = 'admin'
>>> u.save()
```

### Step 6: Run the Server

```bash
python manage.py runserver
```

Visit:
- `http://localhost:8000/admin/` — Django admin
- `http://localhost:8000/api/docs/` — Swagger UI
- `http://localhost:8000/api/v1/books/` — Book list

---

## 3. Django Project vs App

**Project** = the whole thing (`library_api/`)
**App** = a self-contained module (`accounts`, `books`, `loans`)

```
library_api/              ← Project
├── library_api/          ← Project package (settings, urls, wsgi)
└── apps/
    ├── accounts/         ← App: user management
    ├── books/            ← App: book catalog
    └── loans/            ← App: lending system
```

Each app has:
- `models.py` — database table definitions
- `serializers.py` — JSON conversion + validation
- `views.py` — request handling logic
- `urls.py` — URL patterns for this app

---

## 4. The Request-Response Cycle

When a client sends `GET http://localhost:8000/api/v1/books/`:

1. Django's WSGI server receives the request
2. Middleware processes it (security checks, authentication setup)
3. `library_api/urls.py` matches the URL pattern
4. Routes to `apps/books/urls.py` via `include()`
5. Router matches `books/` → `BookViewSet.list()`
6. DRF checks authentication (JWT token)
7. DRF checks permissions (AllowAny for book list)
8. DRF applies throttling (rate limit check)
9. View calls `get_queryset()` → database query
10. Serializer converts queryset to Python dicts
11. DRF applies pagination
12. DRF renders response as JSON
13. Response returns through middleware
14. Client receives JSON

---

## 5. Custom User Model

**Critical rule: Define a custom User model BEFORE your first migration.**

We define it in `apps/accounts/models.py` and tell Django to use it:

```python
# settings.py
AUTH_USER_MODEL = 'accounts.User'
```

Our custom User extends `AbstractUser`:
```python
class User(AbstractUser):
    role = models.CharField(choices=Role.choices, ...)
    bio = models.TextField(blank=True)
    avatar = models.ImageField(...)
    date_of_birth = models.DateField(null=True, blank=True)
```

**Why extend AbstractUser?**
- You keep all Django's built-in fields: username, email, password, is_staff, etc.
- You just add your custom fields
- Much simpler than AbstractBaseUser (which requires implementing everything)

**Why not change it after migrations?**
- The User model is referenced by dozens of Django internal tables
- Changing it mid-project causes migration conflicts and data loss risks

---

## 6. Common Mistakes to Avoid

**Mistake 1: Forgetting to activate virtual environment**
```bash
# Wrong — installs globally, pollutes system Python
pip install django

# Right — activate first
venv\Scripts\activate
pip install django
```

**Mistake 2: Hardcoding SECRET_KEY**
```python
# Wrong — secret is in code, committed to git
SECRET_KEY = 'my-secret-key-123'

# Right — load from environment
SECRET_KEY = os.getenv('SECRET_KEY')
```

**Mistake 3: Running with DEBUG=True in production**
- DEBUG=True shows full stack traces to users — a security risk
- Set DEBUG=False in production

**Mistake 4: Not running migrations after model changes**
```bash
# After changing any model:
python manage.py makemigrations
python manage.py migrate
```

**Mistake 5: Forgetting AUTH_USER_MODEL before first migration**
- Once you have migrations referencing the User table, changing
  AUTH_USER_MODEL requires a fresh database

---

## Key Points to Remember

- Virtual environments isolate project dependencies
- `.env` files store secrets; never commit them to git
- `makemigrations` creates migration files; `migrate` applies them
- Custom User model must be defined before the first migration
- The request-response cycle goes: URL → View → Serializer → Database → JSON
