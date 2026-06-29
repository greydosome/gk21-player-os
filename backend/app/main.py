from fastapi import FastAPI
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine


app = FastAPI(
    title="GK21 API",
    version="0.1.0",
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": settings.app_name,
        "env": settings.app_env,
    }


@app.get("/api/db/ping")
def db_ping():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 AS ping")).scalar_one()

    return {
        "database": "ok",
        "ping": result,
    }
