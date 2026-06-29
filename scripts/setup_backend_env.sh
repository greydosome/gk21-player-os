#!/bin/bash
set -euo pipefail

APP_DIR="/home/rocky/gk21"
BACKEND_DIR="${APP_DIR}/backend"

export PATH="${HOME}/.local/bin:${PATH}"

echo "[GK21] Backend env setup start"

if ! command -v uv >/dev/null 2>&1; then
  echo "[GK21] Install uv"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
fi

mkdir -p "${BACKEND_DIR}"/app/{api,core,db,models,schemas,services,utils}
mkdir -p "${BACKEND_DIR}/tests"

touch "${BACKEND_DIR}"/app/__init__.py
touch "${BACKEND_DIR}"/app/api/__init__.py
touch "${BACKEND_DIR}"/app/core/__init__.py
touch "${BACKEND_DIR}"/app/db/__init__.py
touch "${BACKEND_DIR}"/app/models/__init__.py
touch "${BACKEND_DIR}"/app/schemas/__init__.py
touch "${BACKEND_DIR}"/app/services/__init__.py
touch "${BACKEND_DIR}"/app/utils/__init__.py

cat > "${BACKEND_DIR}/pyproject.toml" <<'PYPROJECT'
[project]
name = "gk21-backend"
version = "0.1.0"
description = "GK21 Backend API"
requires-python = ">=3.12,<3.13"
dependencies = []

[tool.uv]
package = false
PYPROJECT

cd "${BACKEND_DIR}"

uv python install 3.12
uv venv --python 3.12 .venv

uv add fastapi "uvicorn[standard]" sqlalchemy "psycopg[binary]" alembic pydantic-settings python-dotenv

cat > app/main.py <<'PY'
from fastapi import FastAPI

app = FastAPI(title="GK21 API", version="0.1.0")


@app.get("/api/v1/health")
def health_check():
    return {
        "success": True,
        "data": {
            "service": "gk21-backend",
            "status": "ok"
        }
    }
PY

cat > .env.example <<'ENV'
APP_NAME=GK21
APP_ENV=dev
API_HOST=0.0.0.0
API_PORT=8000

DB_HOST=127.0.0.1
DB_PORT=5432
DB_NAME=gk21
DB_USER=gk21_app
DB_PASSWORD=change_me
ENV

cat > run.sh <<'RUN'
#!/bin/bash
set -euo pipefail

cd /home/rocky/gk21/backend
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
RUN

chmod 755 run.sh

echo "[GK21] Backend env setup complete"
