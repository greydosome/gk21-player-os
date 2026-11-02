"""Signed, fixed-lifetime owner sessions; password/key rotation revokes all sessions."""
import hashlib
import hmac
import secrets
import time

from app.core.config import settings

COOKIE = "__Host-gk21-session"
LIFETIME = 30 * 24 * 60 * 60


def signature(payload):
    message = f"{settings.APP_AUTH_USER}:{settings.APP_AUTH_PASSWORD_SHA256}:{payload}"
    return hmac.new(settings.APP_SESSION_SECRET.encode(), message.encode(), hashlib.sha256).hexdigest()


def issue_session():
    if len(settings.APP_SESSION_SECRET) < 32:
        raise ValueError("Session secret must contain at least 32 characters")
    payload = f"{int(time.time()) + LIFETIME}.{secrets.token_hex(16)}"
    return f"{payload}.{signature(payload)}"


def valid_session(token):
    if not token or len(token) > 200 or len(settings.APP_SESSION_SECRET) < 32:
        return False
    try:
        expiration, nonce, mac = token.split(".")
        return (0 < int(expiration) - time.time() <= LIFETIME
                and len(nonce) == 32
                and hmac.compare_digest(signature(f"{expiration}.{nonce}"), mac))
    except (ValueError, TypeError):
        return False
