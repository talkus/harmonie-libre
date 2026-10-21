"""One bounded real-deployment flow. Persist each intent first; never retry mutations."""
from pathlib import Path
import datetime, hashlib, json, secrets, sys, time, urllib.request, uuid

ROOT = Path(__file__).resolve().parents[1]
BASE = 'https://sol-action-verifiee.vercel.app'
PRIVATE = ROOT / 'private' / 'live-http'
PRIVATE.mkdir(mode=0o700, exist_ok=True)
STATE = PRIVATE / 'state.json'
if STATE.exists():
    raise SystemExit('Existing attempt preserved. Read its receipts; do not replay this script.')
source = 'id,currency,amount\na,EUR,0.10\nb,EUR,0.20\nc,USD,999999999999.99\nd,USD,-999999999999.98\n'
plan = {key: str(uuid.uuid4()) for key in ['job_id','create','produce','result','reconcile','verify','complete']}
plan['capability'] = secrets.token_hex(32)
plan['source_sha256'] = hashlib.sha256(source.encode()).hexdigest()
STATE.write_text(json.dumps(plan, indent=2)); STATE.chmod(0o600)
observations = []
checks = []

def scrub(value):
    if isinstance(value, dict):
        return {k: scrub(v) for k,v in value.items() if k not in ['capability','parent_capability','bridge_token','token']}
    if isinstance(value, list): return [scrub(v) for v in value]
    if isinstance(value, str): return value.replace(plan['capability'],'[REDACTED]')
    return value

def save():
    out = {'schema':'SOL_ACTION_HTTP_OBSERVATION/v1','at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'base_url':BASE,'job_id':plan['job_id'],'source_kind':'SYNTHETIC_DECLARED',
           'network_loss_method':'Reconciliation response is deliberately discarded by the test application after receipt, then retrieved by original UUID. No actual TCP fault is claimed.',
           'observations':observations,'checks':checks,'passed':sum(x['passed'] for x in checks),'total':len(checks),
           'semantic_truth':'UNKNOWN','completion_scope':'CSV_EXACT_CENTS_ONLY'}
    (ROOT/'evidence/live-http-current.json').write_text(json.dumps(scrub(out),ensure_ascii=False,indent=2)+'\n')

def check(name, condition):
    checks.append({'name':name,'passed':bool(condition)}); save()
    if not condition: raise RuntimeError('STOP: '+name)

def post(action, extra=None, receipt_label=None):
    data = {'job_id':plan['job_id'],'capability':plan['capability']}
    if action not in ['status','audit','receipt']: data['request_id'] = plan[action]
    data.update(extra or {})
    body = {'action':action,'input':data}
    label=receipt_label or action
    # Intent is durable before this sole network send; this script has no retry loop.
    intent_file=PRIVATE/(label+'-intent.json')
    with intent_file.open('x') as f: json.dump(body,f)
    intent_file.chmod(0o600)
    started=time.monotonic()
    try:
        req=urllib.request.Request(BASE+'/api/job',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
        with urllib.request.urlopen(req,timeout=35) as response:
            result=json.load(response); status=response.status
    except Exception as exc:
        observations.append({'label':label,'action':action,'outcome':'UNKNOWN_TRANSPORT','error_type':type(exc).__name__});save()
        raise RuntimeError('Ambiguous attempt preserved; no automatic retry.') from None
    observations.append({'label':label,'action':action,'http_status':status,'elapsed_seconds':time.monotonic()-started,'response':scrub(result)})
    save()
    return result

r=post('create',{'mandate':'Test borné de reprise et calcul exact ; source synthétique, aucune réussite générale demandée ici.',
    'requirements':['Conserver les quatre lignes.','EUR 0.30 et USD 0.01 exactement.'],
    'source_csv':source,'source_origin':{'kind':'declared','reference':'SYNTHETIC_CURRENT_RELEASE_HTTP_TEST'}})
check('create_correlated',r.get('ok') is True and r.get('job_id')==plan['job_id'] and r.get('request_id')==plan['create'])
r=post('produce',{'expected_step_id':'produce','result_request_id':plan['result']})
check('production_result_correlated',r.get('ok') is True and r.get('action')=='result' and r.get('request_id')==plan['result'] and r.get('production_request_id')==plan['produce'])
result=r.get('result',{})
check('exact_two_currency_totals',result.get('totals')==[{'currency':'EUR','amount':'0.30'},{'currency':'USD','amount':'0.01'}] and result.get('source_sha256')==plan['source_sha256'] and result.get('rows')==4)
r=post('reconcile',{'target_request_id':plan['produce'],'production_request_id':plan['produce']})
check('reconciliation_durable_before_discard',r.get('ok') is True and r.get('pending') is False)
del r
for label in ['receipt-first-read','receipt-second-read']:
    r=post('receipt',{'target_request_id':plan['reconcile']},label)
    hist=r.get('receipt',{})
    check(label+'_exact_historical_no_grant',r.get('found') is True and r.get('job_id')==plan['job_id'] and r.get('target_request_id')==plan['reconcile'] and r.get('current_reuse_authorized') is False and hist.get('request_id')==plan['reconcile'] and hist.get('action')=='reconcile' and hist.get('pending') is False and hist.get('current_reuse_authorized') is False and hist.get('result')==result)
    check(label+'_no_source_or_capability', 'source_csv' not in json.dumps(r) and plan['capability'] not in json.dumps(r))
r=post('verify',{'expected_step_id':'verify'})
check('separate_sql_oracle_pass',r.get('ok') is True and r.get('verification',{}).get('status')=='PASS')
r=post('complete',{'expected_step_id':'complete'})
check('fresh_bounded_completion',r.get('ok') is True and r.get('status')=='COMPLETED_BOUNDED' and r.get('current_reuse_authorized') is True and r.get('completion',{}).get('scope')=='CSV_EXACT_CENTS_ONLY' and datetime.datetime.fromisoformat(r['completion']['expires_at'].replace('Z','+00:00'))>datetime.datetime.now(datetime.timezone.utc))
r=post('status')
check('status_does_not_refresh_authority',r.get('current_reuse_authorized') is False)
r=post('audit')
audit=r.get('audit',{})
check('append_only_job_chain_valid',audit.get('status')=='PASS' and all(audit.get(k) is True for k in ['chain_valid','relations_valid','source_hash_valid','definition_hash_valid']))
print(json.dumps({'job_id':plan['job_id'],'passed':sum(x['passed'] for x in checks),'total':len(checks)},ensure_ascii=False))
