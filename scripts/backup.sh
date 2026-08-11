#!/bin/sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
DB_HOST="${POSTGRES_HOST:-db}"
DB_PORT="${POSTGRES_PORT:-5432}"
DB_NAME="${POSTGRES_DB:-uranai_app}"
DB_USER="${POSTGRES_USER:-app}"
TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
FILE="$BACKUP_DIR/uranai_app_$TIMESTAMP.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[BACKUP] creating $FILE"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" --no-owner --no-privileges | gzip -9 > "$FILE"

echo "[BACKUP] removing backups older than $RETENTION_DAYS days"
find "$BACKUP_DIR" -type f -name 'uranai_app_*.sql.gz' -mtime "+$RETENTION_DAYS" -delete

echo "[BACKUP] complete"
