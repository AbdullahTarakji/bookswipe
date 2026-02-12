# BookSwipe

![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?logo=fastapi&logoColor=white)
![Flutter](https://img.shields.io/badge/Flutter-3.x-02569B?logo=flutter&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![Redis](https://img.shields.io/badge/Redis-7-DC382D?logo=redis&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-yellow)

**Tinder for Books** -- Swipe right to like, swipe left to skip. Discover your next read.

## Quick Start

```bash
# Clone and start everything
git clone https://github.com/AbdullahTarakji/bookswipe.git
cd bookswipe
docker compose up --build

# Backend API:  http://localhost:8000/docs
# Frontend:     http://localhost:8080
# Health check: http://localhost:8000/health
```

That's it. One command starts PostgreSQL, Redis, the FastAPI backend, and the Flutter web frontend.

### Seed Demo Data

```bash
# After services are running, populate demo users and sample data
docker compose exec backend python -m scripts.seed_demo
```

Demo accounts:

| Email | Password | Role |
|-------|----------|------|
| `admin@bookswipe.app` | `Admin123!` | Admin |
| `reader1@bookswipe.app` | `Reader123!` | User |
| `reader2@bookswipe.app` | `Reader123!` | User |

## Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                        Client (Browser/App)                    │
└──────────────────────────────┬─────────────────────────────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Flutter Web (:8080) │
                    │  nginx + SPA        │
                    └──────────┬──────────┘
                               │ HTTP
                    ┌──────────▼──────────┐
                    │  FastAPI    (:8000)  │
                    │  gunicorn + uvicorn  │
                    ├─────────────────────┤
                    │  Routers            │──▶ Pydantic Schemas
                    │  Services           │──▶ Google Books API
                    │  Repositories       │──▶ SQLAlchemy ORM
                    └──┬──────────────┬───┘
                       │              │
              ┌────────▼────┐  ┌──────▼──────┐
              │ PostgreSQL  │  │    Redis     │
              │   (:5432)   │  │   (:6379)   │
              │  11 tables  │  │ cache/rates │
              └─────────────┘  └─────────────┘
```

### Backend Layers

```
HTTP Request → Router → Service → Repository → Database
                          ↓
                     External APIs (Google Books, Stripe, FCM)
```

| Layer | Location | Responsibility |
|-------|----------|----------------|
| **Routers** | `app/routers/` | HTTP parsing, status codes, delegation |
| **Services** | `app/services/` | Business logic, external APIs, auth |
| **Repositories** | `app/repositories/` | SQLAlchemy queries, data access |
| **Models** | `app/models.py` | ORM definitions, constraints, seeds |
| **Schemas** | `app/schemas.py` | Pydantic request/response validation |

## Features

- Swipe through books with a Tinder-style card UI
- Filter by 14 categories (Fiction, Romance, Sci-Fi, Thriller, etc.)
- Content-based recommendation engine with preference learning
- Save liked books to a personal reading list
- Book details: description, page count, ratings, cover image
- OAuth login (Google, Apple) and email/password authentication
- Push notifications (FCM) with preference management
- Stripe subscription billing (free tier with swipe limits)
- Admin panel for user management
- Cross-platform: Android, iOS, Web, Desktop

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Flutter 3.x, Riverpod, GoRouter, Dio |
| Backend | Python 3.12, FastAPI, SQLAlchemy 2.0, Pydantic 2.0 |
| Database | PostgreSQL 16 (prod), SQLite (dev fallback) |
| Cache | Redis 7 (rate limiting, caching, token blacklist) |
| Auth | JWT (access + refresh), OAuth 2.0 (Google, Apple) |
| Payments | Stripe subscriptions |
| Notifications | Firebase Cloud Messaging |
| Book Data | Google Books API |
| Monitoring | Prometheus, Sentry, structured JSON logging |
| CI/CD | GitHub Actions (lint, test, Docker build, deploy) |
| Infrastructure | Docker Compose, Nginx, Kubernetes |

## API Overview

Base URL: `http://localhost:8000`

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| `POST` | `/api/auth/register` | No | Register a new user |
| `POST` | `/api/auth/login` | No | Login with email/password |
| `POST` | `/api/auth/google` | No | Google OAuth login |
| `POST` | `/api/auth/refresh` | No | Refresh token pair |
| `POST` | `/api/auth/logout` | Yes | Invalidate token |
| `GET` | `/api/auth/me` | Yes | Get current user profile |
| `GET` | `/api/books/discover` | Optional | Discover books by category |
| `GET` | `/api/books/{id}` | Optional | Get book details |
| `GET` | `/api/books/liked` | Yes | List liked books |
| `POST` | `/api/books/like` | Yes | Like a book |
| `POST` | `/api/books/skip` | Yes | Skip a book |
| `GET` | `/api/categories` | No | List all categories |
| `GET` | `/api/recommendations/` | Yes | Get personalized recommendations |
| `GET` | `/health` | No | Health check |

Full API reference: [docs/API.md](docs/API.md)

### Example: Discover Books

```bash
curl http://localhost:8000/api/books/discover?category=fiction&page=1
```

```json
{
  "books": [
    {
      "google_book_id": "abc123",
      "title": "Example Book",
      "authors": ["Author Name"],
      "thumbnail": "https://...",
      "average_rating": 4.2
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

### Example: Login and Like a Book

```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"reader1@bookswipe.app","password":"Reader123!"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Like a book
curl -X POST http://localhost:8000/api/books/like \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"google_book_id":"wrOQLV6xB-wC","title":"The Hobbit","authors":"J.R.R. Tolkien","thumbnail":"https://..."}'
```

## Screenshots

<!-- Add screenshots of the app here -->

| Discover | Book Detail | Liked Books | Profile |
|----------|-------------|-------------|---------|
| *Coming soon* | *Coming soon* | *Coming soon* | *Coming soon* |

## Project Structure

```
bookswipe/
├── frontend/              # Flutter app
│   ├── Dockerfile         # Multi-stage: Flutter build → nginx serve
│   └── lib/
│       ├── models/        # Data models (Book, User, Category)
│       ├── providers/     # Riverpod state management
│       ├── services/      # API client, auth storage
│       ├── screens/       # UI screens
│       ├── widgets/       # Reusable widgets
│       └── theme/         # App theming
├── backend/               # FastAPI server
│   ├── Dockerfile         # Multi-stage: pip install → gunicorn
│   ├── scripts/
│   │   └── seed_demo.py   # Demo data seed script
│   ├── alembic/           # Database migrations
│   └── app/
│       ├── routers/       # HTTP endpoint handlers
│       ├── services/      # Business logic
│       ├── repositories/  # Database access layer
│       ├── workers/       # Background jobs (arq)
│       ├── models.py      # SQLAlchemy ORM models (11 tables)
│       ├── schemas.py     # Pydantic request/response schemas
│       ├── exceptions.py  # Custom exception hierarchy
│       └── config.py      # Environment-based settings
├── nginx/                 # Reverse proxy config (production)
├── k8s/                   # Kubernetes manifests
├── deploy/                # Environment templates
├── scripts/               # Operational scripts (backup)
├── docs/                  # Documentation
│   ├── API.md             # Full API reference
│   ├── ARCHITECTURE.md    # Architecture deep-dive
│   ├── DEPLOYMENT.md      # Deployment guide
│   └── DEMO.md            # Demo walkthrough script
├── docker-compose.yml     # Development stack (one-command start)
├── docker-compose.prod.yml # Production stack (nginx, backups)
├── Makefile               # Dev/ops shortcuts
└── .github/workflows/     # CI/CD pipelines
```

## Development

### Prerequisites

- Docker & Docker Compose (recommended)
- Or: Python 3.12+, Flutter 3.x, PostgreSQL, Redis

### With Docker (recommended)

```bash
make dev          # Start all services
make dev-logs     # Tail logs
make seed-demo    # Seed demo data
make dev-down     # Stop everything
```

### Without Docker

```bash
# Backend
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
flutter pub get
flutter run
```

### Testing

```bash
make test         # Run backend tests with coverage
make lint         # Run linter
make lint-fix     # Auto-fix lint issues
```

### Makefile Targets

| Target | Description |
|--------|-------------|
| `make dev` | Start development environment |
| `make prod` | Start production environment |
| `make test` | Run backend tests with coverage |
| `make lint` | Run linter |
| `make migrate` | Run database migrations |
| `make seed` | Seed default categories |
| `make seed-demo` | Seed demo data (users, books, history) |
| `make backup` | Manual database backup |
| `make clean` | Remove containers, volumes, artifacts |
| `make help` | Show all targets |

## Deployment

See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for the full deployment guide.

### Quick Production Deploy

```bash
cp deploy/production.env .env
# Edit .env — set SECRET_KEY, POSTGRES_PASSWORD, etc.
make prod
```

### Container Registry

Images are published to `ghcr.io/abdullahtarakji/bookswipe-api`:
- **On merge to main** -- tagged with commit SHA + `latest`
- **On `v*` tag push** -- semver tags + GitHub Release

### Kubernetes

K8s manifests in `k8s/` for cluster deployments. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md).

## Documentation

- [API Reference](docs/API.md) -- All endpoints with examples
- [Architecture](docs/ARCHITECTURE.md) -- System design and layers
- [Deployment Guide](docs/DEPLOYMENT.md) -- Step-by-step deploy
- [Demo Script](docs/DEMO.md) -- Walkthrough of key flows
- [Contributing](CONTRIBUTING.md) -- How to contribute
- [Security](SECURITY.md) -- Security policy and reporting
