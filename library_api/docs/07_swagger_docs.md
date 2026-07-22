# Lesson 07: API Documentation with drf-spectacular

## Overview

`drf-spectacular` reads your Django REST Framework code and automatically
generates an OpenAPI 3.0 schema. That schema powers the interactive
Swagger UI and ReDoc documentation pages.

---

## 1. Why API Documentation Matters

- Frontend developers need to know what endpoints exist and what data to send
- Testers need to try requests without writing code
- Future-you needs to remember what an endpoint does
- Swagger UI lets anyone test the API interactively from a browser

---

## 2. Setup

### Install

```bash
pip install drf-spectacular
```

### Add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'drf_spectacular',
]
```

### Set as the schema class

```python
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

### Configure the schema

```python
SPECTACULAR_SETTINGS = {
    'TITLE': 'Library Management API',
    'DESCRIPTION': 'A library system REST API for teaching DRF concepts.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,     # Don't show the schema endpoint in itself
    'SWAGGER_UI_SETTINGS': {
        'persistAuthorization': True,  # Keep JWT token across page refreshes
    },
    'COMPONENT_SPLIT_REQUEST': True,   # Separate read/write schemas
}
```

### Add documentation URLs

```python
# library_api/urls.py
from drf_spectacular.views import (
    SpectacularAPIView,       # Raw OpenAPI schema (YAML/JSON)
    SpectacularSwaggerView,   # Interactive Swagger UI
    SpectacularRedocView,     # Clean alternative UI
)

urlpatterns = [
    ...
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]
```

Visit `http://localhost:8000/api/docs/` — your docs are live!

---

## 3. What Gets Auto-Generated

drf-spectacular inspects your ViewSets and serializers and generates:
- All endpoint URLs and HTTP methods
- Request body schemas (from serializers)
- Response schemas (from serializers)
- Authentication requirements
- Query parameters (from filter backends)

For most simple endpoints, **no annotation is needed** — it just works.

---

## 4. @extend_schema — Customizing Docs

When the auto-generation isn't detailed enough, use `@extend_schema`:

```python
from drf_spectacular.utils import extend_schema, OpenApiParameter

class UserRegistrationView(generics.CreateAPIView):

    @extend_schema(
        summary='Register a new user',
        description='Create a new user account. Returns the created user data.',
        tags=['Authentication'],
        # Explicitly define the response schema
        responses={
            201: UserProfileSerializer,
            400: {'description': 'Validation error'},
        },
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
```

### Documenting query parameters

```python
@extend_schema(
    parameters=[
        OpenApiParameter(
            name='search',
            description='Search by username or email',
            required=False,
            type=str,
            location=OpenApiParameter.QUERY,
        ),
        OpenApiParameter(
            name='role',
            description='Filter by role: admin, librarian, member',
            required=False,
            type=str,
            enum=['admin', 'librarian', 'member'],
        ),
    ]
)
def get(self, request, *args, **kwargs):
    ...
```

---

## 5. @extend_schema_view — Document All Actions at Once

```python
from drf_spectacular.utils import extend_schema_view

@extend_schema_view(
    list=extend_schema(
        summary='List all books',
        tags=['Books'],
    ),
    create=extend_schema(
        summary='Create a book',
        description='Only librarians and admins can create books.',
        tags=['Books'],
    ),
    retrieve=extend_schema(
        summary='Get book details',
        tags=['Books'],
    ),
    update=extend_schema(
        summary='Update a book (full)',
        tags=['Books'],
    ),
    partial_update=extend_schema(
        summary='Update a book (partial)',
        tags=['Books'],
    ),
    destroy=extend_schema(
        summary='Delete a book',
        tags=['Books'],
    ),
)
class BookViewSet(viewsets.ModelViewSet):
    ...
```

---

## 6. Tags — Organizing Endpoints

Tags group endpoints in the Swagger UI sidebar:

```python
@extend_schema(tags=['Authentication'])
class LoginView(APIView):
    ...

@extend_schema(tags=['Books'])
class BookViewSet(viewsets.ModelViewSet):
    ...
```

Without tags, all endpoints appear in a single flat list.
With tags, they're grouped by feature area.

---

## 7. OpenApiParameter — Documenting Query Params

```python
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes

OpenApiParameter(
    name='available',               # Query param name
    type=OpenApiTypes.BOOL,         # Data type
    location=OpenApiParameter.QUERY, # Where it is (QUERY, PATH, HEADER)
    description='Filter for available books only',
    required=False,                 # Is it required?
    default=None,                   # Default value
    enum=['true', 'false'],         # Allowed values (optional)
)
```

---

## 8. Using Swagger UI for Testing

### 1. Open Swagger UI
Visit `http://localhost:8000/api/docs/`

### 2. Authenticate
1. Click the **Authorize** button (lock icon, top right)
2. Enter: `Bearer <your_access_token>`
3. Click **Authorize**

Now all requests include the Authorization header automatically.

### 3. Test an Endpoint
1. Click on an endpoint (e.g., `GET /api/v1/books/`)
2. Click **Try it out**
3. Fill in any parameters
4. Click **Execute**
5. See the response below

### 4. Create Data via Swagger
1. Click `POST /api/v1/books/`
2. Click **Try it out**
3. Edit the request body JSON
4. Click **Execute**
5. Check the response

---

## 9. Exporting the OpenAPI Schema

```bash
# Export as YAML (default)
python manage.py spectacular --file schema.yaml

# Export as JSON
python manage.py spectacular --file schema.json --format json
```

Use the exported schema to:
- Import into Postman (avoids writing all requests manually)
- Generate client SDKs (TypeScript, Python, etc.)
- Share with frontend teams

---

## 10. Importing OpenAPI Schema into Postman

1. Open Postman
2. Click **Import** (top left)
3. Paste the schema URL: `http://localhost:8000/api/schema/`
   or upload the `schema.yaml` file
4. Postman creates a collection with all endpoints pre-filled

---

## 11. Hiding Endpoints from Documentation

```python
@extend_schema(exclude=True)
def internal_endpoint(self, request):
    """This endpoint won't appear in Swagger."""
    ...
```

Or exclude for specific actions:

```python
@extend_schema_view(
    destroy=extend_schema(exclude=True),  # Hide delete from public docs
)
class BookViewSet(viewsets.ModelViewSet):
    ...
```

---

## 12. Documenting Custom Response Schemas

When your response doesn't match a serializer exactly:

```python
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers

@extend_schema(
    responses={
        200: inline_serializer(
            name='AvailabilityResponse',
            fields={
                'id': serializers.IntegerField(),
                'title': serializers.CharField(),
                'is_available': serializers.BooleanField(),
                'available_copies': serializers.IntegerField(),
                'total_copies': serializers.IntegerField(),
            }
        )
    }
)
@action(detail=True, methods=['get'])
def availability(self, request, pk=None):
    book = self.get_object()
    return Response({
        'id': book.id,
        'title': book.title,
        'is_available': book.is_available,
        'available_copies': book.available_copies,
        'total_copies': book.total_copies,
    })
```

---

## 13. ReDoc vs Swagger UI

| | Swagger UI | ReDoc |
|---|---|---|
| Interactive testing | ✅ Yes | ❌ No |
| Clean readable layout | Decent | ✅ Better |
| Mobile-friendly | Limited | ✅ Better |
| Best for | Developers testing | API consumers reading |

Use Swagger for testing during development.
Use ReDoc for sharing docs with clients or teams.

---

## Key Points to Remember

- drf-spectacular auto-generates OpenAPI 3.0 docs from your serializers and views
- Visit `/api/docs/` for Swagger UI, `/api/redoc/` for ReDoc
- Use `@extend_schema` to add summaries, descriptions, and tags
- Use `@extend_schema_view` to annotate all ViewSet actions at once
- Use `OpenApiParameter` to document query parameters
- Export schema with `python manage.py spectacular --file schema.yaml`
- Import exported schema into Postman to auto-create all test requests
- `SWAGGER_UI_SETTINGS: persistAuthorization: True` keeps your JWT across page refreshes
