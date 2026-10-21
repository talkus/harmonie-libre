"""Capability-scoped mission proof proxy; no worker replay or client verdicts."""
import datetime
import json
import re
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from http.server import BaseHTTPRequestHandler

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import bridge_runtime

PROJECT_URL = 'https://jljelwrblfitvjbmrykx.supabase.co'
PUBLIC_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsamVsd3JibGZpdHZqYm1yeWt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk1OTEyMTIsImV4cCI6MjEwNTE2NzIxMn0.SdG9TCcSOpXEPEVhZiXWwSPlZFxrXXnnxK6rLfSe3SQ'
CAP = re.compile(r'[0-9a-f]{64}\Z', re.ASCII)
MAX_BODY = 8192
MAX_RESPONSE = 1048576

class InvalidInput(ValueError):
    pass

class OutcomeUnknown(Exception):
    pass

def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput('DUPLICATE_JSON_KEY')
        result[key] = value
    return result

def validate(body):
    if type(body) is not dict or set(body) != {'action', 'input'}:
        raise InvalidInput('INVALID_ENVELOPE')
    action, data = body['action'], body['input']
    if action not in ('status', 'verify', 'receipt') or type(data) is not dict:
        raise InvalidInput('ACTION_NOT_ALLOWED')
    common = {'job_id', 'capability'}
    required = common | ({'mission_id', 'request_id'} if action == 'verify' else {'mission_id', 'target_request_id'} if action == 'receipt' else set())
    allowed = required | ({'mission_id'} if action == 'status' else set())
    if set(data) - allowed or required - set(data):
        raise InvalidInput('INVALID_FIELDS')
    if type(data['capability']) is not str or not CAP.fullmatch(data['capability']):
        raise InvalidInput('INVALID_CAPABILITY')
    for key in ('job_id', 'mission_id', 'request_id', 'target_request_id'):
        if key in data:
            value = data[key]
            try:
                if type(value) is not str or str(uuid.UUID(value)) != value:
                    raise ValueError()
            except (ValueError, AttributeError):
                raise InvalidInput('INVALID_REFERENCE') from None
    return action, dict(data)

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *_):
        raise OutcomeUnknown()

def call_rpc(action, data):
    request = urllib.request.Request(PROJECT_URL + '/rest/v1/rpc/sol_missions_api',
        data=json.dumps({'p_action': action, 'p_input': data, 'p_actor': 'capability:job-owner'}, ensure_ascii=False, separators=(',', ':')).encode(),
        headers={'Content-Type': 'application/json', 'apikey': PUBLIC_ANON_KEY, 'Authorization': 'Bearer ' + PUBLIC_ANON_KEY}, method='POST')
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=20) as response:
            raw = response.read(MAX_RESPONSE + 1)
        if len(raw) > MAX_RESPONSE:
            raise OutcomeUnknown()
        value = json.loads(raw, object_pairs_hook=unique_object)
        if type(value) is not dict:
            raise OutcomeUnknown()
        return value
    except Exception:
        raise OutcomeUnknown() from None

def scrub(value, secrets):
    if isinstance(value, dict):
        return {key: scrub(item, secrets) for key, item in value.items() if key not in {'capability', 'parent_capability', 'bridge_token', 'runtime_identity', 'token', 'source_csv', 'capability_hash', 'token_sha256'}}
    if isinstance(value, list):
        return [scrub(item, secrets) for item in value]
    if isinstance(value, str):
        for secret in secrets:
            if secret:
                value = value.replace(secret, '[REDACTED]')
    return value


def dispatch(body, rpc=call_rpc, release_loader=bridge_runtime.load_release, token_loader=bridge_runtime.server_token):
    action, data = validate(body)
    secrets = [data['capability']]
    if action == 'verify':
        try:
            identity = release_loader()
            token = token_loader()
            secrets.append(token)
            data['runtime_identity'] = {**identity, 'bridge_token': token, 'observed_at': datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')}
        except Exception:
            return {'ok': False, 'status': 'UNKNOWN', 'error': 'CURRENT_RUNTIME_UNCONFIRMED', 'job_id': data['job_id'], 'mission_id': data['mission_id'], 'request_id': data['request_id'], 'current_reuse_authorized': False, 'automatic_retry': False}
    value = rpc(action, data)
    if value.get('job_id') != data['job_id']:
        if value.get('ok') is False:
            return {'ok': False, 'status': 'REJECTED', 'error': 'NOT_AUTHORIZED_OR_INVALID_REFERENCE', 'job_id': data['job_id'], 'current_reuse_authorized': False, 'automatic_retry': False}
        raise OutcomeUnknown()
    if action == 'verify' and (value.get('mission_id') != data['mission_id'] or value.get('request_id') != data['request_id']):
        raise OutcomeUnknown()
    if action == 'receipt' and (value.get('mission_id') != data['mission_id'] or value.get('target_request_id') != data['target_request_id']):
        raise OutcomeUnknown()
    if action == 'status' and 'mission_id' in data and value.get('mission_id') != data['mission_id']:
        raise OutcomeUnknown()
    return scrub(value, secrets)

class handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, value):
        raw = json.dumps(value, ensure_ascii=False, separators=(',', ':')).encode()
        self.send_response(status)
        for key, val in {'Content-Type': 'application/json; charset=utf-8', 'Cache-Control': 'no-store', 'X-Content-Type-Options': 'nosniff', 'Referrer-Policy': 'no-referrer', 'Content-Length': str(len(raw))}.items():
            self.send_header(key, val)
        self.end_headers()
        self.wfile.write(raw)

    def do_GET(self):
        if '?' in self.path:
            self.reply(400, {'ok': False, 'error': 'QUERY_FORBIDDEN'})
        else:
            self.reply(200, {'ok': True, 'service': 'SOL-Missions', 'scope': 'CSV_EXACT_CENTS/v1', 'general_mandate': 'UNKNOWN', 'public_job_data': False})

    def do_POST(self):
        identity = {}
        try:
            if '?' in self.path or self.headers.get('Content-Type', '').split(';')[0].lower() != 'application/json':
                raise InvalidInput('JSON_POST_REQUIRED')
            size = int(self.headers.get('Content-Length', '0'))
            if not 1 <= size <= MAX_BODY:
                raise InvalidInput('BODY_SIZE')
            raw = self.rfile.read(size)
            if len(raw) != size:
                raise InvalidInput('INCOMPLETE_BODY')
            body = json.loads(raw.decode('utf-8'), object_pairs_hook=unique_object)
            _, data = validate(body)
            identity = {key: data[key] for key in ('job_id', 'mission_id', 'request_id', 'target_request_id') if key in data}
            self.reply(200, dispatch(body))
        except (InvalidInput, ValueError, UnicodeError) as exc:
            self.reply(400, {'ok': False, 'status': 'REJECTED', 'error': str(exc) if isinstance(exc, InvalidInput) else 'INVALID_JSON', 'current_reuse_authorized': False, 'automatic_retry': False, **identity})
        except Exception:
            self.reply(503, {'ok': False, 'status': 'OUTCOME_UNKNOWN', 'error': 'OUTCOME_UNKNOWN', 'current_reuse_authorized': False, 'automatic_retry': False, **identity})
