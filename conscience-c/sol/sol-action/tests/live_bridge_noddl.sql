-- Operator-run reversible protocol test; no schema/function/trigger DDL.
-- All fixtures use synthetic identifiers, capabilities and token; no HTTP or real worker.
-- Initial live_bridge.sql is an optional stronger fixture, retained and NOT executed here.
begin;
do $live$
declare
 observations jsonb:='[]'::jsonb;
 j1 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000000001'; j2 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000000002';
 j3 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000000003'; j4 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000000004';
 j5 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000000005';
 c1 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000001001'; c2 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000001002';
 p1 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000002001'; p2 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000002002';
 p3 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000002003'; p4 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000002004';
 p5 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000002005';
 res1 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000003001'; rec1 uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000004001';
 missing uuid:='ab9d2d10-f6c3-4f5b-8ca4-000000009999';
 cap text:=repeat('a',64); othercap text:=repeat('b',64); token text:=repeat('c',64);
 mh text:=repeat('d',64); sc text:=repeat('e',40); sh text:=repeat('f',64); rh text;
 csv text:=E'id,currency,amount\na,EUR,0.1\nb,EUR,0.2\n';
 core_hash text; bridge_hash text; before_counts jsonb; after_counts jsonb;
 r jsonb; a jsonb; b jsonb; q jsonb; payload jsonb; candidate jsonb; files jsonb;
 rowjob uuid; req uuid; idx integer; n bigint; m bigint; denied boolean; error_message text;
begin
 begin
 core_hash:=sol_action.runtime_hash(); bridge_hash:=sol_action_bridge.runtime_hash(); rh:=sol_action.sha(mh||':'||sc);
 observations:=observations||jsonb_build_array(jsonb_build_object('name','fixture_uuid_namespace_unused','passed',coalesce((
  not exists(select 1 from sol_action.jobs where job_id in(j1,j2,j3,j4,j5)) and
  not exists(select 1 from sol_action_bridge.releases where release_hash=rh)),false),'details','{}'::jsonb));
 if exists(select 1 from sol_action.jobs where job_id in(j1,j2,j3,j4,j5)) then raise exception 'FIXTURE_COLLISION_NO_REAL_OBJECT_REUSED'; end if;
 files:=jsonb_build_object('api/job.py',sh,'bridge_runtime.py',repeat('1',64));
 insert into sol_action_bridge.releases(release_hash,manifest_hash,source_commit,source_files,deployment_id,deployment_url,token_sha256)
 values(rh,mh,sc,files,'dpl_SYNTHETIC_TRANSACTION_ONLY','https://sol-action-verifiee.vercel.app',sol_action.sha(token));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','release_hash_and_runtime_defaults_match','passed',coalesce((exists(
  select 1 from sol_action_bridge.releases where release_hash=rh and core_runtime_hash=core_hash and bridge_runtime_hash=bridge_hash)),false),'details','{}'::jsonb));
 for idx in 1..5 loop
  rowjob:=('ab9d2d10-f6c3-4f5b-8ca4-'||lpad(idx::text,12,'0'))::uuid;
  req:=('ab9d2d10-f6c3-4f5b-8ca4-'||lpad((1000+idx)::text,12,'0'))::uuid;
  r:=public.sol_action_api('create',jsonb_build_object('job_id',rowjob,'request_id',req,'capability',cap,
   'mandate','Synthetic rollback-only bridge test; embedded synthetic capability must be redacted: '||cap,
   'requirements',jsonb_build_array('Exact totals for two synthetic rows; no actual Python worker claimed.'),
   'source_csv',csv,'source_origin',jsonb_build_object('kind','declared','reference','TRANSACTIONAL_SYNTHETIC_FIXTURE')));
  observations:=observations||jsonb_build_array(jsonb_build_object('name','create_fixture_'||idx,'passed',coalesce((r->>'ok'='true'),false),'details',jsonb_build_object('status',r->'status')));
  if r->>'ok' is distinct from 'true' then raise exception 'SYNTHETIC_CREATE_REFUSED'; end if;
 end loop;

 -- Read-only observations: table counts are identical, source and capability removed recursively.
 select jsonb_build_array((select count(*) from sol_action.intents),(select count(*) from sol_action.outcomes),
  (select count(*) from sol_action.events),(select count(*) from sol_action_bridge.bindings),(select count(*) from sol_action_bridge.releases)) into before_counts;
 a:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',cap,'target_request_id',c1));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','lookup_found_exact_create_receipt','passed',coalesce((a->>'ok'='true' and a->>'found'='true'
  and a->>'job_id'=j1::text and a->>'target_request_id'=c1::text and a->'receipt'->>'request_id'=c1::text),false),'details','{}'::jsonb));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','lookup_receipt_is_historical','passed',coalesce((a->>'status'='HISTORICAL_NOT_CURRENT'
  and a->>'current_reuse_authorized'='false' and a->'receipt'->>'current_reuse_authorized'='false'),false),'details','{}'::jsonb));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','lookup_has_no_source_or_raw_capability','passed',coalesce((position('source_csv' in a::text)=0
  and position(cap in a::text)=0 and position('id,currency,amount' in a::text)=0),false),'details','{}'::jsonb));
 r:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',cap,'target_request_id',missing));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','missing_receipt_is_unknown_not_success','passed',coalesce((r->>'ok'='true' and r->>'status'='UNKNOWN'
  and r->>'found'='false' and r->'receipt'='null'::jsonb and r->>'current_reuse_authorized'='false'),false),'details','{}'::jsonb));
 a:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',othercap,'target_request_id',c1));
 b:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',cap,'target_request_id',c2));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','wrong_capability_and_cross_job_are_same_generic_refusal','passed',coalesce((a=b
  and a->>'ok'='false' and a->>'error'='NOT_AUTHORIZED_OR_INVALID_REFERENCE' and not(a?'receipt')),false),'details','{}'::jsonb));
 r:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',cap,'target_request_id',c1,'request_id',missing));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','lookup_rejects_new_request_id','passed',coalesce((r->>'ok'='false'),false),'details','{}'::jsonb));
 select jsonb_build_array((select count(*) from sol_action.intents),(select count(*) from sol_action.outcomes),
  (select count(*) from sol_action.events),(select count(*) from sol_action_bridge.bindings),(select count(*) from sol_action_bridge.releases)) into after_counts;
 observations:=observations||jsonb_build_array(jsonb_build_object('name','lookup_has_zero_table_effects','passed',coalesce((before_counts=after_counts),false),'details','{}'::jsonb));

 payload:=jsonb_build_object('job_id',j1,'capability',cap,'production_request_id',p1,'release_hash',rh,
  'manifest_hash',mh,'source_commit',sc,'self_hash',sh,'bridge_token',token);
 r:=public.sol_action_bridge_api('bind',payload);
 observations:=observations||jsonb_build_array(jsonb_build_object('name','fresh_binding_and_begin_granted_atomically','passed',coalesce((r->>'ok'='true'
  and r->>'binding_granted'='true' and r->>'binding_and_begin_atomic'='true'
  and r->'begin_receipt'->>'begin_granted'='true' and r->'begin_receipt'->>'production_request_id'=p1::text),false),'details','{}'::jsonb));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','binding_and_core_begin_both_persist_in_test_transaction','passed',coalesce((
  exists(select 1 from sol_action_bridge.bindings where job_id=j1 and production_request_id=p1)
  and exists(select 1 from sol_action.intents where request_id=p1 and job_id=j1 and action='begin')
  and exists(select 1 from sol_action.outcomes where request_id=p1 and job_id=j1)),false),'details','{}'::jsonb));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','bind_returns_no_token_or_capability_fields','passed',coalesce((position(token in r::text)=0
  and not(r?'capability') and not(r?'bridge_token') and not(r->'begin_receipt'?'capability') and not(r->'begin_receipt'?'bridge_token')),false),'details','{}'::jsonb));
 select count(*) into n from sol_action.events where job_id=j1;
 r:=public.sol_action_bridge_api('bind',payload);
 select count(*) into m from sol_action.events where job_id=j1;
 observations:=observations||jsonb_build_array(jsonb_build_object('name','duplicate_binding_non_grant_no_new_core_events','passed',coalesce((r->>'ok'='true'
  and r->>'binding_granted'='false' and r->>'status'='HISTORICAL_NOT_CURRENT' and not(r?'begin_receipt') and n=m),false),'details','{}'::jsonb));
 r:=public.sol_action_bridge_api('bind',payload||jsonb_build_object('production_request_id',missing));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','new_uuid_cannot_bypass_existing_binding','passed',coalesce((r->>'ok'='false'
  and (select count(*) from sol_action_bridge.bindings where job_id=j1)=1),false),'details','{}'::jsonb));
 r:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',cap,'target_request_id',p1));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','lost_atomic_bind_begin_is_retrievable_but_never_a_fresh_grant','passed',coalesce((r->>'found'='true'
  and r->'receipt'->>'begin_granted'='false' and r->'receipt'->>'pending'='true' and position('source_csv' in r::text)=0),false),'details','{}'::jsonb));

 -- Result is a known synthetic fixture, not a claimed invocation of the Python worker.
 candidate:=jsonb_build_object('source_sha256',sol_action.sha(csv),'rows',2,'row_ids',jsonb_build_array('a','b'),
  'totals',jsonb_build_array(jsonb_build_object('currency','EUR','amount','0.30')));
 r:=public.sol_action_api('result',jsonb_build_object('job_id',j1,'capability',cap,'request_id',res1,'expected_step_id','produce',
  'production_request_id',p1,'worker_version','SOL-ACTION-PY/0.1.0','result',candidate));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','synthetic_result_fixture_recorded','passed',coalesce((r->>'ok'='true'),false),'details','{}'::jsonb));
 r:=public.sol_action_api('reconcile',jsonb_build_object('job_id',j1,'capability',cap,'request_id',rec1,
  'target_request_id',p1,'production_request_id',p1));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','reconcile_fixture_has_outer_result_and_historical_inner_pending','passed',coalesce((r->>'ok'='true'
  and r->>'pending'='false' and r->'result'=candidate and r->'reconciled_outcome'->>'pending'='true'),false),'details','{}'::jsonb));
 select jsonb_build_array((select count(*) from sol_action.intents),(select count(*) from sol_action.outcomes),(select count(*) from sol_action.events)) into before_counts;
 a:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',cap,'target_request_id',rec1));
 b:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j1,'capability',cap,'target_request_id',rec1));
 select jsonb_build_array((select count(*) from sol_action.intents),(select count(*) from sol_action.outcomes),(select count(*) from sol_action.events)) into after_counts;
 observations:=observations||jsonb_build_array(jsonb_build_object('name','lost_reconcile_receipt_found_without_replay','passed',coalesce((a=b and a->>'found'='true'
  and a->'receipt'->>'action'='reconcile' and a->'receipt'->>'request_id'=rec1::text
  and a->'receipt'->>'pending'='false' and a->'receipt'->'result'=candidate and before_counts=after_counts),false),'details','{}'::jsonb));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','nested_source_and_all_old_authority_markers_redacted','passed',coalesce((
  position('source_csv' in a::text)=0 and position(cap in a::text)=0
  and position('"current_reuse_authorized": true' in a::text)=0
  and position('"begin_granted": true' in a::text)=0
  and a->'receipt'->'reconciled_outcome'->>'pending'='true'),false),'details','{}'::jsonb));

 payload:=payload||jsonb_build_object('job_id',j2,'production_request_id',p2);
 for idx in 1..5 loop
  q:=case idx when 1 then payload||jsonb_build_object('bridge_token',repeat('0',64))
   when 2 then payload||jsonb_build_object('release_hash',repeat('0',64))
   when 3 then payload||jsonb_build_object('self_hash',repeat('0',64))
   when 4 then payload||jsonb_build_object('manifest_hash',repeat('0',64))
   else payload||jsonb_build_object('capability',othercap) end;
  r:=public.sol_action_bridge_api('bind',q);
  observations:=observations||jsonb_build_array(jsonb_build_object('name','bad_token_release_selfhash_manifest_refused_'||idx,'passed',coalesce((r->>'ok'='false'
   and not exists(select 1 from sol_action_bridge.bindings where job_id=j2)
   and not exists(select 1 from sol_action.intents where job_id=j2 and action='begin')),false),'details','{}'::jsonb));
 end loop;
 r:=public.sol_action_api('begin',jsonb_build_object('job_id',j3,'capability',cap,'request_id',p3,'expected_step_id','produce'));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','legacy_unbound_begin_fixture_exists','passed',coalesce((r->>'ok'='true'),false),'details','{}'::jsonb));
 select count(*) into n from sol_action.events where job_id=j3;
 r:=public.sol_action_bridge_api('bind',payload||jsonb_build_object('job_id',j3,'production_request_id',p3));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','old_begin_cannot_be_given_new_release','passed',coalesce((r->>'ok'='false'
  and not exists(select 1 from sol_action_bridge.bindings where job_id=j3)
  and n=(select count(*) from sol_action.events where job_id=j3)),false),'details','{}'::jsonb));

 -- Reach the old core's documented per-job limit using valid synthetic reconciliations.
 for idx in 1..63 loop
  req:=('ab9d2d10-f6c3-4f5b-8ca4-'||lpad((100000+idx)::text,12,'0'))::uuid;
  r:=public.sol_action_api('reconcile',jsonb_build_object('job_id',j4,'capability',cap,'request_id',req,
   'target_request_id','ab9d2d10-f6c3-4f5b-8ca4-000000001004'));
  if r->>'ok' is distinct from 'true' then raise exception 'SYNTHETIC_QUOTA_SETUP_REFUSED'; end if;
 end loop;
 select count(*) into n from sol_action.events where job_id=j4;
 r:=public.sol_action_bridge_api('bind',payload||jsonb_build_object('job_id',j4,'production_request_id',p4));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','core_begin_controlled_refusal_rolls_back_binding','passed',coalesce((r->>'ok'='false'
  and not exists(select 1 from sol_action_bridge.bindings where job_id=j4)
  and not exists(select 1 from sol_action.intents where request_id=p4)
  and n=(select count(*) from sol_action.events where job_id=j4)),false),'details','{}'::jsonb));

 -- Insertion-failure trigger case is not executed by this no-DDL variant.


 -- Private storage: inspect exact grants/RLS and exercise immutable triggers as the owner.
 observations:=observations||jsonb_build_array(jsonb_build_object('name','both_tables_have_rls_without_policies','passed',coalesce((
  (select count(*) from pg_class c join pg_namespace ns on ns.oid=c.relnamespace where ns.nspname='sol_action_bridge'
   and c.relname in('releases','bindings') and c.relrowsecurity)=2
  and not exists(select 1 from pg_policies where schemaname='sol_action_bridge')),false),'details','{}'::jsonb));
 for idx in 1..3 loop
  error_message:=case idx when 1 then 'anon' when 2 then 'authenticated' else 'service_role' end;
  observations:=observations||jsonb_build_array(jsonb_build_object('name','no_direct_table_privileges_'||error_message,'passed',coalesce((
   not has_table_privilege(error_message,'sol_action_bridge.releases','SELECT,INSERT,UPDATE,DELETE,TRUNCATE')
   and not has_table_privilege(error_message,'sol_action_bridge.bindings','SELECT,INSERT,UPDATE,DELETE,TRUNCATE')),false),'details','{}'::jsonb));
 end loop;
 observations:=observations||jsonb_build_array(jsonb_build_object('name','anon_authenticated_can_use_only_rpc_boundary','passed',coalesce((
  has_function_privilege('anon','public.sol_action_bridge_api(text,jsonb)','EXECUTE')
  and has_function_privilege('authenticated','public.sol_action_bridge_api(text,jsonb)','EXECUTE')
  and not has_function_privilege('service_role','public.sol_action_bridge_api(text,jsonb)','EXECUTE')
  and not has_function_privilege('anon','sol_action_bridge.token_matches(text,text)','EXECUTE')),false),'details','{}'::jsonb));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','definer_private_empty_path_and_invoker_public','passed',coalesce((
  (select p.prosecdef and p.proconfig @> array['search_path=""'] from pg_proc p where p.oid='sol_action_bridge.dispatch(text,jsonb)'::regprocedure)
  and (select not p.prosecdef from pg_proc p where p.oid='public.sol_action_bridge_api(text,jsonb)'::regprocedure)),false),'details','{}'::jsonb));
 denied:=false;
 begin update sol_action_bridge.releases set deployment_id='NO_CHANGE_ALLOWED' where release_hash=rh;
 exception when others then denied:=sqlstate='P0001' and sqlerrm='APPEND_ONLY'; end;
 observations:=observations||jsonb_build_array(jsonb_build_object('name','release_update_denied_by_append_only_trigger','passed',coalesce((denied),false),'details','{}'::jsonb));
 denied:=false;
 begin delete from sol_action_bridge.bindings where job_id=j1;
 exception when others then denied:=sqlstate='P0001' and sqlerrm='APPEND_ONLY'; end;
 observations:=observations||jsonb_build_array(jsonb_build_object('name','binding_delete_denied_by_append_only_trigger','passed',coalesce((denied),false),'details','{}'::jsonb));
 -- TRUNCATE trigger execution is not part of this no-DDL variant.
 observations:=observations||jsonb_build_array(jsonb_build_object('name','old_and_bridge_runtime_function_hashes_unchanged','passed',coalesce((
  sol_action.runtime_hash()=core_hash and sol_action_bridge.runtime_hash()=bridge_hash),false),'details','{}'::jsonb));
 observations:=observations||jsonb_build_array(jsonb_build_object('name','no_real_worker_invoked','passed',coalesce((true),false),'details',jsonb_build_object('method','SQL-only synthetic protocol fixtures; no HTTP/worker call exists in this script')));
 exception when others then
  observations:=observations||jsonb_build_array(jsonb_build_object('name','fatal_environment_or_sql_error','passed',false,'details',jsonb_build_object('sqlstate',sqlstate,'error',left(sqlerrm,300))));
 end;

 perform set_config('sol_bridge_test.result',jsonb_build_object(
  'schema','SOL_ACTION_BRIDGE_TRANSACTIONAL_LIVE_TEST_NODDL/v1',
  'observed_at',sol_action.utc(clock_timestamp()),
  'assertions',jsonb_array_length(observations),
  'passed',(select count(*) from jsonb_array_elements(observations) v where v->>'passed'='true'),
  'failed',(select count(*) from jsonb_array_elements(observations) v where v->>'passed'='false'),
  'status',case when exists(select 1 from jsonb_array_elements(observations) v where v->>'passed'='false') then 'FAIL' else 'PASS' end,
  'observations',observations,'synthetic_fixtures_only',true,'real_worker_execution',false,
  'completion_authority','NONE','all_fixture_effects','TO_BE_ROLLED_BACK_BY_FINAL_STATEMENT',
  'not_executed',jsonb_build_array('Binding insertion failure after successful core begin: requires optional temporary trigger fixture.','TRUNCATE trigger execution: DDL excluded from this variant.')
 )::text,true);
end
$live$;
select current_setting('sol_bridge_test.result',true)::jsonb as result;
rollback;
