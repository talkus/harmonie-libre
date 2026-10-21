-- SOL-Action Bridge 0.1.1 corrective migration. Intentionally NOT replayable.
-- Only bridge storage/helpers/dispatch change. Core/Atelier/Preuve are untouched.
-- A transaction around this entire script is required. A failed/ambiguous migration is inspected, never blindly replayed.
do $$ begin
 if sol_action.runtime_hash()<>'c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0'
  or sol_action_bridge.runtime_hash()<>'38c9307df6c049a24ee38ba80cd1973b0ae400f3a920f91a3d4e63fd9be5b755' then
  raise exception 'REVIEWED_PREDECESSOR_RUNTIME_REQUIRED';
 end if;
end $$;

create table sol_action_bridge.refusals(
 request_id uuid primary key, job_id uuid not null references sol_action.jobs(job_id),
 action text not null check(action in ('create','verify','complete','reconcile')),
 payload_hash text not null check(payload_hash ~ '^[0-9a-f]{64}$'),
 capability_hash bytea not null check(octet_length(capability_hash)=32),
 request_binding_hash text not null check(request_binding_hash ~ '^[0-9a-f]{64}$'),
 actor_scope text not null default 'AUTHORIZED_JOB_CAPABILITY_HOLDER_NOT_IDENTITY_ATTESTATION',
 receipt jsonb not null, receipt_sha256 text generated always as (sol_action.sha(receipt::text)) stored,
 core_runtime_hash text not null default sol_action.runtime_hash(),
 bridge_runtime_hash text not null default sol_action_bridge.runtime_hash(),
 recorded_at timestamptz not null default clock_timestamp());
create index on sol_action_bridge.refusals(job_id,recorded_at);
alter table sol_action_bridge.refusals enable row level security;
revoke all on sol_action_bridge.refusals from public,anon,authenticated,service_role;
create trigger immutable_rows before update or delete on sol_action_bridge.refusals for each row execute function sol_action_bridge.no_change();
create trigger immutable_truncate before truncate on sol_action_bridge.refusals for each statement execute function sol_action_bridge.no_change();

create table sol_action_bridge.recovery_outcomes(
 request_id uuid primary key, job_id uuid not null references sol_action.jobs(job_id),
 action text not null check(action in ('create','verify','complete','reconcile')),
 payload_hash text not null check(payload_hash ~ '^[0-9a-f]{64}$'),
 capability_hash bytea not null check(octet_length(capability_hash)=32),
 request_binding_hash text not null check(request_binding_hash ~ '^[0-9a-f]{64}$'),
 actor_scope text not null default 'AUTHORIZED_JOB_CAPABILITY_HOLDER_NOT_IDENTITY_ATTESTATION',
 receipt jsonb not null, receipt_sha256 text generated always as (sol_action.sha(receipt::text)) stored,
 core_runtime_hash text not null default sol_action.runtime_hash(),
 bridge_runtime_hash text not null default sol_action_bridge.runtime_hash(),
 recorded_at timestamptz not null default clock_timestamp());
create index on sol_action_bridge.recovery_outcomes(job_id,recorded_at);
alter table sol_action_bridge.recovery_outcomes enable row level security;
revoke all on sol_action_bridge.recovery_outcomes from public,anon,authenticated,service_role;
create trigger immutable_rows before update or delete on sol_action_bridge.recovery_outcomes for each row execute function sol_action_bridge.no_change();
create trigger immutable_truncate before truncate on sol_action_bridge.recovery_outcomes for each statement execute function sol_action_bridge.no_change();

-- Included by migration.sql. These helpers have no direct caller grants.
create function sol_action_bridge.historical(p jsonb,cap text) returns jsonb language sql immutable set search_path='' as $$
 select sol_action_bridge.redact(p,cap)||jsonb_build_object('historical_status',p->>'status',
  'status','HISTORICAL_NOT_CURRENT','current_reuse_authorized',false,'needs_current_revalidation',true,
  'begin_granted',false,'binding_granted',false,'automatic_retry',false) $$;

create function sol_action_bridge.receipt_lookup(id uuid,target uuid,cap text) returns jsonb language plpgsql set search_path='' as $$
declare j sol_action.jobs; i sol_action.intents; o sol_action.outcomes;
 f sol_action_bridge.refusals; q sol_action_bridge.recovery_outcomes; r jsonb; act text; kind text; n integer;
begin
 select * into j from sol_action.jobs where job_id=id;
 if not found then raise exception 'INVALID'; end if;
 perform sol_action.authorize(j,cap);
 select * into i from sol_action.intents where request_id=target;
 select * into o from sol_action.outcomes where request_id=target;
 select * into f from sol_action_bridge.refusals where request_id=target;
 select * into q from sol_action_bridge.recovery_outcomes where request_id=target;
 if (i.request_id is not null and i.job_id<>id) or (o.request_id is not null and o.job_id<>id)
  or (f.request_id is not null and (f.job_id<>id or f.capability_hash<>j.capability_hash))
  or (q.request_id is not null and (q.job_id<>id or q.capability_hash<>j.capability_hash)) then raise exception 'INVALID'; end if;
 -- Refuse conflicting histories rather than masking one with the other.
 n:=(case when o.request_id is not null then 1 else 0 end)+(case when f.request_id is not null then 1 else 0 end)
  +(case when q.request_id is not null then 1 else 0 end);
 if n>1 or ((f.request_id is not null or q.request_id is not null) and i.request_id is not null)
  or (o.request_id is not null and (i.request_id is null or i.job_id<>o.job_id)) then raise exception 'RECEIPT_COLLISION'; end if;
 if o.request_id is not null then r:=o.receipt; act:=i.action; kind:='CORE_OUTCOME';
 elsif f.request_id is not null then r:=f.receipt;act:=f.action;kind:='CONTROLLED_REFUSAL';
 elsif q.request_id is not null then r:=q.receipt;act:=q.action;kind:='REFUSAL_RECONCILIATION';
 else
  return jsonb_build_object('ok',true,'action','lookup_receipt','status','UNKNOWN','job_id',id,'target_request_id',target,
   'found',false,'intent_found',i.request_id is not null,'receipt',null,'current_reuse_authorized',false,'automatic_retry',false);
 end if;
 return jsonb_build_object('ok',true,'action','lookup_receipt','status','HISTORICAL_NOT_CURRENT','job_id',id,
  'target_request_id',target,'target_action',act,'receipt_kind',kind,'receipt_status',r->>'status',
  'found',true,'intent_found',i.request_id is not null,'receipt',sol_action_bridge.historical(r,cap),
  'current_reuse_authorized',false,'automatic_retry',false);
end $$;

create function sol_action_bridge.execute_core(p jsonb) returns jsonb language plpgsql set search_path='' as $$
declare a text; d jsonb; j sol_action.jobs; id uuid; req uuid; cap text; ph text; bh text; r jsonb; target uuid;
 f sol_action_bridge.refusals; q sol_action_bridge.recovery_outcomes; i sol_action.intents; hit jsonb; has_job boolean;
begin
 perform sol_action.keys(p,array['core_action','core_input'],array['core_action','core_input']);
 a:=sol_action.text_field(p,'core_action',1,20);d:=p->'core_input';
 if a not in ('create','verify','complete','reconcile') or jsonb_typeof(d) is distinct from 'object'
  or octet_length(d::text)>180000 then raise exception 'INVALID'; end if;
 id:=sol_action.text_field(d,'job_id',36,36)::uuid;req:=sol_action.text_field(d,'request_id',36,36)::uuid;
 cap:=sol_action.text_field(d,'capability',64,64);
 if cap !~ '^[0-9a-f]{64}$' then raise exception 'INVALID'; end if;
 -- This is the unchanged reviewed core whose catch rolls back its complete SQL block.
 -- A changed implementation may not inherit its no-effect interpretation.
 if sol_action.runtime_hash()<>'c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0' then raise exception 'CORE_RUNTIME_CHANGED'; end if;
 perform pg_advisory_xact_lock(hashtextextended('sol_action:job:'||id::text,0));
 perform pg_advisory_xact_lock(hashtextextended('sol_action_bridge:request:'||req::text,0));
 select * into j from sol_action.jobs where job_id=id;has_job:=found;
 if has_job then perform sol_action.authorize(j,cap); elsif a<>'create' then raise exception 'INVALID'; end if;
 ph:=sol_action.sha(jsonb_build_object('action',a,'input',d-'capability'-'parent_capability')::text);
 bh:=sol_action.sha(encode(extensions.digest(convert_to(cap,'UTF8'),'sha256'),'hex')||':'||ph||':'||id::text||':'||req::text||':'||a);
 select * into f from sol_action_bridge.refusals where request_id=req;
 select * into q from sol_action_bridge.recovery_outcomes where request_id=req;
 select * into i from sol_action.intents where request_id=req;
 if f.request_id is not null or q.request_id is not null then
  if i.request_id is not null or (f.request_id is not null and q.request_id is not null) then raise exception 'RECEIPT_COLLISION'; end if;
  if f.request_id is not null then
   if f.job_id<>id or f.action<>a or f.payload_hash<>ph or f.request_binding_hash<>bh then raise exception 'INVALID'; end if;
   return sol_action_bridge.historical(f.receipt,cap)||jsonb_build_object('deduplicated',true);
  end if;
  if q.job_id<>id or q.action<>a or q.payload_hash<>ph or q.request_binding_hash<>bh then raise exception 'INVALID'; end if;
  return sol_action_bridge.historical(q.receipt,cap)||jsonb_build_object('deduplicated',true);
 end if;
 -- A prior core intent is resolved exclusively by the unchanged core (including UNKNOWN).
 if i.request_id is not null then return sol_action.dispatch(a,d); end if;
 if has_job and a='reconcile' and d?'target_request_id' then
  -- Keep exactly the old reconcile envelope. No new arbitrary field can bypass validation.
  perform sol_action.keys(d,array['job_id','capability','request_id','target_request_id','production_request_id'],array['job_id','capability','request_id']);
  target:=sol_action.text_field(d,'target_request_id',36,36)::uuid;
  hit:=sol_action_bridge.receipt_lookup(id,target,cap);
  if hit->>'receipt_kind'='CONTROLLED_REFUSAL' and hit->>'found'='true'
   and j.runtime_hash=sol_action.runtime_hash() then
   perform pg_advisory_xact_lock(hashtextextended('sol_action:intent_rate',0));
   if (select count(*) from sol_action.intents where job_id=id)+
      (select count(*) from sol_action_bridge.recovery_outcomes where job_id=id)>=64 then raise exception 'RECOVERY_STORAGE_LIMIT'; end if;
   if (select count(*) from sol_action.intents where created_at>=date_trunc('day',clock_timestamp() at time zone 'UTC') at time zone 'UTC')+
      (select count(*) from sol_action_bridge.recovery_outcomes where recorded_at>=date_trunc('day',clock_timestamp() at time zone 'UTC') at time zone 'UTC')>=2048 then raise exception 'RECOVERY_STORAGE_LIMIT'; end if;
   if d?'production_request_id' then
    -- Composite production remains unknown unless its separate begin identity is valid.
    if not exists(select 1 from sol_action.intents where request_id=sol_action.text_field(d,'production_request_id',36,36)::uuid
     and job_id=id and action='begin') then raise exception 'INVALID'; end if;
   end if;
   r:=sol_action_bridge.redact(sol_action.view_job(j),cap)||jsonb_build_object('ok',true,'status','RECORDED','action','reconcile',
    'job_id',id,'request_id',req,'pending',false,'production_pending',sol_action.view_job(j)->'pending',
    'target_request_id',target,'target_action',hit->'target_action','reconciled_outcome',hit->'receipt',
    'recorded_at',sol_action.utc(clock_timestamp()),
    'outcome_known',true,'worker_reexecuted',false,'receipt_kind','REFUSAL_RECONCILIATION',
    'verification',null,'completion',null,'current_reuse_authorized',false,'automatic_retry',false);
   insert into sol_action_bridge.recovery_outcomes(request_id,job_id,action,payload_hash,capability_hash,request_binding_hash,receipt)
    values(req,id,a,ph,j.capability_hash,bh,r);
   return r;
  end if;
 end if;
 r:=sol_action.dispatch(a,d);
 if r->>'ok'='false' and r->>'status'='REJECTED' and r->>'sqlstate'='P0001'
  and r->>'effect'='NONE_SQL_TRANSACTION_ROLLED_BACK' and r->>'effect_scope'='THIS_RPC_SQL_TRANSACTION_ONLY'
  and r->>'job_id'=id::text and r->>'request_id'=req::text and r->>'action'=a
  and (r->>'error'=any(array['JOB_ALREADY_EXISTS','JOB_INTENT_LIMIT','DAILY_INTENT_LIMIT','RUNTIME_CHANGED_NEW_JOB_REQUIRED',
   'EXPECTED_STEP_MISMATCH','PRODUCTION_PENDING','FRESH_VERIFICATION_REQUIRED','RECONCILE_TARGET_REQUIRED','PRODUCTION_INTENT_MISMATCH'])
   or r->>'error' ~ '^(UNKNOWN_OR_NULL_FIELD|MISSING_FIELD|STRING_REQUIRED|STRING_BOUNDS):[A-Za-z_]+$')
  and has_job
  and not exists(select 1 from sol_action.intents where request_id=req)
  and not exists(select 1 from sol_action.outcomes where request_id=req) then
  if (select count(*) from sol_action_bridge.refusals where job_id=id)>=128 then raise exception 'REFUSAL_STORAGE_LIMIT'; end if;
  r:=r||jsonb_build_object('receipt_kind','CONTROLLED_REFUSAL','terminal',true,'durable_refusal',true,'payload_hash',ph,
   'refused_at',sol_action.utc(clock_timestamp()),
   'core_effect_scope',r->>'effect_scope','effect_scope','CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY',
   'receipt_recording_effect','APPEND_ONLY_BRIDGE_RECEIPT_RECORDED','business_effect','NONE_CORE_ACTION_ROLLED_BACK',
   'actor_scope','AUTHORIZED_JOB_CAPABILITY_HOLDER_NOT_IDENTITY_ATTESTATION','worker_reexecuted',false);
  insert into sol_action_bridge.refusals(request_id,job_id,action,payload_hash,capability_hash,request_binding_hash,receipt)
   values(req,id,a,ph,j.capability_hash,bh,r);
 end if;
 return r;
end $$;

create or replace function sol_action_bridge.dispatch(p_action text,p_input jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
declare j sol_action.jobs; i sol_action.intents; o sol_action.outcomes; b sol_action_bridge.bindings; r sol_action_bridge.releases; core_begin jsonb;
 id uuid; target uuid; production uuid; cap text; rh text; mh text; sc text; sh text; tok text;
begin
 if p_action is null or p_action not in ('health','lookup_receipt','bind','execute') then raise exception 'INVALID'; end if;
 if p_input is null or octet_length(p_input::text)>(case when p_action='execute' then 180000 else 16000 end) then raise exception 'INVALID'; end if;
 if p_action='health' then
  perform sol_action.keys(p_input,array[]::text[],array[]::text[]);
  return jsonb_build_object('ok',true,'module','SOL-Action-Bridge','version','0.1.1','receipt_lookup_read_only',true,
   'core_runtime_hash',sol_action.runtime_hash(),'bridge_runtime_hash',sol_action_bridge.runtime_hash(),
   'current_reuse_authorized',false,'automatic_retry',false);
 end if;
 if p_action='execute' then return sol_action_bridge.execute_core(p_input); end if;
 if p_action='lookup_receipt' then
  perform sol_action.keys(p_input,array['job_id','capability','target_request_id'],array['job_id','capability','target_request_id']);
 else
  perform sol_action.keys(p_input,array['job_id','capability','production_request_id','release_hash','manifest_hash','source_commit','self_hash','bridge_token'],
   array['job_id','capability','production_request_id','release_hash','manifest_hash','source_commit','self_hash','bridge_token']);
 end if;
 id:=sol_action.text_field(p_input,'job_id',36,36)::uuid;
 cap:=sol_action.text_field(p_input,'capability',64,64);
 select * into j from sol_action.jobs where job_id=id;
 if not found then raise exception 'INVALID'; end if;
 perform sol_action.authorize(j,cap);
 if p_action='lookup_receipt' then
  target:=sol_action.text_field(p_input,'target_request_id',36,36)::uuid;
  return sol_action_bridge.receipt_lookup(id,target,cap);
 end if;
 -- The only write path is token-gated bind + unchanged core begin in ONE transaction.
 production:=sol_action.text_field(p_input,'production_request_id',36,36)::uuid;
 rh:=sol_action.text_field(p_input,'release_hash',64,64);mh:=sol_action.text_field(p_input,'manifest_hash',64,64);
 sc:=sol_action.text_field(p_input,'source_commit',40,40);sh:=sol_action.text_field(p_input,'self_hash',64,64);
 tok:=sol_action.text_field(p_input,'bridge_token',64,64);
 if rh !~ '^[0-9a-f]{64}$' or mh !~ '^[0-9a-f]{64}$' or sc !~ '^[0-9a-f]{40}$' or sh !~ '^[0-9a-f]{64}$' then raise exception 'INVALID'; end if;
 select * into r from sol_action_bridge.releases where release_hash=rh;
 if not found then raise exception 'INVALID'; end if;
 if not sol_action_bridge.token_matches(tok,r.token_sha256) then raise exception 'INVALID'; end if;
 if r.manifest_hash<>mh or r.source_commit<>sc or r.source_files->>'api/job.py'<>sh
  or r.core_runtime_hash<>sol_action.runtime_hash() or r.bridge_runtime_hash<>sol_action_bridge.runtime_hash()
  or j.runtime_hash<>r.core_runtime_hash then raise exception 'INVALID'; end if;
 perform pg_advisory_xact_lock(hashtextextended('sol_action:job:'||id::text,0));
 perform pg_advisory_xact_lock(hashtextextended('sol_action_bridge:request:'||production::text,0));
 if exists(select 1 from sol_action_bridge.refusals where request_id=production)
  or exists(select 1 from sol_action_bridge.recovery_outcomes where request_id=production) then raise exception 'INVALID'; end if;
 select * into b from sol_action_bridge.bindings where job_id=id;
 if found then
  if b.production_request_id<>production or b.release_hash<>rh or b.worker_self_hash<>sh then raise exception 'INVALID'; end if;
  return sol_action_bridge.binding_receipt(b,false);
 end if;
 if exists(select 1 from sol_action.intents where job_id=id and action='begin')
  or exists(select 1 from sol_action.results where job_id=id)
  or exists(select 1 from sol_action.intents where request_id=production)
  or exists(select 1 from sol_action_bridge.bindings where production_request_id=production) then raise exception 'INVALID'; end if;
 core_begin:=sol_action.dispatch('begin',jsonb_build_object('job_id',id,'capability',cap,'request_id',production,'expected_step_id','produce'));
 if core_begin->>'ok' is distinct from 'true' or core_begin->>'status' is distinct from 'RECORDED'
  or core_begin->>'begin_granted' is distinct from 'true' or core_begin->>'deduplicated'='true'
  or core_begin->>'job_id' is distinct from id::text
  or core_begin->>'production_request_id' is distinct from production::text
  or core_begin->>'source_sha256' is distinct from j.source_sha256
  or core_begin->>'source_csv' is distinct from j.source_csv then raise exception 'INVALID'; end if;
 insert into sol_action_bridge.bindings(job_id,production_request_id,release_hash,worker_self_hash,core_runtime_hash,bridge_runtime_hash)
 values(id,production,rh,sh,r.core_runtime_hash,r.bridge_runtime_hash) returning * into b;
 return sol_action_bridge.binding_receipt(b,true)||jsonb_build_object('begin_receipt',core_begin,'binding_and_begin_atomic',true);
exception when others then
 return jsonb_build_object('ok',false,'status','REJECTED','error','NOT_AUTHORIZED_OR_INVALID_REFERENCE',
  'current_reuse_authorized',false,'automatic_retry',false);
end $$;

revoke all on function sol_action_bridge.historical(jsonb,text) from public,anon,authenticated,service_role;
revoke all on function sol_action_bridge.receipt_lookup(uuid,uuid,text) from public,anon,authenticated,service_role;
revoke all on function sol_action_bridge.execute_core(jsonb) from public,anon,authenticated,service_role;
