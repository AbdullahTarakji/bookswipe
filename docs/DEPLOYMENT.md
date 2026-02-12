# BookSwipe Deployment Guide

## Local Demo (Docker Compose)

The fastest way to run the full stack locally.

### Prerequisites

- Docker Engine 24+
- Docker Compose v2+
- 4 GB free RAM (Flutter build is memory-intensive)
- Ports 5432, 6379, 8000, 8080 available

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/AbdullahTarakji/bookswipe.git
cd bookswipe

# 2. Start all services
docker compose up --build

# 3. Wait for health checks to pass (backend takes ~15s to start)
# Check: http://localhost:8000/health

# 4. Seed demo data (optional, in a separate terminal)
docker compose exec backend python -m scripts.seed_demo

# 5. Access the app
# Frontend: http://localhost:8080
# API docs: http://localhost:8000/docs
```

### Services Started

| Service | Port | Description |
|---------|------|-------------|
| `db` | 5432 | PostgreSQL 16 |
| `redis` | 6379 | Redis 7 (cache, rate limits) |
| `backend` | 8000 | FastAPI (gunicorn + uvicorn) |
| `frontend` | 8080 | Flutter web (nginx) |

### Stopping

```bash
docker compose down          # Stop containers
docker compose down -v       # Stop + remove volumes (reset data)
```

## Production Deployment

### Architecture

```
Internet → Cloudflare/ALB (TLS) → Nginx (gzip, rate limit) → Gunicorn + Uvicorn → FastAPI
                                                             → PostgreSQL
                                                             → Redis
```

SSL termination is handled upstream by Cloudflare or AWS ALB. The compose stack runs on port 80.

### Step 1: Configure Environment

```bash
cp deploy/production.env .env
```

Edit `.env` and set all required values:

| Variable | Required | Example |
|----------|----------|---------|
| `POSTGRES_PASSWORD` | Yes | `$(openssl rand -hex 32)` |
| `SECRET_KEY` | Yes | `$(openssl rand -hex 64)` |
| `CORS_ORIGINS` | Yes | `["https://bookswipe.app"]` |
| `GOOGLE_BOOKS_API_KEY` | Recommended | Your API key |
| `GOOGLE_CLIENT_ID` | For OAuth | Google OAuth client ID |
| `STRIPE_SECRET_KEY` | For payments | Stripe secret key |
| `SENTRY_DSN` | For monitoring | Sentry DSN |

Generate a secure secret key:

```bash
openssl rand -hex 64
```

### Step 2: Start Production Stack

```bash
make prod
# or
docker compose -f docker-compose.prod.yml up --build -d
```

This starts:
- FastAPI backend with gunicorn (configurable workers via `WEB_CONCURRENCY`)
- PostgreSQL with persistent volume
- Redis with AOF persistence
- Nginx reverse proxy on port 80
- Daily database backup cron (02:00 UTC, 7-day retention)

### Step 3: Run Migrations

```bash
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Step 4: Verify

```bash
# Health check
curl http://localhost/health

# Check all services
docker compose -f docker-compose.prod.yml ps
```

### Scaling

Adjust gunicorn workers via the `WEB_CONCURRENCY` environment variable:

```bash
# In .env
WEB_CONCURRENCY=4  # default: 4, recommended: 2 * CPU cores + 1
```

### Database Backups

Production runs a daily `pg_dump` at 02:00 UTC.

```bash
make backup          # Manual backup
make backup-list     # List available backups
```

Backups are stored in the `backup-data` Docker volume. To extract:

```bash
docker compose -f docker-compose.prod.yml exec backup ls -lh /backups/
docker cp $(docker compose -f docker-compose.prod.yml ps -q backup):/backups/latest.sql.gz ./
```

## Container Registry

Images are automatically published to `ghcr.io/abdullahtarakji/bookswipe-api`:

| Trigger | Tags |
|---------|------|
| Push to `main` | `<commit-sha>`, `latest` |
| Tag push (`v*`) | `<version>`, `<major>.<minor>`, `latest` |

### Using Pre-built Images

Instead of building locally, pull from the registry:

```bash
# In docker-compose.prod.yml, replace build: with image:
# image: ghcr.io/abdullahtarakji/bookswipe-api:latest
```

## Kubernetes

K8s manifests are in `k8s/`:

```
k8s/
├── configmap.yaml     # Environment configuration
├── deployment.yaml    # Backend pods
├── hpa.yaml           # Horizontal Pod Autoscaler
├── ingress.yaml       # Ingress rules
└── service.yaml       # ClusterIP service
```

### Deploy to Cluster

```bash
# Update image tag in deployment.yaml
kubectl apply -f k8s/

# Verify
kubectl get pods -l app=bookswipe
kubectl logs -l app=bookswipe --tail=50
```

## Environment Reference

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./bookswipe.db` | Database connection string |
| `SECRET_KEY` | (dev default) | JWT signing key (32+ chars in prod) |
| `REDIS_URL` | `redis://localhost:6379/0` | Redis connection string |
| `CORS_ORIGINS` | `["*"]` | Allowed CORS origins |
| `ENVIRONMENT` | `development` | `development` or `production` |
| `DEBUG` | `false` | Enable debug mode |
| `GOOGLE_BOOKS_API_KEY` | (empty) | Google Books API key |
| `GOOGLE_CLIENT_ID` | (empty) | Google OAuth client ID |
| `APPLE_CLIENT_ID` | (empty) | Apple OAuth client ID |
| `STRIPE_SECRET_KEY` | (empty) | Stripe secret key |
| `STRIPE_WEBHOOK_SECRET` | (empty) | Stripe webhook signing secret |
| `SENTRY_DSN` | (empty) | Sentry error tracking DSN |
| `FCM_CREDENTIALS_PATH` | (empty) | Firebase credentials JSON path |
| `ADMIN_EMAIL` | (empty) | Auto-seed admin email |
| `ADMIN_PASSWORD` | (empty) | Auto-seed admin password |
| `WEB_CONCURRENCY` | `4` | Gunicorn worker count |
| `DB_POOL_SIZE` | `20` | SQLAlchemy connection pool size |
| `AUTH_RATE_LIMIT` | `5/minute` | Auth endpoint rate limit |
| `API_RATE_LIMIT` | `30/minute` | General API rate limit |

## Domains

| Environment | URL |
|-------------|-----|
| Production | https://bookswipe.app |
| API | https://api.bookswipe.app |
| Staging | https://staging.bookswipe.app |
