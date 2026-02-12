# BookSwipe API Reference

Base URL: `http://localhost:8000`

All endpoints return JSON. Authentication uses Bearer tokens in the `Authorization` header.

## Authentication

### POST /api/auth/register

Register a new user account.

**Rate limit:** 5 requests/minute

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (201):**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "password_strength": {
    "strength": "strong",
    "score": 5,
    "feedback": []
  }
}
```

**Password requirements:** 8+ characters, at least one uppercase letter, one lowercase letter, one number. Common passwords are rejected.

---

### POST /api/auth/login

Authenticate with email and password.

**Rate limit:** 5 requests/minute

**Request body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer"
}
```

---

### POST /api/auth/google

Authenticate via Google OAuth.

**Rate limit:** 5 requests/minute

**Request body:**
```json
{
  "id_token": "google-oauth-id-token"
}
```

**Response (200):** Same as login.

---

### POST /api/auth/apple

Authenticate via Apple OAuth.

**Rate limit:** 5 requests/minute

**Request body:**
```json
{
  "authorization_code": "apple-auth-code",
  "identity_token": "apple-identity-token"
}
```

**Response (200):** Same as login.

---

### POST /api/auth/refresh

Exchange a refresh token for a new token pair (token rotation).

**Rate limit:** 5 requests/minute

**Request body:**
```json
{
  "refresh_token": "eyJhbG..."
}
```

**Response (200):** Same as login.

---

### POST /api/auth/logout

Invalidate the current access token.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

---

### GET /api/auth/me

Get the authenticated user's profile.

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2024-01-15T10:30:00"
}
```

---

### DELETE /api/auth/me

Soft-delete the authenticated user's account (GDPR compliance).

**Headers:** `Authorization: Bearer <access_token>`

**Response (200):**
```json
{
  "message": "Account deleted"
}
```

---

## Books

### GET /api/books/discover

Discover books by category. Authenticated users have liked/skipped books filtered out.

**Auth:** Optional

**Query parameters:**
| Parameter   | Type   | Default    | Description                    |
|-------------|--------|------------|--------------------------------|
| `category`  | string | `fiction`  | Google Books subject category  |
| `page`      | int    | `1`        | Page number (>= 1)            |
| `page_size` | int    | `20`       | Results per page (1-40)        |

**Response (200):**
```json
{
  "books": [
    {
      "google_book_id": "abc123",
      "title": "Example Book",
      "authors": ["Author Name"],
      "thumbnail": "https://...",
      "categories": ["Fiction"],
      "average_rating": 4.2,
      "ratings_count": 150
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

---

### GET /api/books/{book_id}

Get detailed information for a single book.

**Auth:** Optional

**Response (200):**
```json
{
  "google_book_id": "abc123",
  "title": "Example Book",
  "authors": ["Author Name"],
  "thumbnail": "https://...",
  "categories": ["Fiction"],
  "average_rating": 4.2,
  "ratings_count": 150,
  "description": "A fascinating story...",
  "page_count": 320,
  "published_date": "2023-01-15",
  "publisher": "Publisher Name",
  "preview_link": "https://...",
  "info_link": "https://..."
}
```

---

### GET /api/books/liked

Get the authenticated user's liked books (paginated).

**Auth:** Required

**Query parameters:**
| Parameter   | Type | Default | Description             |
|-------------|------|---------|-------------------------|
| `page`      | int  | `1`     | Page number (>= 1)     |
| `page_size` | int  | `20`    | Results per page (1-100)|

**Response (200):**
```json
{
  "books": [
    {
      "id": 1,
      "google_book_id": "abc123",
      "title": "Example Book",
      "authors": "Author Name",
      "thumbnail": "https://...",
      "liked_at": "2024-01-15T10:30:00"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

---

### POST /api/books/like

Add a book to the user's liked list.

**Auth:** Required

**Request body:**
```json
{
  "google_book_id": "abc123",
  "title": "Example Book",
  "authors": "Author Name",
  "thumbnail": "https://..."
}
```

**Response (201):** Returns the created liked book record.

---

### POST /api/books/skip

Mark a book as skipped.

**Auth:** Required

**Request body:**
```json
{
  "google_book_id": "abc123"
}
```

**Response (201):**
```json
{
  "message": "Book skipped"
}
```

---

### DELETE /api/books/liked/{google_book_id}

Remove a book from the user's liked list.

**Auth:** Required

**Response (200):**
```json
{
  "message": "Book removed from liked list"
}
```

---

## Categories

### GET /api/categories

List all available book categories (sorted alphabetically).

**Auth:** Not required

**Response (200):**
```json
[
  {
    "id": 1,
    "name": "Biography",
    "google_category_key": "biography"
  },
  {
    "id": 2,
    "name": "Comics",
    "google_category_key": "comics"
  }
]
```

---

### GET /api/categories/{category_id}

Get a single category by ID.

**Auth:** Not required

**Response (200):**
```json
{
  "id": 1,
  "name": "Fiction",
  "google_category_key": "fiction"
}
```

---

## Health

### GET /health

Application health check.

**Response (200):**
```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development"
}
```

---

## Error Responses

All errors follow this structure:

```json
{
  "detail": "Human-readable error message",
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": null
  }
}
```

**Error codes:**
| Code                | HTTP Status | Description                  |
|---------------------|-------------|------------------------------|
| `AUTH_ERROR`        | 401         | Authentication failed        |
| `NOT_FOUND`        | 404         | Resource not found           |
| `VALIDATION_ERROR` | 409         | Validation/conflict error    |
| `RATE_LIMIT_EXCEEDED` | 429      | Too many requests            |
| `EXTERNAL_API_ERROR`  | 502      | Google Books API failure     |
| `INTERNAL_ERROR`   | 500         | Unexpected server error      |

Pydantic validation errors (422) use FastAPI's default format with a `detail` array.
