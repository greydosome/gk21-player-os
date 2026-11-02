import hashlib
import time

from fastapi.testclient import TestClient

from app.main import app
from app.core.config import settings
from app.core.session import COOKIE, issue_session, valid_session

PASSWORD = "test-password-not-a-real-secret"


def setup(monkeypatch):
    monkeypatch.setattr(settings, "APP_AUTH_ENABLED", True)
    monkeypatch.setattr(settings, "APP_SESSION_SECRET", "test-only-session-secret-32-characters-long")
    monkeypatch.setattr(settings, "APP_AUTH_PASSWORD_SHA256", hashlib.sha256(PASSWORD.encode()).hexdigest())


def test_login_cookie_and_logout(monkeypatch):
    setup(monkeypatch)
    with TestClient(app, base_url="https://testserver") as client:
        assert client.get("/api/auth/check").status_code == 401
        page = client.get("/login")
        assert page.status_code == 200 and "30일" in page.text
        assert "frame-ancestors 'none'" in page.headers["content-security-policy"]
        assert client.post("/api/auth/login", json={"password": PASSWORD}).status_code == 403
        headers = {"Origin": "https://testserver"}
        assert client.post("/api/auth/login", json={"password": "wrong"}, headers=headers).status_code == 401
        result = client.post("/api/auth/login", json={"password": PASSWORD}, headers=headers)
        assert result.status_code == 200
        cookie = result.headers["set-cookie"]
        for attribute in ["Secure", "HttpOnly", "SameSite=strict", "Max-Age=2592000", "Path=/"]:
            assert attribute in cookie
        assert client.get("/api/auth/check").status_code == 204
        # Browser session cannot use the upload-only endpoint.
        assert client.post("/api/integrations/apple-health/daily", json={}, headers=headers).status_code == 401
        assert client.post("/api/auth/logout", json={}, headers={"Origin": "https://elsewhere.invalid"}).status_code == 403
        assert client.post("/api/auth/logout", json={}, headers=headers).status_code == 200
        assert client.get("/api/auth/check").status_code == 401


def test_session_tampering_expiry_and_revocation(monkeypatch):
    setup(monkeypatch)
    token = issue_session()
    assert valid_session(token)
    assert not valid_session(token + "x")
    assert not valid_session("not.a.session")
    with monkeypatch.context() as patch:
        patch.setattr(time, "time", lambda: 9999999999)
        assert not valid_session(token)
    monkeypatch.setattr(settings, "APP_AUTH_PASSWORD_SHA256", "rotated")
    assert not valid_session(token)


def test_login_tls_configuration_and_limits(monkeypatch):
    setup(monkeypatch)
    with TestClient(app, base_url="http://testserver") as client:
        assert client.get("/login").status_code == 403
    with TestClient(app, base_url="https://testserver") as client:
        headers = {"Origin": "https://testserver", "Content-Type": "application/json"}
        assert client.post("/api/auth/login", content='x' * 1025, headers=headers).status_code == 413
        assert client.post("/api/auth/login", json=[], headers=headers).status_code == 401
        monkeypatch.setattr(settings, "APP_SESSION_SECRET", "")
        assert client.post("/api/auth/login", json={"password": PASSWORD}, headers=headers).status_code == 503
        assert COOKIE not in client.cookies
