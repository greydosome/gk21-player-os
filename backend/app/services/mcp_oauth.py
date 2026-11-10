"""Single-owner OAuth: enrollment is approved through the owner's SSH access.

No web request can approve itself. Codes and tokens are stored as hashes;
the SDK handles PKCE, client authentication, and redirect matching.
"""
import hashlib
import json
import os
import re
from pathlib import Path
import secrets
import sqlite3
import time
from urllib.parse import urlencode, urlsplit, urlunsplit, parse_qsl

from mcp.server.auth.provider import (
    AccessToken, AuthorizationCode, AuthorizationParams, AuthorizeError,
    RefreshToken, RegistrationError, TokenError,
)
from mcp.shared.auth import OAuthClientInformationFull, OAuthToken

SCOPE = 'workout:sync'
CALLBACKS = {'https://chatgpt.com/connector_platform/oauth_redirect',
             'https://chat.openai.com/connector_platform/oauth_redirect'}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


class Transaction:
    # A class context manager also preserves SDK's frozen exception dataclasses.
    def __init__(self, path):
        self.path = path

    def __enter__(self):
        self.conn = sqlite3.connect(self.path, timeout=10)
        self.conn.execute('BEGIN IMMEDIATE')
        return self.conn

    def __exit__(self, exc_type, exc_value, traceback):
        try:
            if exc_type is None:
                self.conn.commit()
            else:
                self.conn.rollback()
        finally:
            self.conn.close()
        return False


class OwnerOAuth:
    def __init__(self, path, base_url):
        self.path = Path(path)
        self.base_url = base_url.rstrip('/')
        self.resource = self.base_url + '/mcp'
        callback = os.environ.get('GK21_MCP_CALLBACK_URL')
        if callback and not re.fullmatch(r'https://chatgpt\.com/connector/oauth/[A-Za-z0-9_-]+', callback):
            raise ValueError('Invalid ChatGPT callback configuration')
        self.callbacks = {callback} if callback else CALLBACKS
        if not self.path.exists():
            self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            os.close(fd)
        os.chmod(self.path, 0o600)
        with self.db() as db:
            db.executescript('''
                CREATE TABLE IF NOT EXISTS clients (id TEXT PRIMARY KEY, data TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS pending
                    (id TEXT PRIMARY KEY, data TEXT NOT NULL, expires REAL NOT NULL, approved INTEGER DEFAULT 0);
                CREATE TABLE IF NOT EXISTS tokens
                    (hash TEXT PRIMARY KEY, kind TEXT NOT NULL, data TEXT NOT NULL,
                     expires REAL NOT NULL, family TEXT NOT NULL);
            ''')

    def db(self):
        return Transaction(self.path)

    def put_token(self, db, kind, value, data, expires, family):
        data = {k: v for k, v in data.items() if k not in {'code', 'token'}}
        db.execute('INSERT INTO tokens VALUES (?,?,?,?,?)',
                   (digest(value), kind, json.dumps(data), expires, family))

    def get_token(self, kind, value, model, client_id=None):
        with self.db() as db:
            row = db.execute('SELECT data,expires FROM tokens WHERE hash=? AND kind=?',
                             (digest(value), kind)).fetchone()
        if not row or row[1] <= time.time():
            return None
        data = json.loads(row[0])
        if client_id is not None and data['client_id'] != client_id:
            return None
        data['code' if kind == 'code' else 'token'] = value
        return model.model_validate(data)

    async def get_client(self, client_id):
        with self.db() as db:
            row = db.execute('SELECT data FROM clients WHERE id=?', (client_id,)).fetchone()
        return OAuthClientInformationFull.model_validate_json(row[0]) if row else None

    async def register_client(self, client_info):
        if not client_info.redirect_uris or any(str(uri) not in self.callbacks for uri in client_info.redirect_uris):
            raise RegistrationError('invalid_redirect_uri', 'Only the ChatGPT connector callback is allowed')
        if client_info.scope and set(client_info.scope.split()) != {SCOPE}:
            raise RegistrationError('invalid_client_metadata', 'Only workout:sync is supported')
        with self.db() as db:
            if db.execute('SELECT count(*) FROM clients').fetchone()[0] >= 256:
                raise RegistrationError('invalid_client_metadata', 'Registration limit reached')
            db.execute('INSERT INTO clients VALUES (?,?)', (client_info.client_id, client_info.model_dump_json()))

    async def authorize(self, client, params):
        if params.resource != self.resource or params.scopes != [SCOPE]:
            raise AuthorizeError('invalid_request', 'Exact workout resource and scope are required')
        if not params.code_challenge or len(params.code_challenge) != 43:
            raise AuthorizeError('invalid_request', 'S256 PKCE required')
        request_id = secrets.token_urlsafe(32)
        data = {'client_id': client.client_id, 'params': params.model_dump(mode='json')}
        with self.db() as db:
            db.execute('DELETE FROM pending WHERE expires<?', (time.time(),))
            if db.execute('SELECT count(*) FROM pending').fetchone()[0] >= 100:
                raise AuthorizeError('temporarily_unavailable', 'Too many pending requests')
            db.execute('INSERT INTO pending(id,data,expires) VALUES (?,?,?)',
                       (request_id, json.dumps(data), time.time()+600))
        return self.base_url + '/gk21-connect?' + urlencode({'request': request_id})

    def pending(self, request_id):
        with self.db() as db:
            row = db.execute('SELECT data,expires,approved FROM pending WHERE id=?', (request_id,)).fetchone()
        if not row or row[1] <= time.time():
            return None
        return {**json.loads(row[0]), 'approved': bool(row[2])}

    def approve(self, request_id):
        """Admin CLI only; never exposed as an HTTP action."""
        with self.db() as db:
            changed = db.execute('UPDATE pending SET approved=1 WHERE id=? AND expires>? AND approved=0',
                                 (request_id, time.time())).rowcount
            if changed != 1:
                raise ValueError('Request missing, expired, or already approved')

    def finish(self, request_id):
        with self.db() as db:
            row = db.execute('SELECT data FROM pending WHERE id=? AND approved=1 AND expires>?',
                             (request_id, time.time())).fetchone()
            if not row:
                return None
            db.execute('DELETE FROM pending WHERE id=?', (request_id,))
            data = json.loads(row[0])
            params = AuthorizationParams.model_validate(data['params'])
            code = secrets.token_urlsafe(32)
            auth = AuthorizationCode(code=code, client_id=data['client_id'], scopes=[SCOPE],
                expires_at=time.time()+120, code_challenge=params.code_challenge,
                redirect_uri=params.redirect_uri, redirect_uri_provided_explicitly=params.redirect_uri_provided_explicitly,
                resource=self.resource, subject='gk21-owner')
            self.put_token(db, 'code', code, auth.model_dump(mode='json'), auth.expires_at, secrets.token_hex(16))
        parts = urlsplit(str(params.redirect_uri))
        query = parse_qsl(parts.query) + [('code', code)]
        if params.state is not None:
            query.append(('state', params.state))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), ''))

    async def load_authorization_code(self, client, authorization_code):
        return self.get_token('code', authorization_code, AuthorizationCode, client.client_id)

    def issue(self, db, client_id, scopes, family):
        now = int(time.time())
        access = secrets.token_urlsafe(48)
        refresh = secrets.token_urlsafe(48)
        common = dict(client_id=client_id, scopes=scopes, resource=self.resource, subject='gk21-owner')
        self.put_token(db, 'access', access, dict(**common, expires_at=now+3600), now+3600, family)
        self.put_token(db, 'refresh', refresh, dict(**common, expires_at=now+90*86400), now+90*86400, family)
        return OAuthToken(access_token=access, token_type='Bearer', expires_in=3600,
                          refresh_token=refresh, scope=' '.join(scopes))

    def consume(self, db, kind, value):
        row = db.execute('SELECT family FROM tokens WHERE hash=? AND kind=? AND expires>?',
                         (digest(value), kind, time.time())).fetchone()
        if not row:
            raise TokenError('invalid_grant', 'Grant expired or already used')
        db.execute('DELETE FROM tokens WHERE hash=?', (digest(value),))
        return row[0]

    async def exchange_authorization_code(self, client, authorization_code):
        if authorization_code.client_id != client.client_id or authorization_code.resource != self.resource:
            raise TokenError('invalid_grant', 'Grant does not match client or resource')
        with self.db() as db:
            family = self.consume(db, 'code', authorization_code.code)
            return self.issue(db, client.client_id, authorization_code.scopes, family)

    async def load_refresh_token(self, client, refresh_token):
        return self.get_token('refresh', refresh_token, RefreshToken, client.client_id)

    async def exchange_refresh_token(self, client, refresh_token, scopes):
        if (refresh_token.client_id != client.client_id or refresh_token.resource != self.resource
                or set(scopes) != {SCOPE} or not set(scopes) <= set(refresh_token.scopes)):
            raise TokenError('invalid_scope', 'Grant does not match client, scope, or resource')
        with self.db() as db:
            family = self.consume(db, 'refresh', refresh_token.token)
            db.execute('DELETE FROM tokens WHERE family=?', (family,))
            return self.issue(db, client.client_id, scopes, family)

    async def load_access_token(self, token):
        return self.get_token('access', token, AccessToken)

    async def revoke_token(self, token):
        with self.db() as db:
            row = db.execute('SELECT family FROM tokens WHERE hash=?', (digest(token.token),)).fetchone()
            if row:
                db.execute('DELETE FROM tokens WHERE family=?', (row[0],))
