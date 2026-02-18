#!/usr/bin/env bash
# ============================================================
# BookSwipe — Rollback Script
# ============================================================
# Usage: ./scripts/rollback.sh [IMAGE_TAG]
#   Reverts to the specified image tag (or previous tag).
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ROLLBACK_TAG="${1:-}"
HEALTH_URL="http://localhost:${HTTP_PORT:-80}/health"
HEALTH_RETRIES=20
HEALTH_INTERVAL=2

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[ROLLBACK]${NC} $(date -Iseconds) $*"; }
err()  { echo -e "${RED}[ROLLBACK]${NC} $(date -Iseconds) $*"; }
die()  { err "$@"; exit 1; }

cd "$PROJECT_DIR"

if [ -z "$ROLLBACK_TAG" ]; then
    # Try to find previous image from docker history
    ROLLBACK_TAG=$(docker images --format '{{.Tag}}' "ghcr.io/abdullahtarakji/bookswipe-api" | grep -v latest | head -1 || echo "")
    if [ -z "$ROLLBACK_TAG" ]; then
        die "No rollback tag specified and could not find previous image. Usage: $0 <IMAGE_TAG>"
    fi
    log "Auto-detected previous tag: $ROLLBACK_TAG"
fi

log "Rolling back to tag: $ROLLBACK_TAG"

# Export tag for docker-compose
export IMAGE_TAG="$ROLLBACK_TAG"

# Restart backend with previous image
docker compose -f "$COMPOSE_FILE" up -d --no-deps backend 2>&1
docker compose -f "$COMPOSE_FILE" up -d --no-deps nginx 2>&1

# Verify health
log "Verifying health after rollback..."
HEALTHY=false
for i in $(seq 1 "$HEALTH_RETRIES"); do
    if curl -sf "$HEALTH_URL" >/dev/null 2>&1; then
        HEALTHY=true
        break
    fi
    sleep "$HEALTH_INTERVAL"
done

if [ "$HEALTHY" = true ]; then
    log "✅ Rollback successful. Running on tag: $ROLLBACK_TAG"
else
    err "❌ Rollback health check failed. Manual intervention required!"
    err "   Check: docker compose -f $COMPOSE_FILE logs backend"
    exit 1
fi
