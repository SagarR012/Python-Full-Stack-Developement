# Lesson 04: JWT Authentication with SimpleJWT

## Overview

JWT (JSON Web Tokens) is the standard way to authenticate REST APIs.
Instead of sessions stored on the server, the client holds a cryptographic
token that proves who they are on every request.

---

## 1. What is a JWT?

A JWT is a Base64-encoded string with three parts separated by dots:

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9   ← Header
.eyJ1c2VyX2lkIjoxLCJleHAiOjE3MDAwMDB9  ← Payload (claims)
.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV    ← Signature
```

**Decode the payload:**
```json
{
  "user_id": 1,
  "username": "alice",
  "exp": 1700000000,
  "iat": 1699999000
}
```

The server verifies the **signature** using `SECRET_KEY`.
If the signature is valid and the token hasn't expired → the user is authenticated.

**Key point:** The payload is NOT encrypted, just encoded. Don't store secrets in JWTs.

---

## 2. Access Token vs Refresh Token

| | Access Token | Refresh Token |
|---|---|---|
| **Purpose** | Authenticate API requests | Get new access tokens |
| **Lifetime** | Short (15 minutes) | Long (7 days) |
| **Sent with** | Every API request | Only to `/auth/refresh/` |
| **If stolen** | Attacker has 15 min | Attacker can keep refreshing |

**Why short-lived access tokens?**
If an access token is stolen, the attacker can only use it for 15 minutes.
After that, it expires and is useless.

**Why rotation?**
Each time the refresh token is used, you get a NEW refresh token.
The old one is blacklisted. If an attacker steals a refresh token,
using it alerts the legitimate user (their next refresh will fail).

---

## 3. The JWT Flow

```
┌─────────────────────────────────────────────────────────────┐
│  STEP 1: LOGIN                                              │
│                                                             │
│  Client ──POST /auth/login/──────────────────────► Server  │
│         { username, password }                             │
│                                                             │
│  Server ◄──────────────────────────────────────────────── │
│         { access: "eyJ...", refresh: "eyJ..." }            │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  STEP 2: USE API                                            │
│                                                             │
│  Client ──GET /api/v1/books/──────────────────────► Server │
│         Header: Authorization: Bearer eyJ...access...      │
│                                                             │
│  Server checks: is the signature valid? is it expired?     │
│  Server ◄── 200 OK { books: [...] }                        │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  STEP 3: REFRESH (when access token expires after 15 min)  │
│                                                             │
│  Client ──POST /auth/refresh/─────────────────────► Server │
│         { refresh: "eyJ...old_refresh..." }                │
│                                                             │
│  Server ◄── 200 OK { access: "eyJ...new...",               │
│                       refresh: "eyJ...new_refresh..." }    │
│  (old refresh token is now blacklisted)                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  STEP 4: LOGOUT                                             │
│                                                             │
│  Client ──POST /auth/logout/──────────────────────► Server │
│         { refresh: "eyJ...refresh..." }                    │
│                                                             │
│  Server blacklists the token                               │
│  Server ◄── 205 Reset Content                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. SimpleJWT Configuration

```python
# settings.py
from datetime import timedelta

SIMPLE_JWT = {
    # Access token expires quickly — limits damage if stolen
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),

    # Refresh token lives longer
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),

    # Each refresh generates a NEW refresh token (rotation)
    'ROTATE_REFRESH_TOKENS': True,

    # Old refresh token is blacklisted after rotation
    # Requires 'rest_framework_simplejwt.token_blacklist' in INSTALLED_APPS
    'BLACKLIST_AFTER_ROTATION': True,

    # Update user.last_login on every token obtain
    'UPDATE_LAST_LOGIN': True,

    'ALGORITHM': 'HS256',          # HMAC-SHA256 signing
    'AUTH_HEADER_TYPES': ('Bearer',),  # Authorization: Bearer <token>
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',    # Name of the claim in the JWT payload
}
```

---

## 5. Setting Up JWT — Required Pieces

### 1. Install and add to INSTALLED_APPS

```python
INSTALLED_APPS = [
    ...
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',  # Required for BLACKLIST_AFTER_ROTATION
]
```

### 2. Set as default authentication

```python
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',  # Keep for browsable API
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}
```

### 3. Add URL patterns

```python
# accounts/urls.py
from rest_framework_simplejwt.views import (
    TokenObtainPairView,   # POST credentials → tokens
    TokenRefreshView,       # POST refresh → new tokens
    TokenBlacklistView,     # POST refresh → blacklist (logout)
)

urlpatterns = [
    path('auth/login/',   TokenObtainPairView.as_view(),  name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(),     name='token-refresh'),
    path('auth/logout/',  TokenBlacklistView.as_view(),   name='logout'),
]
```

### 4. Run migrations (for the blacklist table)

```bash
python manage.py migrate
```

---

## 6. Using JWT in Requests

### Setting the Authorization Header

```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

Note: `Bearer` is a prefix (the token type). Your actual token comes after the space.

### In Postman

1. Go to your request → **Authorization** tab
2. Type: `Bearer Token`
3. Token: paste your access token

Or set the header manually:
- Key: `Authorization`
- Value: `Bearer <your_access_token>`

---

## 7. Accessing the Current User in Views

```python
class MyView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        # DRF's JWTAuthentication sets request.user automatically
        user = request.user          # The User instance from the token
        user.id                      # User's primary key
        user.username                # Username
        user.role                    # Custom role field
        user.is_authenticated        # Always True here (IsAuthenticated ensures it)

        return Response({'user': user.username})
```

---

## 8. Custom Token Claims

By default, the access token payload contains `user_id` and `token_type`.
You can add custom claims:

```python
# accounts/views.py or serializers.py
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims to the JWT payload
        token['username'] = user.username
        token['role'] = user.role
        token['email'] = user.email
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
```

```python
# accounts/urls.py — use the custom view
path('auth/login/', CustomTokenObtainPairView.as_view(), name='login'),
```

---

## 9. Token Blacklisting — How Logout Works

Logout in JWT requires blacklisting because tokens are stateless.
You can't "delete" a token on the server — it's just a string the client holds.

The blacklist approach:
1. Client sends the refresh token to `POST /auth/logout/`
2. Server stores the token's unique identifier (jti) in the blacklist table
3. On future refresh attempts, server checks the blacklist → rejects

```python
# The TokenBlacklistView does all this automatically.
# You just need the token_blacklist app installed and migrated.
```

**Important:** The access token is still valid until it expires (15 min).
This is acceptable — if you need instant invalidation, use a shorter lifetime.

---

## 10. Common JWT Errors

| Error | Meaning | Fix |
|-------|---------|-----|
| `401 Unauthorized - No credentials provided` | No Authorization header | Add `Authorization: Bearer <token>` |
| `401 - Given token not valid for any token type` | Token is malformed or wrong type | Use the access token, not refresh |
| `401 - Token is expired` | Access token expired | Call `/auth/refresh/` for a new one |
| `401 - Token is blacklisted` | Refresh token was already used or logged out | User must log in again |
| `400 - This field may not be blank` | Missing `refresh` field in body | Send `{"refresh": "..."}` |

---

## 11. Security Best Practices

**Store tokens safely:**
- Never in `localStorage` for sensitive apps (XSS vulnerability)
- Better: `httpOnly` cookies (not accessible from JavaScript)
- Acceptable: `sessionStorage` (cleared on tab close)
- For mobile/desktop apps: secure key store

**Never put secrets in the payload:**
The JWT payload is Base64-encoded, not encrypted. Anyone who gets the token
can decode and read the payload. Never put passwords or private data there.

**Use HTTPS in production:**
JWTs in plain HTTP can be intercepted. Always use HTTPS.

**Keep access tokens short-lived:**
15 minutes is common. Some security-sensitive apps use 5 minutes.

---

## Key Points to Remember

- JWT = cryptographically signed token the client stores and sends with every request
- Access token: short-lived (15 min), sent with every API call
- Refresh token: long-lived (7 days), only sent to `/auth/refresh/`
- Token rotation: each refresh generates new tokens, old one is blacklisted
- `request.user` is set automatically by `JWTAuthentication` from the token
- Logout = blacklist the refresh token (access token expires naturally)
- Never store secrets in the JWT payload — it's readable, just not writable
