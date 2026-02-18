#!/usr/bin/env bash
# ============================================================
# BookSwipe — PostgreSQL Backup Script
# ============================================================
# Usage: ./scripts/backup.sh
#
# Can run standalone or inside the backup container (via cron).
# Supports:
#   - Compressed custom-format dumps
#   - Retention-based rotation
#   - Optional S3 upload
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"

BACKUP_DIR="${BACKUP_DIR:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/bookswipe_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log() { echo -e "${GREEN}[BACKUP]${NC} $(date -Iseconds) $*"; }
err() { echo -e "${RED}[BACKUP]${NC} $(date -Iseconds) $*"; }

mkdir -p "$BACKUP_DIR"

log "Starting database backup..."

# Detect if running inside a container (PGHOST set) or on host
if [ -n "${PGHOST:-}" ]; then
    # Running inside container
    pg_dump -Fc | gzip > "$BACKUP_FILE"
else
    # Running on host — dump via docker
    docker compose -f "$COMPOSE_FILE" exec -T db \
        pg_dump -U "${POSTGRES_USER:-bookswipe}" -Fc "${POSTGRES_DB:-bookswipe}" \
        | gzip > "$BACKUP_FILE"
fi

if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    log "Backup complete: $BACKUP_FILE ($SIZE)"
else
    err "Backup failed or file is empty"
    exit 1
fi

# Rotate old backups
DELETED=$(find "$BACKUP_DIR" -name "bookswipe_*.sql.gz" -mtime +"$RETENTION_DAYS" -print -delete | wc -l)
log "Cleaned up $DELETED old backup(s) (retention: ${RETENTION_DAYS} days)"

# ── Optional S3 Upload ──────────────────────────────────────
# Uncomment and configure to enable S3 backup offloading:
#
# S3_BUCKET="${S3_BACKUP_BUCKET:-}"
# if [ -n "$S3_BUCKET" ]; then
#     log "Uploading to s3://$S3_BUCKET/backups/"
#     aws s3 cp "$BACKUP_FILE" "s3://$S3_BUCKET/backups/$(basename "$BACKUP_FILE")" \
#         --storage-class STANDARD_IA
#     log "S3 upload complete"
# fi
