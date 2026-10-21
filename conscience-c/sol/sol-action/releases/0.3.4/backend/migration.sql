-- SOL-Creation-Guard 0.1.0 for application 0.3.4. Additive and intentionally non-replayable.
-- Existing Action/Bridge/Atelier/Preuve definitions, ACLs, releases and data remain untouched.
BEGIN;
DO $$ BEGIN
 IF sol_action.runtime_hash()<>'c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0' OR sol_action_bridge.runtime_hash()<>'d7ee0d9d373978aa9e05892c491f6c115710bd6ad9c29923fba42ba3c64328f7' THEN RAISE EXCEPTION 'REVIEWED_PREDECESSOR_REQUIRED'; END IF;
END $$;
CREATE SCHEMA sol_creation_guard;
REVOKE ALL ON SCHEMA sol_creation_guard FROM PUBLIC,anon,authenticated,service_role;
CREATE FUNCTION sol_creation_guard.sha(p text) RETURNS text LANGUAGE sql IMMUTABLE STRICT SET search_path='' AS $$ SELECT encode(extensions.digest(convert_to(p,'UTF8'),'sha256'),'hex') $$;
CREATE FUNCTION sol_creation_guard.runtime_hash() RETURNS text LANGUAGE sql STABLE SET search_path='' AS $$
 SELECT sol_creation_guard.sha(string_agg(pg_get_functiondef(p.oid),E'\n' ORDER BY n.nspname,p.proname,pg_get_function_identity_arguments(p.oid))) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE p.prokind='f' AND (n.nspname='sol_creation_guard' OR (n.nspname='public' AND p.proname='sol_action_creation_api')) $$;
CREATE TABLE sol_creation_guard.admissions(release_hash text PRIMARY KEY CHECK(release_hash ~ '^[0-9a-f]{64}$'),guard_runtime_hash text NOT NULL DEFAULT sol_creation_guard.runtime_hash(),core_runtime_hash text NOT NULL DEFAULT sol_action.runtime_hash(),bridge_runtime_hash text NOT NULL DEFAULT sol_action_bridge.runtime_hash(),release_metadata_hash text NOT NULL,admitted_at timestamptz NOT NULL DEFAULT clock_timestamp(),admitted_by text NOT NULL DEFAULT session_user);
CREATE TABLE sol_creation_guard.requests(request_id uuid PRIMARY KEY,job_id uuid UNIQUE NOT NULL,payload_hash text NOT NULL CHECK(payload_hash ~ '^[0-9a-f]{64}$'),capability_hash bytea NOT NULL CHECK(octet_length(capability_hash)=32),request_binding_hash text NOT NULL CHECK(request_binding_hash ~ '^[0-9a-f]{64}$'),release_hash text NOT NULL,guard_runtime_hash text NOT NULL,core_runtime_hash text NOT NULL,bridge_runtime_hash text NOT NULL,reserved_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE INDEX ON sol_creation_guard.requests(reserved_at);
CREATE TABLE sol_creation_guard.refusals(request_id uuid PRIMARY KEY REFERENCES sol_creation_guard.requests(request_id),job_id uuid NOT NULL,receipt jsonb NOT NULL,receipt_sha256 text GENERATED ALWAYS AS (sol_creation_guard.sha(receipt::text)) STORED,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TABLE sol_creation_guard.events(sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,id uuid UNIQUE NOT NULL,job_id uuid NOT NULL,request_id uuid NOT NULL,kind text NOT NULL CHECK(kind IN ('reservation','refusal','core_outcome','unknown')),at timestamptz NOT NULL,data jsonb NOT NULL,previous_hash text NOT NULL,event_hash text NOT NULL);
CREATE FUNCTION sol_creation_guard.no_change() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$ BEGIN RAISE EXCEPTION 'SOL_CREATION_GUARD_APPEND_ONLY' USING ERRCODE='42501'; END $$;
DO $$ DECLARE t text; BEGIN FOREACH t IN ARRAY ARRAY['admissions','requests','refusals','events'] LOOP
 EXECUTE format('ALTER TABLE sol_creation_guard.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON sol_creation_guard.%I FOR EACH ROW EXECUTE FUNCTION sol_creation_guard.no_change()',t);
 EXECUTE format('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON sol_creation_guard.%I FOR EACH STATEMENT EXECUTE FUNCTION sol_creation_guard.no_change()',t);
END LOOP; END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA sol_creation_guard FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA sol_creation_guard FROM PUBLIC,anon,authenticated,service_role;
CREATE FUNCTION sol_creation_guard.release_metadata(r sol_action_bridge.releases) RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT jsonb_build_object('release_hash',r.release_hash,'manifest_hash',r.manifest_hash,'source_commit',r.source_commit,'source_files',r.source_files,'deployment_id',r.deployment_id,'deployment_url',r.deployment_url,'core_runtime_hash',r.core_runtime_hash,'bridge_runtime_hash',r.bridge_runtime_hash,'admitted_at',sol_action.utc(r.admitted_at),'admitted_by',r.admitted_by) $$;
CREATE FUNCTION sol_creation_guard.admission_check() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$
DECLARE r sol_action_bridge.releases%ROWTYPE; h text;
BEGIN
 IF session_user NOT IN ('postgres','supabase_admin') THEN RAISE EXCEPTION 'SQL_OPERATOR_ADMISSION_REQUIRED'; END IF;
 SELECT * INTO r FROM sol_action_bridge.releases x WHERE x.release_hash=NEW.release_hash;
 IF NOT FOUND OR r.core_runtime_hash<>sol_action.runtime_hash() OR r.bridge_runtime_hash<>sol_action_bridge.runtime_hash() OR NEW.guard_runtime_hash<>sol_creation_guard.runtime_hash() OR NEW.core_runtime_hash<>r.core_runtime_hash OR NEW.bridge_runtime_hash<>r.bridge_runtime_hash THEN RAISE EXCEPTION 'CURRENT_ADMITTED_RELEASE_REQUIRED'; END IF;
 h:=sol_creation_guard.sha(sol_creation_guard.release_metadata(r)::text);
 IF NEW.release_metadata_hash IS NOT NULL AND NEW.release_metadata_hash<>h THEN RAISE EXCEPTION 'RELEASE_METADATA_MISMATCH'; END IF;
 NEW.release_metadata_hash:=h; RETURN NEW;
END $$;
CREATE TRIGGER admission_validate BEFORE INSERT ON sol_creation_guard.admissions FOR EACH ROW EXECUTE FUNCTION sol_creation_guard.admission_check();
CREATE FUNCTION sol_creation_guard.append_event(j uuid,r uuid,k text,d jsonb) RETURNS void LANGUAGE plpgsql SET search_path='' AS $$
DECLARE ident uuid:=gen_random_uuid(); stamp timestamptz:=clock_timestamp(); prev text;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended('sol_creation_guard:journal',0)); SELECT event_hash INTO prev FROM sol_creation_guard.events ORDER BY sequence DESC LIMIT 1; prev:=coalesce(prev,repeat('0',64));
 INSERT INTO sol_creation_guard.events(id,job_id,request_id,kind,at,data,previous_hash,event_hash) VALUES(ident,j,r,k,stamp,d,prev,sol_creation_guard.sha(jsonb_build_object('id',ident,'job_id',j,'request_id',r,'kind',k,'at',sol_action.utc(stamp),'data',d,'previous_hash',prev)::text));
END $$;
CREATE FUNCTION sol_creation_guard.audit() RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path='' AS $$
DECLARE entry record; prev text:=repeat('0',64); bad bigint:=0; links bigint:=0; n bigint:=0; h text; pending bigint;
BEGIN
 FOR entry IN SELECT * FROM sol_creation_guard.events ORDER BY sequence LOOP
 h:=sol_creation_guard.sha(jsonb_build_object('id',entry.id,'job_id',entry.job_id,'request_id',entry.request_id,'kind',entry.kind,'at',sol_action.utc(entry.at),'data',entry.data,'previous_hash',entry.previous_hash)::text);
 IF entry.previous_hash IS DISTINCT FROM prev OR entry.event_hash IS DISTINCT FROM h THEN bad:=bad+1; END IF; prev:=entry.event_hash; n:=n+1; END LOOP;
 SELECT count(*) INTO links FROM sol_creation_guard.requests q WHERE q.request_binding_hash IS DISTINCT FROM sol_creation_guard.sha(encode(q.capability_hash,'hex')||':'||q.payload_hash||':'||q.job_id::text||':'||q.request_id::text||':create') OR (SELECT count(*) FROM sol_creation_guard.events e WHERE e.request_id=q.request_id AND e.job_id=q.job_id AND e.kind='reservation' AND e.data->>'payload_hash'=q.payload_hash AND e.data->>'request_binding_hash'=q.request_binding_hash)<>1;
 SELECT links+count(*) INTO links FROM sol_creation_guard.refusals f WHERE NOT EXISTS(SELECT 1 FROM sol_creation_guard.requests q WHERE q.request_id=f.request_id AND q.job_id=f.job_id) OR f.receipt->>'job_id' IS DISTINCT FROM f.job_id::text OR f.receipt->>'request_id' IS DISTINCT FROM f.request_id::text OR f.receipt->>'action' IS DISTINCT FROM 'create' OR f.receipt->>'effect_scope' IS DISTINCT FROM 'CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY' OR f.receipt->>'core_effect_scope' IS DISTINCT FROM 'THIS_RPC_SQL_TRANSACTION_ONLY' OR f.receipt->'durable_refusal' IS DISTINCT FROM 'true'::jsonb OR (SELECT count(*) FROM sol_creation_guard.events e WHERE e.request_id=f.request_id AND e.job_id=f.job_id AND e.kind='refusal' AND e.data->>'receipt_sha256'=f.receipt_sha256)<>1 OR EXISTS(SELECT 1 FROM sol_action.intents i WHERE i.request_id=f.request_id) OR EXISTS(SELECT 1 FROM sol_action.outcomes o WHERE o.request_id=f.request_id);
 SELECT links+count(*) INTO links FROM sol_creation_guard.events e WHERE
 (e.kind='reservation' AND NOT EXISTS(SELECT 1 FROM sol_creation_guard.requests q WHERE q.request_id=e.request_id AND q.job_id=e.job_id AND q.payload_hash=e.data->>'payload_hash' AND q.request_binding_hash=e.data->>'request_binding_hash')) OR
 (e.kind='refusal' AND NOT EXISTS(SELECT 1 FROM sol_creation_guard.refusals f WHERE f.request_id=e.request_id AND f.job_id=e.job_id AND f.receipt_sha256=e.data->>'receipt_sha256')) OR
 (e.kind='core_outcome' AND NOT EXISTS(SELECT 1 FROM sol_action.outcomes o JOIN sol_action.intents i USING(request_id) JOIN sol_creation_guard.requests q ON q.request_id=o.request_id WHERE o.request_id=e.request_id AND o.job_id=e.job_id AND i.action='create' AND i.payload_hash=q.payload_hash AND sol_creation_guard.sha(o.receipt::text)=e.data->>'receipt_sha256')) OR
 (e.kind='unknown' AND NOT EXISTS(SELECT 1 FROM sol_creation_guard.requests q WHERE q.request_id=e.request_id AND q.job_id=e.job_id));
 SELECT count(*) INTO pending FROM sol_creation_guard.requests q WHERE NOT EXISTS(SELECT 1 FROM sol_creation_guard.refusals f WHERE f.request_id=q.request_id) AND NOT EXISTS(SELECT 1 FROM sol_action.outcomes o JOIN sol_action.intents i USING(request_id) WHERE o.request_id=q.request_id AND o.job_id=q.job_id AND i.action='create' AND i.payload_hash=q.payload_hash);
 RETURN jsonb_build_object('valid',bad=0 AND links=0,'events',n,'head',prev,'invalid_events',bad,'incoherent_records',links,'pending_creation_requests',pending,'scope','GUARD_HASH_CHAIN_AND_RECEIPT_LINKS','owner_tamper_resistance','NOT_WORM','current_reuse_authorized',false);
END $$;
CREATE FUNCTION sol_creation_guard.cap_matches(cap text,expected bytea) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT coalesce(octet_length(expected)=32 AND sol_action_bridge.token_matches(cap,encode(expected,'hex')),false) $$;
CREATE FUNCTION sol_creation_guard.validate_create(d jsonb) RETURNS void LANGUAGE plpgsql SET search_path='' AS $$
DECLARE v jsonb; k text; parent sol_action.jobs%ROWTYPE;
BEGIN
 PERFORM sol_action.keys(d,ARRAY['job_id','capability','request_id','mandate','requirements','source_csv','source_origin','parent_job_id','parent_capability'],ARRAY['job_id','capability','request_id','mandate','requirements','source_csv','source_origin']);
 IF octet_length(d::text)>180000 THEN RAISE EXCEPTION 'INVALID'; END IF;
 PERFORM sol_action.text_field(d,'job_id',36,36)::uuid; PERFORM sol_action.text_field(d,'request_id',36,36)::uuid;
 IF d->>'job_id'<>((d->>'job_id')::uuid)::text OR d->>'request_id'<>((d->>'request_id')::uuid)::text OR sol_action.text_field(d,'capability',64,64) !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID'; END IF;
 PERFORM sol_action.text_field(d,'mandate',1,10000); PERFORM sol_action.text_field(d,'source_csv',1,32768); IF octet_length(d->>'source_csv')>32768 THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF jsonb_typeof(d->'requirements') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'INVALID'; END IF; IF jsonb_array_length(d->'requirements') NOT BETWEEN 1 AND 32 THEN RAISE EXCEPTION 'INVALID'; END IF;
 FOR v IN SELECT value FROM jsonb_array_elements(d->'requirements') LOOP IF jsonb_typeof(v) IS DISTINCT FROM 'string' OR length(v#>>'{}') NOT BETWEEN 1 AND 2000 OR btrim(v#>>'{}')='' THEN RAISE EXCEPTION 'INVALID'; END IF; END LOOP;
 PERFORM sol_action.keys(d->'source_origin',ARRAY['kind','provider','reference'],ARRAY['kind']); IF sol_action.text_field(d->'source_origin','kind',1,30) NOT IN ('declared','connector-retrieved') THEN RAISE EXCEPTION 'INVALID'; END IF;
 FOREACH k IN ARRAY ARRAY['provider','reference'] LOOP IF d->'source_origin' ? k THEN PERFORM sol_action.text_field(d->'source_origin',k,1,512); END IF; END LOOP;
 IF (d ? 'parent_job_id') IS DISTINCT FROM (d ? 'parent_capability') THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF d ? 'parent_job_id' THEN
 SELECT * INTO parent FROM sol_action.jobs x WHERE x.job_id=sol_action.text_field(d,'parent_job_id',36,36)::uuid;
 IF NOT FOUND OR d->>'parent_capability'=d->>'capability' THEN RAISE EXCEPTION 'INVALID'; END IF; PERFORM sol_action.authorize(parent,sol_action.text_field(d,'parent_capability',64,64));
 END IF;
END $$;
CREATE FUNCTION sol_creation_guard.controlled_create_refusal(r jsonb,j uuid,q uuid) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$
 SELECT coalesce(r->'ok'='false'::jsonb AND r->>'status'='REJECTED' AND r->>'sqlstate'='P0001' AND r->>'effect'='NONE_SQL_TRANSACTION_ROLLED_BACK' AND r->>'effect_scope'='THIS_RPC_SQL_TRANSACTION_ONLY' AND r->>'job_id'=j::text AND r->>'request_id'=q::text AND r->>'action'='create' AND r->>'error'=ANY(ARRAY['CSV_SIZE','CSV_LONE_CR','CSV_AFTER_QUOTE','CSV_QUOTE_IN_UNQUOTED','CSV_UNCLOSED_QUOTE','CSV_ROW_COUNT','CSV_ROW_LIMIT','CSV_HEADER','CSV_COLUMNS','CSV_ID','CSV_CURRENCY','CSV_AMOUNT','DAILY_JOB_LIMIT','DAILY_INTENT_LIMIT','JOB_INTENT_LIMIT','JOB_ALREADY_EXISTS','PARENT_PRODUCTION_PENDING_NO_COMPENSATION','PARENT_REQUIREMENTS_OMITTED','PARENT_REQUIREMENTS_CHANGED']),false) $$;
CREATE FUNCTION sol_creation_guard.lookup(jid uuid,target uuid,cap text) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE j sol_action.jobs%ROWTYPE; q sol_creation_guard.requests%ROWTYPE; f sol_creation_guard.refusals%ROWTYPE; i sol_action.intents%ROWTYPE; o sol_action.outcomes%ROWTYPE; receipt jsonb; kind text; present boolean;
BEGIN
 IF cap IS NULL OR cap !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID'; END IF;
 SELECT * INTO j FROM sol_action.jobs x WHERE x.job_id=jid; present:=FOUND; IF present THEN PERFORM sol_action.authorize(j,cap); END IF;
 SELECT * INTO q FROM sol_creation_guard.requests x WHERE x.request_id=target;
 IF FOUND AND (q.job_id<>jid OR NOT sol_creation_guard.cap_matches(cap,q.capability_hash)) THEN RAISE EXCEPTION 'INVALID'; END IF;
 -- No registry scan or legacy read without an authorized job or exact cap-bound request.
 -- Missing, wrong-cap and cross-job references have the same opaque denial.
 IF NOT present AND q.request_id IS NULL THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF sol_creation_guard.audit()->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF q.request_id IS NOT NULL THEN
 SELECT * INTO f FROM sol_creation_guard.refusals x WHERE x.request_id=target;
 IF FOUND THEN
 IF f.job_id<>jid OR f.receipt->>'job_id' IS DISTINCT FROM jid::text OR f.receipt->>'request_id' IS DISTINCT FROM target::text OR f.receipt->>'action' IS DISTINCT FROM 'create' OR f.receipt->'durable_refusal' IS DISTINCT FROM 'true'::jsonb OR EXISTS(SELECT 1 FROM sol_action.intents x WHERE x.request_id=target) OR EXISTS(SELECT 1 FROM sol_action.outcomes x WHERE x.request_id=target) THEN RAISE EXCEPTION 'RECEIPT_COLLISION'; END IF;
 receipt:=f.receipt; kind:='CONTROLLED_CREATION_REFUSAL';
 END IF;
 END IF;
 SELECT * INTO i FROM sol_action.intents x WHERE x.request_id=target; SELECT * INTO o FROM sol_action.outcomes x WHERE x.request_id=target;
 IF (i.request_id IS NOT NULL AND (i.job_id<>jid OR i.action<>'create')) OR (o.request_id IS NOT NULL AND (o.job_id<>jid OR i.request_id IS NULL)) THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF receipt IS NULL AND present AND o.request_id IS NOT NULL AND o.receipt->'ok'='true'::jsonb THEN
 IF q.request_id IS NOT NULL AND (i.payload_hash<>q.payload_hash OR j.capability_hash<>q.capability_hash) THEN RAISE EXCEPTION 'RECEIPT_COLLISION'; END IF;
 receipt:=o.receipt; kind:='CORE_CREATION_OUTCOME';
 END IF;
 RETURN jsonb_build_object('ok',true,'action','lookup_receipt','status',CASE WHEN receipt IS NULL THEN 'UNKNOWN' ELSE 'HISTORICAL_NOT_CURRENT' END,'job_id',jid,'target_request_id',target,'target_action','create','receipt_kind',kind,'found',receipt IS NOT NULL,'intent_found',q.request_id IS NOT NULL OR i.request_id IS NOT NULL,'receipt_status',receipt->>'status','receipt',CASE WHEN receipt IS NULL THEN NULL ELSE sol_action_bridge.historical(receipt,cap) END,'current_reuse_authorized',false,'automatic_retry',false,'worker_reexecuted',false,'legacy_unrecorded_refusal','UNKNOWN');
END $$;
CREATE FUNCTION sol_creation_guard.create_guarded(p jsonb) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE d jsonb; jid uuid; req uuid; cap text; ph text; bh text; q sol_creation_guard.requests%ROWTYPE; existing sol_creation_guard.requests%ROWTYPE; j sol_action.jobs%ROWTYPE; rel sol_action_bridge.releases%ROWTYPE; admitted sol_creation_guard.admissions%ROWTYPE; r jsonb; hit jsonb; today timestamptz; k text; raw_cap_hash bytea;
BEGIN
 PERFORM sol_action.keys(p,ARRAY['core_input','release_hash','manifest_hash','source_commit','self_hash','bridge_token'],ARRAY['core_input','release_hash','manifest_hash','source_commit','self_hash','bridge_token']); d:=p->'core_input'; PERFORM sol_creation_guard.validate_create(d);
 jid:=(d->>'job_id')::uuid; req:=(d->>'request_id')::uuid; cap:=d->>'capability'; raw_cap_hash:=extensions.digest(convert_to(cap,'UTF8'),'sha256');
 FOREACH k IN ARRAY ARRAY['release_hash','manifest_hash','self_hash','bridge_token'] LOOP IF sol_action.text_field(p,k,64,64) !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID'; END IF; END LOOP;
 IF sol_action.text_field(p,'source_commit',40,40) !~ '^[0-9a-f]{40}$' THEN RAISE EXCEPTION 'INVALID'; END IF;
 SELECT * INTO rel FROM sol_action_bridge.releases x WHERE x.release_hash=p->>'release_hash'; SELECT * INTO admitted FROM sol_creation_guard.admissions x WHERE x.release_hash=p->>'release_hash';
 IF rel.release_hash IS NULL OR admitted.release_hash IS NULL OR NOT sol_action_bridge.token_matches(p->>'bridge_token',rel.token_sha256) OR rel.manifest_hash<>p->>'manifest_hash' OR rel.source_commit<>p->>'source_commit' OR rel.source_files->>'api/job.py'<>p->>'self_hash' OR rel.core_runtime_hash<>sol_action.runtime_hash() OR rel.bridge_runtime_hash<>sol_action_bridge.runtime_hash() OR admitted.guard_runtime_hash<>sol_creation_guard.runtime_hash() OR admitted.core_runtime_hash<>rel.core_runtime_hash OR admitted.bridge_runtime_hash<>rel.bridge_runtime_hash OR admitted.release_metadata_hash<>sol_creation_guard.sha(sol_creation_guard.release_metadata(rel)::text) OR sol_action.runtime_hash()<>'c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0' THEN RAISE EXCEPTION 'INVALID'; END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('sol_action:job:'||jid::text,0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol_action_bridge:request:'||req::text,0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol_creation_guard:journal',0));
 SELECT * INTO j FROM sol_action.jobs x WHERE x.job_id=jid; IF FOUND THEN PERFORM sol_action.authorize(j,cap); END IF;
 ph:=sol_creation_guard.sha(jsonb_build_object('action','create','input',d-'capability'-'parent_capability')::text); bh:=sol_creation_guard.sha(encode(raw_cap_hash,'hex')||':'||ph||':'||jid::text||':'||req::text||':create');
 SELECT * INTO q FROM sol_creation_guard.requests x WHERE x.request_id=req;
 IF FOUND THEN
 IF q.job_id<>jid OR NOT sol_creation_guard.cap_matches(cap,q.capability_hash) OR q.payload_hash<>ph OR q.request_binding_hash<>bh THEN RAISE EXCEPTION 'INVALID'; END IF;
 hit:=sol_creation_guard.lookup(jid,req,cap);
 IF hit->'found'='true'::jsonb THEN RETURN (hit->'receipt')||jsonb_build_object('deduplicated',true); END IF;
 RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','action','create','job_id',jid,'request_id',req,'pending',true,'automatic_retry',false,'current_reuse_authorized',false);
 END IF;
 SELECT * INTO existing FROM sol_creation_guard.requests x WHERE x.job_id=jid;
 IF FOUND THEN
 IF NOT sol_creation_guard.cap_matches(cap,existing.capability_hash) THEN RAISE EXCEPTION 'INVALID'; END IF;
 RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','action','create','job_id',jid,'request_id',req,'original_request_id',existing.request_id,'error','PRIOR_CREATION_INTENT_REQUIRES_ORIGINAL_RECEIPT','pending',true,'automatic_retry',false,'current_reuse_authorized',false);
 END IF;
 IF EXISTS(SELECT 1 FROM sol_action.intents x WHERE x.request_id=req) OR EXISTS(SELECT 1 FROM sol_action.outcomes x WHERE x.request_id=req) OR EXISTS(SELECT 1 FROM sol_action_bridge.refusals x WHERE x.request_id=req) OR EXISTS(SELECT 1 FROM sol_action_bridge.recovery_outcomes x WHERE x.request_id=req) THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF sol_creation_guard.audit()->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'INVALID'; END IF;
 today:=date_trunc('day',clock_timestamp() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC';
 IF (SELECT count(*) FROM sol_creation_guard.requests x WHERE x.reserved_at>=today)>=128 OR (SELECT count(*) FROM sol_creation_guard.requests x WHERE x.reserved_at>=today AND x.capability_hash=raw_cap_hash)>=32 THEN RETURN jsonb_build_object('ok',false,'status','REJECTED','action','create','job_id',jid,'request_id',req,'error','CREATION_ADMISSION_LIMIT','admission_recorded',false,'automatic_retry',false,'current_reuse_authorized',false); END IF;
 INSERT INTO sol_creation_guard.requests(request_id,job_id,payload_hash,capability_hash,request_binding_hash,release_hash,guard_runtime_hash,core_runtime_hash,bridge_runtime_hash) VALUES(req,jid,ph,raw_cap_hash,bh,rel.release_hash,sol_creation_guard.runtime_hash(),sol_action.runtime_hash(),sol_action_bridge.runtime_hash());
 PERFORM sol_creation_guard.append_event(jid,req,'reservation',jsonb_build_object('payload_hash',ph,'request_binding_hash',bh,'release_hash',rel.release_hash,'actor_scope','SERVER_RELEASE_TOKEN_AND_REQUEST_CAPABILITY_NOT_JOB_IDENTITY'));
 -- No network is called here. Only the pinned core may justify the narrow rollback receipt.
 r:=sol_action.dispatch('create',d);
 IF r->'ok'='true'::jsonb AND r->>'job_id'=jid::text AND r->>'request_id'=req::text AND r->>'action'='create' AND EXISTS(SELECT 1 FROM sol_action.outcomes x JOIN sol_action.intents i USING(request_id) WHERE x.request_id=req AND x.job_id=jid AND i.action='create' AND i.payload_hash=ph AND x.receipt=r) THEN
 PERFORM sol_creation_guard.append_event(jid,req,'core_outcome',jsonb_build_object('receipt_sha256',sol_creation_guard.sha(r::text))); RETURN r;
 ELSIF sol_creation_guard.controlled_create_refusal(r,jid,req) AND NOT EXISTS(SELECT 1 FROM sol_action.intents x WHERE x.request_id=req) AND NOT EXISTS(SELECT 1 FROM sol_action.outcomes x WHERE x.request_id=req) THEN
 r:=r||jsonb_build_object('receipt_kind','CONTROLLED_CREATION_REFUSAL','terminal',true,'durable_refusal',true,'payload_hash',ph,'refused_at',sol_action.utc(clock_timestamp()),'core_effect_scope','THIS_RPC_SQL_TRANSACTION_ONLY','effect_scope','CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY','receipt_recording_effect','APPEND_ONLY_CREATION_GUARD_RECEIPT_RECORDED','business_effect','NONE_CORE_ACTION_ROLLED_BACK','capability_activated_by_this_call',false,'guard_runtime_hash',sol_creation_guard.runtime_hash(),'core_runtime_hash',sol_action.runtime_hash(),'bridge_runtime_hash',sol_action_bridge.runtime_hash(),'release_hash',rel.release_hash,'actor_scope','SERVER_RELEASE_TOKEN_AND_REQUEST_CAPABILITY_NOT_JOB_IDENTITY','worker_reexecuted',false);
 INSERT INTO sol_creation_guard.refusals(request_id,job_id,receipt) VALUES(req,jid,r); PERFORM sol_creation_guard.append_event(jid,req,'refusal',jsonb_build_object('receipt_sha256',sol_creation_guard.sha(r::text))); RETURN r;
 END IF;
 PERFORM sol_creation_guard.append_event(jid,req,'unknown',jsonb_build_object('reason','UNCLASSIFIED_CORE_RESPONSE','automatic_retry',false));
 RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','action','create','job_id',jid,'request_id',req,'pending',true,'automatic_retry',false,'current_reuse_authorized',false);
END $$;
CREATE FUNCTION sol_creation_guard.api(p_action text,p_input jsonb DEFAULT '{}') RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE jid uuid; target uuid; cap text;
BEGIN
 IF jsonb_typeof(p_input) IS DISTINCT FROM 'object' OR octet_length(p_input::text)>200000 THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF p_action='health' THEN PERFORM sol_action.keys(p_input,ARRAY[]::text[],ARRAY[]::text[]); RETURN jsonb_build_object('ok',true,'module','SOL-Creation-Guard','version','0.1.0','runtime_hash',sol_creation_guard.runtime_hash(),'no_existing_module_replaced',true,'durable_refused_creation_requires_new_guarded_path',true,'legacy_unrecorded_refusal','UNKNOWN','daily_request_limit',128,'daily_capability_limit',32,'current_reuse_authorized',false); END IF;
 IF p_action='create_guarded' THEN RETURN sol_creation_guard.create_guarded(p_input); END IF;
 IF p_action='lookup_receipt' THEN
 PERFORM sol_action.keys(p_input,ARRAY['job_id','capability','target_request_id'],ARRAY['job_id','capability','target_request_id']); jid:=sol_action.text_field(p_input,'job_id',36,36)::uuid; target:=sol_action.text_field(p_input,'target_request_id',36,36)::uuid; cap:=sol_action.text_field(p_input,'capability',64,64);
 RETURN sol_creation_guard.lookup(jid,target,cap);
 END IF;
 RAISE EXCEPTION 'INVALID';
EXCEPTION WHEN OTHERS THEN RETURN jsonb_build_object('ok',false,'status','REJECTED','error','NOT_AUTHORIZED_OR_INVALID_REFERENCE','current_reuse_authorized',false,'automatic_retry',false);
END $$;
CREATE FUNCTION public.sol_action_creation_api(p_action text,p_input jsonb DEFAULT '{}') RETURNS jsonb LANGUAGE sql SECURITY INVOKER SET search_path='' AS $$ SELECT sol_creation_guard.api(p_action,p_input) $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA sol_creation_guard FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON FUNCTION public.sol_action_creation_api(text,jsonb) FROM PUBLIC,anon,authenticated,service_role;
GRANT USAGE ON SCHEMA sol_creation_guard TO anon,authenticated;
GRANT EXECUTE ON FUNCTION sol_creation_guard.api(text,jsonb) TO anon,authenticated;
GRANT EXECUTE ON FUNCTION public.sol_action_creation_api(text,jsonb) TO anon,authenticated;
COMMENT ON SCHEMA sol_creation_guard IS 'Creation refusal recovery 0.1.0. Append-only scoped SQL receipts without a dummy job, release-token gated; legacy direct creation remains outside this guard. No general success or WORM claim.';
COMMIT;
