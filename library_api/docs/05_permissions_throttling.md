# Lesson 05: Permissions & Throttling

## Overview

Permissions control WHO can access your API.
Throttling controls HOW OFTEN they can access it.
Both are critical for building secure, production-ready APIs.

---

## 1. How Permissions Work

For every request, DRF runs two checks:

1. **`has_permission(request, view)`** — called for every request
2. **`has_object_permission(request, view, obj)`** — called when accessing a specific object

```
Request comes in
    ↓
Authentication (who are you? → sets request.user)
    ↓
has_permission() — can you access this view at all?
    ↓
View logic runs, fetches object
    ↓
has_object_permission() — can you access this specific object?
    ↓
Response
```

If any permission check returns `False`:
- Unauthenticated user → `401 Unauthorized`
- Authenticated user → `403 Forbidden`

---

## 2. Built-in Permission Classes

```python
from rest_framework.permissions import (
    AllowAny,           # Everyone, including anonymous users
    IsAuthenticated,    # Must have a valid JWT
    IsAdminUser,        # Must have is_staff=True (Django built-in)
    IsAuthenticatedOrReadOnly,  # Authenticated for writes, anyone for reads
)
```

### Setting permissions globally

```python
# settings.py — applies to ALL views by default
REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### Overriding per view

```python
class BookListView(generics.ListAPIView):
    # Override the global default for this view
    permission_classes = [AllowAny]
```

---

## 3. Custom Permission Classes

```python
# accounts/permissions.py
from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsLibrarianOrAdmin(BasePermission):
    """
    Custom permission: only librarians and admins can write.
    Anyone can read (safe methods: GET, HEAD, OPTIONS).
    """

    # This message is returned in the 403 response
    message = 'Only librarians and administrators can perform this action.'

    def has_permission(self, request, view):
        # Safe methods (GET, HEAD, OPTIONS) — allow everyone
        if request.method in SAFE_METHODS:
            return True

        # For writes — require authentication and correct role
        return (
            request.user and
            request.user.is_authenticated and
            request.user.is_librarian_or_admin
        )
```

### Object-level permissions

```python
class IsOwnerOrAdmin(BasePermission):
    """Users can only access their own data. Admins can access anything."""

    def has_permission(self, request, view):
        # Must be authenticated for any access
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        """
        obj is the actual model instance (a User, a Loan, etc.)
        Called only when get_object() is used in the view.
        """
        if request.user.is_admin:
            return True

        # Check if the object belongs to the requesting user
        if hasattr(obj, 'user'):
            return obj.user == request.user  # e.g., Loan.user == request.user

        return obj == request.user  # e.g., User == request.user (profile)
```

---

## 4. Combining Permissions

Permissions in a list are AND-ed — ALL must pass:

```python
permission_classes = [IsAuthenticated, IsAdminUser]
# User must be both authenticated AND admin
```

OR logic requires a custom permission or `operator` approach:

```python
# Custom OR permission
class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user.is_admin
```

---

## 5. Dynamic Permissions (get_permissions)

```python
class BookViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        """Return different permissions based on the action."""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['create', 'update', 'partial_update']:
            return [IsLibrarianOrAdmin()]
        elif self.action == 'destroy':
            return [IsAdminUser()]
        return [IsAuthenticated()]
```

This is more flexible than `permission_classes` because different
operations can have different access requirements.

---

## 6. SAFE_METHODS Pattern

```python
from rest_framework.permissions import SAFE_METHODS
# SAFE_METHODS = ('GET', 'HEAD', 'OPTIONS')

class IsLibrarianOrAdmin(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True   # Reading is always allowed
        # Writing requires authentication + role
        return request.user.is_authenticated and request.user.is_librarian_or_admin
```

This implements the common "read public, write restricted" pattern.

---

## 7. What is Throttling?

Throttling limits how many requests a client can make in a time window.

**Why throttle?**
- Protect against DDoS attacks (someone hammering your API)
- Prevent API abuse (scraping all your data)
- Fair usage for all users
- Reduce server load

---

## 8. Built-in Throttle Classes

```python
REST_FRAMEWORK = {
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',   # Unauthenticated users
        'rest_framework.throttling.UserRateThrottle',   # Authenticated users
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',    # 100 requests per day (anonymous)
        'user': '1000/day',   # 1000 requests per day (logged in)
    },
}
```

**Rate format:** `number/period`
- `'100/day'` — 100 per day
- `'60/hour'` — 60 per hour
- `'30/min'` — 30 per minute
- `'10/second'` — 10 per second

**How it identifies users:**
- Authenticated: by user ID
- Anonymous: by IP address

---

## 9. Per-View Throttling

```python
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class LoginView(APIView):
    # Stricter rate limit on login (prevent brute force)
    throttle_classes = [AnonRateThrottle]
    # Uses the global 'anon' rate from settings

# For custom rates, create a custom throttle class
class LoginRateThrottle(UserRateThrottle):
    scope = 'login'   # Uses settings: THROTTLE_RATES = {'login': '5/min'}

class LoginView(APIView):
    throttle_classes = [LoginRateThrottle]
```

And in settings:
```python
'DEFAULT_THROTTLE_RATES': {
    'anon':  '100/day',
    'user':  '1000/day',
    'login': '5/min',    # Custom scope for login endpoint
}
```

---

## 10. Custom Throttle Classes

```python
from rest_framework.throttling import SimpleRateThrottle

class BorrowBookThrottle(SimpleRateThrottle):
    """
    Limit book borrowing to 10 per hour per user.
    Prevents abuse of the borrow endpoint.
    """
    scope = 'borrow'

    def get_cache_key(self, request, view):
        if not request.user.is_authenticated:
            return None   # Don't throttle unauthenticated (other throttles handle that)
        return f'borrow_{request.user.id}'
```

```python
# settings.py
'DEFAULT_THROTTLE_RATES': {
    'borrow': '10/hour',
}

# loans/views.py
class LoanViewSet(viewsets.ModelViewSet):
    throttle_classes = [BorrowBookThrottle]
```

---

## 11. Throttle Response

When a client exceeds the rate limit, DRF returns:

```
HTTP 429 Too Many Requests

{
    "detail": "Request was throttled. Expected available in 3600 seconds."
}
```

The `Retry-After` header tells the client when they can try again.

---

## 12. Role-Based Access Control (RBAC) Pattern

The full permission pattern used in this project:

```
                 ┌─────────────────────────────────┐
                 │         Request comes in         │
                 └──────────────┬──────────────────┘
                                │
              ┌─────────────────▼─────────────────┐
              │   Is user authenticated?            │
              │   (JWTAuthentication runs)          │
              └────────┬────────────────┬──────────┘
                       │ Yes            │ No
              ┌────────▼───┐     ┌──────▼──────────┐
              │ request.user│    │ AnonymousUser    │
              │ = User obj  │    │ AllowAny only    │
              └────────┬───┘    └─────────────────┘
                       │
        ┌──────────────┼──────────────────┐
        │              │                  │
   ┌────▼───┐    ┌──────▼─────┐   ┌──────▼─────┐
   │ ADMIN  │    │ LIBRARIAN  │   │  MEMBER    │
   │        │    │            │   │            │
   │ Full   │    │ Manage     │   │ Own data   │
   │ access │    │ books &    │   │ & borrow   │
   │        │    │ loans      │   │ books      │
   └────────┘    └────────────┘   └────────────┘
```

---

## 13. Testing Permissions Manually

```bash
# No token → should get 401
curl http://localhost:8000/api/v1/loans/

# Member token → should get only own loans
curl -H "Authorization: Bearer <member_token>" http://localhost:8000/api/v1/loans/

# Member token → should get 403 trying to create a book
curl -X POST -H "Authorization: Bearer <member_token>" \
  http://localhost:8000/api/v1/books/ \
  -d '{"title": "...", ...}'

# Admin token → should see all loans
curl -H "Authorization: Bearer <admin_token>" http://localhost:8000/api/v1/loans/
```

---

## Key Points to Remember

- `has_permission()` runs for every request
- `has_object_permission()` runs only when a specific object is being accessed
- Return `True` to allow, `False` to deny (→ 401 or 403)
- Multiple permissions are AND-ed — all must pass
- `SAFE_METHODS` = `('GET', 'HEAD', 'OPTIONS')` — use for read-public, write-restricted
- `get_permissions()` lets you use different permissions per action
- Throttling limits requests per time window — protects against abuse
- `429 Too Many Requests` is the throttle response code
- Anonymous users get stricter limits than authenticated users
