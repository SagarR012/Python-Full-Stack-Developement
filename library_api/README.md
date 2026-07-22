# Library Management API

A **complete teaching project** built with Django REST Framework that demonstrates
professional API development patterns from authentication to documentation.

---

## Learning Objectives

By working through this project, you will understand:

1. **REST API design** — conventions, URL structure, HTTP methods, status codes
2. **Django REST Framework** — serializers, views, viewsets, routers
3. **JWT Authentication** — access/refresh tokens, rotation, blacklisting
4. **Permissions & Security** — custom permission classes, role-based access control
5. **Throttling & Rate Limiting** — protecting your API from abuse
6. **Pagination & Filtering** — handling large datasets efficiently
7. **API Documentation** — automatic Swagger/ReDoc with drf-spectacular
8. **Testing with Postman** — writing tests, managing environments, pre-request scripts

---

## Project Overview

The Library Management API allows:
- Members to browse the book catalog and borrow books
- Librarians to manage the book catalog
- Admins to manage users and have full access

**Three main resources:**
- `accounts` — User registration, JWT auth, profile management
- `books` — Authors, Categories, and the Book catalog
- `loans` — Book borrowing and return tracking

---

## Setup Instructions

### 1. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python -m venv venv
source venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

```bash
# Copy the example file
cp .env.example .env

# Edit .env and set a real SECRET_KEY
# Generate one: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 4. Run database migrations

```bash
python manage.py migrate
```

This creates:
- All Django built-in tables
- Token blacklist table (for JWT logout)
- Your custom User, Author, Category, Book, and Loan tables

### 5. Create a superuser (admin account)

```bash
python manage.py createsuperuser
```

This creates an account with `is_staff=True` and `is_superuser=True`.
**Note:** Set the `role` field to `admin` via the Django admin panel or shell.

```bash
# Set role via Django shell
python manage.py shell
>>> from apps.accounts.models import User
>>> user = User.objects.get(username='your_superuser')
>>> user.role = 'admin'
>>> user.save()
```

### 6. Start the development server

```bash
python manage.py runserver
```

The API is now available at `http://localhost:8000`

---

## API Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|--------------|
| POST | `/api/v1/auth/register/` | Register new user | No |
| POST | `/api/v1/auth/login/` | Login, get JWT tokens | No |
| POST | `/api/v1/auth/refresh/` | Refresh access token | No |
| POST | `/api/v1/auth/logout/` | Blacklist refresh token | Yes |
| GET/PUT/PATCH | `/api/v1/auth/profile/` | View/update own profile | Yes |
| POST | `/api/v1/auth/change-password/` | Change password | Yes |
| GET | `/api/v1/auth/users/` | List all users | Admin only |
| GET | `/api/v1/authors/` | List all authors | No |
| POST | `/api/v1/authors/` | Create author | Librarian/Admin |
| GET | `/api/v1/authors/{id}/` | Author detail | No |
| PUT/PATCH | `/api/v1/authors/{id}/` | Update author | Librarian/Admin |
| DELETE | `/api/v1/authors/{id}/` | Delete author | Librarian/Admin |
| GET | `/api/v1/categories/` | List categories | No |
| POST | `/api/v1/categories/` | Create category | Librarian/Admin |
| GET | `/api/v1/books/` | List books (filterable) | No |
| POST | `/api/v1/books/` | Create book | Librarian/Admin |
| GET | `/api/v1/books/{id}/` | Book detail | No |
| PUT/PATCH | `/api/v1/books/{id}/` | Update book | Librarian/Admin |
| DELETE | `/api/v1/books/{id}/` | Delete book | Librarian/Admin |
| GET | `/api/v1/books/{id}/availability/` | Check availability | No |
| GET | `/api/v1/loans/` | List loans (own or all) | Yes |
| POST | `/api/v1/loans/` | Borrow a book | Yes |
| GET | `/api/v1/loans/{id}/` | Loan detail | Yes |
| POST | `/api/v1/loans/{id}/return/` | Return a book | Yes |
| GET | `/api/v1/loans/my-loans/` | Current user's loans | Yes |
| GET | `/api/docs/` | Swagger UI | No |
| GET | `/api/redoc/` | ReDoc UI | No |
| GET | `/api/schema/` | Raw OpenAPI schema | No |

---

## Key Filtering Options for `/api/v1/books/`

```
?search=tolkien          # Full-text search
?category=1              # Filter by category ID
?category_slug=fiction   # Filter by category slug
?author=2                # Filter by author ID
?available=true          # Only available books
?min_copies=2            # At least 2 copies available
?published_after=2020-01-01
?published_before=2023-12-31
?ordering=-published_date  # Sort descending by date
?page=2                  # Page 2 of results
```

---

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Django secret key — **CHANGE IN PRODUCTION** | Dev key |
| `DEBUG` | Enable debug mode | `True` |
| `ALLOWED_HOSTS` | Comma-separated allowed hostnames | `localhost,127.0.0.1` |

---

## Key Concepts Summary

### JWT Flow
```
Client → POST /auth/login/ with credentials
Server → Returns {access: "...", refresh: "..."}

Client → GET /api/resource/ with header: Authorization: Bearer <access>
Server → Verifies token, returns data

# When access token expires (15 min):
Client → POST /auth/refresh/ with {refresh: "..."}
Server → Returns new {access: "...", refresh: "..."} (rotation)

# On logout:
Client → POST /auth/logout/ with {refresh: "..."}
Server → Blacklists refresh token
```

### Permission Levels
- **AllowAny** — No authentication required (book list, register)
- **IsAuthenticated** — Valid JWT required (loans, profile)
- **IsLibrarianOrAdmin** — Role must be librarian or admin (book management)
- **IsAdminUser** — Role must be admin (user list)
- **IsOwnerOrAdmin** — Must be the record owner or admin

---

## Documentation

| File | Topic |
|------|-------|
| `docs/01_setup.md` | Project setup and Django fundamentals |
| `docs/02_models_serializers.md` | Models and serializers deep dive |
| `docs/03_viewsets_routers.md` | ViewSets, Routers, and generic views |
| `docs/04_jwt_auth.md` | JWT authentication with simplejwt |
| `docs/05_permissions_throttling.md` | Permissions and rate limiting |
| `docs/06_pagination_filtering.md` | Pagination, filtering, and search |
| `docs/07_swagger_docs.md` | API documentation with drf-spectacular |
| `docs/08_postman_testing.md` | Testing APIs with Postman |

---

## Project Structure

```
library_api/
├── manage.py               # Django CLI entry point
├── requirements.txt        # Python dependencies
├── .env.example            # Environment variable template
├── library_api/            # Django project package
│   ├── settings.py         # All project configuration
│   └── urls.py             # Root URL dispatcher
├── apps/
│   ├── accounts/           # User management + JWT auth
│   ├── books/              # Book catalog (Author, Category, Book)
│   └── loans/              # Book lending system
├── postman/
│   └── Library_API.postman_collection.json
└── docs/
    └── *.md                # Lesson files for each concept
```
