#!/bin/bash
set -euo pipefail

DB_NAME="gk21"
BACKUP_DIR="/postgres/backup"
LOG_DIR="/postgres/logs"
RETENTION_DAYS=3
DATE="$(date +%F)"

BACKUP_FILE="${BACKUP_DIR}/${DB_NAME}_${DATE}.dump"
LOG_FILE="${LOG_DIR}/backup_gk21.log"

mkdir -p "$BACKUP_DIR" "$LOG_DIR"

log() {
  echo "[$(date '+%F %T')] $*" >> "$LOG_FILE"
}

fail() {
  log "ERROR: $*"
  echo "[$(date '+%F %T')] ERROR: $*"
  exit 1
}

trap 'fail "backup failed at line ${LINENO}"' ERR

log "Backup started. db=${DB_NAME}, file=${BACKUP_FILE}"

su - postgres -c "psql -Atqc \"SELECT 1 FROM pg_database WHERE datname='${DB_NAME}';\"" | grep -qx "1" \
  || fail "database does not exist: ${DB_NAME}"

rm -f "$BACKUP_FILE"

su - postgres -c "pg_dump -Fc -d '${DB_NAME}' -f '${BACKUP_FILE}'"

[ -s "$BACKUP_FILE" ] || fail "backup file is empty or missing: ${BACKUP_FILE}"

log "Backup completed. size=$(du -h "$BACKUP_FILE" | awk '{print $1}')"

find "$BACKUP_DIR" \
  -type f \
  -name "${DB_NAME}_*.dump" \
  -mtime +"${RETENTION_DAYS}" \
  -print \
  -delete >> "$LOG_FILE" 2>&1

log "Retention cleanup completed. retention_days=${RETENTION_DAYS}"
