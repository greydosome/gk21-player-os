"""Authenticated remote tools for the owner's ChatGPT workout conversation.

Run separately from the existing HTTP API; does not use an OpenAI API key.
"""
from datetime import date, datetime, timedelta
import html
import os

from fastapi.encoders import jsonable_encoder
from mcp.server.auth.settings import AuthSettings, ClientRegistrationOptions, RevocationOptions
from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings
from mcp.types import ToolAnnotations
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import HTMLResponse, JSONResponse, RedirectResponse

from app.api.workout_reports import persist, report_status
from app.core.config import settings
from app.schemas.workout_report import WorkoutReport, DETAILS
from app.services.health_records import KOREA
from app.services.mcp_oauth import OwnerOAuth, SCOPE


def create_server(provider):
    base = provider.base_url
    mcp = FastMCP('GK21 운동 기록',
        instructions='사용자가 실제 완료한 운동만 기존 GK21 항목에 반영한다. 계획·추천·질문은 저장하지 않는다. '
        '날짜는 사용자 메시지의 한국 시간 기준이며 어제 운동을 오늘로 옮기지 않는다. '
        '먼저 운동 분류와 해당 날짜 기록을 확인한다. 실제 원본 메시지 ID를 사용하고 없는 ID는 만들지 않는다. '
        '워치 시간 우선, 미기록은 명시된 경우만 추가한다. 중복 제출은 같은 메시지 ID와 같은 본문을 유지한다. '
        '다른 대화나 건강 원문을 읽는 도구는 없다.',
        auth_server_provider=provider,
        auth=AuthSettings(issuer_url=base, resource_server_url=provider.resource, validate_token_resource=True,
            required_scopes=[SCOPE], client_registration_options=ClientRegistrationOptions(
                enabled=True, valid_scopes=[SCOPE], default_scopes=[SCOPE]),
            revocation_options=RevocationOptions(enabled=True)),
        transport_security=TransportSecuritySettings(allowed_hosts=[base.split('://',1)[1]],
            allowed_origins=[base, 'https://chatgpt.com', 'https://chat.openai.com']),
        json_response=True, stateless_http=True, max_request_body_size=32768)

    def enabled():
        if not settings.WORKOUT_CONVERSATION_ENABLED:
            raise ValueError('Workout integration is disabled')

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    def workout_catalog() -> dict:
        """Use before reporting a completed workout to obtain existing categories and checkbox names."""
        enabled()
        return {'timezone':'Asia/Seoul', 'categories':{k:sorted(v) for k,v in DETAILS.items()}}

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=True, openWorldHint=False))
    def workout_status(record_date: date) -> dict:
        """Use to find prior message IDs and Watch session candidates for one workout date, within 14 days.

        Do not guess which Watch session matches when multiple candidates exist.
        """
        enabled()
        today = datetime.now(KOREA).date()
        if not today-timedelta(days=14) <= record_date <= today:
            raise ValueError('Date outside import window')
        return jsonable_encoder(report_status(record_date))

    @mcp.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False,
        idempotentHint=True, openWorldHint=False))
    def record_completed_workout(report: WorkoutReport) -> dict:
        """Use only for the user's actual completed workout or explicit correction in this conversation.

        Submit the real source message ID and timestamp, actual exercise date, known minutes or null,
        stable session_key, canonical category/details. Plans and questions must be skipped.
        Do not invent durations or mark untracked unless the user explicitly says Watch did not record it.
        Existing Watch time wins; reports refine the same diary items without duplicating minutes.
        Reuse the exact report on retry. Corrections use a new message ID and the same session_key.
        No raw conversation, sleep, pain, route, or heart-rate data is accepted.
        """
        enabled()
        return jsonable_encoder(persist(report))

    @mcp.custom_route('/gk21-connect', methods=['GET'])
    async def connect(request):
        request_id = request.query_params.get('request', '')
        pending = provider.pending(request_id)
        if not pending:
            return HTMLResponse('연결 요청이 만료되었습니다. ChatGPT에서 다시 연결해주세요.', status_code=410)
        redirect = provider.finish(request_id) if pending['approved'] and request.query_params.get('continue') == '1' else None
        if redirect:
            return RedirectResponse(redirect, status_code=303)
        code = html.escape(request_id)
        client = html.escape(pending['client_id'])
        callback = html.escape(pending['params']['redirect_uri'])
        refresh = '' if pending['approved'] else '<meta http-equiv="refresh" content="4">'
        action = (f'<p>서버 승인이 완료되었습니다.</p><p><a href="/gk21-connect?request={code}&amp;continue=1">ChatGPT로 돌아가기</a></p>'
                  if pending['approved'] else '<p>소유자의 서버 승인을 기다리고 있습니다. 이 페이지에서는 권한을 부여할 수 없습니다.</p>')
        return HTMLResponse(f'''<!doctype html><html lang="ko"><meta charset="utf-8">
        <meta name="viewport" content="width=device-width">{refresh}
        <title>GK21 연결 승인 대기</title><main style="max-width:640px;margin:60px auto;font:18px sans-serif;padding:20px">
        <h1>GK21 운동 기록 연결</h1><p>운동 날짜의 워치 기록 조회와 완료 운동 저장 권한을 요청했습니다.</p>
        <p>수면·식단·심박·이동 경로를 제공하지 않습니다.</p>
        {action}
        <p>연결 요청 번호</p><code>{code}</code><p>클라이언트: {client}</p><p>돌아갈 주소: {callback}</p></main></html>''')

    app = mcp.streamable_http_app()

    class PrivateHeaders(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            if request.url.scheme != 'https':
                return JSONResponse({'detail':'HTTPS required'}, status_code=403)
            response = await call_next(request)
            response.headers.update({'Cache-Control':'no-store', 'Referrer-Policy':'no-referrer',
                'X-Content-Type-Options':'nosniff', 'Content-Security-Policy':"default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'none'; base-uri 'none'"})
            return response

    app.add_middleware(PrivateHeaders)
    return app


def app_factory():
    return create_server(OwnerOAuth(os.environ.get('GK21_MCP_AUTH_DB', '/var/lib/gk21-mcp/oauth.sqlite3'),
                                   os.environ.get('GK21_MCP_BASE_URL', 'https://217.142.230.185')))
