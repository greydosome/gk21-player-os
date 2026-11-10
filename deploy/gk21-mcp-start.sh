#!/bin/bash
set -euo pipefail
cd /home/rocky/gk21/backend
exec /home/rocky/gk21/backend/.venv/bin/python -m uvicorn app.mcp_server:app_factory --factory --host 127.0.0.1 --port 8010 --proxy-headers --forwarded-allow-ips=127.0.0.1 --no-access-log
