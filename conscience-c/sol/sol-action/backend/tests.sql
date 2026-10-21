-- OPERATOR ONLY. Run after migration in a rollback-only transaction, never as a persistent fixture.
-- No HTTP, no real worker, no production token/capability, no prior object overwritten.
begin;
create temporary table refusal_assertions(name text primary key,passed boolean,details jsonb default '{}') on commit drop;
create function pg_temp.a(n text,b boolean,d jsonb default '{}') returns void language plpgsql as $$
 begin insert into pg_temp.refusal_assertions values(n,coalesce(b,false),d);end $$;
do $tests$
declare j uuid:='a171bc92-4dc0-44c9-a660-000000000001'; j2 uuid:='a171bc92-4dc0-44c9-a660-000000000002';
 c uuid:='a171bc92-4dc0-44c9-a660-000000000101';c2 uuid:='a171bc92-4dc0-44c9-a660-000000000102';
 bad uuid:='a171bc92-4dc0-44c9-a660-000000000201';bad2 uuid:='a171bc92-4dc0-44c9-a660-000000000202';
 rec uuid:='a171bc92-4dc0-44c9-a660-000000000301';miss uuid:='a171bc92-4dc0-44c9-a660-000000009999';
 prod uuid:='a171bc92-4dc0-44c9-a660-000000000401';res uuid:='a171bc92-4dc0-44c9-a660-000000000402';
 ver uuid:='a171bc92-4dc0-44c9-a660-000000000403';comp uuid:='a171bc92-4dc0-44c9-a660-000000000404';
 cap text:=repeat('a',64);other text:=repeat('b',64);csv text:=E'id,currency,amount\na,EUR,0.10\nb,EUR,0.20\n';
 r jsonb;s jsonb;t jsonb;d jsonb;ev bigint;rh text;bh text;phase text;denied boolean;role_name text;tbl text;
begin
 rh:=sol_action.runtime_hash();bh:=sol_action_bridge.runtime_hash();
 if exists(select 1 from sol_action.jobs where job_id in(j,j2)) then raise exception 'FIXTURE_COLLISION';end if;
 for d in select jsonb_build_object('job_id',x,'request_id',case when x=j then c else c2 end,'capability',cap,
  'mandate','Synthetic test only, candidate does not prove semantic truth.', 'requirements',jsonb_build_array('Exact CSV cents.'),
  'source_csv',csv,'source_origin',jsonb_build_object('kind','declared')) from unnest(array[j,j2]) x loop
  r:=public.sol_action_api('create',d);
  if r->>'ok' is distinct from 'true' then raise exception 'FIXTURE_CREATE_FAILED';end if;
 end loop;
 perform pg_temp.a('core_runtime_same_reviewed_predecessor',rh='c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0');
 -- Reproduce the defect without fabricating an UNKNOWN terminal observation.
 d:=jsonb_build_object('job_id',j,'capability',cap,'request_id',bad,'expected_step_id','complete');
 select count(*) into ev from sol_action.events where job_id=j;
 r:=public.sol_action_api('complete',d);
 perform pg_temp.a('baseline_core_refusal_known_no_effect',r->>'status'='REJECTED' and r->>'error'='PRODUCTION_PENDING'
  and r->>'effect'='NONE_SQL_TRANSACTION_ROLLED_BACK' and r->>'sqlstate'='P0001');
 perform pg_temp.a('baseline_refusal_not_retrievable_in_core',not exists(select 1 from sol_action.intents where request_id=bad)
  and not exists(select 1 from sol_action.outcomes where request_id=bad) and ev=(select count(*) from sol_action.events where job_id=j));
 r:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j,'capability',cap,'target_request_id',bad));
 perform pg_temp.a('baseline_lookup_absence_unknown',r->>'found'='false' and r->>'status'='UNKNOWN');
 -- New request captures its actual controlled refusal outside the unchanged core block.
 d:=d||jsonb_build_object('request_id',bad2);
 r:=public.sol_action_bridge_api('execute',jsonb_build_object('core_action','complete','core_input',d));
 perform pg_temp.a('refusal_durably_terminal_no_effect',r->>'status'='REJECTED' and r->>'durable_refusal'='true'
  and r->>'terminal'='true' and r->>'effect_scope'='CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY'
  and r->>'core_effect_scope'='THIS_RPC_SQL_TRANSACTION_ONLY' and r->>'business_effect'='NONE_CORE_ACTION_ROLLED_BACK'
  and r->>'receipt_recording_effect'='APPEND_ONLY_BRIDGE_RECEIPT_RECORDED' and r->>'current_reuse_authorized'='false',r);
 perform pg_temp.a('refusal_identity_and_input_hash_exact',r->>'job_id'=j::text and r->>'request_id'=bad2::text
  and r->>'action'='complete' and r->>'payload_hash'=sol_action.sha(jsonb_build_object('action','complete','input',d-'capability'-'parent_capability')::text));
 perform pg_temp.a('refusal_internal_capability_and_actor_bound',exists(select 1 from sol_action_bridge.refusals where request_id=bad2
  and capability_hash=extensions.digest(convert_to(cap,'UTF8'),'sha256') and actor_scope='AUTHORIZED_JOB_CAPABILITY_HOLDER_NOT_IDENTITY_ATTESTATION'
  and receipt_sha256=sol_action.sha(receipt::text) and core_runtime_hash=rh and bridge_runtime_hash=bh));
 perform pg_temp.a('refused_action_no_core_effect',not exists(select 1 from sol_action.intents where request_id=bad2)
  and not exists(select 1 from sol_action.outcomes where request_id=bad2) and ev=(select count(*) from sol_action.events where job_id=j));
 s:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j,'capability',cap,'target_request_id',bad2));
 perform pg_temp.a('lost_refusal_lookup_terminal_historical',s->>'found'='true' and s->>'target_action'='complete'
  and s->>'receipt_kind'='CONTROLLED_REFUSAL' and s->'receipt'->>'historical_status'='REJECTED'
  and s->'receipt'->>'status'='HISTORICAL_NOT_CURRENT' and s->'receipt'->>'durable_refusal'='true');
 t:=public.sol_action_bridge_api('execute',jsonb_build_object('core_action','complete','core_input',d));
 perform pg_temp.a('same_uuid_refusal_never_reexecuted',t->>'deduplicated'='true' and t->>'status'='HISTORICAL_NOT_CURRENT'
  and (select count(*) from sol_action_bridge.refusals where request_id=bad2)=1 and ev=(select count(*) from sol_action.events where job_id=j));
 t:=public.sol_action_bridge_api('execute',jsonb_build_object('core_action','complete','core_input',d||jsonb_build_object('expected_step_id','changed')));
 perform pg_temp.a('same_uuid_changed_payload_refused',t->>'ok'='false' and not(t?'receipt') and not(t?'durable_refusal'));
 t:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j,'capability',other,'target_request_id',bad2));
 perform pg_temp.a('wrong_capability_no_receipt_disclosure',t->>'ok'='false' and not(t?'receipt'));
 t:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j2,'capability',cap,'target_request_id',bad2));
 perform pg_temp.a('cross_job_refusal_no_disclosure',t->>'ok'='false' and not(t?'receipt'));
 d:=jsonb_build_object('job_id',j,'capability',cap,'request_id',rec,'target_request_id',bad2);
 r:=public.sol_action_bridge_api('execute',jsonb_build_object('core_action','reconcile','core_input',d));
 perform pg_temp.a('reconcile_refusal_no_worker_or_oracle',r->>'ok'='true' and r->>'outcome_known'='true'
  and r->>'worker_reexecuted'='false' and r->>'pending'='false' and r->'verification'='null'::jsonb
  and r->'completion'='null'::jsonb and not exists(select 1 from sol_action.intents where request_id=rec));
 perform pg_temp.a('reconcile_correlates_original_action',r->>'target_request_id'=bad2::text and r->>'target_action'='complete'
  and r->'reconciled_outcome'->>'request_id'=bad2::text and r->'reconciled_outcome'->>'action'='complete'
  and r->'reconciled_outcome'->>'historical_status'='REJECTED');
 s:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j,'capability',cap,'target_request_id',rec));
 perform pg_temp.a('lost_reconcile_itself_recoverable',s->>'found'='true' and s->>'target_action'='reconcile'
  and s->>'receipt_kind'='REFUSAL_RECONCILIATION' and s->'receipt'->>'request_id'=rec::text
  and s->'receipt'->'reconciled_outcome'->>'request_id'=bad2::text);
 t:=public.sol_action_bridge_api('execute',jsonb_build_object('core_action','reconcile','core_input',d));
 perform pg_temp.a('reconcile_uuid_dedup_no_new_observation',t->>'deduplicated'='true' and (select count(*) from sol_action_bridge.recovery_outcomes where request_id=rec)=1
  and ev=(select count(*) from sol_action.events where job_id=j));
 perform pg_temp.a('historical_redaction_no_authority',position(cap in s::text)=0 and position('source_csv' in s::text)=0
  and position('"current_reuse_authorized": true' in s::text)=0 and position('"begin_granted": true' in s::text)=0);
 s:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j,'capability',cap,'target_request_id',miss));
 perform pg_temp.a('absence_stays_unknown_no_refusal_fabricated',s->>'found'='false' and s->>'status'='UNKNOWN'
  and not exists(select 1 from sol_action_bridge.refusals where request_id=miss));
 -- Preserve successful flow and the original 60 second observation discipline.
 r:=public.sol_action_api('begin',jsonb_build_object('job_id',j,'capability',cap,'request_id',prod,'expected_step_id','produce'));
 if r->>'ok' is distinct from 'true' then raise exception 'FIXTURE_BEGIN_FAILED';end if;
 r:=public.sol_action_api('result',jsonb_build_object('job_id',j,'capability',cap,'request_id',res,'expected_step_id','produce',
  'production_request_id',prod,'worker_version','SOL-ACTION-PY/0.1.0','result',sol_action.oracle(csv)));
 if r->>'ok' is distinct from 'true' then raise exception 'FIXTURE_RESULT_FAILED';end if;
 r:=public.sol_action_bridge_api('execute',jsonb_build_object('core_action','verify','core_input',jsonb_build_object('job_id',j,'capability',cap,'request_id',ver,'expected_step_id','verify')));
 perform pg_temp.a('success_verify_uses_unchanged_oracle_and_ttl',r->>'ok'='true' and r->'verification'->>'status'='PASS'
  and (r->'verification'->>'expires_at')::timestamptz-(r->'verification'->>'observed_at')::timestamptz=interval '60 seconds');
 r:=public.sol_action_bridge_api('execute',jsonb_build_object('core_action','complete','core_input',jsonb_build_object('job_id',j,'capability',cap,'request_id',comp,'expected_step_id','complete')));
 perform pg_temp.a('success_complete_bounded_scope_preserved',r->>'status'='COMPLETED_BOUNDED' and r->'completion'->>'scope'='CSV_EXACT_CENTS_ONLY'
  and r->'completion'->>'semantic_truth'='UNKNOWN');
 s:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j,'capability',cap,'target_request_id',comp));
 perform pg_temp.a('successful_history_not_replaced_by_refusal',s->>'receipt_kind'='CORE_OUTCOME' and s->>'found'='true'
  and s->'receipt'->>'current_reuse_authorized'='false' and not exists(select 1 from sol_action_bridge.refusals where request_id=comp));
 -- Explicitly exhibit legacy bypass collision; lookup refuses rather than hiding either record.
 insert into sol_action.intents(request_id,job_id,action,payload_hash) values(bad2,j,'complete',repeat('0',64));
 s:=public.sol_action_bridge_api('lookup_receipt',jsonb_build_object('job_id',j,'capability',cap,'target_request_id',bad2));
 perform pg_temp.a('core_bridge_collision_refuses_all_receipts',s->>'ok'='false' and not(s?'receipt'));
 foreach tbl in array array['refusals','recovery_outcomes'] loop
  perform pg_temp.a(tbl||'_rls_no_policy', (select c.relrowsecurity from pg_class c where c.oid=('sol_action_bridge.'||tbl)::regclass)
   and not exists(select 1 from pg_policies where schemaname='sol_action_bridge' and tablename=tbl));
  foreach role_name in array array['anon','authenticated','service_role'] loop
   perform pg_temp.a(tbl||'_no_direct_'||role_name,not has_table_privilege(role_name,'sol_action_bridge.'||tbl,'SELECT,INSERT,UPDATE,DELETE,TRUNCATE'));
  end loop;
  denied:=false;begin execute format('update sol_action_bridge.%I set action=action',tbl);exception when others then denied:=sqlstate='P0001' and sqlerrm='APPEND_ONLY';end;
  perform pg_temp.a(tbl||'_update_denied',denied);
  denied:=false;begin execute format('delete from sol_action_bridge.%I',tbl);exception when others then denied:=sqlstate='P0001' and sqlerrm='APPEND_ONLY';end;
  perform pg_temp.a(tbl||'_delete_denied',denied);
  denied:=false;begin execute format('truncate sol_action_bridge.%I',tbl);exception when others then denied:=sqlstate='P0001' and sqlerrm='APPEND_ONLY';end;
  perform pg_temp.a(tbl||'_truncate_denied',denied);
 end loop;
 perform pg_temp.a('helpers_not_directly_granted',not has_function_privilege('anon','sol_action_bridge.execute_core(jsonb)','EXECUTE')
  and not has_function_privilege('authenticated','sol_action_bridge.receipt_lookup(uuid,uuid,text)','EXECUTE'));
 perform pg_temp.a('old_core_hash_preserved_and_bridge_stable_during_tests',sol_action.runtime_hash()=rh and sol_action_bridge.runtime_hash()=bh);
exception when others then
 insert into pg_temp.refusal_assertions values('fatal_error',false,jsonb_build_object('sqlstate',sqlstate,'error',left(sqlerrm,300)));
end $tests$;
select jsonb_build_object('schema','SOL_ACTION_DURABLE_REFUSAL_SQL_TEST/v1','observed_at',sol_action.utc(clock_timestamp()),
 'passed',(select count(*) from pg_temp.refusal_assertions where passed),'failed',(select count(*) from pg_temp.refusal_assertions where not passed),
 'observations',(select jsonb_agg(jsonb_build_object('name',name,'passed',passed,'details',details) order by name) from pg_temp.refusal_assertions),
 'fixture_effects','ROLLED_BACK_BY_FINAL_STATEMENT','worker_execution',false) as result;
rollback;
