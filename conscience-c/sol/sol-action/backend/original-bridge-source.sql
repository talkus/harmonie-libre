-- SOL-Action Bridge 0.1.0. ADDITIVE: never replace sol_action or its public wrapper.
-- Intentionally fails if the bridge schema already exists; never replay an ambiguous migration.
create schema sol_action_bridge;
revoke all on schema sol_action_bridge from public,anon,authenticated,service_role;

create function sol_action_bridge.runtime_hash() returns text language sql stable set search_path='' as $$
 select sol_action.sha(string_agg(pg_get_functiondef(p.oid),E'\n' order by n.nspname,p.proname,pg_get_function_identity_arguments(p.oid)))
 from pg_proc p join pg_namespace n on n.oid=p.pronamespace
 where n.nspname='sol_action_bridge' or (n.nspname='public' and p.proname='sol_action_bridge_api') $$;

create function sol_action_bridge.valid_files(p jsonb) returns boolean language plpgsql immutable set search_path='' as $$
declare k text; v jsonb; n integer:=0; begin
 if jsonb_typeof(p) is distinct from 'object' or octet_length(p::text)>100000 then return false; end if;
 for k,v in select key,value from jsonb_each(p) loop
  n:=n+1;
  if n>128 or length(k)>180 or k !~ '^[A-Za-z0-9_.-]+(/[A-Za-z0-9_.-]+)*$'
   or k ~ '(^|/)\.{1,2}(/|$)' or k in ('release-source.json','build-info.json')
   or jsonb_typeof(v)<>'string' or (v#>>'{}') !~ '^[0-9a-f]{64}$' then return false; end if;
 end loop;
 return n>0 and p?'api/job.py' and p?'bridge_runtime.py';
end $$;

create table sol_action_bridge.releases(
 release_hash text primary key check(release_hash ~ '^[0-9a-f]{64}$'),
 manifest_hash text not null check(manifest_hash ~ '^[0-9a-f]{64}$'),
 source_commit text not null check(source_commit ~ '^[0-9a-f]{40}$'),
 source_files jsonb not null check(sol_action_bridge.valid_files(source_files)),
 deployment_id text not null check(length(deployment_id) between 5 and 160),
 deployment_url text not null check(length(deployment_url)<=500 and deployment_url ~ '^https://[A-Za-z0-9.-]+\.vercel\.app/?$'),
 token_sha256 text not null check(token_sha256 ~ '^[0-9a-f]{64}$'),
 core_runtime_hash text not null default sol_action.runtime_hash(),
 bridge_runtime_hash text not null default sol_action_bridge.runtime_hash(),
 admitted_at timestamptz not null default clock_timestamp(),
 admitted_by text not null default current_user,
 check(release_hash=sol_action.sha(manifest_hash||':'||source_commit)),
 unique(manifest_hash,source_commit)
);

create table sol_action_bridge.bindings(
 job_id uuid primary key references sol_action.jobs(job_id),
 production_request_id uuid not null unique,
 release_hash text not null references sol_action_bridge.releases(release_hash),
 worker_self_hash text not null check(worker_self_hash ~ '^[0-9a-f]{64}$'),
 core_runtime_hash text not null,
 bridge_runtime_hash text not null,
 bound_at timestamptz not null default clock_timestamp(),
 unique(job_id,production_request_id)
);

create function sol_action_bridge.no_change() returns trigger language plpgsql set search_path='' as $$
begin raise exception using errcode='P0001',message='APPEND_ONLY'; end $$;
do $$ declare t text; begin
 foreach t in array array['releases','bindings'] loop
  execute format('alter table sol_action_bridge.%I enable row level security',t);
  execute format('revoke all on sol_action_bridge.%I from public,anon,authenticated,service_role',t);
  execute format('create trigger immutable_rows before update or delete on sol_action_bridge.%I for each row execute function sol_action_bridge.no_change()',t);
  execute format('create trigger immutable_truncate before truncate on sol_action_bridge.%I for each statement execute function sol_action_bridge.no_change()',t);
 end loop;
end $$;

create function sol_action_bridge.redact(p jsonb,cap text) returns jsonb language plpgsql immutable set search_path='' as $$
declare k text; v jsonb; o jsonb; begin
 if jsonb_typeof(p)='object' then
  o:='{}'::jsonb;
  for k,v in select key,value from jsonb_each(p) loop
   if k in ('source_csv','capability','parent_capability','bridge_token','token') then continue; end if;
   if k in ('current_reuse_authorized','begin_granted','binding_granted') then v:='false'::jsonb;
   elsif k='needs_current_revalidation' then v:='true'::jsonb;
   else v:=sol_action_bridge.redact(v,cap); end if;
   o:=o||jsonb_build_object(k,v);
  end loop;
  return o;
 elsif jsonb_typeof(p)='array' then
  select coalesce(jsonb_agg(sol_action_bridge.redact(value,cap) order by ord),'[]'::jsonb) into o from jsonb_array_elements(p) with ordinality a(value,ord);
  return o;
 elsif jsonb_typeof(p)='string' then
  return to_jsonb(replace(p#>>'{}',cap,'[REDACTED]'));
 end if;
 return p;
end $$;

create function sol_action_bridge.token_matches(raw text,expected_hash text) returns boolean language plpgsql immutable set search_path='' as $$
declare actual bytea; expected bytea; d integer:=0; n integer; begin
 if raw is null or raw !~ '^[0-9a-f]{64}$' or expected_hash !~ '^[0-9a-f]{64}$' then return false; end if;
 actual:=extensions.digest(convert_to(raw,'UTF8'),'sha256');expected:=decode(expected_hash,'hex');
 for n in 0..31 loop d:=d | (get_byte(actual,n) # get_byte(expected,n)); end loop;
 return d=0;
end $$;

create function sol_action_bridge.binding_receipt(b sol_action_bridge.bindings, granted boolean) returns jsonb language sql stable set search_path='' as $$
 select jsonb_build_object('ok',true,'action','bind','status',case when granted then 'BOUND_RELEASE' else 'HISTORICAL_NOT_CURRENT' end,
  'job_id',b.job_id,'production_request_id',b.production_request_id,'release_hash',b.release_hash,'self_hash',b.worker_self_hash,
  'binding_granted',granted,'binding_found',true,'deduplicated',not granted,'bound_at',sol_action.utc(b.bound_at),
  'worker_identity','TOKEN_HOLDER_AND_LOCAL_SELF_HASH_NOT_MACHINE_ATTESTATION',
  'current_reuse_authorized',false,'automatic_retry',false) $$;

create function sol_action_bridge.dispatch(p_action text,p_input jsonb) returns jsonb language plpgsql security definer set search_path='' as $$
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

create function public.sol_action_bridge_api(p_action text,p_input jsonb default '{}'::jsonb) returns jsonb language sql security invoker set search_path='' as $$
 select sol_action_bridge.dispatch(p_action,p_input) $$;
revoke all on all functions in schema sol_action_bridge from public,anon,authenticated,service_role;
revoke all on function public.sol_action_bridge_api(text,jsonb) from public,anon,authenticated,service_role;
grant usage on schema sol_action_bridge to anon,authenticated;
grant execute on function sol_action_bridge.dispatch(text,jsonb) to anon,authenticated;
grant execute on function public.sol_action_bridge_api(text,jsonb) to anon,authenticated;
