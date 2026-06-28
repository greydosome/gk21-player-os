#!/bin/bash
set -euo pipefail

APP_DIR="/home/rocky/gk21"
PG_DIR="/postgres"

echo "[GK21] Deploy start"

install -m 700 -o root -g root \
  "${APP_DIR}/scripts/backup_gk21.sh" \
  "${PG_DIR}/scripts/backup_gk21.sh"

install -m 640 -o postgres -g postgres \
  "${APP_DIR}/sql/create_gk21_schema.sql" \
  "${PG_DIR}/scripts/create_gk21_schema.sql"

echo "[GK21] Deploy complete"
