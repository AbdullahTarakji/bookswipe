# BookSwipe API Documentation

**Version:** 1.0.0
**Base URL:** `http://localhost:8000`

BookSwipe is a FastAPI-powered backend for a book discovery application. Users can browse books from the Google Books catalog, like or skip them, and manage their reading lists. This document covers every endpoint, including request/response formats, authentication requirements, rate limits, and error handling.

---

## Table of Contents

1. [Authentication](#authentication)
2. [Rate Limiting](#rate-limiting)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Health](#health)
   - [Auth](#auth-endpoints)
   - [Books](#books-endpoints)
   - [Categories](#categories-endpoints)
5. [Data Models](#data-models)
6. [Password Requirements](#password-requirements)

---

## Authentication

BookSwipe uses **JWT (JSON Web Token) Bearer authentication**. Tokens are issued on registration or login and must be included in the `Authorization` header for protected endpoints.

### Token Types

| Token | Lifetime | Purpose |
|-------|----------|---------|
| Access Token | 15 minutes | Authenticates API requests |
| Refresh Token | 7 days | Obtains new access/refresh token pairs |

### How to Authenticate

1. **Register** or **login** to receive an `access_token` and `refresh_token`.
2. Include the access token in the `Authorization` header for all protected requests:

```
Authorization: Bearer <access_token>
```

3. When the access token expires, use the `/api/auth/refresh` endpoint with your refresh token to obtain a new token pair. The old refresh token is invalidated upon use (token rotation).
4. On **logout**, the current access token is blacklisted and can no longer be used.

### Token Details

- **Algorithm:** HS256
- **Issuer:** `bookswipe-api`
- **Audience:** `bookswipe-client`
- Each token includes a unique `jti` (JWT ID) claim used for blacklisting.

---

## Rate Limiting

Rate limiting is enforced per client IP address using the `slowapi` library.

| Scope | Limit |
|-------|-------|
| Auth endpoints (register, login, refresh) | 5 requests per minute |
| General API endpoints | 30 requests per minute |

When the rate limit is exceeded, the API responds with HTTP `429`:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded. Try again later.",
    "details": null
  }
}
```

---

## Error Handling

All errors are returned as structured JSON with a consistent format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of the error",
    "details": null
  }
}
```

The `details` field may contain additional context (for example, a list of field-level validation errors) or be `null`.

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `AUTH_ERROR` | 401 | Authentication or authorization failure (invalid credentials, expired token, missing token) |
| `NOT_FOUND` | 404 | Requested resource does not exist |
| `CONFLICT` | 409 | Resource already exists or conflicts with the current state (e.g., duplicate email, book already liked) |
| `VALIDATION_ERROR` | 422 | Request body failed validation (malformed fields, missing required fields, password policy violations) |
| `RATE_LIMIT_EXCEEDED` | 429 | Client has exceeded the allowed request rate |
| `EXTERNAL_API_ERROR` | 502 | An external service (Google Books API) returned an error or is unavailable |
| `INTERNAL_ERROR` | 500 | An unexpected server-side error occurred |

### Validation Error Details

When a `VALIDATION_ERROR` occurs, the `details` field contains an array of field-level errors:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": [
      {
        "field": "body.email",
        "message": "value is not a valid email address"
      },
      {
        "field": "body.password",
        "message": "String should have at least 8 characters"
      }
    ]
  }
}
```

---

## Endpoints

### Health

#### GET /health

Returns the current health status of the API. No authentication required.

**Response:** `200 OK`

```json
{
  "status": "ok",
  "version": "1.0.0",
  "environment": "development"
}
```

**curl example:**

```bash
curl http://localhost:8000/health
```

---

### Auth Endpoints

All auth endpoints are under the `/api/auth` prefix.

---

#### POST /api/auth/register

Register a new user account. Returns access and refresh tokens along with a password strength assessment.

**Rate limit:** 5 requests per minute

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email, max 255 characters |
| `password` | string | Yes | 8-128 characters, must contain uppercase, lowercase, and a digit; must not be a common password |

**Response:** `201 Created`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "password_strength": {
    "strength": "strong",
    "score": 5,
    "feedback": []
  }
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 409 | `CONFLICT` | Email already registered |
| 422 | `VALIDATION_ERROR` | Invalid email or password policy violation |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many registration attempts |

**curl example:**

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "MySecure1Pass"
  }'
```

---

#### POST /api/auth/login

Authenticate an existing user and receive tokens.

**Rate limit:** 5 requests per minute

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email, max 255 characters |
| `password` | string | Yes | Max 128 characters |

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "password_strength": null
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Invalid email or password |
| 422 | `VALIDATION_ERROR` | Malformed request body |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many login attempts |

**curl example:**

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "MySecure1Pass"
  }'
```

---

#### POST /api/auth/logout

Invalidate the current access token by adding it to the blacklist. The `Authorization` header is optional; if no token is provided, the endpoint still returns a success response.

**Request headers (optional):**

```
Authorization: Bearer <access_token>
```

**Response:** `200 OK`

```json
{
  "message": "Successfully logged out"
}
```

**curl example:**

```bash
curl -X POST http://localhost:8000/api/auth/logout \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

#### POST /api/auth/refresh

Exchange a valid refresh token for a new access/refresh token pair. The old refresh token is blacklisted (token rotation).

**Rate limit:** 5 requests per minute

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | A valid, non-blacklisted refresh token |

**Response:** `200 OK`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "password_strength": null
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Invalid, expired, or blacklisted refresh token; user not found or deactivated |
| 429 | `RATE_LIMIT_EXCEEDED` | Too many refresh attempts |

**curl example:**

```bash
curl -X POST http://localhost:8000/api/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

---

#### GET /api/auth/me

Return the authenticated user's profile information.

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
{
  "id": 1,
  "email": "user@example.com",
  "created_at": "2025-01-15T10:30:00"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Missing, invalid, or expired access token |

**curl example:**

```bash
curl http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

#### DELETE /api/auth/me

Soft-delete the authenticated user's account. The user record is marked as inactive with a `deleted_at` timestamp rather than being permanently removed (GDPR compliant). The user will no longer be able to log in.

**Authentication:** Required (Bearer token)

**Response:** `200 OK`

```json
{
  "message": "Account deleted"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Missing, invalid, or expired access token |

**curl example:**

```bash
curl -X DELETE http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

### Books Endpoints

All book endpoints are under the `/api/books` prefix.

---

#### GET /api/books/discover

Discover books from the Google Books catalog. When authenticated, books that the user has already liked or skipped are excluded from results.

**Authentication:** Optional (Bearer token)

**Query parameters:**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `category` | string | `"fiction"` | Min 1 character | Book category to search |
| `page` | integer | `1` | >= 1 | Page number |
| `page_size` | integer | `20` | 1-40 | Number of results per page |

**Response:** `200 OK`

```json
{
  "books": [
    {
      "google_book_id": "zyTCAlFPjgYC",
      "title": "The Lord of the Rings",
      "authors": ["J.R.R. Tolkien"],
      "thumbnail": "http://books.google.com/books/content?id=zyTCAlFPjgYC&printsec=frontcover&img=1&zoom=1",
      "categories": ["Fiction", "Fantasy"],
      "average_rating": 4.5,
      "ratings_count": 2584
    }
  ],
  "total": 150,
  "page": 1,
  "page_size": 20
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 502 | `EXTERNAL_API_ERROR` | Google Books API failure |

**curl examples:**

```bash
# Without authentication (browse as guest)
curl "http://localhost:8000/api/books/discover?category=fiction&page=1&page_size=20"

# With authentication (excludes already-seen books)
curl "http://localhost:8000/api/books/discover?category=mystery&page=2&page_size=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

#### GET /api/books/{book_id}

Retrieve detailed information about a single book by its Google Books ID.

**Authentication:** Optional (Bearer token)

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `book_id` | string | Google Books volume ID |

**Response:** `200 OK`

```json
{
  "google_book_id": "zyTCAlFPjgYC",
  "title": "The Lord of the Rings",
  "authors": ["J.R.R. Tolkien"],
  "thumbnail": "http://books.google.com/books/content?id=zyTCAlFPjgYC&printsec=frontcover&img=1&zoom=1",
  "categories": ["Fiction", "Fantasy"],
  "average_rating": 4.5,
  "ratings_count": 2584,
  "description": "One Ring to rule them all...",
  "page_count": 1216,
  "published_date": "2012-02-15",
  "publisher": "Mariner Books",
  "preview_link": "http://books.google.com/books?id=zyTCAlFPjgYC&printsec=frontcover&source=gbs_ge_summary_r&cad=0",
  "info_link": "https://play.google.com/store/books/details?id=zyTCAlFPjgYC&source=gbs_api"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 404 | `NOT_FOUND` | Book not found in Google Books |
| 502 | `EXTERNAL_API_ERROR` | Google Books API failure |

**curl example:**

```bash
curl http://localhost:8000/api/books/zyTCAlFPjgYC
```

---

#### POST /api/books/like

Add a book to the authenticated user's liked collection.

**Authentication:** Required (Bearer token)

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `google_book_id` | string | Yes | Max 50 characters |
| `title` | string | No | Max 500 characters (default: `""`) |
| `authors` | string | No | Max 500 characters (default: `""`) |
| `thumbnail` | string | No | Max 500 characters (default: `""`) |

Note: The `title` and `authors` fields are sanitized to remove HTML and script tags.

**Response:** `201 Created`

```json
{
  "id": 42,
  "google_book_id": "zyTCAlFPjgYC",
  "title": "The Lord of the Rings",
  "authors": "J.R.R. Tolkien",
  "thumbnail": "http://books.google.com/books/content?id=zyTCAlFPjgYC&printsec=frontcover&img=1&zoom=1",
  "liked_at": "2025-01-15T14:30:00"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Missing, invalid, or expired access token |
| 409 | `CONFLICT` | Book already liked by this user |
| 422 | `VALIDATION_ERROR` | Invalid request body |

**curl example:**

```bash
curl -X POST http://localhost:8000/api/books/like \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "google_book_id": "zyTCAlFPjgYC",
    "title": "The Lord of the Rings",
    "authors": "J.R.R. Tolkien",
    "thumbnail": "http://books.google.com/books/content?id=zyTCAlFPjgYC&printsec=frontcover&img=1&zoom=1"
  }'
```

---

#### POST /api/books/skip

Record that the authenticated user skipped (dismissed) a book. Skipped books are excluded from future `/discover` results. If the book was already skipped, the endpoint returns success without creating a duplicate.

**Authentication:** Required (Bearer token)

**Request body:**

| Field | Type | Required | Constraints |
|-------|------|----------|-------------|
| `google_book_id` | string | Yes | Max 50 characters |
| `title` | string | No | Max 500 characters (default: `""`) |
| `authors` | string | No | Max 500 characters (default: `""`) |
| `thumbnail` | string | No | Max 500 characters (default: `""`) |

**Response:** `201 Created`

```json
{
  "message": "Book skipped"
}
```

If the book was already skipped:

```json
{
  "message": "Book already skipped"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Missing, invalid, or expired access token |
| 422 | `VALIDATION_ERROR` | Invalid request body |

**curl example:**

```bash
curl -X POST http://localhost:8000/api/books/skip \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..." \
  -H "Content-Type: application/json" \
  -d '{
    "google_book_id": "abc123def"
  }'
```

---

#### GET /api/books/liked

Retrieve the authenticated user's liked books with pagination, ordered by most recently liked first.

**Authentication:** Required (Bearer token)

**Query parameters:**

| Parameter | Type | Default | Constraints | Description |
|-----------|------|---------|-------------|-------------|
| `page` | integer | `1` | >= 1 | Page number |
| `page_size` | integer | `20` | 1-100 | Number of results per page |

**Response:** `200 OK`

```json
{
  "books": [
    {
      "id": 42,
      "google_book_id": "zyTCAlFPjgYC",
      "title": "The Lord of the Rings",
      "authors": "J.R.R. Tolkien",
      "thumbnail": "http://books.google.com/books/content?id=zyTCAlFPjgYC&printsec=frontcover&img=1&zoom=1",
      "liked_at": "2025-01-15T14:30:00"
    }
  ],
  "total": 5,
  "page": 1,
  "page_size": 20
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Missing, invalid, or expired access token |

**curl example:**

```bash
curl "http://localhost:8000/api/books/liked?page=1&page_size=10" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

#### DELETE /api/books/liked/{google_book_id}

Remove a book from the authenticated user's liked collection.

**Authentication:** Required (Bearer token)

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `google_book_id` | string | Google Books volume ID |

**Response:** `200 OK`

```json
{
  "message": "Book removed from liked list"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 401 | `AUTH_ERROR` | Missing, invalid, or expired access token |
| 404 | `NOT_FOUND` | Book not found in the user's liked list |

**curl example:**

```bash
curl -X DELETE http://localhost:8000/api/books/liked/zyTCAlFPjgYC \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

---

### Categories Endpoints

All category endpoints are under the `/api/categories` prefix. No authentication is required.

---

#### GET /api/categories

Retrieve all book categories, ordered alphabetically by name.

**Authentication:** None

**Response:** `200 OK`

```json
[
  {
    "id": 1,
    "name": "Biography",
    "google_category_key": "biography"
  },
  {
    "id": 2,
    "name": "Business",
    "google_category_key": "business"
  },
  {
    "id": 3,
    "name": "Comics",
    "google_category_key": "comics"
  },
  {
    "id": 4,
    "name": "Fantasy",
    "google_category_key": "fantasy"
  },
  {
    "id": 5,
    "name": "Fiction",
    "google_category_key": "fiction"
  },
  {
    "id": 6,
    "name": "History",
    "google_category_key": "history"
  },
  {
    "id": 7,
    "name": "Horror",
    "google_category_key": "horror"
  },
  {
    "id": 8,
    "name": "Mystery",
    "google_category_key": "mystery"
  },
  {
    "id": 9,
    "name": "Poetry",
    "google_category_key": "poetry"
  },
  {
    "id": 10,
    "name": "Romance",
    "google_category_key": "romance"
  },
  {
    "id": 11,
    "name": "Sci-Fi",
    "google_category_key": "science+fiction"
  },
  {
    "id": 12,
    "name": "Science",
    "google_category_key": "science"
  },
  {
    "id": 13,
    "name": "Self-Help",
    "google_category_key": "self-help"
  },
  {
    "id": 14,
    "name": "Thriller",
    "google_category_key": "thriller"
  }
]
```

**curl example:**

```bash
curl http://localhost:8000/api/categories
```

---

#### GET /api/categories/{category_id}

Retrieve a single category by its ID.

**Authentication:** None

**Path parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `category_id` | integer | The category's numeric ID |

**Response:** `200 OK`

```json
{
  "id": 4,
  "name": "Fantasy",
  "google_category_key": "fantasy"
}
```

**Error responses:**

| Status | Code | Condition |
|--------|------|-----------|
| 404 | `NOT_FOUND` | Category with the given ID does not exist |

**curl example:**

```bash
curl http://localhost:8000/api/categories/4
```

---

## Data Models

### TokenResponse

Returned by register, login, and refresh endpoints.

| Field | Type | Description |
|-------|------|-------------|
| `access_token` | string | JWT access token (15-minute lifetime) |
| `refresh_token` | string | JWT refresh token (7-day lifetime) |
| `token_type` | string | Always `"bearer"` |
| `password_strength` | object or null | Password strength assessment (only on registration) |

### PasswordStrength

Included in `TokenResponse.password_strength` on registration.

| Field | Type | Description |
|-------|------|-------------|
| `strength` | string | One of: `"weak"`, `"moderate"`, `"strong"` |
| `score` | integer | Numeric score from 0 to 6 |
| `feedback` | array of strings | Suggestions for improvement (empty if strong) |

### UserResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | User's unique identifier |
| `email` | string | User's email address |
| `created_at` | datetime | Account creation timestamp (ISO 8601) |

### BookSummary

| Field | Type | Description |
|-------|------|-------------|
| `google_book_id` | string | Google Books volume identifier |
| `title` | string | Book title |
| `authors` | array of strings | List of author names |
| `thumbnail` | string | URL to the book's cover thumbnail |
| `categories` | array of strings | Genre/category labels |
| `average_rating` | float or null | Average user rating from Google Books |
| `ratings_count` | integer or null | Total number of ratings |

### BookDetail

Extends BookSummary with additional fields.

| Field | Type | Description |
|-------|------|-------------|
| _(all BookSummary fields)_ | | |
| `description` | string | Full book description or synopsis |
| `page_count` | integer or null | Total number of pages |
| `published_date` | string or null | Publication date |
| `publisher` | string or null | Publisher name |
| `preview_link` | string or null | URL to preview the book on Google Books |
| `info_link` | string or null | URL to the book's Google Play/Books page |

### LikedBookResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Liked book record ID |
| `google_book_id` | string | Google Books volume identifier |
| `title` | string | Book title |
| `authors` | string | Author names (as stored string) |
| `thumbnail` | string | Cover thumbnail URL |
| `liked_at` | datetime | Timestamp when the book was liked (ISO 8601) |

### CategoryResponse

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Category's unique identifier |
| `name` | string | Display name (e.g., "Sci-Fi") |
| `google_category_key` | string | Key used for Google Books API queries (e.g., "science+fiction") |

### MessageResponse

| Field | Type | Description |
|-------|------|-------------|
| `message` | string | Human-readable status message |

### PaginatedBooks

| Field | Type | Description |
|-------|------|-------------|
| `books` | array of BookSummary | List of books for the current page |
| `total` | integer | Total number of matching books |
| `page` | integer | Current page number |
| `page_size` | integer | Number of books per page |

### PaginatedLikedBooks

| Field | Type | Description |
|-------|------|-------------|
| `books` | array of LikedBookResponse | List of liked books for the current page |
| `total` | integer | Total number of liked books |
| `page` | integer | Current page number |
| `page_size` | integer | Number of books per page |

---

## Password Requirements

When registering a new account, the password must satisfy the following rules:

- Minimum 8 characters, maximum 128 characters
- Must contain at least one uppercase letter (A-Z)
- Must contain at least one lowercase letter (a-z)
- Must contain at least one digit (0-9)
- Must not be a commonly used password (e.g., "password1", "admin123", "qwerty123")

After successful registration, a password strength assessment is returned with a score from 0 to 6:

| Score Range | Strength |
|-------------|----------|
| 0-2 | weak |
| 3-4 | moderate |
| 5-6 | strong |

The scoring criteria are:

- +1 point: 8 or more characters
- +1 point: 12 or more characters
- +1 point: contains an uppercase letter
- +1 point: contains a lowercase letter
- +1 point: contains a digit
- +1 point: contains a special character (!@#$%^&*(),.?":{}|<>)

---

## Interactive Documentation

In non-production environments, FastAPI's built-in interactive documentation is available:

- **Swagger UI:** `http://localhost:8000/docs`
- **ReDoc:** `http://localhost:8000/redoc`

These are disabled when the `ENVIRONMENT` variable is set to `"production"`.

---

## Request Headers

All requests should include appropriate headers:

| Header | Required | Description |
|--------|----------|-------------|
| `Content-Type: application/json` | For POST/PUT/DELETE with body | Indicates JSON request body |
| `Authorization: Bearer <token>` | For protected endpoints | JWT access token |
| `X-Request-ID` | Optional | Client-provided request correlation ID; if omitted, the server generates one and returns it in the response |

The server includes the following headers in every response:

| Header | Value |
|--------|-------|
| `X-Request-ID` | Unique request identifier (for log correlation) |
| `X-Content-Type-Options` | `nosniff` |
| `X-Frame-Options` | `DENY` |
| `X-XSS-Protection` | `1; mode=block` |
| `Strict-Transport-Security` | `max-age=31536000; includeSubDomains` |
| `Content-Security-Policy` | `default-src 'self'` |
| `Referrer-Policy` | `strict-origin-when-cross-origin` |
| `Permissions-Policy` | `camera=(), microphone=(), geolocation=()` |
