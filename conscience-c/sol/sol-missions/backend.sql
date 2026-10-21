-- SOL-Missions 0.1.0. Additive bridge: exact scoped job evidence, never general mandate completion.
BEGIN;
CREATE SCHEMA sol_missions;
REVOKE ALL ON SCHEMA sol_missions FROM PUBLIC;
CREATE TABLE sol_missions.requests(request_id uuid PRIMARY KEY,job_id uuid NOT NULL,mission_id uuid,action text NOT NULL CHECK(action IN ('register','verify')),actor text NOT NULL,input jsonb NOT NULL,input_hash text NOT NULL,reserved_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TABLE sol_missions.missions(id uuid PRIMARY KEY,request_id uuid UNIQUE NOT NULL REFERENCES sol_missions.requests(request_id),workspace text NOT NULL,bundle_id uuid NOT NULL,job_id uuid NOT NULL,allow_job_owner_view boolean NOT NULL,definition jsonb NOT NULL,definition_hash text NOT NULL,source_csv text NOT NULL,registered_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE INDEX ON sol_missions.missions(job_id,registered_at);
CREATE TABLE sol_missions.reports(id uuid PRIMARY KEY,mission_id uuid NOT NULL REFERENCES sol_missions.missions(id),request_id uuid UNIQUE NOT NULL REFERENCES sol_missions.requests(request_id),job_id uuid NOT NULL,report jsonb NOT NULL,report_hash text NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TABLE sol_missions.outcomes(request_id uuid PRIMARY KEY REFERENCES sol_missions.requests(request_id),job_id uuid NOT NULL,mission_id uuid,response jsonb NOT NULL,response_hash text NOT NULL,completed_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TABLE sol_missions.events(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),sequence bigint GENERATED ALWAYS AS IDENTITY UNIQUE,job_id uuid NOT NULL,kind text NOT NULL CHECK(kind IN ('reservation','mission','report','result','error')),actor text NOT NULL,at timestamptz NOT NULL,data jsonb NOT NULL,previous_hash text NOT NULL,event_hash text NOT NULL);
CREATE FUNCTION sol_missions.hash(p jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT SET search_path='' AS $$ SELECT encode(extensions.digest(convert_to(p::text,'UTF8'),'sha256'),'hex') $$;
CREATE FUNCTION sol_missions.keys(p jsonb,a text[],r text[]) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT CASE WHEN jsonb_typeof(p) IS DISTINCT FROM 'object' THEN false ELSE NOT EXISTS(SELECT 1 FROM jsonb_each(p) e WHERE NOT e.key=ANY(a) OR e.value='null'::jsonb) AND p ?& r END $$;
CREATE FUNCTION sol_missions.uuid_ok(p jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT coalesce(jsonb_typeof(p)='string' AND (p#>>'{}') ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',false) $$;
CREATE FUNCTION sol_missions.text_ok(p jsonb,n integer) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT coalesce(jsonb_typeof(p)='string' AND length(p#>>'{}') BETWEEN 1 AND n AND length(btrim(p#>>'{}'))>0,false) $$;
CREATE FUNCTION sol_missions.no_change() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$ BEGIN RAISE EXCEPTION 'SOL_MISSIONS_APPEND_ONLY' USING ERRCODE='42501'; END $$;
DO $$ DECLARE t text; BEGIN FOREACH t IN ARRAY ARRAY['requests','missions','reports','outcomes','events'] LOOP
 EXECUTE format('ALTER TABLE sol_missions.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON sol_missions.%I FOR EACH ROW EXECUTE FUNCTION sol_missions.no_change()',t);
 EXECUTE format('CREATE TRIGGER no_truncate BEFORE TRUNCATE ON sol_missions.%I FOR EACH STATEMENT EXECUTE FUNCTION sol_missions.no_change()',t);
END LOOP; END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA sol_missions FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA sol_missions FROM PUBLIC,anon,authenticated,service_role;
CREATE FUNCTION sol_missions.runtime_hash() RETURNS text LANGUAGE sql STABLE SET search_path='' AS $$
 SELECT sol_missions.hash(jsonb_agg(jsonb_build_object('signature',n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')','definition',pg_get_functiondef(p.oid)) ORDER BY n.nspname,p.proname,pg_get_function_identity_arguments(p.oid))) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE p.prokind='f' AND (n.nspname='sol_missions' OR (n.nspname='public' AND p.proname='sol_missions_api')) $$;
CREATE FUNCTION sol_missions.dependencies() RETURNS jsonb LANGUAGE sql STABLE SET search_path='' AS $$
 SELECT jsonb_build_object('missions_runtime_hash',sol_missions.runtime_hash(),'action_runtime_hash',sol_action.runtime_hash(),'bridge_runtime_hash',sol_action_bridge.runtime_hash(),'coordination_runtime_hash',sol_coordination.runtime_hash(),'atelier_runtime_hash',sol_atelier.runtime_hash(),
 'expected_action_runtime_hash','c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0','expected_bridge_runtime_hash','38c9307df6c049a24ee38ba80cd1973b0ae400f3a920f91a3d4e63fd9be5b755','expected_coordination_runtime_hash','856afa9e4adab59b513691f2080348a55f3786ee07ccdadc5f4500ed8882f996','expected_atelier_runtime_hash','ac94dcdaf0cafaf29b63a337ce8b98b6459de19a2fe682745af510eca7a8f108',
 'dependencies_match',sol_action.runtime_hash()='c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0' AND sol_action_bridge.runtime_hash()='38c9307df6c049a24ee38ba80cd1973b0ae400f3a920f91a3d4e63fd9be5b755' AND sol_coordination.runtime_hash()='856afa9e4adab59b513691f2080348a55f3786ee07ccdadc5f4500ed8882f996' AND sol_atelier.runtime_hash()='ac94dcdaf0cafaf29b63a337ce8b98b6459de19a2fe682745af510eca7a8f108') $$;
CREATE FUNCTION sol_missions.append_event(j uuid,k text,a text,d jsonb) RETURNS void LANGUAGE plpgsql SET search_path='' AS $$
DECLARE ident uuid:=gen_random_uuid(); stamp timestamptz:=clock_timestamp(); prev text;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended('sol-missions:global-journal',0)); SELECT event_hash INTO prev FROM sol_missions.events ORDER BY sequence DESC LIMIT 1; prev:=coalesce(prev,repeat('0',64));
 INSERT INTO sol_missions.events(id,job_id,kind,actor,at,data,previous_hash,event_hash) VALUES(ident,j,k,a,stamp,d,prev,sol_missions.hash(jsonb_build_object('id',ident,'job_id',j,'kind',k,'actor',a,'at',to_char(stamp AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'data',d,'previous_hash',prev)));
END $$;
CREATE FUNCTION sol_missions.audit_chain() RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path='' AS $$
DECLARE entry record; prev text:=repeat('0',64); bad bigint:=0; links bigint:=0; n bigint:=0; h text;
BEGIN
 FOR entry IN SELECT * FROM sol_missions.events ORDER BY sequence LOOP
 h:=sol_missions.hash(jsonb_build_object('id',entry.id,'job_id',entry.job_id,'kind',entry.kind,'actor',entry.actor,'at',to_char(entry.at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'data',entry.data,'previous_hash',entry.previous_hash));
 IF entry.previous_hash IS DISTINCT FROM prev OR entry.event_hash IS DISTINCT FROM h THEN bad:=bad+1; END IF; prev:=entry.event_hash; n:=n+1; END LOOP;
 SELECT count(*) INTO links FROM sol_missions.requests q WHERE q.input ? 'capability' OR coalesce(q.input->'runtime_identity','{}'::jsonb) ? 'bridge_token' OR sol_missions.hash(jsonb_build_object('action',q.action,'input',q.input,'actor',q.actor)) IS DISTINCT FROM q.input_hash OR (SELECT count(*) FROM sol_missions.events e WHERE e.job_id=q.job_id AND e.kind='reservation' AND e.data->>'request_id'=q.request_id::text AND e.data->>'input_hash'=q.input_hash AND e.actor=q.actor)<>1;
 SELECT links+count(*) INTO links FROM sol_missions.missions m WHERE sol_missions.hash(m.definition) IS DISTINCT FROM m.definition_hash OR sol_action.sha(m.source_csv) IS DISTINCT FROM m.definition->'job'->>'source_sha256' OR m.definition->>'job_id' IS DISTINCT FROM m.job_id::text OR m.definition->>'bundle_id' IS DISTINCT FROM m.bundle_id::text OR m.definition->>'workspace' IS DISTINCT FROM m.workspace OR m.definition->'allow_job_owner_view' IS DISTINCT FROM to_jsonb(m.allow_job_owner_view) OR NOT EXISTS(SELECT 1 FROM sol_missions.requests q WHERE q.request_id=m.request_id AND q.action='register' AND q.job_id=m.job_id AND lower(q.input->>'bundle_id')=m.bundle_id::text AND q.input->>'workspace'=m.workspace) OR (SELECT count(*) FROM sol_missions.events e WHERE e.kind='mission' AND e.job_id=m.job_id AND e.data->>'mission_id'=m.id::text AND e.data->>'definition_hash'=m.definition_hash AND e.data->>'request_id'=m.request_id::text)<>1 OR NOT EXISTS(SELECT 1 FROM sol_missions.outcomes o WHERE o.request_id=m.request_id AND o.mission_id=m.id AND o.response->'ok'='true'::jsonb);
 SELECT links+count(*) INTO links FROM sol_missions.reports r WHERE sol_missions.hash(r.report) IS DISTINCT FROM r.report_hash OR NOT EXISTS(SELECT 1 FROM sol_missions.missions m WHERE m.id=r.mission_id AND m.job_id=r.job_id AND r.report->>'definition_hash'=m.definition_hash AND r.report->'requirements'=m.definition->'requirements_matrix') OR NOT EXISTS(SELECT 1 FROM sol_missions.requests q WHERE q.request_id=r.request_id AND q.action='verify' AND q.mission_id=r.mission_id AND q.job_id=r.job_id) OR (SELECT count(*) FROM sol_missions.events e WHERE e.kind='report' AND e.job_id=r.job_id AND e.data->>'report_id'=r.id::text AND e.data->>'report_hash'=r.report_hash AND e.data->>'request_id'=r.request_id::text)<>1 OR NOT EXISTS(SELECT 1 FROM sol_missions.outcomes o WHERE o.request_id=r.request_id AND o.mission_id=r.mission_id AND o.response->>'report_id'=r.id::text AND o.response->'report'=r.report);
 SELECT links+count(*) INTO links FROM sol_missions.outcomes o WHERE sol_missions.hash(o.response) IS DISTINCT FROM o.response_hash OR (SELECT count(*) FROM sol_missions.events e WHERE e.kind IN ('result','error') AND e.job_id=o.job_id AND e.data->>'request_id'=o.request_id::text AND e.data->>'response_hash'=o.response_hash)<>1;
 SELECT links+count(*) INTO links FROM sol_missions.events e WHERE
 (e.kind='reservation' AND NOT EXISTS(SELECT 1 FROM sol_missions.requests q WHERE q.request_id::text=e.data->>'request_id' AND q.job_id=e.job_id AND q.input_hash=e.data->>'input_hash' AND q.actor=e.actor)) OR
 (e.kind='mission' AND NOT EXISTS(SELECT 1 FROM sol_missions.missions m WHERE m.id::text=e.data->>'mission_id' AND m.job_id=e.job_id AND m.definition_hash=e.data->>'definition_hash' AND m.request_id::text=e.data->>'request_id')) OR
 (e.kind='report' AND NOT EXISTS(SELECT 1 FROM sol_missions.reports r WHERE r.id::text=e.data->>'report_id' AND r.job_id=e.job_id AND r.report_hash=e.data->>'report_hash' AND r.request_id::text=e.data->>'request_id')) OR
 (e.kind IN ('result','error') AND NOT EXISTS(SELECT 1 FROM sol_missions.outcomes o JOIN sol_missions.requests q USING(request_id) WHERE o.request_id::text=e.data->>'request_id' AND o.job_id=e.job_id AND o.response_hash=e.data->>'response_hash' AND q.actor=e.actor));
 RETURN jsonb_build_object('valid',bad=0 AND links=0,'events',n,'head',prev,'invalid_events',bad,'incoherent_records',links,'scope','GLOBAL_CHAIN_MISSION_REPORT_REQUEST_OUTCOME_LINKS','owner_tamper_resistance','NOT_WORM');
END $$;
CREATE FUNCTION sol_missions.job_definition(j sol_action.jobs) RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT jsonb_build_object('job_id',j.job_id,'mandate',j.mandate,'requirements',j.requirements,'source_sha256',j.source_sha256,'source_origin',j.source_origin,'parent_job_id',j.parent_job_id,'runtime_hash',j.runtime_hash,'definition_hash',j.definition_hash) $$;
CREATE FUNCTION sol_missions.release_definition(r sol_action_bridge.releases) RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT jsonb_build_object('release_hash',r.release_hash,'manifest_hash',r.manifest_hash,'source_commit',r.source_commit,'source_files',r.source_files,'deployment_id',r.deployment_id,'deployment_url',r.deployment_url,'core_runtime_hash',r.core_runtime_hash,'bridge_runtime_hash',r.bridge_runtime_hash,'admitted_at',sol_action.utc(r.admitted_at),'admitted_by',r.admitted_by) $$;
CREATE FUNCTION sol_missions.release_binding(j uuid) RETURNS jsonb LANGUAGE sql STABLE SET search_path='' AS $$
 SELECT jsonb_build_object('job_id',b.job_id,'production_request_id',b.production_request_id,'release_hash',b.release_hash,'worker_self_hash',b.worker_self_hash,'core_runtime_hash',b.core_runtime_hash,'bridge_runtime_hash',b.bridge_runtime_hash,'bound_at',sol_action.utc(b.bound_at),'release',sol_missions.release_definition(r)) FROM sol_action_bridge.bindings b JOIN sol_action_bridge.releases r USING(release_hash) WHERE b.job_id=j $$;
CREATE FUNCTION sol_missions.bundle_snapshot(w text,bid uuid) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE b sol_coordination.bundles%ROWTYPE; t sol_atelier.tasks%ROWTYPE; child sol_atelier.tasks%ROWTYPE; anchors uuid[]; terminals uuid[]:='{}'; cur uuid; seen uuid[]; prior_req jsonb; p jsonb; chain jsonb; chains jsonb:='[]'; matrix jsonb:='[]'; x jsonb; q jsonb; n integer:=0; i integer; k integer; amount integer; role text;
BEGIN
 IF sol_coordination.audit_chain()->'valid' IS DISTINCT FROM 'true'::jsonb OR sol_atelier.audit_chain()->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'SOURCE_JOURNAL_INVALID'; END IF;
 SELECT * INTO b FROM sol_coordination.bundles WHERE id=bid AND workspace=w; IF NOT FOUND THEN RAISE EXCEPTION 'BUNDLE_NOT_FOUND'; END IF;
 IF sol_coordination.hash(b.definition) IS DISTINCT FROM b.definition_hash THEN RAISE EXCEPTION 'BUNDLE_DEFINITION_HASH_MISMATCH'; END IF;
 anchors:=ARRAY[b.root_anchor_id]; FOR x IN SELECT value FROM jsonb_array_elements(b.definition->'companion_anchor_ids') LOOP anchors:=array_append(anchors,(x#>>'{}')::uuid); END LOOP;
 IF cardinality(anchors)>17 OR (SELECT count(DISTINCT u) FROM unnest(anchors) u)<>cardinality(anchors) THEN RAISE EXCEPTION 'INVALID_BUNDLE_ANCHORS'; END IF;
 FOREACH cur IN ARRAY anchors LOOP
 seen:='{}'; chain:='[]'; prior_req:=NULL; role:=CASE WHEN n=0 THEN 'ROOT' ELSE 'COMPANION' END;
 FOR i IN 1..64 LOOP
 IF cur=ANY(seen) THEN RAISE EXCEPTION 'SUCCESSION_CYCLE'; END IF; seen:=array_append(seen,cur);
 SELECT * INTO t FROM sol_atelier.tasks WHERE id=cur; IF NOT FOUND OR t.workspace IS DISTINCT FROM w OR sol_atelier.hash(t.definition) IS DISTINCT FROM t.definition_hash THEN RAISE EXCEPTION 'TASK_DEFINITION_MISMATCH'; END IF;
 IF jsonb_typeof(t.definition->'requirements') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'INVALID_TASK_REQUIREMENTS'; END IF;
 IF jsonb_array_length(t.definition->'requirements') NOT BETWEEN 1 AND 16 THEN RAISE EXCEPTION 'INVALID_TASK_REQUIREMENTS'; END IF;
 IF prior_req IS NOT NULL THEN
 IF jsonb_array_length(t.definition->'requirements')<jsonb_array_length(prior_req) THEN RAISE EXCEPTION 'REQUIREMENTS_PREFIX_LOST'; END IF;
 FOR k IN 0..jsonb_array_length(prior_req)-1 LOOP IF t.definition->'requirements'->k IS DISTINCT FROM prior_req->k THEN RAISE EXCEPTION 'REQUIREMENTS_PREFIX_CHANGED'; END IF; END LOOP; END IF;
 p:=sol_atelier.progress(w,cur); IF p IS NULL OR p->>'phase' NOT IN ('OPEN','IN_PROGRESS','BLOCKED','COMPLETED_BOUNDED','CANCELLED','SUPERSEDED') THEN RAISE EXCEPTION 'TASK_PROGRESS_MISSING'; END IF;
 SELECT count(*) INTO amount FROM sol_atelier.tasks WHERE lower(definition->>'supersedes_task_id')=cur::text;
 IF amount>1 THEN RAISE EXCEPTION 'SUCCESSION_FORK'; END IF;
 chain:=chain||jsonb_build_array(jsonb_build_object('task_id',t.id,'definition',t.definition,'definition_hash',t.definition_hash));
 IF amount=0 THEN
 IF p->>'phase' IN ('CANCELLED','SUPERSEDED') OR p ? 'successor_task_id' THEN RAISE EXCEPTION 'TERMINAL_NOT_ACTIVE'; END IF;
 IF t.definition->'bindings' IS DISTINCT FROM sol_atelier.bindings() THEN RAISE EXCEPTION 'TERMINAL_RUNTIME_CHANGED'; END IF;
 IF cur=ANY(terminals) THEN RAISE EXCEPTION 'DUPLICATE_TERMINAL'; END IF; terminals:=array_append(terminals,cur);
 chains:=chains||jsonb_build_array(jsonb_build_object('role',role,'anchor_task_id',anchors[n+1],'terminal_task_id',cur,'chain',chain,'definition',t.definition,'definition_hash',t.definition_hash));
 FOR q IN SELECT value FROM jsonb_array_elements(t.definition->'requirements') LOOP matrix:=matrix||jsonb_build_array(jsonb_build_object('compound_id',cur::text||':'||(q->>'id'),'task_id',cur,'anchor_task_id',anchors[n+1],'role',role,'requirement',q,'mapping_basis','OPERATOR_DECLARED','validation','UNKNOWN')); END LOOP;
 EXIT;
 END IF;
 SELECT * INTO child FROM sol_atelier.tasks WHERE lower(definition->>'supersedes_task_id')=cur::text;
 IF child.workspace IS DISTINCT FROM w OR p->>'phase' IS DISTINCT FROM 'SUPERSEDED' OR p->>'successor_task_id' IS DISTINCT FROM child.id::text THEN RAISE EXCEPTION 'SUCCESSOR_POINTER_MISMATCH'; END IF;
 prior_req:=t.definition->'requirements'; cur:=child.id;
 IF i=64 THEN RAISE EXCEPTION 'SUCCESSION_DEPTH_LIMIT'; END IF;
 END LOOP; n:=n+1; END LOOP;
 IF EXISTS(SELECT 1 FROM sol_atelier.requests r WHERE r.workspace=w AND NOT EXISTS(SELECT 1 FROM sol_atelier.outcomes o WHERE o.workspace=r.workspace AND o.request_id=r.request_id)) THEN RAISE EXCEPTION 'ATELIER_OUTCOME_UNKNOWN'; END IF;
 RETURN jsonb_build_object('bundle_id',bid,'workspace',w,'definition_hash',b.definition_hash,'historical_definition',b.definition,'terminals',chains,'requirements_matrix',matrix,'requirement_count',jsonb_array_length(matrix));
END $$;
CREATE FUNCTION sol_missions.clean(p jsonb,cap text DEFAULT NULL,tok text DEFAULT NULL,historical boolean DEFAULT false) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SET search_path='' AS $$
DECLARE k text; v jsonb; outp jsonb;
BEGIN
 IF jsonb_typeof(p)='object' THEN outp:='{}'; FOR k,v IN SELECT key,value FROM jsonb_each(p) LOOP
 IF k IN ('capability','parent_capability','capability_hash','bridge_token','token','token_sha256','source_csv') THEN CONTINUE; END IF;
 IF historical AND k IN ('current_reuse_authorized','begin_granted','binding_granted') THEN v:='false'; ELSIF historical AND k='needs_current_revalidation' THEN v:='true'; ELSE v:=sol_missions.clean(v,cap,tok,historical); END IF; outp:=outp||jsonb_build_object(k,v); END LOOP; RETURN outp;
 ELSIF jsonb_typeof(p)='array' THEN SELECT coalesce(jsonb_agg(sol_missions.clean(value,cap,tok,historical) ORDER BY ordinality),'[]') INTO outp FROM jsonb_array_elements(p) WITH ORDINALITY; RETURN outp;
 ELSIF jsonb_typeof(p)='string' THEN k:=p#>>'{}'; IF cap IS NOT NULL AND length(cap)=64 THEN k:=replace(k,cap,'[REDACTED]'); END IF; IF tok IS NOT NULL AND length(tok)=64 THEN k:=replace(k,tok,'[REDACTED]'); END IF; RETURN to_jsonb(k);
 ELSE RETURN p; END IF;
END $$;
CREATE FUNCTION sol_missions.check_item(n text,v text,r text,e jsonb DEFAULT '{}') RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT jsonb_build_object('name',n,'verdict',v,'reason',r,'evidence',e) $$;
CREATE FUNCTION sol_missions.observe(m sol_missions.missions,j sol_action.jobs,ri jsonb) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE checks jsonb:='[]'; deps jsonb:=sol_missions.dependencies(); snap jsonb; binding jsonb; rr sol_action.results%ROWTYPE; b sol_action_bridge.bindings%ROWTYPE; rel sol_action_bridge.releases%ROWTYPE; prod sol_action.intents%ROWTYPE; expected jsonb; aj jsonb; verdict text; reason text; started timestamptz:=clock_timestamp(); finished timestamptz; expiry timestamptz; local_at timestamptz; malformed boolean:=false;
BEGIN
 checks:=checks||jsonb_build_array(sol_missions.check_item('runtime_dependencies',CASE WHEN deps=m.definition->'dependencies' AND deps->'dependencies_match'='true'::jsonb THEN 'PASS' ELSE 'UNKNOWN' END,CASE WHEN deps=m.definition->'dependencies' AND deps->'dependencies_match'='true'::jsonb THEN 'PINNED_SQL_RUNTIMES_MATCH' ELSE 'RUNTIME_CHANGED' END,deps));
 checks:=checks||jsonb_build_array(sol_missions.check_item('mission_integrity',CASE WHEN sol_missions.hash(m.definition)=m.definition_hash AND sol_missions.audit_chain()->'valid'='true'::jsonb THEN 'PASS' ELSE 'FAIL' END,'REGISTRY_AND_DEFINITION_RECALCULATED',jsonb_build_object('definition_hash',m.definition_hash)));
 checks:=checks||jsonb_build_array(sol_missions.check_item('job_and_source_identity',CASE WHEN sol_missions.job_definition(j)=m.definition->'job' AND j.source_csv=m.source_csv AND sol_action.sha(j.source_csv)=j.source_sha256 THEN 'PASS' ELSE 'FAIL' END,'EXACT_JOB_DEFINITION_AND_FROZEN_SOURCE_COMPARISON',jsonb_build_object('job_id',j.job_id,'source_sha256',j.source_sha256,'computed_source_sha256',sol_action.sha(j.source_csv),'job_definition_hash',j.definition_hash)));
 BEGIN snap:=sol_missions.bundle_snapshot(m.workspace,m.bundle_id);
 checks:=checks||jsonb_build_array(sol_missions.check_item('bundle_current_resolution',CASE WHEN snap=m.definition->'bundle' THEN 'PASS' ELSE 'FAIL' END,CASE WHEN snap=m.definition->'bundle' THEN 'EXACT_MANDATES_REQUIREMENTS_TERMINALS_MATCH' ELSE 'BUNDLE_OR_TERMINAL_DRIFT' END,jsonb_build_object('current_snapshot_hash',sol_missions.hash(snap),'registered_snapshot_hash',sol_missions.hash(m.definition->'bundle'),'requirement_count',snap->'requirement_count')));
 EXCEPTION WHEN OTHERS THEN checks:=checks||jsonb_build_array(sol_missions.check_item('bundle_current_resolution',CASE WHEN SQLERRM IN ('TERMINAL_NOT_ACTIVE','TASK_DEFINITION_MISMATCH','REQUIREMENTS_PREFIX_CHANGED','REQUIREMENTS_PREFIX_LOST','SUCCESSOR_POINTER_MISMATCH') THEN 'FAIL' ELSE 'UNKNOWN' END,'BUNDLE_RESOLUTION_NOT_AVAILABLE',jsonb_build_object('sqlstate',SQLSTATE))); END;
 aj:=sol_action.audit_job(j.job_id); checks:=checks||jsonb_build_array(sol_missions.check_item('job_journal',CASE WHEN aj->>'status'='PASS' THEN 'PASS' ELSE 'FAIL' END,'JOB_CHAIN_SOURCE_DEFINITION_AND_RECEIPT_LINKS',aj));
 SELECT * INTO rr FROM sol_action.results WHERE job_id=j.job_id;
 SELECT * INTO b FROM sol_action_bridge.bindings WHERE job_id=j.job_id;
 SELECT * INTO rel FROM sol_action_bridge.releases WHERE release_hash=m.definition->'expected_release'->>'release_hash';
 SELECT * INTO prod FROM sol_action.intents WHERE job_id=j.job_id AND action='begin' ORDER BY created_at LIMIT 1;
 checks:=checks||jsonb_build_array(sol_missions.check_item('pending_intents',CASE WHEN prod.request_id IS NULL OR rr.job_id IS NULL OR EXISTS(SELECT 1 FROM sol_action.intents i WHERE i.job_id=j.job_id AND NOT EXISTS(SELECT 1 FROM sol_action.outcomes o WHERE o.request_id=i.request_id AND o.job_id=i.job_id)) THEN 'UNKNOWN' WHEN (SELECT count(*) FROM sol_action.intents WHERE job_id=j.job_id AND action='begin')<>1 OR rr.production_request_id<>prod.request_id THEN 'FAIL' ELSE 'PASS' END,'NO_REPLAY_PENDING_PRODUCTION_OR_UNKNOWN_ISSUE_BLOCKS_CURRENT_SUCCESS',jsonb_build_object('production_request_id',prod.request_id,'result_found',rr.job_id IS NOT NULL,'unresolved_intents',(SELECT count(*) FROM sol_action.intents i WHERE i.job_id=j.job_id AND NOT EXISTS(SELECT 1 FROM sol_action.outcomes o WHERE o.request_id=i.request_id AND o.job_id=i.job_id)))));
 binding:=sol_missions.release_binding(j.job_id);
 IF b.job_id IS NULL OR binding IS NULL THEN verdict:='UNKNOWN'; reason:='BINDING_OR_ADMISSION_MISSING';
 ELSIF rr.job_id IS NULL OR prod.request_id IS NULL THEN verdict:='UNKNOWN'; reason:='PRODUCTION_NOT_COMPLETE_FOR_BINDING_CHECK';
 ELSE
 verdict:=CASE WHEN (m.definition->'release_binding'='null'::jsonb OR binding IS NOT DISTINCT FROM m.definition->'release_binding') AND binding->'release'=m.definition->'expected_release' AND b.release_hash=rel.release_hash AND b.production_request_id=prod.request_id AND b.production_request_id=rr.production_request_id AND b.core_runtime_hash=j.runtime_hash AND b.core_runtime_hash=deps->>'action_runtime_hash' AND b.bridge_runtime_hash=deps->>'bridge_runtime_hash' AND rel.core_runtime_hash=b.core_runtime_hash AND rel.bridge_runtime_hash=b.bridge_runtime_hash AND b.worker_self_hash=rel.source_files->>'api/job.py' AND rel.release_hash=sol_action.sha(rel.manifest_hash||':'||rel.source_commit) AND rel.admitted_at<=prod.created_at AND prod.created_at<=b.bound_at AND b.bound_at<=rr.created_at THEN 'PASS' ELSE 'FAIL' END;
 reason:='PINNED_BRIDGE_RELEASE_CHECK_PRECEDES_BEGIN_IN_ATOMIC_PATH'; END IF;
 checks:=checks||jsonb_build_array(sol_missions.check_item('production_release_binding',verdict,reason,coalesce(binding,'{}'::jsonb)));
 IF rr.job_id IS NULL THEN checks:=checks||jsonb_build_array(sol_missions.check_item('independent_sql_oracle','UNKNOWN','RESULT_NOT_AVAILABLE'));
 ELSE
 BEGIN expected:=sol_action.oracle(j.source_csv);
 verdict:=CASE WHEN expected=rr.result AND rr.result_sha256=sol_action.sha(rr.result::text) AND expected->>'source_sha256'=j.source_sha256 AND rr.runtime_hash=j.runtime_hash AND j.runtime_hash=deps->>'action_runtime_hash' THEN 'PASS' ELSE 'FAIL' END;
 checks:=checks||jsonb_build_array(sol_missions.check_item('independent_sql_oracle',verdict,CASE WHEN verdict='PASS' THEN 'EXACT_CSV_CONTRACT_MATCH' ELSE 'CANDIDATE_OR_HASH_DIFFERS' END,jsonb_build_object('oracle','INDEPENDENT_SQL_STATE_MACHINE','expected_result',expected,'persisted_result',rr.result,'computed_result_sha256',sol_action.sha(rr.result::text),'stored_result_sha256',rr.result_sha256,'production_request_id',rr.production_request_id,'result_request_id',rr.result_request_id,'worker_identity','DECLARED_NOT_ATTESTED')));
 EXCEPTION WHEN OTHERS THEN checks:=checks||jsonb_build_array(sol_missions.check_item('independent_sql_oracle','FAIL','SOURCE_OUTSIDE_CSV_CONTRACT',jsonb_build_object('sqlstate',SQLSTATE))); END;
 END IF;
 verdict:='UNKNOWN'; reason:='RUNTIME_OBSERVATION_REQUIRED';
 IF ri IS NOT NULL THEN
 IF NOT sol_missions.keys(ri,ARRAY['release_hash','manifest_hash','source_commit','self_hash','files','bridge_token','observed_at'],ARRAY['release_hash','manifest_hash','source_commit','self_hash','files','bridge_token','observed_at']) THEN malformed:=true;
 ELSIF NOT sol_missions.text_ok(ri->'observed_at',50) OR (ri->>'observed_at') !~ '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(\.[0-9]{1,6})?(Z|[+]00:00)$' THEN malformed:=true;
 ELSE BEGIN local_at:=(ri->>'observed_at')::timestamptz; EXCEPTION WHEN OTHERS THEN malformed:=true; END; END IF;
 IF malformed THEN reason:='RUNTIME_IDENTITY_INVALID';
 ELSIF b.job_id IS NULL OR rel.release_hash IS NULL THEN reason:='RUNTIME_RELEASE_UNAVAILABLE';
 ELSIF NOT sol_action_bridge.token_matches(ri->>'bridge_token',rel.token_sha256) THEN reason:='RUNTIME_HOLDER_NOT_AUTHENTICATED';
 ELSIF local_at<clock_timestamp()-interval '60 seconds' OR local_at>clock_timestamp()+interval '5 seconds' THEN reason:='RUNTIME_OBSERVATION_EXPIRED_OR_FUTURE';
 ELSIF ri->>'release_hash' IS DISTINCT FROM rel.release_hash OR ri->>'manifest_hash' IS DISTINCT FROM rel.manifest_hash OR ri->>'source_commit' IS DISTINCT FROM rel.source_commit OR ri->>'self_hash' IS DISTINCT FROM b.worker_self_hash OR ri->'files' IS DISTINCT FROM rel.source_files OR NOT sol_action_bridge.valid_files(ri->'files') OR NOT (ri->'files' ?& ARRAY['api/job.py','api/mcp.py','api/mission.py','bridge_runtime.py']) THEN verdict:='FAIL'; reason:='RUNTIME_FILES_OR_RELEASE_MISMATCH';
 ELSE verdict:='PASS'; reason:='TOKEN_HOLDER_REPORTS_EXACT_LOCALLY_RECHECKED_RELEASE_FILES'; END IF;
 END IF;
 checks:=checks||jsonb_build_array(sol_missions.check_item('runtime_file_observation',verdict,reason,jsonb_build_object('release_hash',ri->'release_hash','manifest_hash',ri->'manifest_hash','source_commit',ri->'source_commit','self_hash',ri->'self_hash','files',ri->'files','observed_at',ri->'observed_at','trust','TOKEN_HOLDER_LOCAL_FILES_DECLARATION_NOT_MACHINE_ATTESTATION','scope','BUNDLED_SERVER_FILES_ONLY')));
 finished:=clock_timestamp(); expiry:=least(finished+interval '60 seconds',coalesce(local_at+interval '60 seconds',finished+interval '60 seconds'));
 IF local_at IS NOT NULL AND expiry<=finished THEN checks:=checks||jsonb_build_array(sol_missions.check_item('runtime_freshness_at_close','UNKNOWN','RUNTIME_OBSERVATION_EXPIRED_DURING_VERIFICATION')); END IF;
 verdict:=CASE WHEN EXISTS(SELECT 1 FROM jsonb_array_elements(checks) x WHERE x->>'verdict'='FAIL') THEN 'FAIL' WHEN EXISTS(SELECT 1 FROM jsonb_array_elements(checks) x WHERE x->>'verdict' IS DISTINCT FROM 'PASS') THEN 'UNKNOWN' ELSE 'PASS' END;
 RETURN jsonb_build_object('schema','SOL_MISSIONS_REPORT/v1','mission_id',m.id,'job_id',j.job_id,'definition_hash',m.definition_hash,'status',CASE WHEN verdict='PASS' THEN 'TECHNICAL_RESULT_VERIFIED' ELSE 'NOT_VERIFIED' END,'technical_verdict',verdict,'narrow_scope','CSV_EXACT_CENTS/v1','link_kind','EVIDENCE_FOR_REVIEW','checks',checks,'observation_started_at',sol_action.utc(started),'verified_at',sol_action.utc(finished),'expires_at',sol_action.utc(expiry),'source_sha256',j.source_sha256,'result_sha256',rr.result_sha256,'requirements',m.definition->'requirements_matrix','job_requirements',m.definition->'job'->'requirements','general_mandate','UNKNOWN','all_original_requirements_satisfied',false,'requirements_semantic_coverage','UNKNOWN','semantic_truth','UNKNOWN','current_reuse_authorized',verdict='PASS','dependencies',deps,'worker_reexecuted',false,'begin_granted',false);
END $$;
CREATE FUNCTION sol_missions.api(p_action text,p_input jsonb DEFAULT '{}',p_actor text DEFAULT 'connector:operator') RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE is_sql boolean:=session_user IN ('postgres','supabase_admin'); is_operator boolean:=false; allowed text[]; required text[]; v_job_id uuid; mid uuid; req uuid; target uuid; w text; cap text; tok text; ih text; clean_input jsonb; j sol_action.jobs%ROWTYPE; m sol_missions.missions%ROWTYPE; rel sol_action_bridge.releases%ROWTYPE; prior sol_missions.requests%ROWTYPE; old sol_missions.outcomes%ROWTYPE; deps jsonb; snap jsonb; nav jsonb; d jsonb; rpt jsonb; result jsonb; rid uuid; x jsonb;
BEGIN
 IF p_action IS NULL OR p_action NOT IN ('health','register','status','verify','receipt') THEN RAISE EXCEPTION 'UNSUPPORTED_ACTION'; END IF;
 IF jsonb_typeof(p_input) IS DISTINCT FROM 'object' OR octet_length(p_input::text)>200000 THEN RAISE EXCEPTION 'INPUT_OBJECT_MAX_200KB_REQUIRED'; END IF;
 IF p_action='health' THEN IF NOT sol_missions.keys(p_input,ARRAY[]::text[],ARRAY[]::text[]) THEN RAISE EXCEPTION 'INVALID_INPUT'; END IF; RETURN jsonb_build_object('ok',true,'module','SOL-Missions','version','0.1.0','runtime_hash',sol_missions.runtime_hash(),'narrow_scope','CSV_EXACT_CENTS/v1','general_mandate','UNKNOWN','current_reuse_authorized',false); END IF;
 allowed:=CASE p_action WHEN 'register' THEN ARRAY['workspace','bundle_id','job_id','request_id','narrow_scope','allow_job_owner_view','expected_release_hash'] WHEN 'status' THEN ARRAY['job_id','mission_id','capability'] WHEN 'verify' THEN ARRAY['job_id','mission_id','request_id','capability','runtime_identity'] ELSE ARRAY['job_id','mission_id','target_request_id','capability'] END;
 required:=CASE p_action WHEN 'register' THEN ARRAY['workspace','bundle_id','job_id','request_id','narrow_scope','allow_job_owner_view','expected_release_hash'] WHEN 'status' THEN ARRAY['job_id'] WHEN 'verify' THEN ARRAY['job_id','mission_id','request_id'] ELSE ARRAY['job_id','mission_id','target_request_id'] END;
 IF NOT sol_missions.keys(p_input,allowed,required) THEN RAISE EXCEPTION 'INVALID_INPUT'; END IF;
 FOREACH w IN ARRAY ARRAY['job_id','mission_id','request_id','bundle_id','target_request_id'] LOOP IF p_input ? w AND NOT sol_missions.uuid_ok(p_input->w) THEN RAISE EXCEPTION 'INVALID_UUID'; END IF; END LOOP;
 v_job_id:=(p_input->>'job_id')::uuid; cap:=p_input->>'capability'; tok:=p_input->'runtime_identity'->>'bridge_token';
 SELECT * INTO j FROM sol_action.jobs WHERE job_id=v_job_id; IF NOT FOUND THEN RAISE EXCEPTION 'NOT_AUTHORIZED_OR_INVALID_REFERENCE'; END IF;
 IF is_sql THEN IF p_actor IS DISTINCT FROM 'connector:operator' THEN RAISE EXCEPTION 'NOT_AUTHORIZED_OR_INVALID_REFERENCE'; END IF; is_operator:=true;
 ELSE
 IF p_actor IS DISTINCT FROM 'capability:job-owner' OR NOT sol_missions.text_ok(p_input->'capability',64) THEN RAISE EXCEPTION 'NOT_AUTHORIZED_OR_INVALID_REFERENCE'; END IF; PERFORM sol_action.authorize(j,cap);
 END IF;
 IF p_action='register' THEN
 IF NOT is_sql OR NOT sol_missions.text_ok(p_input->'workspace',80) OR p_input->>'narrow_scope' IS DISTINCT FROM 'CSV_EXACT_CENTS/v1' OR jsonb_typeof(p_input->'allow_job_owner_view') IS DISTINCT FROM 'boolean' OR NOT sol_missions.text_ok(p_input->'expected_release_hash',64) OR (p_input->>'expected_release_hash') !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'REGISTER_SQL_OPERATOR_EXPLICIT_SCOPE_REQUIRED'; END IF;
 w:=p_input->>'workspace';
 ELSIF p_input ? 'mission_id' THEN
 mid:=(p_input->>'mission_id')::uuid; SELECT * INTO m FROM sol_missions.missions mm WHERE mm.id=mid AND mm.job_id=v_job_id;
 IF NOT FOUND OR (NOT is_operator AND NOT m.allow_job_owner_view) THEN RAISE EXCEPTION 'NOT_AUTHORIZED_OR_INVALID_REFERENCE'; END IF; w:=m.workspace;
 END IF;
 IF p_input ? 'runtime_identity' THEN
 x:=p_input->'runtime_identity';
 IF NOT sol_missions.keys(x,ARRAY['release_hash','manifest_hash','source_commit','self_hash','files','bridge_token','observed_at'],ARRAY['release_hash','manifest_hash','source_commit','self_hash','files','bridge_token','observed_at']) OR NOT sol_action_bridge.valid_files(x->'files') OR NOT sol_missions.text_ok(x->'observed_at',50) THEN RAISE EXCEPTION 'INVALID_RUNTIME_IDENTITY'; END IF;
 FOREACH w IN ARRAY ARRAY['release_hash','manifest_hash','self_hash','bridge_token'] LOOP IF jsonb_typeof(x->w) IS DISTINCT FROM 'string' OR (x->>w) !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID_RUNTIME_IDENTITY'; END IF; END LOOP;
 IF jsonb_typeof(x->'source_commit') IS DISTINCT FROM 'string' OR (x->>'source_commit') !~ '^[0-9a-f]{40}$' THEN RAISE EXCEPTION 'INVALID_RUNTIME_IDENTITY'; END IF;
 w:=m.workspace;
 END IF;
 -- No existing Action/Coordination path takes the Missions lock; never acquire their locks after it.
 IF p_action IN ('register','verify') THEN PERFORM pg_advisory_xact_lock(hashtextextended('sol-lamarck:'||w,0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol-atelier:global-journal',0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol-coordination:global-journal',0)); END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('sol_action:job:'||v_job_id::text,0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol-missions:global-journal',0));
 SELECT * INTO j FROM sol_action.jobs WHERE job_id=v_job_id; IF NOT is_operator THEN PERFORM sol_action.authorize(j,cap); END IF;
 IF p_action='status' THEN
 SELECT coalesce(jsonb_agg(jsonb_build_object('mission_id',z.id,'definition',z.definition,'definition_hash',z.definition_hash,'registered_at',sol_action.utc(z.registered_at),'last_report',(SELECT sol_missions.clean(r.report,cap,NULL,true) FROM sol_missions.reports r WHERE r.mission_id=z.id ORDER BY r.created_at DESC,r.id DESC LIMIT 1),'current_reuse_authorized',false) ORDER BY z.registered_at DESC,z.id),'[]') INTO x FROM sol_missions.missions z WHERE z.job_id=v_job_id AND (mid IS NULL OR z.id=mid) AND (is_operator OR z.allow_job_owner_view);
 RETURN sol_missions.clean(jsonb_build_object('ok',true,'action','status','job_id',v_job_id,'mission_id',mid,'status','HISTORICAL_NOT_CURRENT','missions',x,'found',jsonb_array_length(x)>0,'current_reuse_authorized',false,'needs_current_revalidation',true,'general_mandate','UNKNOWN','limit','NO_CURRENT_AUTHORITY','automatic_retry',false),cap,NULL,true);
 END IF;
 IF p_action='receipt' THEN
 target:=(p_input->>'target_request_id')::uuid; SELECT * INTO prior FROM sol_missions.requests WHERE request_id=target;
 IF FOUND AND (prior.job_id<>v_job_id OR (prior.mission_id IS NOT NULL AND prior.mission_id<>mid)) THEN RAISE EXCEPTION 'NOT_AUTHORIZED_OR_INVALID_REFERENCE'; END IF;
 SELECT * INTO old FROM sol_missions.outcomes WHERE request_id=target;
 IF FOUND AND (old.job_id<>v_job_id OR old.mission_id IS DISTINCT FROM mid) THEN RAISE EXCEPTION 'NOT_AUTHORIZED_OR_INVALID_REFERENCE'; END IF;
 RETURN sol_missions.clean(jsonb_build_object('ok',true,'action','receipt','job_id',v_job_id,'mission_id',mid,'target_request_id',target,'status',CASE WHEN old.request_id IS NULL THEN 'UNKNOWN' ELSE 'HISTORICAL_NOT_CURRENT' END,'found',old.request_id IS NOT NULL,'intent_found',prior.request_id IS NOT NULL,'receipt',old.response,'current_reuse_authorized',false,'needs_current_revalidation',true,'automatic_retry',false,'general_mandate','UNKNOWN'),cap,NULL,true);
 END IF;
 req:=(p_input->>'request_id')::uuid; clean_input:=p_input-'capability'; IF clean_input ? 'runtime_identity' THEN clean_input:=jsonb_set(clean_input,'{runtime_identity}',(clean_input->'runtime_identity')-'bridge_token'-'observed_at'); END IF; clean_input:=sol_missions.clean(clean_input,cap,tok,false);
 ih:=sol_missions.hash(jsonb_build_object('action',p_action,'input',clean_input,'actor',p_actor)); SELECT * INTO prior FROM sol_missions.requests WHERE request_id=req;
 IF FOUND THEN
 IF prior.job_id<>v_job_id OR prior.action<>p_action OR prior.actor<>p_actor OR prior.input_hash<>ih THEN RAISE EXCEPTION 'REQUEST_ID_PAYLOAD_MISMATCH'; END IF;
 SELECT * INTO old FROM sol_missions.outcomes WHERE request_id=req; IF NOT FOUND THEN RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','job_id',v_job_id,'request_id',req,'automatic_retry',false,'current_reuse_authorized',false); END IF;
 IF sol_missions.hash(old.response) IS DISTINCT FROM old.response_hash THEN RAISE EXCEPTION 'OUTCOME_INTEGRITY_FAILED'; END IF;
 RETURN sol_missions.clean(old.response||jsonb_build_object('status','HISTORICAL_NOT_CURRENT','deduplicated',true,'historical_result',true,'current_reuse_authorized',false,'needs_current_revalidation',true,'automatic_retry',false),cap,tok,true);
 END IF;
 IF EXISTS(SELECT 1 FROM sol_missions.requests q WHERE q.job_id=v_job_id AND NOT EXISTS(SELECT 1 FROM sol_missions.outcomes o WHERE o.request_id=q.request_id)) THEN RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','error','UNRESOLVED_PRIOR_OUTCOME','job_id',v_job_id,'current_reuse_authorized',false,'automatic_retry',false); END IF;
 INSERT INTO sol_missions.requests(request_id,job_id,mission_id,action,actor,input,input_hash) VALUES(req,v_job_id,mid,p_action,p_actor,clean_input,ih); PERFORM sol_missions.append_event(v_job_id,'reservation',p_actor,jsonb_build_object('request_id',req,'mission_id',mid,'action',p_action,'input_hash',ih));
 BEGIN
 IF sol_missions.audit_chain()->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'MISSIONS_JOURNAL_INVALID'; END IF; deps:=sol_missions.dependencies();
 IF p_action='register' THEN
 IF deps->'dependencies_match' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'DEPENDENCY_RUNTIME_CHANGED'; END IF;
 SELECT * INTO rel FROM sol_action_bridge.releases er WHERE er.release_hash=p_input->>'expected_release_hash';
 IF NOT FOUND OR rel.core_runtime_hash IS DISTINCT FROM deps->>'action_runtime_hash' OR rel.bridge_runtime_hash IS DISTINCT FROM deps->>'bridge_runtime_hash' OR j.runtime_hash IS DISTINCT FROM rel.core_runtime_hash OR rel.release_hash IS DISTINCT FROM sol_action.sha(rel.manifest_hash||':'||rel.source_commit) OR NOT sol_action_bridge.valid_files(rel.source_files) OR NOT (rel.source_files ?& ARRAY['api/job.py','api/mcp.py','api/mission.py','bridge_runtime.py']) THEN RAISE EXCEPTION 'EXPECTED_RELEASE_NOT_ADMITTED_OR_COMPATIBLE'; END IF;
 IF EXISTS(SELECT 1 FROM sol_action_bridge.bindings eb WHERE eb.job_id=v_job_id AND eb.release_hash IS DISTINCT FROM rel.release_hash) THEN RAISE EXCEPTION 'EXISTING_BINDING_RELEASE_MISMATCH'; END IF;
 nav:=public.sol_coordination_api('bundle_status',jsonb_build_object('workspace',w,'bundle_id',p_input->'bundle_id'),p_actor); IF nav->'ok' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'BUNDLE_STATUS_NOT_AVAILABLE'; END IF;
 snap:=sol_missions.bundle_snapshot(w,(p_input->>'bundle_id')::uuid);
 IF nav->>'definition_hash' IS DISTINCT FROM snap->>'definition_hash' OR nav->'historical_definition' IS DISTINCT FROM snap->'historical_definition' OR nav->'current_resolution'->'requirement_matrix' IS DISTINCT FROM snap->'requirements_matrix' THEN RAISE EXCEPTION 'NAVIGATION_SNAPSHOT_NOT_CORRELATED'; END IF;
 IF sol_action.audit_job(v_job_id)->>'status' IS DISTINCT FROM 'PASS' THEN RAISE EXCEPTION 'JOB_JOURNAL_INVALID'; END IF;
 mid:=gen_random_uuid(); d:=jsonb_build_object('schema','SOL_MISSIONS_DEFINITION/v1','workspace',w,'bundle_id',(p_input->>'bundle_id')::uuid,'job_id',v_job_id,'narrow_scope','CSV_EXACT_CENTS/v1','allow_job_owner_view',p_input->'allow_job_owner_view','association_basis','SQL_OPERATOR_DECLARED','link_kind','EVIDENCE_FOR_REVIEW','bundle',snap,'requirements_matrix',snap->'requirements_matrix','job',sol_missions.job_definition(j),'expected_release',sol_missions.release_definition(rel),'release_binding',sol_missions.release_binding(v_job_id),'dependencies',deps,'general_mandate','UNKNOWN','all_original_requirements_satisfied',false,'semantic_truth','UNKNOWN');
 INSERT INTO sol_missions.missions(id,request_id,workspace,bundle_id,job_id,allow_job_owner_view,definition,definition_hash,source_csv) VALUES(mid,req,w,(p_input->>'bundle_id')::uuid,v_job_id,(p_input->>'allow_job_owner_view')::boolean,d,sol_missions.hash(d),j.source_csv);
 PERFORM sol_missions.append_event(v_job_id,'mission',p_actor,jsonb_build_object('request_id',req,'mission_id',mid,'definition_hash',sol_missions.hash(d)));
 result:=jsonb_build_object('ok',true,'action','register','status','REGISTERED_EVIDENCE_FOR_REVIEW','job_id',v_job_id,'mission_id',mid,'definition',d,'definition_hash',sol_missions.hash(d),'current_reuse_authorized',false,'general_mandate','UNKNOWN','all_original_requirements_satisfied',false,'automatic_retry',false);
 ELSE
 rpt:=sol_missions.observe(m,j,p_input->'runtime_identity'); rpt:=sol_missions.clean(rpt,cap,tok,false); rid:=gen_random_uuid();
 INSERT INTO sol_missions.reports(id,mission_id,request_id,job_id,report,report_hash) VALUES(rid,mid,req,v_job_id,rpt,sol_missions.hash(rpt)); PERFORM sol_missions.append_event(v_job_id,'report',p_actor,jsonb_build_object('request_id',req,'mission_id',mid,'report_id',rid,'report_hash',sol_missions.hash(rpt)));
 result:=jsonb_build_object('ok',true,'action','verify','job_id',v_job_id,'mission_id',mid,'report_id',rid,'report',rpt,'status',rpt->'status','technical_verdict',rpt->'technical_verdict','current_reuse_authorized',rpt->'current_reuse_authorized','expires_at',rpt->'expires_at','general_mandate','UNKNOWN','all_original_requirements_satisfied',false,'automatic_retry',false);
 END IF;
 EXCEPTION WHEN OTHERS THEN result:=jsonb_build_object('ok',false,'status','REJECTED','action',p_action,'job_id',v_job_id,'mission_id',mid,'error',CASE WHEN SQLERRM IN ('EXPECTED_RELEASE_NOT_ADMITTED_OR_COMPATIBLE','EXISTING_BINDING_RELEASE_MISMATCH','MISSIONS_JOURNAL_INVALID','DEPENDENCY_RUNTIME_CHANGED','BUNDLE_STATUS_NOT_AVAILABLE','NAVIGATION_SNAPSHOT_NOT_CORRELATED','JOB_JOURNAL_INVALID','BUNDLE_NOT_FOUND','SOURCE_JOURNAL_INVALID','TERMINAL_NOT_ACTIVE','ATELIER_OUTCOME_UNKNOWN') THEN SQLERRM ELSE 'OBSERVATION_NOT_COMPLETED' END,'sqlstate',SQLSTATE,'current_reuse_authorized',false,'automatic_retry',false,'general_mandate','UNKNOWN'); END;
 result:=sol_missions.clean(result||jsonb_build_object('request_id',req),cap,tok,false);
 INSERT INTO sol_missions.outcomes(request_id,job_id,mission_id,response,response_hash) VALUES(req,v_job_id,mid,result,sol_missions.hash(result)); PERFORM sol_missions.append_event(v_job_id,CASE WHEN result->'ok'='true'::jsonb THEN 'result' ELSE 'error' END,p_actor,jsonb_build_object('request_id',req,'mission_id',mid,'response_hash',sol_missions.hash(result))); RETURN result;
 EXCEPTION WHEN OTHERS THEN RETURN jsonb_build_object('ok',false,'status','REJECTED','error',CASE WHEN SQLERRM IN ('UNSUPPORTED_ACTION','INPUT_OBJECT_MAX_200KB_REQUIRED','INVALID_INPUT','INVALID_UUID','INVALID_RUNTIME_IDENTITY','REGISTER_SQL_OPERATOR_EXPLICIT_SCOPE_REQUIRED','REQUEST_ID_PAYLOAD_MISMATCH','OUTCOME_INTEGRITY_FAILED') THEN SQLERRM ELSE 'NOT_AUTHORIZED_OR_INVALID_REFERENCE' END,'current_reuse_authorized',false,'automatic_retry',false,'general_mandate','UNKNOWN');
END $$;
CREATE FUNCTION public.sol_missions_api(p_action text,p_input jsonb DEFAULT '{}',p_actor text DEFAULT 'connector:operator') RETURNS jsonb LANGUAGE sql SECURITY INVOKER SET search_path='' AS $$ SELECT sol_missions.api(p_action,p_input,p_actor) $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA sol_missions FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON FUNCTION public.sol_missions_api(text,jsonb,text) FROM PUBLIC,anon,authenticated,service_role;
GRANT USAGE ON SCHEMA sol_missions TO anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION sol_missions.api(text,jsonb,text) TO anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION public.sol_missions_api(text,jsonb,text) TO anon,authenticated,service_role;
COMMENT ON SCHEMA sol_missions IS 'SOL-Missions 0.1.0. Operator-authorized exact bundle to job association and current SQL CSV observations. EVIDENCE_FOR_REVIEW only, not general mandate satisfaction, external attestation or WORM.';
COMMIT;
