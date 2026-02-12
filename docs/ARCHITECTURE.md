# BookSwipe Architecture

> "Tinder for Books" -- swipe right to like, left to skip, powered by Google Books.

This document describes the end-to-end architecture of BookSwipe, covering the
backend API server, the Flutter mobile client, data flow, external integrations,
security posture, and key design decisions.

---

## Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Diagram](#architecture-diagram)
3. [Backend (Python / FastAPI)](#backend-python--fastapi)
4. [Frontend (Flutter / Dart)](#frontend-flutter--dart)
5. [Data Flow](#data-flow)
6. [API Endpoints](#api-endpoints)
7. [Database Schema](#database-schema)
8. [Authentication and Security](#authentication-and-security)
9. [Error Handling](#error-handling)
10. [Rate Limiting](#rate-limiting)
11. [Caching Strategy](#caching-strategy)
12. [Design Decisions](#design-decisions)
13. [Project Structure](#project-structure)

---

## System Overview

BookSwipe is a two-tier application consisting of:

- A **FastAPI backend** that serves a REST API, manages user accounts, persists
  book interactions (likes, skips), and proxies the Google Books API with
  caching and rate limiting.
- A **Flutter mobile client** that presents a card-swiping interface for book
  discovery, manages authentication state with Riverpod, and communicates with
  the backend over HTTP via Dio.

The backend uses SQLite in development and PostgreSQL in production. Book
metadata is sourced from the Google Books API and cached server-side with a
one-hour TTL.

---

## Architecture Diagram

```
+---------------------------------------------------------------------+
|                        FLUTTER CLIENT                                |
|                                                                      |
|  +------------+   +----------------+   +---------------------------+ |
|  | GoRouter   |   | Riverpod       |   | Screens                   | |
|  | (routing)  |   | Providers      |   |  HomeScreen (CardSwiper)  | |
|  |            |   |  AuthNotifier   |   |  CategoriesScreen         | |
|  | /          |   |  DiscoverBooks  |   |  LikedBooksScreen         | |
|  | /login     |   |  LikedBooks    |   |  ProfileScreen            | |
|  | /register  |   |  bookDetail    |   |  BookDetailScreen         | |
|  | /categories|   |  categories    |   |  LoginScreen              | |
|  | /liked     |   +-------+--------+   |  RegisterScreen           | |
|  | /profile   |           |             +---------------------------+ |
|  | /book/:id  |           v                                          |
|  +------------+   +----------------+   +---------------------------+ |
|                   | ApiService     |   | AuthService               | |
|                   | (Dio HTTP)     |   | (FlutterSecureStorage)    | |
|                   |  Token refresh |   |  JWT persistence          | |
|                   |  Retry backoff |   |  Encrypted keychain       | |
|                   +-------+--------+   +---------------------------+ |
+-------------------|-------|-----------------------------------------+
                    |       |
                    | HTTPS |
                    v       v
+---------------------------------------------------------------------+
|                        FASTAPI BACKEND                               |
|                                                                      |
|  +--------------------------------------------------------------+   |
|  |                      Middleware Stack                          |   |
|  |  Request ID -> Security Headers -> CORS -> SlowAPI Rate Limit |   |
|  +--------------------------------------------------------------+   |
|                              |                                       |
|  +--------------------------------------------------------------+   |
|  |                    Exception Handlers                          |   |
|  |  BookSwipeException | RequestValidationError | catch-all 500   |   |
|  +--------------------------------------------------------------+   |
|                              |                                       |
|  +------------------+  +-----------------+  +-------------------+   |
|  | /api/auth        |  | /api/books      |  | /api/categories   |   |
|  |  POST /register  |  |  GET /discover  |  |  GET /            |   |
|  |  POST /login     |  |  GET /liked     |  |  GET /:id         |   |
|  |  POST /logout    |  |  GET /:book_id  |  +-------------------+   |
|  |  POST /refresh   |  |  POST /like     |                          |
|  |  GET  /me        |  |  POST /skip     |                          |
|  |  DELETE /me      |  |  DELETE /liked/* |                          |
|  +--------+---------+  +--------+--------+                          |
|           |                      |                                   |
|  +--------+---------+  +--------+--------+                          |
|  | Auth Service      |  | Google Books    |                          |
|  |  JWT create/      |  | Service         |                          |
|  |  validate         |  |  TTL cache      |                          |
|  |  bcrypt hash      |  |  Per-user rate  |                          |
|  |  Token blacklist  |  |  limit          |                          |
|  +--------+---------+  +--------+--------+                          |
|           |                      |                                   |
+-----------|----------------------|-----------------------------------+
            |                      |
            v                      v
  +-------------------+   +-------------------+
  | SQLite / Postgres |   | Google Books API  |
  |  users            |   | googleapis.com    |
  |  liked_books      |   | /books/v1/volumes |
  |  skipped_books    |   +-------------------+
  |  blacklisted_tkns |
  |  categories       |
  +-------------------+
```

---

## Backend (Python / FastAPI)

### Entry Point and Middleware

**File:** `backend/app/main.py`

The FastAPI application is initialized with a lifespan handler that creates
database tables and seeds default categories on startup. The middleware stack
processes every request in the following order:

1. **Request ID middleware** -- Generates a UUID per request (or accepts
   `X-Request-ID` from the client), attaches it to `request.state`, includes it
   in the response header, and logs it alongside method, path, status code, and
   duration in milliseconds.
2. **Security headers middleware** -- Adds `X-Content-Type-Options: nosniff`,
   `X-Frame-Options: DENY`, `X-XSS-Protection`, `Strict-Transport-Security`
   (HSTS with 1-year max-age), `Content-Security-Policy: default-src 'self'`,
   `Referrer-Policy`, and `Permissions-Policy`.
3. **CORS middleware** -- Configured via `settings.cors_origins` (defaults to
   `["*"]` in development).
4. **SlowAPI rate limiting middleware** -- Enforces global per-IP rate limits.

Structured JSON logging is configured via `python-json-logger` with a
`_RedactingFilter` that scrubs sensitive fields (password, secret_key,
access_token, refresh_token, authorization) from log messages.

### Configuration

**File:** `backend/app/config.py`

All configuration is managed through Pydantic Settings (`BaseSettings`),
loading values from environment variables or a `.env` file. Key settings:

| Setting                       | Default                          | Description                              |
|-------------------------------|----------------------------------|------------------------------------------|
| `database_url`                | `sqlite:///./bookswipe.db`       | SQLAlchemy connection string             |
| `secret_key`                  | (dev placeholder)                | JWT signing key (must change in prod)    |
| `algorithm`                   | `HS256`                          | JWT signing algorithm                    |
| `access_token_expire_minutes` | `15`                             | Access token lifetime                    |
| `refresh_token_expire_days`   | `7`                              | Refresh token lifetime                   |
| `jwt_issuer`                  | `bookswipe-api`                  | JWT `iss` claim                          |
| `jwt_audience`                | `bookswipe-client`               | JWT `aud` claim                          |
| `google_books_cache_ttl`      | `3600`                           | Cache TTL in seconds (1 hour)            |
| `rate_limit_requests`         | `60`                             | Google Books per-user requests per window|
| `rate_limit_window`           | `60`                             | Rate limit window in seconds             |
| `auth_rate_limit`             | `5/minute`                       | SlowAPI limit for auth endpoints         |
| `api_rate_limit`              | `30/minute`                      | SlowAPI default limit for all endpoints  |

A runtime check raises `RuntimeError` if the default secret key is used in
a production environment.

### Database Layer

**File:** `backend/app/database.py`

SQLAlchemy 2.0 with the `DeclarativeBase` pattern. The engine conditionally
sets `check_same_thread=False` for SQLite. An event listener enables WAL
journal mode and foreign key enforcement for SQLite connections.

Session management uses a `get_db()` dependency generator that yields a
session and ensures cleanup in a `finally` block.

### ORM Models

**File:** `backend/app/models.py`

| Model              | Table                | Purpose                                              |
|--------------------|----------------------|------------------------------------------------------|
| `User`             | `users`              | Account with email, hashed password, soft-delete flag |
| `BlacklistedToken` | `blacklisted_tokens` | Revoked JWT identifiers (JTI)                        |
| `LikedBook`        | `liked_books`        | User-book like relationship with metadata snapshot    |
| `SkippedBook`      | `skipped_books`      | User-book skip relationship                          |
| `Category`         | `categories`         | Book categories mapping to Google Books subjects      |

All models use SQLAlchemy `Mapped` typed annotations. `LikedBook` and
`SkippedBook` enforce uniqueness via composite unique constraints on
`(user_id, google_book_id)` and include indexed timestamp columns for
efficient ordering. Foreign keys use `CASCADE` on delete.

The `User` model supports GDPR-compliant soft deletion via `is_active` and
`deleted_at` fields.

14 seed categories are auto-populated on first startup if the categories table
is empty (Fiction, Romance, Mystery, Sci-Fi, Fantasy, Thriller, Biography,
History, Self-Help, Science, Business, Poetry, Horror, Comics).

### Request/Response Schemas

**File:** `backend/app/schemas.py`

Pydantic v2 models with strict validation:

- **`UserRegister`** -- Email normalization, password strength validation
  (requires uppercase, lowercase, digit; rejects common passwords from a
  blocklist of 40 entries).
- **`BookAction`** -- XSS sanitization via `_sanitize_string()` which strips
  `<script>` tags and all HTML tags from title and authors fields.
- **`PaginatedBooks` / `PaginatedLikedBooks`** -- Standard pagination wrappers
  with `books`, `total`, `page`, `page_size`.
- **`TokenResponse`** -- Returns `access_token`, `refresh_token`, `token_type`,
  and optional `password_strength` feedback on registration.

### Routers

**`backend/app/routers/auth.py`** -- Registration, login, logout, token refresh,
profile retrieval, and account deletion. All auth-mutating endpoints are rate
limited to 5 requests per minute per IP. Token refresh implements rotation:
the old refresh token is blacklisted and a new pair is issued.

**`backend/app/routers/books.py`** -- Book discovery (proxied from Google Books
with exclusion of previously liked/skipped books), liked books listing, book
detail, like, skip, and unlike operations. Discovery supports optional
authentication for personalized exclusion filtering.

**`backend/app/routers/categories.py`** -- Lists all categories or retrieves a
single category by ID.

### Services

**`backend/app/services/auth.py`** -- JWT creation and validation using
`python-jose` with `bcrypt` password hashing via `passlib`. Tokens include
`sub` (user ID), `exp`, `type` (access/refresh), `iss`, `aud`, and `jti`
(unique token identifier for blacklisting). Provides two FastAPI dependencies:
`get_current_user` (requires authentication) and `get_optional_user` (returns
`None` for unauthenticated requests).

**`backend/app/services/google_books.py`** -- Async HTTP client using `httpx`
with a 10-second timeout. Features:
- **TTL cache** (`cachetools.TTLCache`, maxsize=1024, TTL=1hr) keyed by
  search parameters or book ID.
- **Per-user rate limiting** using a sliding window algorithm (default
  60 requests per 60 seconds per user).
- **Error handling** for timeouts, connection errors, HTTP 429 (Google rate
  limit), and non-200 responses, all mapped to typed exceptions.
- Thumbnail URLs are upgraded from `http://` to `https://`.

---

## Frontend (Flutter / Dart)

### Entry Point

**File:** `frontend/lib/main.dart`

Initializes Flutter bindings and wraps the app in Riverpod's `ProviderScope`
for dependency injection.

### Routing and Shell

**File:** `frontend/lib/app.dart`

Uses `go_router` with a `ShellRoute` pattern:

- **Shell routes** (rendered inside `AppShell` with `BottomNavigationBar`):
  `/` (Discover), `/categories`, `/liked`, `/profile`
- **Full-screen routes** (outside the shell): `/book/:id`, `/login`, `/register`

The `AppShell` widget includes an `OfflineBanner` at the top of every shell
page, displaying connectivity status. The `NavigationBar` has four
destinations: Discover, Categories, Liked, and Profile.

### State Management (Riverpod)

**File:** `frontend/lib/providers/providers.dart`

| Provider                    | Type                        | Description                                    |
|-----------------------------|-----------------------------|------------------------------------------------|
| `apiServiceProvider`        | `Provider<ApiService>`      | Singleton HTTP client                          |
| `authServiceProvider`       | `Provider<AuthService>`     | Singleton secure storage wrapper               |
| `authStateProvider`         | `StateNotifierProvider`     | Auth state: loading, authenticated, or null    |
| `selectedCategoryProvider`  | `StateProvider<String?>`    | Currently selected book category               |
| `categoriesProvider`        | `FutureProvider`            | Fetches categories from API, falls back to defaults |
| `discoverBooksProvider`     | `AsyncNotifierProvider`     | Paginated book discovery with loadMore/refresh |
| `likedBooksProvider`        | `AsyncNotifierProvider`     | Liked books list with like/unlike mutations     |
| `bookDetailProvider`        | `FutureProvider.family`     | Fetches single book detail by ID               |

**`AuthNotifier`** -- On construction, checks `FlutterSecureStorage` for a
stored JWT. If found, sets the token on the Dio client and validates it by
fetching the user profile. Handles login, register, and logout flows. Sets up
a callback on `ApiService.onTokenRefreshNeeded` to persist rotated tokens.

**`DiscoverBooksNotifier`** -- Watches `selectedCategoryProvider` and
re-fetches when the category changes. Supports `loadMore()` with page
increment (reverts on failure to preserve current data) and `refresh()`.
`removeBook()` optimistically removes a book from the local list after a
swipe action.

**`LikedBooksNotifier`** -- Watches `authStateProvider` and returns an empty
list if unauthenticated. Supports `likeBook()` with optimistic local insert
and `unlikeBook()` with optimistic local removal.

All notifiers use `AsyncValue` (loading/data/error) to drive UI state,
and format errors via `ApiService.formatError()` for user-friendly messages.

### HTTP Client

**File:** `frontend/lib/services/api_service.dart`

`ApiService` wraps Dio with two interceptors:

1. **Retry interceptor** (`_RetryInterceptor`) -- Retries transient network
   errors (connection timeout, send timeout, receive timeout, connection error)
   up to 3 times with exponential backoff (`500ms * 2^attempt`). Does not
   retry 4xx/5xx HTTP errors.

2. **Token refresh interceptor** -- On a 401 response, attempts to refresh the
   access token using the stored refresh token via `POST /api/auth/refresh`.
   On success, updates the auth header and retries the original request. On
   failure, propagates the original 401 error.

**`formatError()`** -- Static method that extracts user-friendly messages from
the backend's structured error format (`{"error": {"message": ...}}`), the
legacy `{"detail": ...}` format, or falls back to status-code-based messages.

### Secure Storage

**File:** `frontend/lib/services/auth_service.dart`

Wraps `FlutterSecureStorage` with platform-specific configuration:
- **Android:** Uses `EncryptedSharedPreferences`.
- **iOS:** Uses Keychain with `first_unlock_this_device` accessibility.

Stores the serialized `User` object (including tokens) under the key
`bookswipe_user`.

### Models

**`frontend/lib/models/book.dart`** -- Dual-format JSON parsing. The `fromJson`
factory detects whether the input is Google Books API format (has `volumeInfo`
key) or backend flat format (has `google_book_id`). Handles `authors` as either
a `List<String>` (discovery endpoint) or a comma-separated `String` (liked
books endpoint). Upgrades thumbnail URLs from HTTP to HTTPS.

**`frontend/lib/models/user.dart`** -- Immutable user with `id`, `email`,
`token`, and `refreshToken`. Includes `copyWithTokens()` for token rotation.

**`frontend/lib/models/category.dart`** -- `BookCategory` with `name`, `key`,
`icon`, and `color`. Includes a static `defaults` list of 14 hardcoded
categories with Material icons and brand colors, used as a fallback if the
API is unreachable.

### Screens

| Screen               | Route         | Description                                          |
|----------------------|---------------|------------------------------------------------------|
| `HomeScreen`         | `/`           | Card swiper for book discovery (swipe right/left)    |
| `CategoriesScreen`   | `/categories` | Grid of book categories to filter discovery          |
| `LikedBooksScreen`   | `/liked`      | List of liked books with unlike capability            |
| `ProfileScreen`      | `/profile`    | User info and logout                                 |
| `BookDetailScreen`   | `/book/:id`   | Full book details (description, metadata, links)     |
| `LoginScreen`        | `/login`      | Email/password login form                            |
| `RegisterScreen`     | `/register`   | Email/password registration form                     |

### Widgets

| Widget             | Description                                             |
|--------------------|---------------------------------------------------------|
| `BookCard`         | Card display for swipe interface with cover and metadata |
| `BookListTile`     | Compact list item for liked books list                   |
| `ErrorView`        | Standardized error display with retry action             |
| `LoadingIndicator` | Consistent loading spinner                               |
| `OfflineBanner`    | Connectivity status banner shown in AppShell              |
| `SwipeOverlay`     | Visual feedback overlay during swipe gestures             |

### Utilities

| File                | Description                                             |
|---------------------|---------------------------------------------------------|
| `validators.dart`   | Form field validators (email, password)                  |
| `error_handler.dart`| Centralized error handling utilities                     |
| `snackbar_utils.dart`| Snackbar display helpers for success/error feedback    |

---

## Data Flow

### 1. App Startup and Authentication Check

```
App Launch
  |
  v
ProviderScope initializes
  |
  v
AuthNotifier constructor
  |
  v
FlutterSecureStorage.read("bookswipe_user")
  |
  +-- No stored user --> state = AsyncValue.data(null) --> Show LoginScreen
  |
  +-- Stored user found
        |
        v
      Set Dio auth header (Bearer token)
      Set refresh token on ApiService
        |
        v
      GET /api/auth/me (validate token)
        |
        +-- Success --> state = AsyncValue.data(user) --> Show HomeScreen
        |
        +-- 401 --> Dio interceptor attempts refresh
                      |
                      +-- Refresh success --> Retry /me --> Show HomeScreen
                      |
                      +-- Refresh fail --> state = AsyncValue.data(user)
                                           (stale user, will refresh on next call)
```

### 2. Book Discovery

```
User opens Discover tab (or selects a category)
  |
  v
DiscoverBooksNotifier.build() watches selectedCategoryProvider
  |
  v
ApiService.discoverBooks(category, page)
  |
  v
GET /api/books/discover?category=fiction&page=1
  |
  v
Backend: get_optional_user() checks auth
  |
  +-- Authenticated: query liked_books + skipped_books for user
  |                   to build exclude_ids set
  +-- Unauthenticated: no exclusions
  |
  v
google_books.search_books(category, page, page_size, exclude_ids, user_id)
  |
  v
Check per-user rate limit (sliding window: 60 req / 60 sec)
  |
  v
Check TTL cache (key = "search:{category}:{startIndex}:{pageSize}")
  |
  +-- Cache hit --> Return cached results (filter out exclude_ids)
  |
  +-- Cache miss --> GET googleapis.com/books/v1/volumes
                       ?q=subject:{category}&startIndex=0&maxResults=20
                       &printType=books&orderBy=relevance&langRestrict=en
                     |
                     v
                   Parse response, store in cache, return results
  |
  v
Flutter: Book.fromJson() (backend flat format) for each item
  |
  v
HomeScreen renders CardSwiper with book cards
```

### 3. Swipe Right (Like a Book)

```
User swipes right on a BookCard
  |
  v
DiscoverBooksNotifier.removeBook(bookId)  <-- optimistic UI removal
LikedBooksNotifier.likeBook(book)         <-- optimistic local insert
  |
  v
ApiService.likeBook(book)
  |
  v
POST /api/books/like
  Body: { google_book_id, title, authors, thumbnail }
  |
  v
Backend: Validate auth, sanitize input (strip HTML/script tags)
  |
  v
Check unique constraint (user_id, google_book_id)
  |
  +-- Already liked --> 409 ConflictError
  +-- New --> INSERT into liked_books --> 201 Created
```

### 4. Token Refresh Flow

```
Any API call returns 401
  |
  v
Dio token refresh interceptor activates
  |
  v
POST /api/auth/refresh  { refresh_token: "..." }
  |
  v
Backend: decode_token(refresh_token, expected_type="refresh")
  |
  v
Validate: not expired, correct issuer/audience, not blacklisted
  |
  v
Blacklist old refresh token (by JTI)
Issue new access_token + refresh_token pair (token rotation)
  |
  v
Flutter: Update Dio auth header with new access token
         Call onTokenRefreshNeeded callback
         AuthService.storeUser() with new tokens
         Retry original failed request with new token
```

---

## API Endpoints

### Authentication (`/api/auth`)

| Method | Path             | Auth     | Rate Limit | Description                     |
|--------|------------------|----------|------------|---------------------------------|
| POST   | `/register`      | No       | 5/min      | Create account, return tokens   |
| POST   | `/login`         | No       | 5/min      | Authenticate, return tokens     |
| POST   | `/logout`        | Optional | 30/min     | Blacklist current access token  |
| POST   | `/refresh`       | No       | 5/min      | Rotate tokens                   |
| GET    | `/me`            | Required | 30/min     | Get current user profile        |
| DELETE | `/me`            | Required | 30/min     | Soft-delete account (GDPR)      |

### Books (`/api/books`)

| Method | Path                    | Auth     | Rate Limit | Description                          |
|--------|-------------------------|----------|------------|--------------------------------------|
| GET    | `/discover`             | Optional | 30/min     | Paginated discovery, excludes seen   |
| GET    | `/liked`                | Required | 30/min     | Paginated liked books                |
| GET    | `/{book_id}`            | Optional | 30/min     | Single book detail from Google Books |
| POST   | `/like`                 | Required | 30/min     | Like a book                          |
| POST   | `/skip`                 | Required | 30/min     | Skip a book                          |
| DELETE | `/liked/{google_book_id}` | Required | 30/min   | Remove from liked                    |

### Categories (`/api/categories`)

| Method | Path             | Auth | Rate Limit | Description             |
|--------|------------------|------|------------|-------------------------|
| GET    | `/`              | No   | 30/min     | List all categories     |
| GET    | `/{category_id}` | No   | 30/min     | Get category by ID      |

### Health Check

| Method | Path      | Description                              |
|--------|-----------|------------------------------------------|
| GET    | `/health` | Returns status, version, and environment |

### Error Response Format

All error responses follow a consistent structure:

```json
{
  "error": {
    "code": "AUTH_ERROR",
    "message": "Invalid email or password",
    "details": null
  }
}
```

---

## Database Schema

```
+-------------------+       +----------------------+       +-------------------+
|      users        |       |    liked_books       |       |   skipped_books   |
+-------------------+       +----------------------+       +-------------------+
| id          (PK)  |<--+   | id            (PK)  |   +-->| id          (PK)  |
| email      (UQ,IX)|   |   | user_id    (FK,IX)  |---+   | user_id  (FK,IX)  |
| hashed_password   |   +---| google_book_id (IX)  |       | google_book_id(IX)|
| is_active         |       | title                |       | skipped_at        |
| deleted_at        |       | authors              |       +-------------------+
| created_at        |       | thumbnail            |       UQ(user_id,
+-------------------+       | liked_at          (IX)|         google_book_id)
                             +----------------------+
                             UQ(user_id,
                               google_book_id)

+----------------------+       +-------------------+
| blacklisted_tokens   |       |    categories     |
+----------------------+       +-------------------+
| id            (PK)   |       | id          (PK)  |
| jti        (UQ, IX)  |       | name        (UQ)  |
| blacklisted_at       |       | google_category_key|
+----------------------+       +-------------------+
```

**Legend:** PK = Primary Key, FK = Foreign Key, UQ = Unique, IX = Index

---

## Authentication and Security

### JWT Token Design

- **Access tokens**: 15-minute expiry, type `access`.
- **Refresh tokens**: 7-day expiry, type `refresh`.
- Both include `iss` (issuer), `aud` (audience), and `jti` (unique identifier).
- Token validation checks: expiry, algorithm, issuer, audience, type, and
  blacklist status.
- Refresh endpoint implements **token rotation**: the old refresh token is
  blacklisted by JTI and a new pair is issued.

### Password Security

- Hashed with **bcrypt** via `passlib`.
- Registration enforces: minimum 8 characters, at least one uppercase letter,
  one lowercase letter, one digit.
- Rejects passwords from a blocklist of 40 common passwords.
- Returns password strength feedback (weak/moderate/strong with a score and
  suggestions) on registration.

### Input Sanitization

- Pydantic field validators enforce max lengths on all string fields.
- `BookAction` schema strips `<script>` tags and all HTML markup from
  `title` and `authors` fields via `_sanitize_string()`.
- Email addresses are normalized to lowercase and trimmed.

### Transport and Header Security

- **HSTS**: `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- **Frame protection**: `X-Frame-Options: DENY`
- **Content sniffing protection**: `X-Content-Type-Options: nosniff`
- **XSS protection**: `X-XSS-Protection: 1; mode=block`
- **CSP**: `Content-Security-Policy: default-src 'self'`
- **Referrer policy**: `strict-origin-when-cross-origin`
- **Permissions policy**: Camera, microphone, and geolocation disabled.

### Client-Side Security

- Tokens stored in **FlutterSecureStorage** (Android: EncryptedSharedPreferences;
  iOS: Keychain with `first_unlock_this_device` accessibility).
- SSL pinning service available (`frontend/lib/services/ssl_pinning.dart`).
- Biometric authentication service available
  (`frontend/lib/services/biometric_service.dart`).

### Sensitive Data Redaction

- The backend logging filter (`_RedactingFilter`) scrubs sensitive field names
  (`password`, `secret_key`, `access_token`, `refresh_token`, `authorization`)
  from all log output.
- Production environments disable Swagger UI (`/docs`) and ReDoc (`/redoc`).
- A runtime check prevents startup with the default secret key in production.

### GDPR Compliance

- Account deletion is a **soft delete**: `is_active` is set to `False` and
  `deleted_at` is recorded. Soft-deleted users cannot authenticate.
- All user queries filter on `is_active == True`.

---

## Error Handling

### Backend Exception Hierarchy

```
BookSwipeException (base)
  |-- AuthError            401   AUTH_ERROR            Authentication/authorization failure
  |-- NotFoundError        404   NOT_FOUND             Resource not found
  |-- ValidationError      422   VALIDATION_ERROR      Request data validation failure
  |-- ConflictError        409   CONFLICT              Duplicate resource
  |-- RateLimitError       429   RATE_LIMIT_EXCEEDED   Rate limit exceeded
  |-- ExternalAPIError     502   EXTERNAL_API_ERROR    Google Books API failure
```

All `BookSwipeException` subclasses are caught by the global exception handler
and returned as structured JSON with `code`, `message`, and optional `details`.

Pydantic `RequestValidationError` is caught separately and reformatted to
include per-field error details.

An unhandled exception catch-all logs the full traceback with the request ID
and returns a generic 500 response without leaking internal details.

### Frontend Error Handling

`ApiService.formatError()` maps backend errors to user-friendly strings:

1. Checks for structured `{"error": {"message": ...}}` format.
2. Falls back to legacy `{"detail": ...}` format.
3. Falls back to status-code-based messages (401, 403, 404, 422, 429, 5xx).
4. Falls back to `DioExceptionType`-based messages for network errors.

All Riverpod notifiers wrap API calls in try/catch and emit
`AsyncValue.error()` with formatted messages, allowing screens to render
the `ErrorView` widget with a retry action.

---

## Rate Limiting

BookSwipe implements rate limiting at two levels:

### Global API Rate Limiting (SlowAPI)

- **Default**: 30 requests per minute per IP address for all endpoints.
- **Auth endpoints** (`/register`, `/login`, `/refresh`): 5 requests per
  minute per IP address.
- Enforced by SlowAPI middleware using `get_remote_address` as the key function.
- Exceeding the limit returns HTTP 429.

### Per-User Google Books Rate Limiting

- **Limit**: 60 requests per 60-second sliding window per authenticated user.
- Implemented with an in-memory dictionary mapping `user_id` to a list of
  request timestamps.
- Timestamps outside the window are pruned on each check.
- Exceeding the limit raises `RateLimitError` (HTTP 429).
- Unauthenticated requests bypass per-user limits.

---

## Caching Strategy

### Server-Side Google Books Cache

- **Implementation**: `cachetools.TTLCache` (in-memory).
- **Max entries**: 1024.
- **TTL**: 1 hour (configurable via `GOOGLE_BOOKS_CACHE_TTL`).
- **Cache keys**:
  - Search: `search:{category}:{startIndex}:{pageSize}`
  - Book detail: `book:{book_id}`
- Cache is checked before making external HTTP calls.
- After-swipe exclusion filtering (`exclude_ids`) is applied post-cache, so
  cached results still serve users who have not interacted with those books.
- `clear_cache()` is available for cache invalidation.

### Client-Side Category Fallback

- The Flutter client fetches categories from `/api/categories` on startup.
- If the API call fails, it falls back to a hardcoded `BookCategory.defaults`
  list, ensuring the app remains functional offline.

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| **SQLite for dev, PostgreSQL for prod** | SQLAlchemy's `database_url` abstraction allows seamless switching. SQLite simplifies local development with zero setup. WAL mode and foreign keys are explicitly enabled for SQLite. |
| **JWT with access + refresh token rotation** | Short-lived access tokens (15 min) limit the damage window of a compromised token. Refresh token rotation with JTI blacklisting prevents replay attacks. |
| **TTL cache (1 hr) for Google Books API** | Reduces external API calls and latency. Book metadata changes infrequently, making a 1-hour TTL a good trade-off between freshness and efficiency. Max 1024 entries bounds memory usage. |
| **Per-user rate limiting for Google Books** | Prevents a single user from exhausting the Google Books API quota. The sliding window algorithm (60 req/min) is simple and effective for the expected user base. |
| **Global rate limiting with SlowAPI** | Protects against brute-force attacks on auth endpoints (5/min) and general API abuse (30/min). Per-IP keying is appropriate for a mobile app backend. |
| **Structured JSON error responses** | Every error returns `{error: {code, message, details}}`, giving the Flutter client a consistent contract for error handling. Error codes enable programmatic error handling; messages enable user-facing display. |
| **Request ID tracking** | UUID per request (or client-provided) enables end-to-end tracing across logs. Returned in `X-Request-ID` header for client-side correlation. |
| **Soft delete for GDPR** | User data is deactivated rather than destroyed, allowing a grace period for account recovery while immediately preventing authentication. All queries filter on `is_active`. |
| **Riverpod with AsyncValue** | `AsyncValue<T>` provides a type-safe union of loading, data, and error states, eliminating ad-hoc boolean flags and ensuring every screen handles all three states. |
| **Exponential backoff retry** | The Dio retry interceptor (500ms, 1s, 2s) handles transient network errors without overwhelming the server, and only retries timeout/connection errors (not 4xx/5xx). |
| **Dual JSON parsing in Book model** | The Book model handles both Google Books API format (`volumeInfo` nested) and backend flat format (`google_book_id` top-level), allowing the same model class to be used everywhere. |
| **Optimistic UI updates** | Like and skip operations update the local Riverpod state before the API call completes, providing instant visual feedback. Pagination failure reverts the page counter to preserve current data. |
| **GoRouter ShellRoute pattern** | Tab-based navigation within `AppShell` preserves the `BottomNavigationBar` across pages, while full-screen routes (login, book detail) render outside the shell. |
| **Sensitive log redaction** | The `_RedactingFilter` prevents accidental exposure of credentials in structured logs, which is critical for production log aggregation systems. |

---

## Project Structure

```
bookswipe/
|
+-- backend/
|   +-- app/
|   |   +-- __init__.py
|   |   +-- main.py              # FastAPI app, middleware, lifespan, exception handlers
|   |   +-- config.py            # Pydantic Settings (env-based configuration)
|   |   +-- database.py          # SQLAlchemy engine, session factory, Base
|   |   +-- models.py            # ORM models: User, BlacklistedToken, LikedBook, SkippedBook, Category
|   |   +-- schemas.py           # Pydantic request/response schemas with validation
|   |   +-- exceptions.py        # Custom exception hierarchy
|   |   +-- routers/
|   |   |   +-- __init__.py
|   |   |   +-- auth.py          # /api/auth endpoints
|   |   |   +-- books.py         # /api/books endpoints
|   |   |   +-- categories.py    # /api/categories endpoints
|   |   +-- services/
|   |       +-- __init__.py
|   |       +-- auth.py          # JWT, bcrypt, token blacklist, user dependencies
|   |       +-- google_books.py  # Google Books API client with cache and rate limiting
|   +-- alembic/                 # Database migrations
|   +-- tests/
|   +-- requirements.txt
|   +-- .env
|
+-- frontend/
|   +-- lib/
|   |   +-- main.dart            # App entry point with ProviderScope
|   |   +-- app.dart             # GoRouter, AppShell, BottomNavigationBar, OfflineBanner
|   |   +-- models/
|   |   |   +-- book.dart        # Book model with dual JSON parsing
|   |   |   +-- user.dart        # User model with token management
|   |   |   +-- category.dart    # BookCategory with defaults fallback
|   |   +-- providers/
|   |   |   +-- providers.dart   # All Riverpod providers and notifiers
|   |   +-- screens/
|   |   |   +-- home_screen.dart
|   |   |   +-- login_screen.dart
|   |   |   +-- register_screen.dart
|   |   |   +-- categories_screen.dart
|   |   |   +-- liked_books_screen.dart
|   |   |   +-- profile_screen.dart
|   |   |   +-- book_detail_screen.dart
|   |   +-- services/
|   |   |   +-- api_service.dart      # Dio HTTP client, token refresh, retry
|   |   |   +-- auth_service.dart     # FlutterSecureStorage wrapper
|   |   |   +-- biometric_service.dart# Biometric authentication
|   |   |   +-- ssl_pinning.dart      # SSL certificate pinning
|   |   +-- widgets/
|   |   |   +-- book_card.dart
|   |   |   +-- book_list_tile.dart
|   |   |   +-- error_view.dart
|   |   |   +-- loading_indicator.dart
|   |   |   +-- offline_banner.dart
|   |   |   +-- swipe_overlay.dart
|   |   +-- utils/
|   |   |   +-- validators.dart
|   |   |   +-- error_handler.dart
|   |   |   +-- snackbar_utils.dart
|   |   +-- theme/
|   |       +-- app_theme.dart        # Light and dark theme definitions
|   +-- test/
|   +-- pubspec.yaml
|
+-- docs/
    +-- ARCHITECTURE.md          # This file
```
