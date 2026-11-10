import asyncio
import base64
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import time
from urllib.parse import parse_qs, urlsplit

from fastapi.testclient import TestClient
import pytest
from mcp.server.auth.provider import AuthorizationParams, AuthorizeError, RegistrationError, TokenError
from mcp.shared.auth import OAuthClientInformationFull

from app.core.config import settings
from app.mcp_server import create_server
from app.services.mcp_oauth import OwnerOAuth, SCOPE

BASE = 'https://gk21.example'
CALLBACK = 'https://chatgpt.com/connector_platform/oauth_redirect'
VERIFIER = 'a' * 64
CHALLENGE = base64.urlsafe_b64encode(hashlib.sha256(VERIFIER.encode()).digest()).decode().rstrip('=')


def run(coro):
    return asyncio.run(coro)


@pytest.fixture
def oauth(tmp_path):
    return OwnerOAuth(tmp_path/'oauth.sqlite3', BASE)


def client_info(client_id='chatgpt'):
    return OAuthClientInformationFull(client_id=client_id, redirect_uris=[CALLBACK],
        token_endpoint_auth_method='none', grant_types=['authorization_code','refresh_token'],
        response_types=['code'], scope=SCOPE)


def params(**changes):
    values = dict(state='synthetic-state', scopes=[SCOPE], code_challenge=CHALLENGE,
        redirect_uri=CALLBACK, redirect_uri_provided_explicitly=True, resource=BASE+'/mcp')
    return AuthorizationParams(**(values|changes))


def grant(oauth):
    client = client_info()
    run(oauth.register_client(client))
    request_id = parse_qs(urlsplit(run(oauth.authorize(client, params()))).query)['request'][0]
    assert oauth.finish(request_id) is None  # No owner approval, no code.
    oauth.approve(request_id)
    code = parse_qs(urlsplit(oauth.finish(request_id)).query)['code'][0]
    return client, code


def test_owner_approval_codes_single_use_tokens_survive_restart_and_are_hashed(oauth):
    client, code = grant(oauth)
    authorization = run(oauth.load_authorization_code(client, code))
    token = run(oauth.exchange_authorization_code(client, authorization))
    assert run(oauth.load_authorization_code(client, code)) is None
    with pytest.raises(TokenError):
        run(oauth.exchange_authorization_code(client, authorization))
    restart = OwnerOAuth(oauth.path, BASE)
    access = run(restart.load_access_token(token.access_token))
    assert access.resource == BASE+'/mcp'
    assert access.subject == 'gk21-owner'
    assert oauth.path.stat().st_mode & 0o777 == 0o600
    raw = oauth.path.read_bytes()
    assert token.access_token.encode() not in raw
    assert token.refresh_token.encode() not in raw
    assert code.encode() not in raw
    refresh = run(restart.load_refresh_token(client, token.refresh_token))
    newer = run(restart.exchange_refresh_token(client, refresh, [SCOPE]))
    assert run(restart.load_access_token(token.access_token)) is None
    assert run(restart.load_refresh_token(client, token.refresh_token)) is None
    assert run(restart.load_access_token(newer.access_token))
    run(restart.revoke_token(run(restart.load_access_token(newer.access_token))))
    assert run(restart.load_refresh_token(client, newer.refresh_token)) is None


def test_rejects_external_redirect_resource_scope_and_expired_approval(oauth):
    bad = client_info(); bad.redirect_uris=['https://attacker.example/callback']
    with pytest.raises(RegistrationError):
        run(oauth.register_client(bad))
    for changes in ({'resource':'https://other.example/mcp'}, {'scopes':['everything']}, {'code_challenge':'bad'}):
        with pytest.raises(AuthorizeError):
            run(oauth.authorize(client_info(), params(**changes)))
    request_id = parse_qs(urlsplit(run(oauth.authorize(client_info(), params()))).query)['request'][0]
    with oauth.db() as db:
        db.execute('UPDATE pending SET expires=?', (time.time()-1,))
    assert oauth.pending(request_id) is None
    with pytest.raises(ValueError):
        oauth.approve(request_id)


def test_concurrent_code_exchange_issues_only_one_grant(oauth):
    client, code = grant(oauth)
    auth = run(oauth.load_authorization_code(client, code))
    def exchange(_):
        try:
            run(oauth.exchange_authorization_code(client, auth))
            return True
        except TokenError:
            return False
    with ThreadPoolExecutor(2) as pool:
        assert sum(pool.map(exchange, range(2))) == 1


def test_http_oauth_pkce_discovery_and_authenticated_mcp(oauth, monkeypatch):
    monkeypatch.setattr(settings, 'WORKOUT_CONVERSATION_ENABLED', True)
    with TestClient(create_server(oauth), base_url=BASE) as http:
        unauth = http.post('/mcp', json={})
        assert unauth.status_code == 401
        assert 'resource_metadata=' in unauth.headers['www-authenticate']
        assert http.get('/.well-known/oauth-protected-resource/mcp').json()['resource']==BASE+'/mcp'
        metadata = http.get('/.well-known/oauth-authorization-server').json()
        assert metadata['issuer']==BASE+'/' or metadata['issuer']==BASE
        registration = http.post('/register', json={'redirect_uris':[CALLBACK],
            'token_endpoint_auth_method':'none', 'grant_types':['authorization_code','refresh_token'],
            'response_types':['code'], 'scope':SCOPE})
        assert registration.status_code == 201
        client_id = registration.json()['client_id']
        query = dict(client_id=client_id, response_type='code', redirect_uri=CALLBACK,
            scope=SCOPE, state='state-1', code_challenge=CHALLENGE, code_challenge_method='S256', resource=BASE+'/mcp')
        pending = http.get('/authorize', params=query, follow_redirects=False)
        assert pending.status_code == 302
        request_id = parse_qs(urlsplit(pending.headers['location']).query)['request'][0]
        page = http.get(pending.headers['location'])
        assert '승인' in page.text and page.headers['cache-control']=='no-store'
        # No HTTP approve endpoint; owner CLI controls the actual permission grant.
        assert http.post('/gk21-connect', json={'request':request_id}).status_code==405
        oauth.approve(request_id)
        redirect = http.get(pending.headers['location'], follow_redirects=False)
        code = parse_qs(urlsplit(redirect.headers['location']).query)['code'][0]
        body = dict(grant_type='authorization_code', client_id=client_id,
            code=code, redirect_uri=CALLBACK, code_verifier='incorrect', resource=BASE+'/mcp')
        assert http.post('/token', data=body).status_code == 400
        body['code_verifier']=VERIFIER
        token_response = http.post('/token', data=body)
        assert token_response.status_code==200, token_response.text
        token = token_response.json()['access_token']
        headers={'Authorization':'Bearer '+token, 'Accept':'application/json, text/event-stream'}
        def rpc(method, payload=None):
            return http.post('/mcp', json={'jsonrpc':'2.0', 'id':1, 'method':method, 'params':payload or {}}, headers=headers)
        init = rpc('initialize', {'protocolVersion':'2025-06-18','capabilities':{},'clientInfo':{'name':'synthetic','version':'1'}})
        assert init.status_code==200, init.text
        tools = rpc('tools/list').json()['result']['tools']
        assert {t['name'] for t in tools}=={'workout_catalog','workout_status','record_completed_workout'}
        assert next(t for t in tools if t['name']=='record_completed_workout')['annotations']['readOnlyHint'] is False
        result = rpc('tools/call', {'name':'workout_catalog','arguments':{}}).json()['result']
        assert not result.get('isError') and '런지' in json.dumps(result,ensure_ascii=False)
        assert http.post('/token', data=body).status_code==400
        refresh_response=http.post('/token',data={'grant_type':'refresh_token','client_id':client_id,
            'refresh_token':token_response.json()['refresh_token'],'resource':BASE+'/mcp'})
        assert refresh_response.status_code==200, refresh_response.text
        assert rpc('tools/list').status_code==401  # Prior access token rotated.
    with TestClient(create_server(oauth),base_url='http://gk21.example') as plain:
        assert plain.get('/.well-known/oauth-authorization-server').status_code==403
