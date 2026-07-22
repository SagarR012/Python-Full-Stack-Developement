# Lesson 1 — Django REST Framework & API Design Principles

## What is Django REST Framework?

Django REST Framework (DRF) is a toolkit built on top of Django that makes it
easy to build Web APIs. It gives you:

- **Serializers** — convert Python objects ↔ JSON
- **Views / ViewSets** — handle HTTP requests
- **Routers** — auto-generate URL patterns
- **Authentication** — JWT, Session, Basic
- **Permissions** — control who can do what
- **Pagination, Filtering, Throttling** — production-ready out of the box

---

## REST Conventions

REST (Representational State Transfer) uses HTTP methods to represent actions:

| HTTP Method | Action       | Example URL              | What it does                |
|-------------|-------------|--------------------------|----------------------------|
| GET         | Read         | `/api/v1/students/`      | List all students           |
| GET         | Read         | `/api/v1/students/5/`    | Get student with id=5       |
| POST        | Create       | `/api/v1/students/`      | Create a new student        |
| PUT         | Full Update  | `/api/v1/students/5/`    | Replace all student fields  |
| PATCH       | Partial Update| `/api/v1/students/5/`   | Update only some fields     |
| DELETE      | Delete       | `/api/v1/students/5/`    | Delete student with id=5    |

### URL Versioning

Notice `/api/v1/` in every URL. This is **API versioning**:

```python
# student_api/urls.py
path('api/v1/', include('apps.students.urls', namespace='students')),
path('api/v1/', include('apps.courses.urls', namespace='courses')),
path('api/v1/', include('apps.grades.urls', namespace='grades')),
```

If you need to make breaking changes later, you add `/api/v2/` without
removing v1. Existing clients keep working.

---

## Project Structure

```
student_api/
├── student_api/         ← Django project (settings, root URLs)
│   ├── settings.py
│   └── urls.py
└── apps/                ← Django applications (feature modules)
    ├── accounts/        ← Users + Authentication
    ├── students/        ← StudentProfile, TeacherProfile, Department
    ├── courses/         ← Course, Enrollment
    └── grades/          ← Grade records
```

Each `app/` folder follows the same structure:
```
app_name/
├── models.py       ← Database tables
├── serializers.py  ← JSON ↔ Python conversion
├── views.py        ← Request handling logic
├── urls.py         ← URL routing
├── filters.py      ← Query parameter filtering
└── permissions.py  ← (accounts only) Who can do what
```

---

## DRF Settings (settings.py)

```python
# student_api/settings.py

REST_FRAMEWORK = {
    # Who is making this request?
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],

    # Are they allowed to do this?
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],

    # Auto-generate OpenAPI/Swagger schema
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',

    # Return 10 items per page
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 10,

    # Filtering backends enabled for all views
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',  # ?department=1
        'rest_framework.filters.SearchFilter',                # ?search=alice
        'rest_framework.filters.OrderingFilter',              # ?ordering=-score
    ],

    # Rate limiting
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day',
    },
}
```

---

## Try it Now

The server is running at **http://127.0.0.1:8000/**

Open these URLs in your browser:
- http://127.0.0.1:8000/api/docs/ — Swagger UI (interactive docs)
- http://127.0.0.1:8000/api/redoc/ — ReDoc (readable docs)
- http://127.0.0.1:8000/admin/ — Django Admin

---

## Key Takeaways

1. REST uses HTTP methods (GET/POST/PUT/PATCH/DELETE) to represent CRUD operations
2. URL versioning (`/api/v1/`) lets you evolve an API without breaking clients
3. DRF settings configure auth, permissions, pagination, and filtering globally
4. Each Django app handles one domain (students, courses, grades)
