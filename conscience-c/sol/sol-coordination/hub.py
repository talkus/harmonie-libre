#!/usr/bin/env python3
"""Cooperative transport for SOL-Coordination. No tool, network or candidate execution."""
import argparse, datetime as dt, hashlib, json, os, re, sqlite3, sys, time, uuid
from pathlib import Path

VERSION='SOL-COORDINATION-HUB/0.1.0'
LIMIT=8*1024*1024
class Refusal(Exception): pass
def need(value,why):
    if not value: raise Refusal(why)
def canonical(value): return json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def digest(value): return hashlib.sha256(canonical(value).encode()).hexdigest()
def pairs(items):
    out={}
    for k,v in items:
        need(k not in out,'DUPLICATE_JSON_KEY');out[k]=v
    return out
def decode(value):
    try:return json.loads(value,object_pairs_hook=pairs,parse_constant=lambda x: (_ for _ in ()).throw(Refusal('NONFINITE_JSON')))
    except (ValueError,TypeError,RecursionError) as e:raise Refusal('MALFORMED_JSON') from e
def read(path):
    p=Path(path);need(p.is_file() and not p.is_symlink(),'REGULAR_FILE_REQUIRED');b=p.read_bytes();need(len(b)<=LIMIT,'EXPORT_TOO_LARGE');return decode(b.decode('utf-8'))
def unwrap(v,depth=0):
    need(depth<12,'EXPORT_DEPTH');
    if isinstance(v,str):
        try:return unwrap(decode(v),depth+1)
        except Refusal:
            opens=re.findall(r'^<(untrusted-data-[\w-]+)>[ \t]*$',v,re.M);closes=re.findall(r'^</(untrusted-data-[\w-]+)>[ \t]*$',v,re.M)
            blocks=re.findall(r'^<(untrusted-data-[\w-]+)>[ \t]*\n(.*?)\n</\1>[ \t]*$',v,re.M|re.S)
            need(len(opens)==len(closes)==len(blocks)==1,'SINGLE_SQL_RESULT_BLOCK_REQUIRED');return unwrap(decode(blocks[0][1]),depth+1)
    if isinstance(v,list):need(len(v)==1,'SINGLE_RESULT_REQUIRED');return unwrap(v[0],depth+1)
    need(isinstance(v,dict),'OBJECT_REQUIRED');need(v.get('isError') is not True,'TOOL_ERROR')
    if v.get('structuredContent') is not None:
        a=unwrap(v['structuredContent'],depth+1)
        if v.get('content') is not None:need(a==unwrap({'content':v['content']},depth+1),'CONTRADICTORY_EXPORT')
        return a
    if 'content' in v:
        texts=[x.get('text') for x in v['content'] if isinstance(x,dict) and x.get('type')=='text'];need(len(texts)==1,'SINGLE_TEXT_REQUIRED');return unwrap(texts[0],depth+1)
    if 'current_resolution' in v or 'definition' in v or 'task' in v or 'error' in v:return v
    if len(v)==1:return unwrap(next(iter(v.values())),depth+1)
    return v
def own_hash(): return hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
def valid_uuid(v):
    need(isinstance(v,str),'UUID_REQUIRED')
    try:need(str(uuid.UUID(v))==v,'CANONICAL_UUID_REQUIRED')
    except ValueError as e:raise Refusal('UUID_REQUIRED') from e
    return v
def call(manifest,api,action,value):
    text=json.dumps(value,ensure_ascii=False,separators=(',',':')).replace("'","''")
    return {'tool':'mcp__codex_apps__supabase_execute_sql','arguments':{'project_id':manifest['project_id'],'query':f"SELECT public.{api}('{action}','{text}'::jsonb,'connector:operator') AS result;"}}
def connect(folder):
    p=Path(folder);need(p.is_dir() and not p.is_symlink(),'STATE_DIRECTORY_REQUIRED');db=sqlite3.connect(p/'journal.sqlite3');db.execute('BEGIN IMMEDIATE');return db
def events(db):
    out=[];prev='0'*64
    for seq,kind,payload,previous,h in db.execute('select seq,kind,payload,previous_hash,event_hash from events order by seq'):
        obj={'seq':seq,'kind':kind,'payload':decode(payload),'previous_hash':previous};need(previous==prev and digest(obj)==h,'LOCAL_CHAIN_MISMATCH');out.append(obj);prev=h
    return out
def append(db,kind,payload):
    row=db.execute('select seq,event_hash from events order by seq desc limit 1').fetchone();seq=row[0]+1 if row else 1;prev=row[1] if row else '0'*64
    event={'seq':seq,'kind':kind,'payload':payload,'previous_hash':prev};db.execute('insert into events values(?,?,?,?,?)',(seq,kind,canonical(payload),prev,digest(event)))
def view(rows):
    state={'manifest':None,'snapshot':None,'pending':None}
    for r in rows:
        k,p=r['kind'],r['payload']
        if k=='INIT':state['manifest']=p
        elif k=='OBSERVATION':state['snapshot']=p
        elif k=='DRIFT_REVIEW':
            need(state['snapshot'] is not None and p['observation_hash']==digest(state['snapshot']['response']),'REVIEW_OBSERVATION_MISMATCH');state['snapshot']['drift_reviewed']=True
        elif k=='INTENT':state['pending']=p
        elif k=='RECEIPT':need(state['pending'] and state['pending']['request_id']==p['request_id'],'RECEIPT_WITHOUT_INTENT');state['pending']=None;state['snapshot']=None
        elif k=='REFRESH':state['snapshot']=None
    return state
def validate_snapshot(v,m):
    need(v.get('ok') is True and v.get('status')=='BUNDLE_RESOLVED_FOR_NAVIGATION_ONLY','CURRENT_BUNDLE_READ_REQUIRED')
    need(v.get('bundle_id')==m['bundle_id'] and v.get('workspace')==m['workspace'],'BUNDLE_IDENTITY_MISMATCH')
    need(v.get('current_reuse_authorized') is False and v.get('limit')=='NO_CURRENT_AUTHORITY','AUTHORITY_MARKER_REQUIRED');need(v.get('source_journal_integrity_checked') is True,'SOURCE_JOURNAL_NOT_CHECKED')
    need(v.get('coordination_runtime_hash')==m.get('coordination_runtime_hash') and isinstance(m.get('coordination_runtime_hash'),str),'COORDINATION_RUNTIME_CHANGED')
    r=v.get('current_resolution');need(isinstance(r,dict),'RESOLUTION_REQUIRED')
    resolutions=r.get('resolutions');matrix=r.get('requirement_matrix');need(isinstance(resolutions,list) and 1<=len(resolutions)<=17 and isinstance(matrix,list),'RESOLUTION_LISTS_REQUIRED')
    need([p['resolution'].get('anchor_task_id') for p in resolutions]==m.get('anchors'),'ANCHOR_SET_MISMATCH')
    need(type(r.get('unresolved_atelier_request_count')) is int and r['unresolved_atelier_request_count']>=0,'PENDING_INTENT_COUNT_REQUIRED')
    expected=[];seen=set()
    for part in resolutions:
        rr=part['resolution'];term=rr['terminal'];tid=valid_uuid(rr['terminal_task_id']);need(tid not in seen,'DUPLICATE_TERMINAL');seen.add(tid)
        need(term.get('task_id')==tid and term.get('workspace')==m['workspace'] and term.get('bindings_match_creation') is True,'TERMINAL_NOT_CORRELATED')
        need(term.get('bindings_current')==term['task'].get('bindings'),'CONTRADICTORY_RUNTIME_BINDINGS');need(term.get('progress',{}).get('phase')!='SUPERSEDED','SUPERSEDED_TERMINAL')
        chain=rr.get('chain');need(isinstance(chain,list) and 1<=len(chain)<=64,'LINEAGE_REQUIRED');seen_nodes=set()
        need(chain[0].get('task_id')==rr.get('anchor_task_id') and chain[-1].get('task_id')==tid,'LINEAGE_ENDPOINT_MISMATCH')
        for index,node in enumerate(chain):
            need(node.get('task_id') not in seen_nodes,'LINEAGE_CYCLE');seen_nodes.add(node.get('task_id'))
            if index<len(chain)-1:
                child=chain[index+1];need(node.get('progress_phase')=='SUPERSEDED' and node.get('successor_task_id')==child.get('task_id'),'LINEAGE_LINK_MISMATCH');need(child['requirements'][:len(node['requirements'])]==node['requirements'],'REQUIREMENT_PREFIX_LOST')
        need(chain[-1].get('requirements')==term['task'].get('requirements') and chain[-1].get('mandate')==term['task'].get('mandate') and chain[-1].get('definition_hash')==term.get('definition_hash'),'TERMINAL_DEFINITION_MISMATCH')
        need(rr.get('current_reuse_authorized') is False and rr.get('limit')=='NO_CURRENT_AUTHORITY','RESOLUTION_AUTHORITY_MARKER')
        for q in term['task']['requirements']:expected.append((tid+':'+q['id'],tid,q,part['role'],rr['anchor_task_id']))
    actual=[(q['compound_id'],q['task_id'],q['requirement'],q['role'],q['anchor_task_id']) for q in matrix]
    need(actual==expected and r.get('requirement_count')==len(expected),'REQUIREMENT_MATRIX_MISMATCH')
    need(isinstance(r.get('expires_at'),str),'EXPIRY_REQUIRED');return v
def fresh(snapshot):
    need(snapshot is not None,'FRESH_READ_REQUIRED');age=time.monotonic()-snapshot['ingested_monotonic'];need(0<=age<=60,'LOCAL_OBSERVATION_EXPIRED')
    exp=dt.datetime.fromisoformat(snapshot['response']['current_resolution']['expires_at'].replace('Z','+00:00'));need(exp>dt.datetime.now(dt.timezone.utc),'SERVER_OBSERVATION_EXPIRED')
def perform(args):
    if args.command=='init':
        m=read(args.manifest);valid_uuid(m.get('bundle_id'));need(isinstance(m.get('project_id'),str) and re.fullmatch('[a-z]{20}',m['project_id']),'PROJECT_REF_REQUIRED');need(isinstance(m.get('workspace'),str) and 1<=len(m['workspace'])<=80,'WORKSPACE_REQUIRED')
        p=Path(args.state);need(not p.exists() and p.parent.is_dir(),'FRESH_STATE_PATH_REQUIRED');p.mkdir(mode=0o700);db=sqlite3.connect(p/'journal.sqlite3')
        db.executescript("CREATE TABLE events(seq INTEGER PRIMARY KEY,kind TEXT NOT NULL,payload TEXT NOT NULL,previous_hash TEXT NOT NULL,event_hash TEXT NOT NULL); CREATE TRIGGER no_update BEFORE UPDATE ON events BEGIN SELECT RAISE(ABORT,'APPEND_ONLY'); END; CREATE TRIGGER no_delete BEFORE DELETE ON events BEGIN SELECT RAISE(ABORT,'APPEND_ONLY'); END;")
        m['hub_source_sha256']=own_hash();append(db,'INIT',m);db.commit();return {'ok':True,'version':VERSION,'current_reuse_authorized':False}
    db=connect(args.state)
    try:
        rows=events(db);s=view(rows);m=s['manifest'];need(m is not None,'MANIFEST_REQUIRED');need(m.get('hub_source_sha256')==own_hash(),'HUB_SOURCE_CHANGED_NEW_STATE_REQUIRED')
        if args.command=='resume':append(db,'REFRESH',{'at':time.time()});result={'ok':True,'read_request':call(m,'sol_coordination_api','bundle_status',{'workspace':m['workspace'],'bundle_id':m['bundle_id']}),'pending':s['pending']}
        elif args.command=='observe':
            raw=Path(args.receipt).read_bytes();v=validate_snapshot(unwrap(read(args.receipt)),m)
            signature=lambda assembly:[(p['role'],p['resolution']['anchor_task_id'],p['resolution']['terminal_task_id'],p['resolution']['terminal']['definition_hash']) for p in assembly['resolutions']]
            historical=v.get('historical_definition',{}).get('assembly');need(isinstance(historical,dict),'HISTORICAL_ASSEMBLY_REQUIRED');drift=signature(historical)!=signature(v['current_resolution'])
            append(db,'OBSERVATION',{'drift':drift,'drift_reviewed':False,'response':v,'file_sha256':hashlib.sha256(raw).hexdigest(),'ingested_monotonic':time.monotonic(),'ingested_wall':time.time(),'authentication':'UNSIGNED_CONNECTOR_EXPORT_OWNER_TRUSTED'})
            result={'ok':True,'requirements':v['current_resolution']['requirement_count'],'terminal_tasks':[p['resolution']['terminal_task_id'] for p in v['current_resolution']['resolutions']],'pending_preserved':s['pending'] is not None,'drift':drift,'review_required_before_prepare':drift}
        elif args.command=='review-drift':
            fresh(s['snapshot']);need(s['snapshot'].get('drift') is True,'NO_STRUCTURAL_DRIFT_TO_REVIEW');need(isinstance(args.reason,str) and len(args.reason.strip())>=12,'REVIEW_REASON_REQUIRED');append(db,'DRIFT_REVIEW',{'observation_hash':digest(s['snapshot']['response']),'reason':args.reason,'scope':'LOCAL_OPERATOR_REVIEW_NO_EXTERNAL_PERMISSION'});result={'ok':True,'reviewed_observation_only':True}
        elif args.command=='prepare':
            need(s['pending'] is None,'PENDING_INTENT_NO_REPLAY');fresh(s['snapshot']);valid_uuid(args.request_id);valid_uuid(args.task_id)
            need(not any(r['kind']=='INTENT' and r['payload']['request_id']==args.request_id for r in rows),'REQUEST_ID_ALREADY_USED_NO_REPLAY')
            need(s['snapshot']['response']['current_resolution']['unresolved_atelier_request_count']==0,'SERVER_INTENT_UNRESOLVED_NO_DISPATCH');need(not s['snapshot'].get('drift') or s['snapshot'].get('drift_reviewed') is True,'STRUCTURAL_DRIFT_REVIEW_REQUIRED')
            parts=s['snapshot']['response']['current_resolution']['resolutions'];matches=[p['resolution']['terminal'] for p in parts if p['resolution']['terminal_task_id']==args.task_id];need(len(matches)==1,'TASK_NOT_IN_CURRENT_BUNDLE');t=matches[0]
            need(t['progress']['phase'] not in ('CANCELLED','SUPERSEDED') and not t['progress'].get('requires_reopen',False),'TASK_REQUIRES_EXPLICIT_REVIEW')
            value={'workspace':m['workspace'],'task_id':args.task_id,'request_id':args.request_id}
            if args.action=='advance':need(t.get('next_step') and t['next_step']['id']==args.expected_step_id,'EXPECTED_STEP_MISMATCH');value['expected_step_id']=args.expected_step_id
            else:need(t.get('next_step') is None,'PLAN_NOT_FINISHED')
            intent={'request_id':args.request_id,'action':args.action,'task_id':args.task_id,'definition_hash':t['definition_hash'],'definition':t['task'],'input':value,'tool_call':call(m,'sol_atelier_api',args.action,value)}
            append(db,'INTENT',intent);result={'ok':True,'intent':intent,'automatic_dispatch':False,'external_permission_granted':False}
        elif args.command=='record':
            p=s['pending'];need(p is not None and p['request_id']==args.request_id,'ORIGINAL_INTENT_REQUIRED');v=unwrap(read(args.receipt))
            need(v.get('request_id')==p['request_id'] and v.get('action')==p['action'] and v.get('task_id')==p['task_id'] and v.get('workspace')==m['workspace'],'UNCORRELATED_RECEIPT_PENDING_PRESERVED')
            need(v.get('definition_hash')==p['definition_hash'] and v.get('task')==p['definition'],'DEFINITION_CHANGED_PENDING_PRESERVED')
            if p['action']=='advance':
                matches=[a for a in v.get('progress',{}).get('attempts',[]) if a.get('request_id')==p['request_id']]
                need(len(matches)==1 and matches[0].get('step_id')==p['input']['expected_step_id'],'STEP_RECEIPT_MISMATCH_PENDING_PRESERVED')
            append(db,'RECEIPT',{'request_id':args.request_id,'response':v,'source_sha256':hashlib.sha256(Path(args.receipt).read_bytes()).hexdigest()});result={'ok':True,'phase':v.get('phase'),'historical_only':True,'next_action':'REFRESH_BEFORE_ANOTHER_INTENT'}
        else:result={'ok':True,'events':len(rows),'manifest':m,'pending':s['pending'],'has_observation':s['snapshot'] is not None,'local_integrity':'HASH_CHAIN_MATCH','owner_tamper_resistance':'NOT_WORM'}
        db.commit();return {**result,'current_reuse_authorized':False,'semantic_truth':'UNKNOWN','automatic_retry':False}
    finally:db.close()
def main():
    p=argparse.ArgumentParser();sub=p.add_subparsers(dest='command',required=True)
    for cmd in ('init','resume','observe','review-drift','prepare','record','status','audit'):
        a=sub.add_parser(cmd);a.add_argument('state')
        if cmd=='init':a.add_argument('--manifest',required=True)
        if cmd=='review-drift':a.add_argument('--reason',required=True)
        if cmd in ('observe','record'):a.add_argument('--receipt',required=True)
        if cmd in ('prepare','record'):a.add_argument('--request-id',required=True)
        if cmd=='prepare':a.add_argument('--task-id',required=True);a.add_argument('--action',choices=('advance','complete'),required=True);a.add_argument('--expected-step-id')
    try:print(canonical(perform(p.parse_args())))
    except (Refusal,KeyError,TypeError,ValueError,OSError,sqlite3.Error) as e:print(canonical({'ok':False,'status':'UNKNOWN_OR_REFUSED','error':str(e)[:180],'automatic_retry':False,'current_reuse_authorized':False}));sys.exit(2)
if __name__=='__main__':main()
