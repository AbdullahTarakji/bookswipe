#!/usr/bin/env bash
set -euo pipefail

# BookSwipe Staging Deployment Script
# Usage: ./scripts/deploy-staging.sh [--skip-build]

COMPOSE_FILE="docker-compose.staging.yml"
ENV_FILE="deploy/staging.env"
PROJECT_NAME="bookswipe-staging"
HEALTH_URL="http://localhost:${HTTP_PORT:-80}/health"
MAX_HEALTH_RETRIES=30
HEALTH_INTERVAL=2

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $*"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $*"; }
err()  { echo -e "${RED}[ERROR]${NC} $*" >&2; }

SKIP_BUILD=false
[[ "${1:-}" == "--skip-build" ]] && SKIP_BUILD=true

cd "$(dirname "$0")/.."

# ── Preflight checks ────────────────────────────────────────
log "Running preflight checks..."

if [[ ! -f "$ENV_FILE" ]]; then
    err "Environment file $ENV_FILE not found"
    exit 1
fi

if grep -q "CHANGEME" "$ENV_FILE"; then
    warn "staging.env contains CHANGEME placeholders — make sure they are replaced for real deployments"
fi

if ! command -v docker &>/dev/null; then
    err "docker not found"
    exit 1
fi

# ── Pull latest code ────────────────────────────────────────
log "Pulling latest code..."
git pull --ff-only origin develop || {
    warn "Git pull failed — deploying current working tree"
}

# ── Build ────────────────────────────────────────────────────
if [[ "$SKIP_BUILD" == "false" ]]; then
    log "Building images..."
    docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" build --parallel
else
    log "Skipping build (--skip-build)"
fi

# ── Run database migrations ─────────────────────────────────
log "Running database migrations..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d db
sleep 3  # wait for db to be ready

docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" run --rm \
    -e DATABASE_URL="postgresql://${POSTGRES_USER:-bookswipe}:${POSTGRES_PASSWORD:-password}@db:5432/${POSTGRES_DB:-bookswipe_staging}" \
    backend alembic upgrade head || {
    warn "Migration failed or alembic not configured — continuing"
}

# ── Deploy services ──────────────────────────────────────────
log "Starting services..."
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" up -d

# ── Health check ─────────────────────────────────────────────
log "Waiting for health check at $HEALTH_URL ..."
attempt=0
while [[ $attempt -lt $MAX_HEALTH_RETRIES ]]; do
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
        log "Health check passed ✓"
        break
    fi
    attempt=$((attempt + 1))
    if [[ $attempt -eq $MAX_HEALTH_RETRIES ]]; then
        err "Health check failed after $MAX_HEALTH_RETRIES attempts"
        log "Container status:"
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
        log "Recent logs:"
        docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" logs --tail=50
        exit 1
    fi
    sleep $HEALTH_INTERVAL
done

# ── Cleanup ──────────────────────────────────────────────────
log "Cleaning up old images..."
docker image prune -f --filter "until=168h" 2>/dev/null || true

# ── Summary ──────────────────────────────────────────────────
log "Staging deployment complete! 🚀"
docker compose -f "$COMPOSE_FILE" -p "$PROJECT_NAME" ps
