-- WITHDRAWAL ONLY after explicit operator review. Entire script must be one transaction.
-- Set the reviewed candidate runtime hash via set_config('sol_action_bridge.reviewed_rollback_runtime','HASH',true).
-- Tables, receipts, previous errors and admissions are preserved. Application must also be restored coherently.
do $$ begin
 if current_setting('sol_action_bridge.reviewed_rollback_runtime',true) is null
  or sol_action_bridge.runtime_hash() is distinct from current_setting('sol_action_bridge.reviewed_rollback_runtime',true)
  or sol_action.runtime_hash()<>'c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0' then
  raise exception 'EXACT_REVIEWED_WITHDRAWAL_STATE_REQUIRED';
 end if;
end $$;
create or replace function sol_action_bridge.dispatch(p_action text,p_input jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
declare j sol_action.jobs; i sol_action.intents; o sol_action.outcomes; b sol_action_bridge.bindings; r sol_action_bridge.releases; core_begin jsonb;
 id uuid; target uuid; production uuid; cap text; rh text; mh text; sc text; sh text; tok text;
begin
 if p_action is null or p_action not in ('health','lookup_receipt','bind') then raise exception 'INVALID'; end if;
 if p_input is null or octet_length(p_input::text)>16000 then raise exception 'INVALID'; end if;
 if p_action='health' then
  perform sol_action.keys(p_input,array[]::text[],array[]::text[]);
  return jsonb_build_object('ok',true,'module','SOL-Action-Bridge','version','0.1.0','receipt_lookup_read_only',true,
   'core_runtime_hash',sol_action.runtime_hash(),'bridge_runtime_hash',sol_action_bridge.runtime_hash(),
   'current_reuse_authorized',false,'automatic_retry',false);
 end if;
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
  select * into i from sol_action.intents where request_id=target;
  if found and i.job_id<>id then raise exception 'INVALID'; end if;
  select * into o from sol_action.outcomes where request_id=target;
  if found and o.job_id<>id then raise exception 'INVALID'; end if;
  if o.request_id is null then
   return jsonb_build_object('ok',true,'action','lookup_receipt','status','UNKNOWN','job_id',id,'target_request_id',target,
    'found',false,'intent_found',i.request_id is not null,'receipt',null,'current_reuse_authorized',false,'automatic_retry',false);
  end if;
  if i.request_id is null or i.job_id<>o.job_id then raise exception 'INVALID'; end if;
  return jsonb_build_object('ok',true,'action','lookup_receipt','status','HISTORICAL_NOT_CURRENT','job_id',id,'target_request_id',target,
   'found',true,'intent_found',true,'target_action',i.action,'receipt',sol_action_bridge.redact(o.receipt,cap)||
    jsonb_build_object('status','HISTORICAL_NOT_CURRENT','current_reuse_authorized',false,'needs_current_revalidation',true,'begin_granted',false),
   'current_reuse_authorized',false,'automatic_retry',false);
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

drop function sol_action_bridge.execute_core(jsonb);
drop function sol_action_bridge.receipt_lookup(uuid,uuid,text);
drop function sol_action_bridge.historical(jsonb,text);
do $$ begin
 if sol_action_bridge.runtime_hash()<>'38c9307df6c049a24ee38ba80cd1973b0ae400f3a920f91a3d4e63fd9be5b755' then
  raise exception 'PREDECESSOR_RUNTIME_NOT_RESTORED';
 end if;
end $$;
