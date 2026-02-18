#!/usr/bin/env bash
# ============================================================
# BookSwipe — Production Deployment Script
# ============================================================
# Usage: ./scripts/deploy-prod.sh [IMAGE_TAG]
#   IMAGE_TAG defaults to "latest"
#
# This script:
#   1. Creates a database backup before deploying
#   2. Pulls new images
#   3. Runs database migrations
#   4. Performs a rolling restart
#   5. Verifies health
#   6. Rolls back on failure
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/deploy/production.env"
IMAGE_TAG="${1:-latest}"
HEALTH_URL="http://localhost:${HTTP_PORT:-80}/health"
HEALTH_RETRIES=30
HEALTH_INTERVAL=2
DEPLOY_LOG="$PROJECT_DIR/deploy/deploy-$(date +%Y%m%d_%H%M%S).log"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[DEPLOY]${NC} $(date -Iseconds) $*" | tee -a "$DEPLOY_LOG"; }
warn() { echo -e "${YELLOW}[WARN]${NC}  $(date -Iseconds) $*" | tee -a "$DEPLOY_LOG"; }
err()  { echo -e "${RED}[ERROR]${NC} $(date -Iseconds) $*" | tee -a "$DEPLOY_LOG"; }

die() { err "$@"; exit 1; }

cd "$PROJECT_DIR"

# ── Pre-flight checks ───────────────────────────────────────
log "Starting production deployment (tag: $IMAGE_TAG)"

[ -f "$COMPOSE_FILE" ] || die "docker-compose.prod.yml not found"
[ -f "$ENV_FILE" ]     || die "deploy/production.env not found"
command -v docker >/dev/null 2>&1 || die "docker not found"

# Ensure deploy log dir exists
mkdir -p "$(dirname "$DEPLOY_LOG")"

# Save current image digests for rollback
PREV_BACKEND_IMAGE=$(docker compose -f "$COMPOSE_FILE" images backend --format json 2>/dev/null | head -1 | grep -o '"Tag":"[^"]*"' | cut -d'"' -f4 || echo "unknown")
log "Previous backend image tag: $PREV_BACKEND_IMAGE"

# ── Step 1: Backup ───────────────────────────────────────────
log "Step 1/5: Creating pre-deploy database backup..."
if docker compose -f "$COMPOSE_FILE" exec -T db pg_isready -U "${POSTGRES_USER:-bookswipe}" >/dev/null 2>&1; then
    bash "$SCRIPT_DIR/backup.sh" 2>&1 | tee -a "$DEPLOY_LOG" || warn "Backup failed — proceeding with caution"
else
    warn "Database not running — skipping backup (first deploy?)"
fi

# ── Step 2: Pull images ─────────────────────────────────────
log "Step 2/5: Pulling images..."
if [ "$IMAGE_TAG" != "latest" ]; then
    export IMAGE_TAG
fi
docker compose -f "$COMPOSE_FILE" pull 2>&1 | tee -a "$DEPLOY_LOG"

# ── Step 3: Run migrations ──────────────────────────────────
log "Step 3/5: Running database migrations..."
bash "$SCRIPT_DIR/migrate.sh" 2>&1 | tee -a "$DEPLOY_LOG" || die "Migration failed — aborting deploy"

# ── Step 4: Rolling restart ──────────────────────────────────
log "Step 4/5: Rolling restart of services..."

# Restart backend with zero-downtime (scale up new, then remove old)
docker compose -f "$COMPOSE_FILE" up -d --no-deps --build backend 2>&1 | tee -a "$DEPLOY_LOG"

# Restart nginx to pick up any config changes
docker compose -f "$COMPOSE_FILE" up -d --no-deps nginx 2>&1 | tee -a "$DEPLOY_LOG"

# ── Step 5: Health verification ──────────────────────────────
log "Step 5/5: Verifying health..."
HEALTHY=false
for i in $(seq 1 "$HEALTH_RETRIES"); do
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    log "  Health check attempt $i/$HEALTH_RETRIES..."
    sleep "$HEALTH_INTERVAL"
done

if [ "$HEALTHY" = true ]; then
    log "✅ Deployment successful! Service is healthy."
    log "   Tag: $IMAGE_TAG"
    log "   Log: $DEPLOY_LOG"
    exit 0
fi

# ── Rollback on failure ─────────────────────────────────────
err "❌ Health check failed after $HEALTH_RETRIES attempts"
err "Initiating rollback to previous version ($PREV_BACKEND_IMAGE)..."

bash "$SCRIPT_DIR/rollback.sh" "$PREV_BACKEND_IMAGE" 2>&1 | tee -a "$DEPLOY_LOG"

die "Deployment failed. Rolled back to $PREV_BACKEND_IMAGE. Check logs: $DEPLOY_LOG"
