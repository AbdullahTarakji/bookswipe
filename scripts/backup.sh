#!/bin/sh
set -eu

BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/bookswipe_${TIMESTAMP}.sql.gz"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-7}"

echo "[$(date -Iseconds)] Starting database backup..."

pg_dump -Fc | gzip > "${BACKUP_FILE}"

if [ -f "${BACKUP_FILE}" ] && [ -s "${BACKUP_FILE}" ]; then
    SIZE=$(du -h "${BACKUP_FILE}" | cut -f1)
    echo "[$(date -Iseconds)] Backup complete: ${BACKUP_FILE} (${SIZE})"
else
    echo "[$(date -Iseconds)] ERROR: Backup failed or file is empty"
    exit 1
fi

# Remove backups older than retention period
DELETED=$(find "${BACKUP_DIR}" -name "bookswipe_*.sql.gz" -mtime +"${RETENTION_DAYS}" -print -delete | wc -l)
echo "[$(date -Iseconds)] Cleaned up ${DELETED} old backup(s) (retention: ${RETENTION_DAYS} days)"
