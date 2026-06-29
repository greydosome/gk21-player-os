from fastapi import APIRouter
from sqlalchemy import text

from app.db.session import engine

router = APIRouter()


@router.get("/api/db/ping")
def db_ping():

    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar_one()

    return {
        "database": "ok",
        "ping": result,
    }
