
from fastapi import FastAPI

from app.api import ai_analysis

from app.api import day

from app.api import db

from app.api import health

app = FastAPI(

    title="GK21 API",

    version="0.1.0",

)

app.include_router(health.router)

app.include_router(db.router)

app.include_router(day.router)

app.include_router(ai_analysis.router)

