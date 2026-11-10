"""Owner-only enrollment/revocation. Run on the server with its protected state file."""
import argparse
import json
import os
import time
from app.services.mcp_oauth import OwnerOAuth

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['pending', 'approve', 'revoke-all'])
parser.add_argument('request_id', nargs='?')
args = parser.parse_args()
provider = OwnerOAuth(os.environ.get('GK21_MCP_AUTH_DB', '/var/lib/gk21-mcp/oauth.sqlite3'),
                      os.environ.get('GK21_MCP_BASE_URL', 'https://217.142.230.185'))
if args.action == 'pending':
    with provider.db() as db:
        for request_id, data in db.execute('SELECT id,data FROM pending WHERE expires>? AND approved=0', (time.time(),)):
            print(json.dumps({'request_id':request_id, **json.loads(data)}, ensure_ascii=False))
elif args.action == 'approve':
    if not args.request_id:
        parser.error('request_id required')
    provider.approve(args.request_id)
    print('Connection approved')
else:
    with provider.db() as db:
        db.execute('DELETE FROM tokens')
        db.execute('DELETE FROM pending')
    print('All connections revoked')
