# BookSwipe — Deployment Guide

## Table of Contents

- [Prerequisites](#prerequisites)
- [First-Time Setup](#first-time-setup)
- [Environment Variables](#environment-variables)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [SSL/TLS Setup](#ssltls-setup)
- [Database Migrations](#database-migrations)
- [Monitoring](#monitoring)
- [Backup & Restore](#backup--restore)
- [Rollback Procedure](#rollback-procedure)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

- **Docker** ≥ 24.0 and **Docker Compose** v2
- **Git** for version control
- Server with ≥ 2 GB RAM, 20 GB disk
- Domain name pointing to your server (for SSL)
- GitHub Container Registry access (`ghcr.io`)

## First-Time Setup

### 1. Clone and configure

```bash
git clone https://github.com/abdullahtarakji/bookswipe.git /opt/bookswipe
cd /opt/bookswipe
```

### 2. Create production environment

```bash
cp deploy/production.env .env
# Edit .env — replace ALL "CHANGEME" values
nano .env
```

Generate secure secrets:

```bash
# Secret key (64+ chars)
openssl rand -hex 32

# Database password
openssl rand -base64 24
```

### 3. Start services

```bash
docker compose -f docker-compose.prod.yml up -d
```

### 4. Run initial migrations

```bash
./scripts/migrate.sh
```

### 5. Set up SSL (see [SSL/TLS Setup](#ssltls-setup))

---

## Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Runtime environment | Yes | `production` |
| `DEBUG` | Debug mode | Yes | `false` |
| `POSTGRES_USER` | Database user | Yes | `bookswipe` |
| `POSTGRES_PASSWORD` | Database password | **Yes** | — |
| `POSTGRES_DB` | Database name | Yes | `bookswipe` |
| `SECRET_KEY` | JWT signing key (64+ chars) | **Yes** | — |
| `ALGORITHM` | JWT algorithm | Yes | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Access token TTL | Yes | `15` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Refresh token TTL | Yes | `7` |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | **Yes** | — |
| `APPLE_CLIENT_ID` | Apple Sign-In client ID | **Yes** | — |
| `GOOGLE_BOOKS_API_KEY` | Google Books API key | **Yes** | — |
| `STRIPE_SECRET_KEY` | Stripe secret key | **Yes** | — |
| `STRIPE_WEBHOOK_SECRET` | Stripe webhook secret | **Yes** | — |
| `STRIPE_PRICE_ID` | Stripe subscription price | **Yes** | — |
| `SENTRY_DSN` | Sentry error tracking DSN | No | — |
| `WEB_CONCURRENCY` | Gunicorn worker count | No | `4` |
| `BACKUP_RETENTION_DAYS` | Backup retention period | No | `7` |
| `HTTP_PORT` | Nginx HTTP port | No | `80` |
| `CORS_ORIGINS` | Allowed CORS origins (JSON) | Yes | `["https://bookswipe.app"]` |

---

## Staging Deployment

Staging deploys automatically on push to `develop` via CI:

```bash
git push origin develop
```

Or manually:

```bash
# On staging server
cd /opt/bookswipe
git pull origin develop
docker compose -f docker-compose.prod.yml pull
./scripts/migrate.sh
docker compose -f docker-compose.prod.yml up -d
```

---

## Production Deployment

### Automated (recommended)

Production deploys on tagged releases with manual approval:

```bash
# Create a release tag
git tag v1.2.3
git push origin v1.2.3
```

The CI pipeline will:
1. Run tests
2. Build and push Docker image
3. Create GitHub release with changelog
4. Wait for manual approval (GitHub environment: `production`)
5. Deploy via SSH

### Manual

```bash
ssh prod-server
cd /opt/bookswipe
./scripts/deploy-prod.sh v1.2.3
```

The deploy script automatically:
- Creates a database backup
- Pulls new images
- Runs migrations
- Performs rolling restart
- Verifies health
- Rolls back on failure

---

## SSL/TLS Setup

### Using Let's Encrypt (certbot)

#### 1. Install certbot on the host

```bash
apt install certbot
```

#### 2. Obtain certificates

```bash
# Stop nginx temporarily (or use webroot mode)
docker compose -f docker-compose.prod.yml stop nginx

certbot certonly --standalone -d bookswipe.app -d www.bookswipe.app

docker compose -f docker-compose.prod.yml start nginx
```

#### 3. Switch to SSL nginx config

Update `docker-compose.prod.yml` nginx service:

```yaml
nginx:
  volumes:
    - ./nginx/nginx-ssl.conf:/etc/nginx/nginx.conf:ro
    - /etc/letsencrypt:/etc/letsencrypt:ro
    - ./certbot/www:/var/www/certbot:ro
  ports:
    - "80:80"
    - "443:443"
```

#### 4. Auto-renewal

```bash
# Add cron job
echo "0 3 * * * certbot renew --quiet --deploy-hook 'docker compose -f /opt/bookswipe/docker-compose.prod.yml exec nginx nginx -s reload'" | crontab -
```

---

## Database Migrations

```bash
# Apply all pending migrations
./scripts/migrate.sh

# Check current migration state
./scripts/migrate.sh current

# View migration history
./scripts/migrate.sh history

# Revert last migration
./scripts/migrate.sh downgrade -1

# Create a new migration (development)
cd backend
alembic revision --autogenerate -m "describe change"
```

---

## Monitoring

### Health Check

```bash
curl http://localhost/health
```

### Logs

```bash
# All services
docker compose -f docker-compose.prod.yml logs -f

# Specific service
docker compose -f docker-compose.prod.yml logs -f backend

# Last 100 lines
docker compose -f docker-compose.prod.yml logs --tail=100 backend
```

### Metrics

Prometheus metrics available at `/metrics` (internal network only).

### Sentry

Set `SENTRY_DSN` in production.env for error tracking.

### Resource usage

```bash
docker stats
```

---

## Backup & Restore

### Automated backups

The `backup` service runs daily at 02:00 via cron. Backups are stored in the `backup-data` Docker volume.

### Manual backup

```bash
./scripts/backup.sh
```

### Restore from backup

```bash
# List available backups
docker compose -f docker-compose.prod.yml exec backup ls -la /backups/

# Restore (replace FILENAME)
docker compose -f docker-compose.prod.yml exec -T db \
  sh -c 'gunzip -c - | pg_restore -U bookswipe -d bookswipe --clean --if-exists' \
  < /path/to/bookswipe_YYYYMMDD_HHMMSS.sql.gz
```

### Backup configuration

| Variable | Description | Default |
|----------|-------------|---------|
| `BACKUP_RETENTION_DAYS` | Days to keep backups | `7` |
| `S3_BACKUP_BUCKET` | S3 bucket for offsite backups | — |

---

## Rollback Procedure

### Automatic rollback

The deploy script (`deploy-prod.sh`) automatically rolls back if health checks fail after deployment.

### Manual rollback

```bash
# Rollback to a specific version
./scripts/rollback.sh v1.2.2

# Auto-detect previous version
./scripts/rollback.sh
```

### Database rollback

If a migration needs reverting:

```bash
./scripts/migrate.sh downgrade -1
```

---

## Troubleshooting

### Service won't start

```bash
# Check logs
docker compose -f docker-compose.prod.yml logs backend

# Check container status
docker compose -f docker-compose.prod.yml ps

# Restart a service
docker compose -f docker-compose.prod.yml restart backend
```

### Database connection issues

```bash
# Verify database is healthy
docker compose -f docker-compose.prod.yml exec db pg_isready -U bookswipe

# Connect directly
docker compose -f docker-compose.prod.yml exec db psql -U bookswipe
```

### Migration failures

```bash
# Check current state
./scripts/migrate.sh current

# View history
./scripts/migrate.sh history

# If stuck, stamp to a known revision
docker compose -f docker-compose.prod.yml exec backend alembic stamp <revision>
```

### Nginx 502 Bad Gateway

The backend is not responding. Check:

```bash
docker compose -f docker-compose.prod.yml logs backend
docker compose -f docker-compose.prod.yml exec backend curl -s http://localhost:8000/health
```

### Disk space

```bash
# Check Docker disk usage
docker system df

# Prune unused images
docker image prune -a --filter "until=168h"
```

### Deploy log

All deployments are logged in `deploy/deploy-*.log`.
