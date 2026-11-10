"""Submit a structured, explicitly confirmed workout or meal report to the private GK21 API.

Reading ChatGPT messages and interpreting completion is performed by the authorized
local heartbeat, not by scraping sessions or embedding ChatGPT credentials here.
"""
import argparse
import json
from pathlib import Path
import re
import shlex
import subprocess
import urllib.parse
import urllib.request
from uuid import uuid4


def eligible(payload, resource):
    if resource == 'meal':
        return payload.get('kind') in ('consumed','correction','delete') and payload.get('confirmed_by_user') is True
    return payload.get('kind') == 'completed' and bool(payload.get('workouts'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--resource', choices=['workout','meal'], default='workout')
    parser.add_argument('--token-file', type=Path, required=True)
    parser.add_argument('--base-url', default='https://217.142.230.185')
    parser.add_argument('--ssh-host', help='Use the existing authorized SSH connection to the GK21 server')
    commands = parser.add_subparsers(dest='command', required=True)
    submit = commands.add_parser('submit')
    submit.add_argument('--file', type=Path, required=True)
    status = commands.add_parser('status')
    status.add_argument('--date', required=True)
    args = parser.parse_args()
    if args.ssh_host:
        if args.ssh_host.startswith('-') or not re.fullmatch(r'[A-Za-z0-9_.@-]+', args.ssh_host):
            parser.error('Invalid SSH host')
        remote_file = '/tmp/gk21-workout-report-' + uuid4().hex + '.json'
        command = ['sudo', 'python3', '/home/rocky/gk21/scripts/sync_workout_conversation.py',
                   '--token-file', str(args.token_file), '--base-url', args.base_url, args.command]
        if args.resource != 'workout':
            command[3:3] = ['--resource', args.resource]
        ssh_options = ['-o', 'ControlMaster=no', '-o', 'ControlPath=none', '-o', 'BatchMode=yes',
                       '-o', 'ConnectTimeout=8', '-o', 'ServerAliveInterval=5', '-o', 'ServerAliveCountMax=1']
        ssh = ['ssh', *ssh_options, args.ssh_host]
        if args.command == 'submit':
            payload = json.loads(args.file.read_text())
            if not eligible(payload, args.resource):
                print(json.dumps({'success': True, 'status': 'skipped_not_confirmed_consumption' if args.resource == 'meal' else 'skipped_no_completed_workout'}))
                return
            if args.file.stat().st_size > 32768:
                parser.error('Report exceeds API limit')
            subprocess.run(['scp', '-q', *ssh_options, str(args.file.resolve()), args.ssh_host + ':' + remote_file], check=True)
            command += ['--file', remote_file]
        else:
            command += ['--date', args.date]
        try:
            subprocess.run(ssh + [shlex.join(command)], check=True)
        finally:
            if args.command == 'submit':
                subprocess.run(ssh + [shlex.join(['rm', '-f', remote_file])], check=True)
        return
    base = urllib.parse.urlsplit(args.base_url)
    if base.scheme != 'https' or base.username or base.password or base.query or base.fragment:
        parser.error('A clean HTTPS server URL is required')
    token = args.token_file.read_text().strip()
    if len(token) < 24:
        parser.error('Upload token not configured')
    url = args.base_url.rstrip('/') + '/api/integrations/' + args.resource + '-reports'
    body = None
    if args.command == 'submit':
        payload = json.loads(args.file.read_text())
        if not eligible(payload, args.resource):
            print(json.dumps({'success': True, 'status': 'skipped_not_confirmed_consumption' if args.resource == 'meal' else 'skipped_no_completed_workout'}))
            return
        body = json.dumps(payload, ensure_ascii=False).encode()
        if len(body) > 32768:
            parser.error('Report exceeds API limit')
    else:
        url += '?' + urllib.parse.urlencode({'record_date': args.date})
    request = urllib.request.Request(url, data=body, headers={
        'Authorization': 'Bearer ' + token, 'Content-Type': 'application/json'})
    # No unverified TLS context and no HTTP downgrade or redirect of credentials.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None
    with urllib.request.build_opener(NoRedirect).open(request, timeout=30) as response:
        result = json.load(response)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
