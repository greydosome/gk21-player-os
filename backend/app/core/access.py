"""Single-owner access protection. No secrets are supplied by this repository."""
import base64
import hashlib
import hmac

from starlette.responses import JSONResponse
from app.core.config import settings
from app.core.session import COOKIE, valid_session

UPLOAD_PATH = "/api/integrations/apple-health/daily"


def matches(value, expected_hash):
    return bool(expected_hash) and hmac.compare_digest(hashlib.sha256(value.encode()).hexdigest(), expected_hash)


async def access_guard(request, call_next):
    enabled = settings.APP_AUTH_ENABLED
    if settings.APPLE_HEALTH_ENABLED and not enabled:
        return JSONResponse({"detail": "Health integration requires app authentication"}, status_code=503)
    cookie_authenticated = False
    public_login = request.url.path in {"/login", "/api/auth/login"}
    if enabled:
        if request.url.scheme != "https":
            return JSONResponse({"detail": "HTTPS required"}, status_code=403)
        authorization = request.headers.get("authorization", "")
        if public_login:
            valid, challenge = True, "Session"
        elif request.url.path.rstrip("/") == UPLOAD_PATH:
            valid = authorization.startswith("Bearer ") and matches(authorization[7:], settings.APPLE_HEALTH_TOKEN_SHA256)
            challenge = "Bearer"
        else:
            valid = False
            try:
                scheme, encoded = authorization.split(" ", 1)
                username, password = base64.b64decode(encoded, validate=True).decode().split(":", 1)
                valid = scheme.lower() == "basic" and hmac.compare_digest(username.encode(), settings.APP_AUTH_USER.encode()) and matches(password, settings.APP_AUTH_PASSWORD_SHA256)
            except (ValueError, UnicodeError):
                pass
            cookie_authenticated = valid_session(request.cookies.get(COOKIE))
            valid = valid or cookie_authenticated
            challenge = "Session"
        if not valid:
            return JSONResponse({"detail": "Authentication required"}, status_code=401, headers={"WWW-Authenticate": challenge})
    if enabled and request.method in {"POST", "PUT", "PATCH", "DELETE"}:
        if request.headers.get("content-type", "").split(";")[0] != "application/json":
            return JSONResponse({"detail": "JSON required"}, status_code=415)
        origin = request.headers.get("origin")
        if (cookie_authenticated or public_login) and not origin:
            return JSONResponse({"detail": "Origin required"}, status_code=403)
        if origin and origin != f"https://{request.headers.get('host')}":
            return JSONResponse({"detail": "Origin denied"}, status_code=403)
    response = await call_next(request)
    if enabled:
        response.headers["Cache-Control"] = "no-store"
    return response
