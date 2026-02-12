# BookSwipe Architecture

## Overview

BookSwipe is a full-stack application with a Flutter frontend and a Python FastAPI backend. The backend follows a clean layered architecture; the frontend uses Riverpod for state management with a service-based data layer.

## Backend Architecture

```
HTTP Request
    │
    ▼
┌──────────┐     ┌──────────┐     ┌──────────────┐     ┌──────────┐
│  Router   │────▶│ Service  │────▶│  Repository  │────▶│ Database │
│ (HTTP)    │     │ (Logic)  │     │  (Queries)   │     │ (SQLite/ │
│           │     │          │     │              │     │  Postgres)│
└──────────┘     └──────────┘     └──────────────┘     └──────────┘
    │                 │
    │                 ▼
    │           ┌──────────┐
    │           │ External │
    │           │  APIs    │
    │           │ (Google  │
    │           │  Books)  │
    │           └──────────┘
    ▼
┌──────────┐
│ Schemas  │  (Pydantic validation at API boundary)
└──────────┘
```

### Layer Responsibilities

**Routers** (`app/routers/`)
- Parse HTTP requests and format responses
- Define endpoint paths, methods, and status codes
- Delegate to services and repositories
- No direct database queries

**Services** (`app/services/`)
- Implement business logic (authentication, token management, external API calls)
- Raise custom exceptions from `app/exceptions.py`
- Stateless functions (no request/response awareness)

**Repositories** (`app/repositories/`)
- Encapsulate all SQLAlchemy database queries
- One repository per aggregate root (User, Book, Category)
- Accept a `Session` and return model instances
- No business logic or HTTP concerns

**Models** (`app/models.py`)
- SQLAlchemy ORM model definitions
- Table relationships, constraints, and indexes
- Seed data for categories

**Schemas** (`app/schemas.py`)
- Pydantic models for request validation and response serialization
- Input sanitization (HTML/script tag stripping)
- Password strength validation

**Exceptions** (`app/exceptions.py`)
- Custom exception hierarchy rooted at `BookSwipeException`
- Each exception carries a status code, error code, and message
- Global exception handler in `main.py` converts these to structured JSON

### Exception Handling Flow

```
Code raises AuthError("Invalid email or password")
    │
    ▼
Global exception handler (main.py)
    │
    ▼
JSON Response:
{
  "detail": "Invalid email or password",
  "error": {
    "code": "AUTH_ERROR",
    "message": "Invalid email or password",
    "details": null
  }
}
```

### Middleware Stack

1. **Request ID** -- Assigns UUID to each request, adds `X-Request-ID` header, logs timing
2. **Security Headers** -- Sets CSP, HSTS, X-Frame-Options, etc.
3. **CORS** -- Configurable cross-origin access
4. **Rate Limiting** -- SlowAPI-based per-IP rate limits on auth endpoints

### Authentication

- JWT-based with access tokens (15 min) and refresh tokens (7 days)
- Token rotation on refresh (old refresh token is blacklisted)
- OAuth 2.0 support for Google and Apple with automatic account linking by email
- Passwords hashed with bcrypt

## Frontend Architecture

```
┌─────────────┐
│   Screens   │  (UI layer)
│  & Widgets  │
└──────┬──────┘
       │ watch/read
       ▼
┌─────────────┐
│  Providers  │  (State management - Riverpod)
│  (Notifiers)│
└──────┬──────┘
       │ calls
       ▼
┌─────────────┐
│  Services   │  (API client, secure storage)
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐
│   Backend   │
│     API     │
└─────────────┘
```

### State Management

Uses **Riverpod** with these provider types:

| Provider | Purpose |
|----------|---------|
| `authStateProvider` | Authentication state (loading/user/null) |
| `categoriesProvider` | Book categories from API with local fallback |
| `discoverBooksProvider` | Paginated book discovery with error recovery |
| `likedBooksProvider` | User's liked books with optimistic updates |
| `bookDetailProvider` | Single book detail (parameterized by ID) |
| `selectedCategoryProvider` | Current category filter selection |

### Error Handling

- `ApiService` includes retry logic with exponential backoff for network errors (3 retries)
- All providers use `AsyncValue` for loading/data/error states
- `formatError()` converts `DioException` to user-friendly messages
- `ErrorView` widget provides consistent error display with retry button

### Navigation

GoRouter with shell routes for bottom navigation and modal routes for auth and book detail screens.

## Data Flow: Book Discovery

1. User selects a category (or uses default "fiction")
2. `selectedCategoryProvider` updates
3. `discoverBooksProvider` rebuilds, calling `ApiService.discoverBooks()`
4. `ApiService` sends GET `/api/books/discover?category=fiction`
5. Backend router delegates to `google_books.search_books()`
6. Service checks cache, then calls Google Books API
7. Repository provides excluded book IDs for authenticated users
8. Response is parsed into `BookSummary` schemas and returned
9. Flutter renders `BookCard` widgets for swiping

## Data Flow: Like a Book

1. User swipes right on a book card
2. `DiscoverBooksNotifier.removeBook()` removes it from the list
3. `LikedBooksNotifier.likeBook()` optimistically adds it to liked list
4. `ApiService.likeBook()` sends POST `/api/books/like`
5. Backend `BookRepository.create_liked_book()` persists to database
6. On error, the liked books provider enters error state with user-friendly message
