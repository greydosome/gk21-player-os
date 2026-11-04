"""All database tests use a disposable localhost cluster, never DATABASE_URL from .env."""
import atexit
import os
from pathlib import Path
import shutil
import socket
import subprocess
import tempfile

import pytest

PG_BIN = Path(shutil.which("postgres") or "/missing/postgres").parent
if not (PG_BIN / "initdb").exists():
    raise RuntimeError("Tests require local PostgreSQL initdb/pg_ctl; no external DB fallback")
ROOT = Path(tempfile.mkdtemp(prefix="gk21-health-tests-"))
with socket.socket() as sock:
    sock.bind(("127.0.0.1", 0))
    PORT = sock.getsockname()[1]
subprocess.run([str(PG_BIN / "initdb"), "-D", str(ROOT / "data"), "-A", "trust", "-U", "test_owner"], check=True, capture_output=True)
subprocess.run([str(PG_BIN / "pg_ctl"), "-D", str(ROOT / "data"), "-l", str(ROOT / "postgres.log"), "-o", f"-h 127.0.0.1 -p {PORT} -k {ROOT}", "-w", "start"], check=True, capture_output=True)


def cleanup():
    subprocess.run([str(PG_BIN / "pg_ctl"), "-D", str(ROOT / "data"), "-m", "immediate", "stop"], capture_output=True)
    shutil.rmtree(ROOT, ignore_errors=True)


atexit.register(cleanup)
os.environ["DATABASE_URL"] = f"postgresql+psycopg://test_owner@127.0.0.1:{PORT}/postgres"
os.environ["OPENAI_API_KEY"] = ""
os.environ["APPLE_HEALTH_ENABLED"] = "false"
os.environ["APPLE_HEALTH_COACHING_ENABLED"] = "false"

from sqlalchemy import text
from app.db.session import engine
from app.core.config import settings

with engine.begin() as conn:
    conn.exec_driver_sql("CREATE TABLE day_record(day_record_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY, record_date DATE UNIQUE NOT NULL, memo TEXT, is_injured BOOLEAN DEFAULT false)")
    conn.exec_driver_sql("""CREATE TABLE ai_analysis(
        analysis_id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
        day_record_id BIGINT, analysis_type TEXT, input_snapshot JSONB,
        lookback_days INTEGER, provider TEXT, model_name TEXT, prompt_version TEXT,
        ai_status TEXT, confidence INTEGER, overall_score INTEGER,
        summary TEXT, strength TEXT, weakness TEXT, next_goal TEXT,
        body_comment TEXT, workout_comment TEXT, meal_comment TEXT, sleep_comment TEXT,
        started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ, updated_at TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT now(),
        error_message TEXT, latency_ms INTEGER, token_input INTEGER, token_output INTEGER,
        analysis_detail JSONB, UNIQUE(day_record_id, analysis_type))""")
    migration = (Path(__file__).parents[2] / "sql/migrations/2026-11-02_apple_health.sql").read_text()
    conn.exec_driver_sql(migration.replace("BEGIN;", "").replace("COMMIT;", ""))
    workout_migration = (Path(__file__).parents[2] / "sql/migrations/2026-11-04_health_export_workouts.sql").read_text()
    conn.exec_driver_sql(workout_migration.replace("BEGIN;", "").replace("COMMIT;", ""))


@pytest.fixture(autouse=True)
def isolated(monkeypatch):
    monkeypatch.setattr(settings, "APPLE_HEALTH_ENABLED", False)
    monkeypatch.setattr(settings, "APPLE_HEALTH_COACHING_ENABLED", False)
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE day_record, apple_health_daily, apple_health_coaching_run, apple_health_workout, ai_analysis RESTART IDENTITY CASCADE"))
    yield
