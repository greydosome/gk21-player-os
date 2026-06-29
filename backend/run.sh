#!/bin/bash
set -euo pipefail

cd /home/rocky/gk21/backend
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
