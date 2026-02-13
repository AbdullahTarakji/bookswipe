# BookSwipe Architecture

## Overview

BookSwipe is a full-stack book discovery application with a Flutter frontend and Python FastAPI backend. Users swipe through books (like a dating app), building a personal reading list. The system learns from swipe history to generate personalized recommendations.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                          Client Layer                               │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │  Android     │  │     iOS      │  │    Web (nginx + SPA)      │  │
│  │  Flutter App │  │  Flutter App │  │    Flutter Web Build      │  │
│  └──────┬──────┘  └──────┬───────┘  └─────────────┬─────────────┘  │
│         │                │                         │                │
│         └────────────────┼─────────────────────────┘                │
│                          │ HTTP / REST                              │
└──────────────────────────┼──────────────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────────────┐
│                       API Gateway Layer                             │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  Nginx (production only)                                     │   │
│  │  - TLS termination (upstream Cloudflare/ALB)                │   │
│  │  - Gzip compression                                         │   │
│  │  - Rate limiting (5/min auth, 30/min API)                   │   │
│  │  - Security headers (CSP, HSTS, X-Frame-Options)            │   │
│  └──────────────────────────┬───────────────────────────────────┘   │
│                              │                                      │
└──────────────────────────────┼──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│                      Application Layer                              │
│  ┌──────────────────────────────────────────────────────────────┐   │
│  │  FastAPI (gunicorn + uvicorn workers)                        │   │
│  │                                                              │   │
│  │  Middleware: Request ID → Security Headers → CORS → SlowAPI  │   │
│  │                                                              │   │
│  │  ┌────────────┐  ┌────────────┐  ┌────────────────────────┐ │   │
│  │  │  Routers   │  │  Services  │  │    Repositories        │ │   │
│  │  │  (7 files) │─▶│  (7 files) │─▶│    (6 files)           │ │   │
│  │  │  HTTP I/O  │  │  Logic     │  │    SQL queries         │ │   │
│  │  └────────────┘  └─────┬──────┘  └───────────┬────────────┘ │   │
│  │                        │                      │              │   │
│  │           ┌────────────┼──────────────────────┘              │   │
│  │           ▼            ▼                                     │   │
│  │  ┌──────────────┐  ┌──────────────┐                         │   │
│  │  │  External    │  │  Database    │                         │   │
│  │  │  APIs        │  │  (SQLAlchemy)│                         │   │
│  │  │  - Google    │  └──────────────┘                         │   │
│  │  │    Books     │                                           │   │
│  │  │  - Stripe    │  ┌──────────────┐                         │   │
│  │  │  - FCM       │  │  Background  │                         │   │
│  │  └──────────────┘  │  Workers     │                         │   │
│  │                     │  (arq)       │                         │   │
│  │                     └──────────────┘                         │   │
│  └──────────────────────────────────────────────────────────────┘   │
│                                                                     │
└─────────────────┬───────────────────────┬───────────────────────────┘
                  │                       │
┌─────────────────▼─────────┐  ┌─────────▼───────────────────────────┐
│     Data Layer            │  │     Cache Layer                     │
│  ┌─────────────────────┐  │  │  ┌─────────────────────────────┐   │
│  │  PostgreSQL 16      │  │  │  │  Redis 7                    │   │
│  │  11 tables          │  │  │  │  - API response cache       │   │
│  │  - users            │  │  │  │  - Rate limit counters      │   │
│  │  - liked_books      │  │  │  │  - Token blacklist          │   │
│  │  - skipped_books    │  │  │  │  - Session data             │   │
│  │  - categories       │  │  │  └─────────────────────────────┘   │
│  │  - swipe_events     │  │  │                                     │
│  │  - user_preferences │  │  └─────────────────────────────────────┘
│  │  - notifications    │  │
│  │  - device_tokens    │  │
│  │  - ...              │  │
│  └─────────────────────┘  │
│                            │
└────────────────────────────┘
```

## Backend Architecture

### Layer Responsibilities

**Routers** (`app/routers/`)
- Parse HTTP requests and format responses
- Define endpoint paths, methods, and status codes
- Delegate to services and repositories
- No direct database queries

| Router | Endpoints | Purpose |
|--------|-----------|---------|
| `auth.py` | `/api/auth/*` | Register, login, OAuth, token refresh, logout |
| `books.py` | `/api/books/*` | Discover, like, skip, liked list |
| `categories.py` | `/api/categories/*` | List and get categories |
| `recommendations.py` | `/api/recommendations/*` | Personalized book suggestions |
| `payments.py` | `/api/payments/*` | Stripe subscription management |
| `admin.py` | `/api/admin/*` | User management (ban, list, stats) |
| `notifications.py` | `/api/notifications/*` | FCM tokens, preferences, history |

**Services** (`app/services/`)
- Implement business logic (auth, recommendations, payments)
- Call external APIs (Google Books, Stripe, FCM)
- Raise custom exceptions from `app/exceptions.py`
- Stateless functions (no request/response awareness)

**Repositories** (`app/repositories/`)
- Encapsulate all SQLAlchemy database queries
- One repository per aggregate root (User, Book, Category, etc.)
- Accept a `Session` and return model instances
- No business logic or HTTP concerns

**Models** (`app/models.py`)
- SQLAlchemy ORM model definitions
- Table relationships, constraints, and indexes
- Seed data for categories (14 genres)

**Schemas** (`app/schemas.py`)
- Pydantic models for request validation and response serialization
- Input sanitization (HTML/script tag stripping)
- Password strength validation

### Exception Handling

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

Custom exceptions: `AuthError`, `NotFoundError`, `ValidationError`, `ExternalAPIError`.

### Middleware Stack (order matters)

1. **Request ID** -- UUID per request, timing, structured logging
2. **Security Headers** -- CSP, HSTS, X-Frame-Options, X-Content-Type-Options
3. **CORS** -- Configurable origins (`["*"]` in dev, restricted in prod)
4. **Rate Limiting** -- SlowAPI with Redis storage, in-memory fallback

### Authentication

- JWT-based with access tokens (15 min) and refresh tokens (7 days)
- Token rotation on refresh (old refresh token is blacklisted)
- Blacklist checked in Redis first, then DB fallback
- OAuth 2.0 for Google and Apple with automatic account linking by email
- Passwords hashed with bcrypt

### Recommendation Engine

Content-based filtering from swipe history:
1. Swipe events logged with genre/author/category metadata
2. `UserPreference` aggregates scores from liked vs. skipped actions
3. `RecommendationService` scores candidate books against preference profile
4. Cold start: falls back to popular books in preferred categories

## Database Schema

11 tables across 4 domains:

**Users & Auth:**
- `users` -- Accounts (email, OAuth, Stripe fields, ban/delete support)
- `blacklisted_tokens` -- JWT revocation by JTI

**Books & Discovery:**
- `liked_books` -- User liked books (unique per user+book)
- `skipped_books` -- User skipped books
- `categories` -- 14 book categories with Google Books mapping
- `daily_swipe_counts` -- Free tier swipe limits per day

**Recommendations:**
- `swipe_events` -- Every swipe action with book metadata
- `user_preferences` -- Aggregated taste profile (JSON scores)

**Notifications:**
- `device_tokens` -- FCM push tokens per device
- `notification_preferences` -- Per-user opt-in settings
- `notifications` -- Notification inbox/history

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
       │ HTTP (Dio)
       ▼
┌─────────────┐
│   Backend   │
│     API     │
└─────────────┘
```

### State Management (Riverpod)

| Provider | Purpose |
|----------|---------|
| `authStateProvider` | Authentication state (loading/user/null) |
| `categoriesProvider` | Book categories from API with local fallback |
| `discoverBooksProvider` | Paginated book discovery with error recovery |
| `likedBooksProvider` | User's liked books with optimistic updates |
| `bookDetailProvider` | Single book detail (parameterized by ID) |
| `selectedCategoryProvider` | Current category filter selection |

### Error Handling

- `ApiService` includes retry logic with exponential backoff (3 retries)
- All providers use `AsyncValue` for loading/data/error states
- `formatError()` converts `DioException` to user-friendly messages
- `ErrorView` widget provides consistent error display with retry

### Navigation

GoRouter with shell routes for bottom navigation and modal routes for auth and book detail screens.

## Infrastructure

### Docker Compose (Development)

```
docker-compose.yml
├── db        (postgres:16-alpine)     :5432
├── redis     (redis:7-alpine)         :6379
├── backend   (FastAPI + gunicorn)     :8000
└── frontend  (Flutter web + nginx)    :8080
```

### Docker Compose (Production)

```
docker-compose.prod.yml
├── db        (postgres:16-alpine)     internal
├── redis     (redis:7-alpine)         internal
├── backend   (FastAPI + gunicorn)     internal
├── nginx     (reverse proxy)          :80
└── backup    (pg_dump cron)           internal
```

### CI/CD Pipelines

| Workflow | Trigger | Steps |
|----------|---------|-------|
| `backend-ci.yml` | Push/PR to main on `backend/**` | Lint, test, coverage, Docker build |
| `frontend-ci.yml` | Push/PR to main on `frontend/**` | Analyze, test, Docker build |
| `deploy.yml` | Push to main | Test, build+push to ghcr.io, deploy staging |
| `release.yml` | Tag push (`v*`) | Test, build+push, changelog, GitHub Release |

## Data Flow: Book Discovery

1. User selects a category (or uses default "fiction")
2. `selectedCategoryProvider` updates
3. `discoverBooksProvider` rebuilds, calling `ApiService.discoverBooks()`
4. `ApiService` sends GET `/api/books/discover?category=fiction`
5. Backend router delegates to `google_books.search_books()`
6. Service checks Redis cache, then calls Google Books API
7. Repository provides excluded book IDs for authenticated users
8. Response is parsed into `BookSummary` schemas and returned
9. Flutter renders `BookCard` widgets for swiping

## Data Flow: Like a Book

1. User swipes right on a book card
2. `DiscoverBooksNotifier.removeBook()` removes it from the list
3. `LikedBooksNotifier.likeBook()` optimistically adds it to liked list
4. `ApiService.likeBook()` sends POST `/api/books/like`
5. Backend `BookRepository.create_liked_book()` persists to database
6. `SwipeEvent` is recorded for preference learning
7. On error, the liked books provider enters error state with message
