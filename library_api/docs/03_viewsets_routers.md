# Lesson 03: ViewSets & Routers

## Overview

ViewSets group all operations on a resource into one class.
Routers auto-generate all the URL patterns from that class.
Together they eliminate a huge amount of boilerplate code.

---

## 1. The Problem ViewSets Solve

Without ViewSets, you'd write a separate class for every operation:

```python
# The old way — very repetitive
class BookListView(APIView):
    def get(self, request):   # GET /books/
        ...
    def post(self, request):  # POST /books/
        ...

class BookDetailView(APIView):
    def get(self, request, pk):     # GET /books/{id}/
        ...
    def put(self, request, pk):     # PUT /books/{id}/
        ...
    def delete(self, request, pk):  # DELETE /books/{id}/
        ...
```

With ViewSets, one class handles everything:

```python
# The new way — one class, all operations
class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    # Done! list, create, retrieve, update, partial_update, destroy all work.
```

---

## 2. ViewSet Types — Least to Most Powerful

### ViewSet (bare minimum)

```python
from rest_framework import viewsets
from rest_framework.response import Response

class BookViewSet(viewsets.ViewSet):
    """No built-in actions. You implement everything."""
    def list(self, request):
        books = Book.objects.all()
        serializer = BookSerializer(books, many=True)
        return Response(serializer.data)
```

### GenericViewSet + Mixins (compose what you need)

```python
from rest_framework import viewsets, mixins

class BookViewSet(
    mixins.ListModelMixin,     # adds list()
    mixins.CreateModelMixin,   # adds create()
    mixins.RetrieveModelMixin, # adds retrieve()
    viewsets.GenericViewSet    # base class
):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    # Only list, create, retrieve — no update or delete
```

### ModelViewSet (everything included)

```python
from rest_framework import viewsets

class BookViewSet(viewsets.ModelViewSet):
    """Provides: list, create, retrieve, update, partial_update, destroy."""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
```

**Use ModelViewSet when:** You want full CRUD (or disable specific methods).
**Use mixins when:** You want fine-grained control over which operations exist.

---

## 3. The 6 Standard Actions

| Action | HTTP Method | URL | Description |
|--------|-------------|-----|-------------|
| `list` | GET | `/books/` | Return all objects |
| `create` | POST | `/books/` | Create a new object |
| `retrieve` | GET | `/books/{id}/` | Return one object |
| `update` | PUT | `/books/{id}/` | Full update |
| `partial_update` | PATCH | `/books/{id}/` | Partial update |
| `destroy` | DELETE | `/books/{id}/` | Delete object |

---

## 4. Routers — Auto-Generated URLs

```python
# books/urls.py
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book')
# r'books'  → URL prefix
# basename  → used for URL name reversal: reverse('books:book-list')

urlpatterns = [
    path('', include(router.urls)),
]
```

The router generates all these URLs automatically:

```
GET    /api/v1/books/          → BookViewSet.list()
POST   /api/v1/books/          → BookViewSet.create()
GET    /api/v1/books/{id}/     → BookViewSet.retrieve()
PUT    /api/v1/books/{id}/     → BookViewSet.update()
PATCH  /api/v1/books/{id}/     → BookViewSet.partial_update()
DELETE /api/v1/books/{id}/     → BookViewSet.destroy()
```

---

## 5. get_queryset() — Control What Data Is Returned

```python
class LoanViewSet(viewsets.ModelViewSet):

    def get_queryset(self):
        user = self.request.user

        # Data isolation: users see only their own loans
        if user.is_staff or user.is_admin:
            return Loan.objects.select_related('user', 'book').all()
        return Loan.objects.select_related('user', 'book').filter(user=user)
```

**Override get_queryset() when:**
- You need to filter by the current user
- You need query optimizations (select_related, prefetch_related)
- The result depends on query parameters

---

## 6. get_serializer_class() — Different Serializers Per Action

```python
class BookViewSet(viewsets.ModelViewSet):

    def get_serializer_class(self):
        if self.action == 'list':
            return BookListSerializer       # lightweight for many objects
        elif self.action in ['create', 'update', 'partial_update']:
            return BookCreateUpdateSerializer  # accepts IDs for writes
        else:
            return BookDetailSerializer     # full details for single object
```

**Why?** Different operations need different shapes of data:
- List: many items, show less data per item
- Create: accept IDs (not nested objects)
- Detail: one item, show everything

---

## 7. get_permissions() — Dynamic Permissions

```python
class BookViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]             # Reading: open to everyone
        return [IsLibrarianOrAdmin()]       # Writing: restricted

    # Alternative: use a dictionary approach
    permission_map = {
        'list': [AllowAny],
        'retrieve': [AllowAny],
        'create': [IsLibrarianOrAdmin],
        'update': [IsLibrarianOrAdmin],
        'destroy': [IsAdminUser],
    }

    def get_permissions(self):
        classes = self.permission_map.get(self.action, [IsAuthenticated])
        return [cls() for cls in classes]
```

---

## 8. perform_create() — Inject Data on Creation

```python
class LoanViewSet(viewsets.ModelViewSet):

    def perform_create(self, serializer):
        """
        Called by CreateModelMixin.create() after validation.
        Use it to inject data that shouldn't come from the client.
        """
        # Inject the current user automatically
        serializer.save(user=self.request.user)
```

Similarly:
- `perform_update(serializer)` — called before saving an update
- `perform_destroy(instance)` — called before deleting

---

## 9. Custom Actions with @action

The `@action` decorator adds new endpoints beyond the standard 6.

### detail=True — operates on a single object (needs {pk})

```python
@action(detail=True, methods=['post'], url_path='return')
def return_book(self, request, pk=None):
    """POST /api/v1/loans/{id}/return/"""
    loan = self.get_object()   # Fetches object by pk, handles 404
    loan.process_return()
    return Response(LoanSerializer(loan).data)
```

### detail=False — operates on the collection (no {pk})

```python
@action(detail=False, methods=['get'], url_path='my-loans')
def my_loans(self, request):
    """GET /api/v1/loans/my-loans/"""
    loans = Loan.objects.filter(user=request.user)
    serializer = LoanSerializer(loans, many=True)
    return Response(serializer.data)
```

### Custom action with multiple methods

```python
@action(detail=True, methods=['get', 'post'], url_path='availability')
def availability(self, request, pk=None):
    book = self.get_object()
    if request.method == 'GET':
        return Response({'available': book.is_available})
    # POST logic here
```

---

## 10. Generic Views (Alternative to ViewSets)

When you only need one or two operations, generic views are simpler:

```python
from rest_framework import generics

# GET only
class BookListView(generics.ListAPIView):
    queryset = Book.objects.all()
    serializer_class = BookListSerializer

# POST only
class BookCreateView(generics.CreateAPIView):
    serializer_class = BookCreateUpdateSerializer

# GET + PUT + PATCH
class BookDetailView(generics.RetrieveUpdateAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer

# GET + DELETE
class BookDeleteView(generics.RetrieveDestroyAPIView):
    queryset = Book.objects.all()
    serializer_class = BookSerializer
```

| Class | Methods |
|-------|---------|
| `ListAPIView` | GET (list) |
| `CreateAPIView` | POST |
| `RetrieveAPIView` | GET (single) |
| `UpdateAPIView` | PUT, PATCH |
| `DestroyAPIView` | DELETE |
| `ListCreateAPIView` | GET (list), POST |
| `RetrieveUpdateAPIView` | GET, PUT, PATCH |
| `RetrieveDestroyAPIView` | GET, DELETE |
| `RetrieveUpdateDestroyAPIView` | GET, PUT, PATCH, DELETE |

**Use generic views when:** You have simple non-CRUD views (like profile, change-password).
**Use ViewSets when:** You're building a full resource with CRUD operations.

---

## 11. Disabling Specific HTTP Methods

```python
class LoanViewSet(viewsets.ModelViewSet):
    # Disable PUT and PATCH — use the return_book action instead
    http_method_names = ['get', 'post', 'delete', 'head', 'options']
```

---

## 12. URL Namespacing

```python
# books/urls.py
app_name = 'books'
router = DefaultRouter()
router.register(r'books', views.BookViewSet, basename='book')

# Reversing URLs in code:
from django.urls import reverse
reverse('books:book-list')      # → '/api/v1/books/'
reverse('books:book-detail', kwargs={'pk': 1})  # → '/api/v1/books/1/'
```

---

## 13. The self.action Attribute

Inside any ViewSet method, `self.action` tells you which action is running:

```python
# Values: 'list', 'create', 'retrieve', 'update', 'partial_update',
#          'destroy', or the name of any custom @action method
def get_serializer_class(self):
    print(self.action)   # → 'list', 'create', etc.
```

---

## Key Points to Remember

- `ModelViewSet` gives you all 6 CRUD actions with 2 lines of code
- `DefaultRouter` auto-generates all URL patterns from `register()` calls
- `get_queryset()` scopes data (filter by user, add select_related)
- `get_serializer_class()` returns the right serializer per action
- `get_permissions()` returns the right permissions per action
- `@action(detail=True)` for single-object custom endpoints
- `@action(detail=False)` for collection custom endpoints
- Generic views are simpler when you don't need full CRUD
