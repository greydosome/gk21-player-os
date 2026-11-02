import secrets

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response

from app.core.access import matches
from app.core.config import settings
from app.core.session import COOKIE, LIFETIME, issue_session

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
def login_page():
    nonce = secrets.token_urlsafe(24)
    html = '''<!doctype html><html lang="ko"><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>GK21 로그인</title><style>body{background:#09090b;color:#fafafa;font-family:system-ui;margin:0;display:grid;min-height:100dvh;place-items:center}main{width:min(85vw,360px)}input,button{box-sizing:border-box;width:100%;padding:14px;border-radius:12px;margin-top:12px;font:inherit}button{background:#38bdf8;border:0;cursor:pointer}p{color:#a1a1aa;font-size:14px}#status{min-height:2em}</style>
<main><h1>GK21</h1><p>처음 한 번 로그인하면 이 기기에서 최대 30일간 유지됩니다.</p><form id="login">
<label for="password">앱 비밀번호</label><input id="password" type="password" autocomplete="current-password" required maxlength="256">
<button id="submit" type="submit">로그인</button><p id="status" role="status"></p></form></main>
<script nonce="NONCE">document.getElementById('login').addEventListener('submit',async e=>{e.preventDefault();const b=document.getElementById('submit'),s=document.getElementById('status');b.disabled=true;s.textContent='';try{const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password:document.getElementById('password').value})});if(r.ok){location.replace('/')}else{s.textContent=r.status===429?'잠시 후 다시 시도해 주세요.':'로그인하지 못했습니다. 비밀번호를 확인해 주세요.'}}catch{s.textContent='연결을 확인하고 다시 시도해 주세요.'}finally{b.disabled=false}});</script></html>'''.replace("NONCE", nonce)
    return HTMLResponse(html, headers={"Cache-Control": "no-store", "Content-Security-Policy": f"default-src 'none'; script-src 'nonce-{nonce}'; style-src 'unsafe-inline'; connect-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'", "Referrer-Policy": "no-referrer"})


@router.post("/api/auth/login")
async def login(request: Request):
    if not settings.APP_AUTH_ENABLED:
        raise HTTPException(404, "Authentication disabled")
    body = bytearray()
    async for chunk in request.stream():
        body.extend(chunk)
        if len(body) > 1024:
            raise HTTPException(413, "Payload too large")
    import json
    try:
        data = json.loads(body)
        password = data.get("password")
        valid = isinstance(password, str) and matches(password, settings.APP_AUTH_PASSWORD_SHA256)
    except (ValueError, AttributeError):
        valid = False
    if not valid:
        raise HTTPException(401, "Invalid credentials")
    try:
        token = issue_session()
    except ValueError:
        raise HTTPException(503, "Session configuration required") from None
    response = JSONResponse({"success": True})
    response.set_cookie(COOKIE, token, max_age=LIFETIME, secure=True, httponly=True, samesite="strict", path="/")
    return response


@router.post("/api/auth/logout")
def logout():
    response = JSONResponse({"success": True})
    response.delete_cookie(COOKIE, secure=True, httponly=True, samesite="strict", path="/")
    return response


@router.get("/api/auth/check")
def check():
    return Response(status_code=204, headers={"X-GK21-Auth": "enabled" if settings.APP_AUTH_ENABLED else "disabled"})
