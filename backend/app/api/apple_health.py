import json
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Request
from starlette.concurrency import run_in_threadpool
from app.core.config import settings
from app.db.session import engine
from app.schemas.apple_health import AppleHealthRequest
from app.services.apple_health import save_health
from app.services.health_export import save_export

router = APIRouter()


@router.post("/api/integrations/apple-health/daily")
async def upload_health(request: Request):
    if not settings.APPLE_HEALTH_ENABLED:
        raise HTTPException(404, "Integration disabled")
    payload = bytearray()
    async for chunk in request.stream():
        payload.extend(chunk)
        if len(payload) > 32768:
            raise HTTPException(413, "Payload too large")
    try:
        req = AppleHealthRequest.model_validate(json.loads(payload))
    except ValueError:
        raise HTTPException(422, "Invalid health summary") from None
    # Run synchronous SQL outside the event loop.
    return await run_in_threadpool(persist, req)


def persist(req):
    with engine.begin() as conn:
        status = save_health(conn, req)
    return {"success": True, "status": status, "record_date": req.record_date, "collected_at": req.collected_at}


@router.post("/api/integrations/apple-health/export")
async def upload_export(request: Request):
    if not settings.APPLE_HEALTH_ENABLED:
        raise HTTPException(404, "Integration disabled")
    payload = bytearray()
    async for chunk in request.stream():
        payload.extend(chunk)
        if len(payload) > 32768:
            raise HTTPException(413, "Payload too large")
    try:
        data = json.loads(payload)
        return await run_in_threadpool(persist_export, data)
    except (ValueError, KeyError, TypeError, AttributeError):
        raise HTTPException(422, "Invalid summarized health export") from None


def persist_export(data):
    with engine.begin() as conn:
        return save_export(conn, data, datetime.now(ZoneInfo("Asia/Seoul")))
