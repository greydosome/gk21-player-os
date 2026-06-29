from fastapi import FastAPI

app = FastAPI(
    title="GK21 API",
    version="0.1.0"
)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "GK21"
    }


@app.get("/api/db/ping")
def db_ping():
    return {
        "database": "ok"
    }
