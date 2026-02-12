# BookSwipe

**Tinder for Books** -- Swipe right to like, swipe left to skip. Discover your next read.

## Features

- Swipe through books with a Tinder-style card UI
- Filter by 14 categories (Fiction, Romance, Sci-Fi, Thriller, etc.)
- Save liked books to a personal reading list
- Book details: description, page count, ratings, cover image
- OAuth login (Google, Apple) and email/password authentication
- Cross-platform: Android, iOS, Web, Desktop

## Tech Stack

| Layer     | Technology                             |
|-----------|----------------------------------------|
| Frontend  | Flutter 3.x (Dart), Riverpod, GoRouter |
| Backend   | Python FastAPI, SQLAlchemy ORM          |
| Database  | SQLite (dev) / PostgreSQL (prod)        |
| Book Data | Google Books API                        |
| Auth      | JWT (access + refresh), OAuth 2.0       |
| CI/CD     | GitHub Actions                          |

## Project Structure

```
bookswipe/
├── frontend/              # Flutter app
│   └── lib/
│       ├── models/        # Data models (Book, User, Category)
│       ├── providers/     # Riverpod state management
│       ├── services/      # API client, auth storage
│       ├── screens/       # UI screens
│       ├── widgets/       # Reusable widgets
│       └── theme/         # App theming
├── backend/               # FastAPI server
│   └── app/
│       ├── routers/       # HTTP endpoint handlers
│       ├── services/      # Business logic
│       ├── repositories/  # Database access layer
│       ├── models.py      # SQLAlchemy ORM models
│       ├── schemas.py     # Pydantic request/response schemas
│       ├── exceptions.py  # Custom exception hierarchy
│       └── config.py      # Environment-based settings
├── docs/                  # Documentation
│   ├── API.md             # API endpoint reference
│   └── ARCHITECTURE.md    # Architecture overview
├── .github/workflows/     # CI/CD pipelines
├── CONTRIBUTING.md        # Contribution guidelines
└── SECURITY.md            # Security policy
```

## Getting Started

### Prerequisites

- Python 3.11+
- Flutter 3.x (with Dart SDK)
- Git

### Backend Setup

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Run the server (auto-creates SQLite DB and seeds categories)
uvicorn app.main:app --reload

# Run tests
pip install -r requirements-dev.txt
pytest tests/
```

The API will be available at `http://localhost:8000` with interactive docs at `/docs`.

### Frontend Setup

```bash
cd frontend
flutter pub get

# Run the app (connects to localhost:8000 by default)
flutter run

# Run tests
flutter test

# Check for lint issues
flutter analyze
```

### Environment Variables (Backend)

| Variable                | Default                        | Description              |
|-------------------------|--------------------------------|--------------------------|
| `SECRET_KEY`            | `change-me-in-production...`   | JWT signing key          |
| `DATABASE_URL`          | `sqlite:///./bookswipe.db`     | Database connection URL  |
| `GOOGLE_BOOKS_API_KEY`  | (empty)                        | Google Books API key     |
| `GOOGLE_CLIENT_ID`      | (empty)                        | Google OAuth client ID   |
| `APPLE_CLIENT_ID`       | (empty)                        | Apple OAuth client ID    |
| `ENVIRONMENT`           | `development`                  | `development`/`production` |

Copy `.env.example` to `.env` and fill in your values, or set them as environment variables.

## Documentation

- [API Reference](docs/API.md) -- All endpoints with request/response examples
- [Architecture](docs/ARCHITECTURE.md) -- Layer structure and design decisions
- [Contributing](CONTRIBUTING.md) -- How to contribute
- [Security](SECURITY.md) -- Security policy and reporting
