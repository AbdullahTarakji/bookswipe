#!/usr/bin/env bash
# ============================================================
# BookSwipe — Database Migration Script
# ============================================================
# Usage: ./scripts/migrate.sh [alembic_args...]
#   Default: upgrade head
#   Examples:
#     ./scripts/migrate.sh                    # upgrade to head
#     ./scripts/migrate.sh downgrade -1       # revert last migration
#     ./scripts/migrate.sh history            # show migration history
#     ./scripts/migrate.sh current            # show current revision
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ALEMBIC_ARGS="${*:-upgrade head}"

GREEN='\033[0;32m'
NC='\033[0m'

log() { echo -e "${GREEN}[MIGRATE]${NC} $(date -Iseconds) $*"; }

cd "$PROJECT_DIR"

log "Running: alembic $ALEMBIC_ARGS"

# Run migrations inside the backend container
if docker compose -f "$COMPOSE_FILE" ps backend --status running >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" exec -T backend alembic $ALEMBIC_ARGS
else
    # Backend not running — start a one-off container for migrations
    log "Backend not running — using one-off container"
    docker compose -f "$COMPOSE_FILE" run --rm --no-deps -T backend alembic $ALEMBIC_ARGS
fi

log "Migration complete"
