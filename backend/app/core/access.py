"""Protect only the Apple Health upload; existing app/API access is unchanged."""
import hashlib
import hmac

from starlette.responses import JSONResponse
from app.core.config import settings

UPLOAD_PATH = "/api/integrations/apple-health/daily"
EXPORT_PATH = "/api/integrations/apple-health/export"


async def access_guard(request, call_next):
    if request.url.path.rstrip("/") not in {UPLOAD_PATH, EXPORT_PATH}:
        return await call_next(request)
    if not settings.APPLE_HEALTH_ENABLED:
        return JSONResponse({"detail": "Integration disabled"}, status_code=404)
    if request.url.scheme != "https":
        return JSONResponse({"detail": "HTTPS required"}, status_code=403)
    authorization = request.headers.get("authorization", "")
    expected = settings.APPLE_HEALTH_TOKEN_SHA256
    valid = (bool(expected) and authorization.startswith("Bearer ")
             and hmac.compare_digest(hashlib.sha256(authorization[7:].encode()).hexdigest(), expected))
    if not valid:
        return JSONResponse({"detail": "Upload token required"}, status_code=401, headers={"WWW-Authenticate": "Bearer"})
    if request.headers.get("content-type", "").split(";")[0] != "application/json":
        return JSONResponse({"detail": "JSON required"}, status_code=415)
    origin = request.headers.get("origin")
    if origin and origin != f"https://{request.headers.get('host')}":
        return JSONResponse({"detail": "Origin denied"}, status_code=403)
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response
