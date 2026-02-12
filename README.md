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
├── deploy/                # Environment templates
│   ├── staging.env        # Staging configuration
│   └── production.env     # Production configuration
├── nginx/                 # Nginx reverse proxy config
├── scripts/               # Operational scripts (backup, etc.)
├── k8s/                   # Kubernetes manifests
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
- Docker & Docker Compose
- Git

### Local Development

```bash
# Start everything with Docker Compose
make dev

# Or manually
docker compose up --build -d

# Backend is at http://localhost:8000/docs
# Frontend is at http://localhost:8080
```

### Backend Setup (without Docker)

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

### Frontend Setup

```bash
cd frontend
flutter pub get
flutter run
flutter test
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

## Deployment

### Architecture

```
Internet → Cloudflare/ALB (TLS) → Nginx (gzip, rate limit) → Gunicorn + Uvicorn → FastAPI
                                                            → PostgreSQL
                                                            → Redis (cache, rate limits, token blacklist)
```

SSL termination is handled upstream by Cloudflare or AWS ALB. The compose stack runs on port 80.

### Production Deploy

1. **Configure environment:**
   ```bash
   cp deploy/production.env .env
   # Edit .env — replace all CHANGEME values
   # Generate a secret key: openssl rand -hex 64
   ```

2. **Start production stack:**
   ```bash
   make prod
   ```

   This starts: FastAPI (gunicorn), PostgreSQL, Redis, Nginx, and a daily pg_dump backup cron.

3. **Run migrations:**
   ```bash
   make migrate
   ```

### Staging Deploy

```bash
cp deploy/staging.env .env
# Edit .env
make prod
```

Staging uses a separate PostgreSQL instance and relaxed rate limits for testing.

### Container Registry

Images are published to `ghcr.io/abdullahtarakji/bookswipe-api` automatically:
- **On merge to main** — tagged with commit SHA and `latest`
- **On `v*` tag push** — tagged with semver (e.g., `1.2.3`, `1.2`) and creates a GitHub Release with auto-generated changelog

### Makefile Targets

| Target          | Description                                 |
|-----------------|---------------------------------------------|
| `make dev`      | Start development environment               |
| `make prod`     | Start production environment                |
| `make test`     | Run backend tests with coverage             |
| `make lint`     | Run linter                                  |
| `make lint-fix` | Run linter with auto-fix                    |
| `make migrate`  | Run database migrations                     |
| `make seed`     | Seed database with default categories       |
| `make backup`   | Run a manual database backup                |
| `make clean`    | Remove containers, volumes, build artifacts |
| `make help`     | Show all targets                            |

### Database Backups

Production runs a daily `pg_dump` at 02:00 UTC, keeping the last 7 days. Backups are stored in the `backup-data` Docker volume.

```bash
make backup          # Manual backup
make backup-list     # List available backups
```

### Kubernetes

K8s manifests are in `k8s/` for cluster deployments. Update the image in `k8s/deployment.yaml` to point to `ghcr.io/abdullahtarakji/bookswipe-api:<tag>`.

### Domains

| Environment | URL                          |
|-------------|------------------------------|
| Production  | https://bookswipe.app        |
| API         | https://api.bookswipe.app    |
| Staging     | https://staging.bookswipe.app|

## Documentation

- [API Reference](docs/API.md) -- All endpoints with request/response examples
- [Architecture](docs/ARCHITECTURE.md) -- Layer structure and design decisions
- [Contributing](CONTRIBUTING.md) -- How to contribute
- [Security](SECURITY.md) -- Security policy and reporting
