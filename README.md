# BookSwipe

**Tinder for Books** -- Swipe right to like, swipe left to skip. Discover your next read.

## Overview

BookSwipe is a full-stack book discovery application that lets users browse books
with a card-swiping interface, save favorites, and explore by category. The backend
serves book data from the Google Books API and manages user accounts, while the
Flutter frontend provides a responsive, cross-platform experience.

## Architecture

```
 Flutter App                   FastAPI Backend            External
+-----------+    HTTP/JSON    +----------------+    HTTPS   +---------------+
|  Riverpod |  <---------->  |  Routers       | <--------> | Google Books  |
|  Screens  |                |  Services      |            | API           |
|  Widgets  |                |  SQLAlchemy ORM|            +---------------+
+-----------+                +--------+-------+
                                      |
                                      v
                              +-------+--------+
                              | SQLite (dev)   |
                              | PostgreSQL (prod)|
                              +----------------+
```

For detailed architecture documentation, see [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Tech Stack

| Layer      | Technology                                         |
|------------|----------------------------------------------------|
| Frontend   | Flutter 3.10+, Dart, Riverpod, Dio, GoRouter       |
| Backend    | Python 3.12+, FastAPI, SQLAlchemy 2.0, Pydantic v2 |
| Database   | SQLite (dev), PostgreSQL (prod)                    |
| Book Data  | Google Books API                                   |
| Auth       | JWT (access + refresh tokens), bcrypt               |
| CI/CD      | GitHub Actions                                     |

## Features

- Swipe through books with a card-based discovery UI
- Filter by 14 categories (Fiction, Romance, Sci-Fi, Thriller, etc.)
- Save liked books to a personal reading list
- Detailed book view with description, page count, reviews, cover image
- User authentication with JWT token rotation
- Cross-platform: Android, iOS, Web, Desktop
- Offline detection with connectivity banner
- Retry with exponential backoff for transient network errors
- Structured error handling with error codes
- Request ID tracking across all API calls

## Project Structure

```
bookswipe/
├── backend/               # FastAPI server
│   ├── app/
│   │   ├── main.py        # App entry, middleware, exception handlers
│   │   ├── config.py      # Settings (env vars)
│   │   ├── database.py    # SQLAlchemy engine/session
│   │   ├── models.py      # ORM models
│   │   ├── schemas.py     # Pydantic request/response schemas
│   │   ├── exceptions.py  # Custom exception hierarchy
│   │   ├── routers/       # auth, books, categories endpoints
│   │   └── services/      # auth (JWT), google_books (API client)
│   ├── tests/             # pytest test suite
│   └── alembic/           # Database migrations
├── frontend/              # Flutter app
│   ├── lib/
│   │   ├── main.dart      # Entry point
│   │   ├── app.dart       # Router, AppShell, offline banner
│   │   ├── models/        # Book, User, BookCategory
│   │   ├── providers/     # Riverpod state management
│   │   ├── screens/       # Home, Login, Register, Categories, etc.
│   │   ├── services/      # API client, auth storage
│   │   ├── widgets/       # BookCard, ErrorView, OfflineBanner, etc.
│   │   └── utils/         # Validators, error handler, snackbar utils
│   └── test/              # Flutter test suite
├── docs/                  # Documentation
│   ├── API.md             # API reference with all endpoints
│   └── ARCHITECTURE.md    # Architecture and design decisions
├── docker-compose.yml     # Development environment
├── CONTRIBUTING.md        # Contribution guidelines
└── SECURITY.md            # Security policy
```

## Getting Started

### Prerequisites

- Python 3.12+ and [uv](https://docs.astral.sh/uv/) (or pip)
- Flutter 3.10+ (Dart SDK)
- Docker and Docker Compose (optional)

### Backend Setup

```bash
cd backend
cp .env.example .env          # Configure environment variables
uv venv .venv                 # Create virtual environment
source .venv/bin/activate
uv pip install -r requirements.txt -r requirements-dev.txt
uvicorn app.main:app --reload # Start server on http://localhost:8000
```

### Frontend Setup

```bash
cd frontend
flutter pub get
flutter run                   # Launch on connected device/emulator
```

### Docker (both services)

```bash
docker compose up
# Backend:  http://localhost:8000
# Frontend: http://localhost:8080
```

### Environment Variables

Copy `.env.development.example` to `.env` for development defaults. Key variables:

| Variable                    | Description                       | Default              |
|-----------------------------|-----------------------------------|----------------------|
| `SECRET_KEY`                | JWT signing key                   | (change in prod!)    |
| `DATABASE_URL`              | Database connection string        | `sqlite:///./bookswipe.db` |
| `GOOGLE_BOOKS_API_KEY`      | Google Books API key (optional)   | (empty)              |
| `API_RATE_LIMIT`            | Global rate limit                 | `30/minute`          |
| `AUTH_RATE_LIMIT`           | Auth endpoint rate limit          | `5/minute`           |
| `CORS_ORIGINS`              | Allowed CORS origins              | `["*"]`              |

See `.env.development.example` and `.env.production.example` for full reference.

## API Overview

All endpoints return structured JSON errors:

```json
{"error": {"code": "ERROR_CODE", "message": "Human-readable message", "details": null}}
```

| Group      | Endpoint                          | Method | Auth     |
|------------|-----------------------------------|--------|----------|
| Health     | `/health`                         | GET    | No       |
| Auth       | `/api/auth/register`              | POST   | No       |
| Auth       | `/api/auth/login`                 | POST   | No       |
| Auth       | `/api/auth/logout`                | POST   | Optional |
| Auth       | `/api/auth/refresh`               | POST   | No       |
| Auth       | `/api/auth/me`                    | GET    | Yes      |
| Auth       | `/api/auth/me`                    | DELETE | Yes      |
| Books      | `/api/books/discover`             | GET    | Optional |
| Books      | `/api/books/{book_id}`            | GET    | Optional |
| Books      | `/api/books/like`                 | POST   | Yes      |
| Books      | `/api/books/skip`                 | POST   | Yes      |
| Books      | `/api/books/liked`                | GET    | Yes      |
| Books      | `/api/books/liked/{google_book_id}` | DELETE | Yes   |
| Categories | `/api/categories`                 | GET    | No       |
| Categories | `/api/categories/{id}`            | GET    | No       |

Full API reference: [docs/API.md](docs/API.md)

## Testing

```bash
# Backend
cd backend
source .venv/bin/activate
python -m pytest tests/ -q

# Frontend
cd frontend
flutter test
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, coding standards, and PR process.

## Security

See [SECURITY.md](SECURITY.md) for the security policy and vulnerability reporting process.

## License

This project is for educational purposes.
