# Lesson 08: Testing APIs with Postman

## Overview

Postman is the industry-standard tool for testing and documenting REST APIs.
This lesson covers setting up a Postman collection for the Library API,
writing automated tests, and using environment variables to keep
your JWT tokens current automatically.

---

## 1. Setting Up Postman

### Create an Environment

Environments store variables that change between contexts (local vs staging vs production).

1. Click **Environments** (left sidebar) → **New Environment**
2. Name it: `Library API - Local`
3. Add these variables:

| Variable | Initial Value | Current Value |
|----------|---------------|---------------|
| `base_url` | `http://localhost:8000` | `http://localhost:8000` |
| `access_token` | *(empty)* | *(empty — filled by login test)* |
| `refresh_token` | *(empty)* | *(empty — filled by login test)* |

4. Click **Save**
5. Select this environment from the dropdown (top right)

---

## 2. Creating a Collection

1. Click **Collections** → **New Collection**
2. Name it: `Library Management API`
3. Add a description (optional)

Organize requests into folders:
```
📁 Library Management API
   📁 Auth
      POST Register
      POST Login
      POST Refresh Token
      POST Logout
      GET Profile
      PATCH Update Profile
      POST Change Password
   📁 Books
      GET List Books
      GET Filter Books
      GET Book Detail
      POST Create Book
      PATCH Update Book
      DELETE Delete Book
      GET Book Availability
   📁 Authors & Categories
      GET List Authors
      POST Create Author
      GET List Categories
      POST Create Category
   📁 Loans
      POST Borrow Book
      GET My Loans
      GET All Loans (Admin)
      POST Return Book
```

---

## 3. Using Variables in Requests

Instead of hardcoding the URL:
```
http://localhost:8000/api/v1/books/   ← Bad: hardcoded
{{base_url}}/api/v1/books/            ← Good: uses variable
```

In the Authorization tab, set `Bearer {{access_token}}` so all requests
automatically use the current token.

---

## 4. The Login Request — Auto-Capturing Tokens

This is the most important automation step.

**Request:**
- Method: `POST`
- URL: `{{base_url}}/api/v1/auth/login/`
- Body (JSON):
```json
{
    "username": "your_username",
    "password": "your_password"
}
```

**Tests tab — paste this script:**
```javascript
// This runs after the response is received

pm.test("Login successful", function () {
    pm.response.to.have.status(200);
});

pm.test("Response has tokens", function () {
    const json = pm.response.json();
    pm.expect(json).to.have.property('access');
    pm.expect(json).to.have.property('refresh');
});

// Auto-save tokens to environment variables
if (pm.response.code === 200) {
    const json = pm.response.json();
    pm.environment.set("access_token", json.access);
    pm.environment.set("refresh_token", json.refresh);
    console.log("Tokens saved to environment.");
}
```

Now whenever you run the Login request, the tokens are automatically
saved. All other requests that use `{{access_token}}` will work immediately.

---

## 5. Auto-Refresh Token Script

Add this to the **Collection's Pre-request Script** to auto-refresh
the token when it expires:

```javascript
// Collection → Edit → Pre-request Script tab

const token = pm.environment.get("access_token");

// If no token, skip (the login test will handle it)
if (!token) return;

// Decode the JWT payload (middle section)
function parseJwt(token) {
    try {
        const base64 = token.split('.')[1]
            .replace(/-/g, '+')
            .replace(/_/g, '/');
        return JSON.parse(atob(base64));
    } catch(e) {
        return null;
    }
}

const payload = parseJwt(token);
if (!payload) return;

const expiresAt = payload.exp * 1000;  // Convert to milliseconds
const now = Date.now();
const bufferMs = 60 * 1000;  // Refresh 1 minute before expiry

if (now >= expiresAt - bufferMs) {
    console.log("Access token expiring soon, refreshing...");

    const refreshToken = pm.environment.get("refresh_token");

    pm.sendRequest({
        url: pm.environment.get("base_url") + "/api/v1/auth/refresh/",
        method: "POST",
        header: { "Content-Type": "application/json" },
        body: {
            mode: "raw",
            raw: JSON.stringify({ refresh: refreshToken })
        }
    }, function(err, response) {
        if (!err && response.code === 200) {
            const json = response.json();
            pm.environment.set("access_token", json.access);
            pm.environment.set("refresh_token", json.refresh);
            console.log("Token refreshed successfully.");
        } else {
            console.log("Token refresh failed. Re-login needed.");
        }
    });
}
```

---

## 6. Writing Tests in Postman

Every request can have a **Tests tab** with JavaScript assertions.

### Basic status code test

```javascript
pm.test("Status 200 OK", function () {
    pm.response.to.have.status(200);
});
```

### Test response body

```javascript
pm.test("Response is an array", function () {
    const json = pm.response.json();
    pm.expect(json.results).to.be.an('array');
});

pm.test("Books have required fields", function () {
    const json = pm.response.json();
    const book = json.results[0];
    pm.expect(book).to.have.property('id');
    pm.expect(book).to.have.property('title');
    pm.expect(book).to.have.property('author');
    pm.expect(book).to.have.property('isbn');
});
```

### Test pagination structure

```javascript
pm.test("Pagination structure is correct", function () {
    const json = pm.response.json();
    pm.expect(json).to.have.property('count');
    pm.expect(json).to.have.property('next');
    pm.expect(json).to.have.property('previous');
    pm.expect(json).to.have.property('results');
    pm.expect(json.results).to.be.an('array');
});
```

### Test response time

```javascript
pm.test("Response time under 500ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(500);
});
```

### Test error responses

```javascript
// For a request with invalid data
pm.test("Returns 400 for invalid data", function () {
    pm.response.to.have.status(400);
});

pm.test("Error response has detail field", function () {
    const json = pm.response.json();
    // DRF returns errors in various formats
    pm.expect(json).to.satisfy(function(body) {
        return body.detail || body.username || body.email || body.non_field_errors;
    });
});
```

### Save response data for later requests

```javascript
// In the "Create Book" request's Tests tab
if (pm.response.code === 201) {
    const json = pm.response.json();
    pm.environment.set("book_id", json.id);
    console.log("Book ID saved:", json.id);
}
```

Then use `{{book_id}}` in subsequent requests:
```
GET {{base_url}}/api/v1/books/{{book_id}}/
```

---

## 7. Example Test Suite — Step by Step

Here's a complete test flow to run in sequence:

### 1. Register a new user

- POST `{{base_url}}/api/v1/auth/register/`
- Body:
```json
{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "TestPass123!",
    "password_confirm": "TestPass123!"
}
```
- Test: status 201, response has `user.id`

### 2. Login

- POST `{{base_url}}/api/v1/auth/login/`
- Test script: save tokens to environment

### 3. Get profile

- GET `{{base_url}}/api/v1/auth/profile/`
- Authorization: Bearer `{{access_token}}`
- Test: status 200, username matches

### 4. List books (public)

- GET `{{base_url}}/api/v1/books/`
- No authorization needed
- Test: pagination structure, status 200

### 5. Try to create a book (as member — should fail)

- POST `{{base_url}}/api/v1/books/`
- Authorization: Bearer `{{access_token}}` (member token)
- Test: status 403

### 6. Login as librarian

- POST `{{base_url}}/api/v1/auth/login/`
- Body: librarian credentials
- Test: save new tokens

### 7. Create a book (as librarian)

- POST `{{base_url}}/api/v1/books/`
- Body:
```json
{
    "title": "The Great Gatsby",
    "author": 1,
    "category": 1,
    "isbn": "9780743273565",
    "description": "A novel about the Jazz Age.",
    "published_date": "1925-04-10",
    "total_copies": 3,
    "available_copies": 3
}
```
- Test: status 201, save `book_id`

### 8. Borrow the book (switch back to member)

- POST `{{base_url}}/api/v1/loans/`
- Body: `{"book": {{book_id}}}`
- Test: status 201, `status == "active"`, save `loan_id`

### 9. Check book availability decreased

- GET `{{base_url}}/api/v1/books/{{book_id}}/availability/`
- Test: `available_copies` decreased by 1

### 10. Return the book

- POST `{{base_url}}/api/v1/loans/{{loan_id}}/return/`
- Test: status 200, `status == "returned"`

### 11. Logout

- POST `{{base_url}}/api/v1/auth/logout/`
- Body: `{"refresh": "{{refresh_token}}"}`
- Test: status 200, clear tokens from environment

---

## 8. Collection Runner

To run all tests in sequence automatically:

1. Click **Runner** (top right of Postman)
2. Select your collection
3. Select the `Library API - Local` environment
4. Set the order of requests
5. Click **Run**

Postman runs all requests in sequence and shows pass/fail results.

---

## 9. Common HTTP Status Codes Reference

| Code | Name | When to expect it |
|------|----|-------------------|
| 200 | OK | Successful GET, PUT, PATCH |
| 201 | Created | Successful POST (resource created) |
| 204 | No Content | Successful DELETE |
| 400 | Bad Request | Validation errors (wrong data) |
| 401 | Unauthorized | Missing or invalid JWT token |
| 403 | Forbidden | Authenticated but insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 405 | Method Not Allowed | Wrong HTTP method for this endpoint |
| 429 | Too Many Requests | Rate limit exceeded (throttling) |
| 500 | Server Error | Bug in the server code |

---

## 10. Using the Included Postman Collection

This project includes `postman/Library_API.postman_collection.json`.

To import it:
1. Open Postman
2. Click **Import** → **File**
3. Select `Library_API.postman_collection.json`
4. Create the `Library API - Local` environment with the variables above
5. Run the **Login** request first to get your tokens
6. All other requests will work automatically

---

## Key Points to Remember

- Environments store variables — use `{{base_url}}` and `{{access_token}}` everywhere
- The Login request's Tests tab should auto-save tokens to environment variables
- Use the Collection Pre-request Script for auto-token-refresh
- Tests tab assertions run after every response — catch bugs early
- Save IDs from POST responses (`pm.environment.set("book_id", json.id)`)
- Use those saved IDs in subsequent requests: `{{base_url}}/api/v1/books/{{book_id}}/`
- Collection Runner runs all requests in sequence for full workflow testing
- Import the OpenAPI schema to auto-generate a collection
