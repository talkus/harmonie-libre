-- SOL-Coordination 0.1.0. Additive; fails if already present. No existing runtime is changed.
BEGIN;
CREATE SCHEMA sol_coordination;
REVOKE ALL ON SCHEMA sol_coordination FROM PUBLIC;
CREATE TABLE sol_coordination.requests(workspace text NOT NULL,request_id uuid NOT NULL,actor text NOT NULL,input jsonb NOT NULL,input_hash text NOT NULL,reserved_at timestamptz NOT NULL DEFAULT clock_timestamp(),PRIMARY KEY(workspace,request_id));
CREATE TABLE sol_coordination.bundles(id uuid PRIMARY KEY,workspace text NOT NULL,request_id uuid NOT NULL,actor text NOT NULL,root_anchor_id uuid NOT NULL,definition jsonb NOT NULL,definition_hash text NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp(),UNIQUE(workspace,request_id),FOREIGN KEY(workspace,request_id) REFERENCES sol_coordination.requests(workspace,request_id));
CREATE TABLE sol_coordination.outcomes(id uuid PRIMARY KEY,workspace text NOT NULL,request_id uuid NOT NULL,response jsonb NOT NULL,response_hash text NOT NULL,completed_at timestamptz NOT NULL DEFAULT clock_timestamp(),UNIQUE(workspace,request_id),FOREIGN KEY(workspace,request_id) REFERENCES sol_coordination.requests(workspace,request_id));
CREATE TABLE sol_coordination.events(id uuid PRIMARY KEY DEFAULT gen_random_uuid(),sequence bigint GENERATED ALWAYS AS IDENTITY UNIQUE,workspace text NOT NULL,kind text NOT NULL CHECK(kind IN ('reservation','bundle','result','error')),actor text NOT NULL,at timestamptz NOT NULL,data jsonb NOT NULL,previous_hash text NOT NULL,event_hash text NOT NULL);
CREATE INDEX ON sol_coordination.bundles(workspace,root_anchor_id,created_at);
CREATE INDEX ON sol_coordination.events(workspace,sequence);
CREATE FUNCTION sol_coordination.hash(p jsonb) RETURNS text LANGUAGE sql IMMUTABLE STRICT SET search_path='' AS $$ SELECT encode(extensions.digest(convert_to(p::text,'UTF8'),'sha256'),'hex') $$;
CREATE FUNCTION sol_coordination.keys(p jsonb,a text[],r text[]) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT CASE WHEN jsonb_typeof(p) IS DISTINCT FROM 'object' THEN false ELSE NOT EXISTS(SELECT 1 FROM jsonb_object_keys(p) k WHERE NOT k=ANY(a)) AND p ?& r END $$;
CREATE FUNCTION sol_coordination.text_ok(p jsonb,n integer) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT coalesce(jsonb_typeof(p)='string' AND length(p#>>'{}') BETWEEN 1 AND n AND length(btrim(p#>>'{}'))>0,false) $$;
CREATE FUNCTION sol_coordination.uuid_ok(p jsonb) RETURNS boolean LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT coalesce(jsonb_typeof(p)='string' AND (p#>>'{}') ~ '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$',false) $$;
CREATE FUNCTION sol_coordination.deny_mutation() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$ BEGIN RAISE EXCEPTION 'SOL_COORDINATION_APPEND_ONLY' USING ERRCODE='42501'; END $$;
DO $$ DECLARE n text; BEGIN FOREACH n IN ARRAY ARRAY['requests','bundles','outcomes','events'] LOOP
 EXECUTE format('ALTER TABLE sol_coordination.%I ENABLE ROW LEVEL SECURITY',n);
 EXECUTE format('CREATE TRIGGER immutable BEFORE UPDATE OR DELETE ON sol_coordination.%I FOR EACH ROW EXECUTE FUNCTION sol_coordination.deny_mutation()',n);
 EXECUTE format('CREATE TRIGGER no_truncate BEFORE TRUNCATE ON sol_coordination.%I FOR EACH STATEMENT EXECUTE FUNCTION sol_coordination.deny_mutation()',n);
END LOOP; END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA sol_coordination FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA sol_coordination FROM PUBLIC,anon,authenticated,service_role;
CREATE FUNCTION sol_coordination.append_event(w text,k text,a text,d jsonb) RETURNS void LANGUAGE plpgsql SET search_path='' AS $$
DECLARE ident uuid:=gen_random_uuid(); stamp timestamptz:=clock_timestamp(); prev text;
BEGIN
 PERFORM pg_advisory_xact_lock(hashtextextended('sol-coordination:global-journal',0));
 SELECT event_hash INTO prev FROM sol_coordination.events ORDER BY sequence DESC LIMIT 1; prev:=coalesce(prev,repeat('0',64));
 INSERT INTO sol_coordination.events(id,workspace,kind,actor,at,data,previous_hash,event_hash) VALUES(ident,w,k,a,stamp,d,prev,
 sol_coordination.hash(jsonb_build_object('id',ident,'workspace',w,'kind',k,'actor',a,'at',to_char(stamp AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'data',d,'previous_hash',prev)));
END $$;
CREATE FUNCTION sol_coordination.audit_chain() RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path='' AS $$
DECLARE r record; prev text:=repeat('0',64); bad bigint:=0; links bigint:=0; n bigint:=0; h text;
BEGIN
 FOR r IN SELECT * FROM sol_coordination.events ORDER BY sequence LOOP
 h:=sol_coordination.hash(jsonb_build_object('id',r.id,'workspace',r.workspace,'kind',r.kind,'actor',r.actor,'at',to_char(r.at AT TIME ZONE 'UTC','YYYY-MM-DD"T"HH24:MI:SS.US"Z"'),'data',r.data,'previous_hash',r.previous_hash));
 IF r.previous_hash IS DISTINCT FROM prev OR r.event_hash IS DISTINCT FROM h THEN bad:=bad+1; END IF; prev:=r.event_hash; n:=n+1;
 END LOOP;
 SELECT count(*) INTO links FROM sol_coordination.requests q WHERE sol_coordination.hash(jsonb_build_object('action','assemble','input',q.input,'actor',q.actor)) IS DISTINCT FROM q.input_hash OR
 (SELECT count(*) FROM sol_coordination.events e WHERE e.workspace=q.workspace AND e.kind='reservation' AND e.data->>'request_id'=q.request_id::text AND e.data->>'input_hash'=q.input_hash AND e.actor=q.actor)<>1;
 SELECT links+count(*) INTO links FROM sol_coordination.bundles b WHERE sol_coordination.hash(b.definition) IS DISTINCT FROM b.definition_hash OR
 b.definition->>'root_anchor_id' IS DISTINCT FROM b.root_anchor_id::text OR b.definition->>'actor' IS DISTINCT FROM b.actor OR b.definition->>'workspace' IS DISTINCT FROM b.workspace OR
 NOT EXISTS(SELECT 1 FROM sol_coordination.requests q WHERE q.workspace=b.workspace AND q.request_id=b.request_id AND q.actor=b.actor AND q.input->'purpose'=b.definition->'purpose' AND q.input->'companion_anchor_ids'=b.definition->'companion_anchor_ids' AND lower(q.input->>'root_anchor_id')=b.root_anchor_id::text) OR
 (SELECT count(*) FROM sol_coordination.events e WHERE e.workspace=b.workspace AND e.kind='bundle' AND e.data->>'bundle_id'=b.id::text AND e.data->>'definition_hash'=b.definition_hash AND e.data->>'request_id'=b.request_id::text AND e.actor=b.actor)<>1 OR
 NOT EXISTS(SELECT 1 FROM sol_coordination.outcomes o WHERE o.workspace=b.workspace AND o.request_id=b.request_id AND o.response->>'bundle_id'=b.id::text AND o.response->'ok'='true'::jsonb);
 SELECT links+count(*) INTO links FROM sol_coordination.outcomes o WHERE sol_coordination.hash(o.response) IS DISTINCT FROM o.response_hash OR
 (SELECT count(*) FROM sol_coordination.events e WHERE e.workspace=o.workspace AND e.kind IN ('result','error') AND e.data->>'outcome_id'=o.id::text AND e.data->>'request_id'=o.request_id::text AND e.data->>'response_hash'=o.response_hash)<>1;
 SELECT links+count(*) INTO links FROM sol_coordination.events e WHERE
 (e.kind='reservation' AND NOT EXISTS(SELECT 1 FROM sol_coordination.requests q WHERE q.workspace=e.workspace AND q.request_id::text=e.data->>'request_id' AND q.input_hash=e.data->>'input_hash' AND q.actor=e.actor)) OR
 (e.kind='bundle' AND NOT EXISTS(SELECT 1 FROM sol_coordination.bundles b WHERE b.workspace=e.workspace AND b.id::text=e.data->>'bundle_id' AND b.definition_hash=e.data->>'definition_hash' AND b.request_id::text=e.data->>'request_id' AND b.actor=e.actor)) OR
 (e.kind IN ('result','error') AND NOT EXISTS(SELECT 1 FROM sol_coordination.outcomes o JOIN sol_coordination.requests q USING(workspace,request_id) WHERE o.workspace=e.workspace AND o.id::text=e.data->>'outcome_id' AND o.request_id::text=e.data->>'request_id' AND o.response_hash=e.data->>'response_hash' AND q.actor=e.actor));
 RETURN jsonb_build_object('valid',bad=0 AND links=0,'events',n,'head',prev,'invalid_events',bad,'incoherent_records',links,'scope','GLOBAL_CHAIN_BUNDLE_REQUEST_OUTCOME_LINKS','owner_tamper_resistance','NOT_WORM');
END $$;
CREATE FUNCTION sol_coordination.resolve(w text,anchor uuid,a text) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE cur uuid:=anchor; seen uuid[]:='{}'; t sol_atelier.tasks%ROWTYPE; successor sol_atelier.tasks%ROWTYPE; children bigint; st jsonb; p jsonb; chain jsonb:='[]'; i integer; j integer; previous_requirements jsonb; observed timestamptz; phase text;
BEGIN
 -- API obtains core workspace -> Atelier global -> Coordination global in this order.
 FOR i IN 1..64 LOOP
 IF cur=ANY(seen) THEN RAISE EXCEPTION 'SUCCESSION_CYCLE'; END IF; seen:=array_append(seen,cur);
 SELECT * INTO t FROM sol_atelier.tasks WHERE id=cur;
 IF NOT FOUND THEN RAISE EXCEPTION 'ANCHOR_OR_SUCCESSOR_NOT_FOUND'; END IF;
 IF t.workspace IS DISTINCT FROM w THEN RAISE EXCEPTION 'SUCCESSION_WORKSPACE_MISMATCH'; END IF;
 IF sol_coordination.hash(t.definition) IS DISTINCT FROM t.definition_hash THEN RAISE EXCEPTION 'TASK_DEFINITION_HASH_MISMATCH'; END IF;
 IF NOT sol_coordination.text_ok(t.definition->'mandate',10000) OR jsonb_typeof(t.definition->'requirements') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'INVALID_TASK_DEFINITION'; END IF;
 IF jsonb_array_length(t.definition->'requirements') NOT BETWEEN 1 AND 16 THEN RAISE EXCEPTION 'TASK_REQUIREMENTS_1_TO_16_REQUIRED'; END IF;
 IF EXISTS(SELECT 1 FROM jsonb_array_elements(t.definition->'requirements') x WHERE NOT sol_coordination.keys(x,ARRAY['id','text','contract'],ARRAY['id','text','contract']) OR NOT sol_coordination.text_ok(x->'id',80) OR NOT sol_coordination.text_ok(x->'text',2000)) OR
 (SELECT count(DISTINCT x->>'id') FROM jsonb_array_elements(t.definition->'requirements') x)<>jsonb_array_length(t.definition->'requirements') THEN RAISE EXCEPTION 'INVALID_TASK_REQUIREMENTS'; END IF;
 IF previous_requirements IS NOT NULL THEN
 IF jsonb_array_length(t.definition->'requirements')<jsonb_array_length(previous_requirements) THEN RAISE EXCEPTION 'REQUIREMENTS_PREFIX_LOST'; END IF;
 FOR j IN 0..jsonb_array_length(previous_requirements)-1 LOOP IF t.definition->'requirements'->j IS DISTINCT FROM previous_requirements->j THEN RAISE EXCEPTION 'REQUIREMENTS_EXACT_PREFIX_MISMATCH'; END IF; END LOOP;
 END IF;
 st:=public.sol_atelier_api('status',jsonb_build_object('workspace',w,'task_id',cur),a); p:=st->'progress'; phase:=p->>'phase';
 IF st->'ok' IS DISTINCT FROM 'true'::jsonb OR st->>'task_id' IS DISTINCT FROM cur::text OR st->>'workspace' IS DISTINCT FROM w OR st->'task' IS DISTINCT FROM t.definition OR st->>'definition_hash' IS DISTINCT FROM t.definition_hash OR jsonb_typeof(p) IS DISTINCT FROM 'object' THEN RAISE EXCEPTION 'ATELIER_STATUS_NOT_CORRELATED'; END IF;
 IF phase IS NULL OR phase NOT IN ('OPEN','IN_PROGRESS','BLOCKED','COMPLETED_BOUNDED','CANCELLED','SUPERSEDED') THEN RAISE EXCEPTION 'INVALID_PROGRESS_PHASE'; END IF;
 SELECT count(*) INTO children FROM sol_atelier.tasks WHERE lower(definition->>'supersedes_task_id')=cur::text;
 IF children>1 THEN RAISE EXCEPTION 'SUCCESSION_FORK'; END IF;
 IF children=1 THEN
 SELECT * INTO successor FROM sol_atelier.tasks WHERE lower(definition->>'supersedes_task_id')=cur::text;
 IF successor.workspace IS DISTINCT FROM w THEN RAISE EXCEPTION 'SUCCESSION_WORKSPACE_MISMATCH'; END IF;
 IF phase IS DISTINCT FROM 'SUPERSEDED' OR p->>'successor_task_id' IS DISTINCT FROM successor.id::text THEN RAISE EXCEPTION 'SUCCESSOR_PROGRESS_POINTER_MISMATCH'; END IF;
 ELSE
 IF phase='SUPERSEDED' OR p->>'successor_task_id' IS NOT NULL THEN RAISE EXCEPTION 'SUCCESSOR_MISSING_OR_UNEXPECTED'; END IF;
 IF st->'bindings_match_creation' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'TERMINAL_RUNTIME_BINDINGS_CHANGED'; END IF;
 IF jsonb_typeof(st->'pending_requirement_ids') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'PENDING_REQUIREMENTS_UNAVAILABLE'; END IF;
 END IF;
 chain:=chain||jsonb_build_array(jsonb_build_object('task_id',cur,'mandate',t.definition->'mandate','requirements',t.definition->'requirements','definition_hash',t.definition_hash,'progress_phase',phase,'successor_task_id',p->'successor_task_id','historical_only',true));
 IF children=0 THEN
 observed:=clock_timestamp(); RETURN jsonb_build_object('ok',true,'status','RESOLVED_FOR_NAVIGATION_ONLY','workspace',w,'anchor_task_id',anchor,'terminal_task_id',cur,'resolved_at',observed,'expires_at',observed+interval '60 seconds','coordination_runtime_hash',sol_coordination.runtime_hash(),'atelier_runtime_hash',sol_atelier.runtime_hash(),'chain',chain,'terminal',st,
 'pending_count',jsonb_array_length(st->'pending_requirement_ids'),'pending_requirement_count',jsonb_array_length(st->'pending_requirement_ids'),
 'unresolved_atelier_request_count',(SELECT count(*) FROM sol_atelier.requests q WHERE q.workspace=w AND NOT EXISTS(SELECT 1 FROM sol_atelier.outcomes o WHERE o.workspace=q.workspace AND o.request_id=q.request_id)),
 'unresolved_atelier_request_scope','WORKSPACE_CONSERVATIVE',
 'known_chain_pending_request_count',(SELECT count(*) FROM sol_atelier.requests q WHERE q.workspace=w AND NOT EXISTS(SELECT 1 FROM sol_atelier.outcomes o WHERE o.workspace=q.workspace AND o.request_id=q.request_id) AND EXISTS(SELECT 1 FROM sol_atelier.events e WHERE e.workspace=q.workspace AND e.kind='reservation' AND e.data->>'request_id'=q.request_id::text AND e.data->>'task_id'=ANY(SELECT s::text FROM unnest(seen) s))),
 'current_reuse_authorized',false,'needs_current_revalidation',true,'limit','NO_CURRENT_AUTHORITY','semantic_truth','UNKNOWN','automatic_retry',false);
 END IF;
 previous_requirements:=t.definition->'requirements'; cur:=successor.id;
 END LOOP;
 RAISE EXCEPTION 'SUCCESSION_DEPTH_EXCEEDS_64';
END $$;
CREATE FUNCTION sol_coordination.assembly(w text,root_anchor uuid,companions jsonb,a text) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE anchors uuid[]:=ARRAY[root_anchor]; terminals uuid[]:='{}'; x jsonb; r jsonb; roots jsonb:='[]'; matrix jsonb:='[]'; q jsonb; anchor uuid; terminal_id uuid; role text; n integer:=0; pending integer:=0; expiry timestamptz;
BEGIN
 FOR x IN SELECT value FROM jsonb_array_elements(companions) LOOP anchors:=array_append(anchors,(x#>>'{}')::uuid); END LOOP;
 IF (SELECT count(DISTINCT u) FROM unnest(anchors) u)<>cardinality(anchors) THEN RAISE EXCEPTION 'DUPLICATE_ANCHOR'; END IF;
 FOREACH anchor IN ARRAY anchors LOOP
 r:=sol_coordination.resolve(w,anchor,a); terminal_id:=(r->>'terminal_task_id')::uuid;
 IF terminal_id=ANY(terminals) THEN RAISE EXCEPTION 'DUPLICATE_RESOLVED_TERMINAL'; END IF; terminals:=array_append(terminals,terminal_id);
 role:=CASE WHEN n=0 THEN 'ROOT' ELSE 'COMPANION' END; roots:=roots||jsonb_build_array(jsonb_build_object('role',role,'association_basis','OPERATOR_DECLARED','resolution',r));
 FOR q IN SELECT value FROM jsonb_array_elements(r->'terminal'->'task'->'requirements') LOOP
 matrix:=matrix||jsonb_build_array(jsonb_build_object('compound_id',terminal_id::text||':'||(q->>'id'),'task_id',terminal_id,'anchor_task_id',anchor,'role',role,'requirement',q,'mapping_basis','OPERATOR_DECLARED','validation','UNKNOWN'));
 END LOOP;
 pending:=pending+(r->>'pending_count')::integer; expiry:=least(expiry,(r->>'expires_at')::timestamptz); n:=n+1;
 END LOOP;
 IF expiry<=clock_timestamp() THEN RAISE EXCEPTION 'RESOLUTION_EXPIRED_DURING_ASSEMBLY'; END IF;
 RETURN jsonb_build_object('resolutions',roots,'requirement_matrix',matrix,'requirement_count',jsonb_array_length(matrix),'pending_count',pending,'pending_requirement_count',pending,
 'unresolved_atelier_request_count',(SELECT count(*) FROM sol_atelier.requests q WHERE q.workspace=w AND NOT EXISTS(SELECT 1 FROM sol_atelier.outcomes o WHERE o.workspace=q.workspace AND o.request_id=q.request_id)),
 'expires_at',expiry,'association_basis','OPERATOR_DECLARED','current_reuse_authorized',false,'limit','NO_CURRENT_AUTHORITY');
END $$;
CREATE FUNCTION sol_coordination.runtime_hash() RETURNS text LANGUAGE sql STABLE SET search_path='' AS $$
 SELECT sol_coordination.hash(jsonb_agg(jsonb_build_object('signature',n.nspname||'.'||p.proname||'('||pg_get_function_identity_arguments(p.oid)||')','definition',pg_get_functiondef(p.oid)) ORDER BY n.nspname,p.proname,pg_get_function_identity_arguments(p.oid)))
 FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE p.prokind='f' AND (n.nspname='sol_coordination' OR (n.nspname='public' AND p.proname='sol_coordination_api')) $$;
CREATE FUNCTION sol_coordination.api(p_action text,p_input jsonb DEFAULT '{}',p_actor text DEFAULT 'connector:operator') RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE w text; allowed text[]; required text[]; role text:=auth.jwt()->>'role'; req uuid; ident uuid; outcome uuid; ih text; prior sol_coordination.requests%ROWTYPE; old sol_coordination.outcomes%ROWTYPE; b sol_coordination.bundles%ROWTYPE; result jsonb; d jsonb; assembled jsonb; companions jsonb; x jsonb; err text; stmt text; audit jsonb;
BEGIN
 IF session_user IN ('postgres','supabase_admin') THEN
 IF p_actor IS DISTINCT FROM 'connector:operator' THEN RAISE EXCEPTION 'CONNECTOR_ACTOR_REQUIRED' USING ERRCODE='42501'; END IF;
 ELSIF p_action='health' THEN
 IF role IS NULL OR role NOT IN ('authenticated','service_role') THEN RAISE EXCEPTION 'AUTHENTICATION_REQUIRED' USING ERRCODE='42501'; END IF;
 ELSIF role IS DISTINCT FROM 'authenticated' OR auth.uid() IS NULL OR p_actor IS DISTINCT FROM 'auth:'||auth.uid()::text OR NOT EXISTS(SELECT 1 FROM sol_lamarck.memberships m WHERE m.user_id=auth.uid() AND m.role='operator') THEN
 RAISE EXCEPTION 'ENROLLED_AUTHENTICATED_OPERATOR_REQUIRED' USING ERRCODE='42501'; END IF;
 IF p_action IS NULL OR p_action NOT IN ('health','resolve','assemble','bundle_status','list','audit') THEN RAISE EXCEPTION 'UNSUPPORTED_ACTION'; END IF;
 IF jsonb_typeof(p_input) IS DISTINCT FROM 'object' OR octet_length(p_input::text)>200000 THEN RAISE EXCEPTION 'INPUT_OBJECT_MAX_200KB_REQUIRED'; END IF;
 allowed:=CASE p_action WHEN 'resolve' THEN ARRAY['workspace','anchor_task_id'] WHEN 'assemble' THEN ARRAY['workspace','purpose','root_anchor_id','companion_anchor_ids','request_id'] WHEN 'bundle_status' THEN ARRAY['workspace','bundle_id'] WHEN 'list' THEN ARRAY['workspace','root_anchor_id'] ELSE ARRAY['workspace'] END;
 required:=CASE p_action WHEN 'resolve' THEN ARRAY['anchor_task_id'] WHEN 'assemble' THEN ARRAY['purpose','root_anchor_id','companion_anchor_ids','request_id'] WHEN 'bundle_status' THEN ARRAY['bundle_id'] ELSE ARRAY[]::text[] END;
 IF NOT sol_coordination.keys(p_input,allowed,required) THEN RAISE EXCEPTION 'UNSUPPORTED_OR_MISSING_INPUT_FIELD'; END IF;
 IF p_input ? 'workspace' AND NOT sol_coordination.text_ok(p_input->'workspace',80) THEN RAISE EXCEPTION 'INVALID_WORKSPACE'; END IF; w:=coalesce(p_input->>'workspace','default');
 FOREACH stmt IN ARRAY ARRAY['anchor_task_id','root_anchor_id','bundle_id','request_id'] LOOP IF p_input ? stmt AND NOT sol_coordination.uuid_ok(p_input->stmt) THEN RAISE EXCEPTION 'INVALID_UUID_FIELD_%',stmt; END IF; END LOOP;
 IF p_action='assemble' THEN
 IF NOT sol_coordination.text_ok(p_input->'purpose',10000) OR jsonb_typeof(p_input->'companion_anchor_ids') IS DISTINCT FROM 'array' THEN RAISE EXCEPTION 'PURPOSE_AND_COMPANION_ARRAY_REQUIRED'; END IF;
 companions:=p_input->'companion_anchor_ids'; IF jsonb_array_length(companions)>16 THEN RAISE EXCEPTION 'MAX_16_COMPANIONS'; END IF;
 FOR x IN SELECT value FROM jsonb_array_elements(companions) LOOP IF NOT sol_coordination.uuid_ok(x) THEN RAISE EXCEPTION 'COMPANION_UUID_REQUIRED'; END IF; END LOOP;
 END IF;
 IF p_action='health' THEN RETURN jsonb_build_object('ok',true,'application','SOL-Coordination','version','0.1.0','runtime_hash',sol_coordination.runtime_hash(),'actions',jsonb_build_array('resolve','assemble','bundle_status','list','audit'),'current_reuse_authorized',false,'limits',jsonb_build_array('NO_CURRENT_AUTHORITY','NO_ATELIER_MUTATIONS','NO_SEMANTIC_COVERAGE_ORACLE','NO_EXTERNAL_TOOL_EXECUTION','NO_COMPLETE_ACTION','NOT_WORM')); END IF;
 -- Never take Coordination before Atelier; nested status takes core then Atelier.
 PERFORM pg_advisory_xact_lock(hashtextextended('sol-lamarck:'||w,0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol-atelier:global-journal',0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol-coordination:global-journal',0));
 audit:=sol_coordination.audit_chain(); IF audit->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'COORDINATION_JOURNAL_INVALID'; END IF;
 IF p_action IN ('resolve','assemble','bundle_status') AND sol_atelier.audit_chain()->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'SOURCE_ATELIER_JOURNAL_INVALID'; END IF;
 IF p_action='audit' THEN RETURN jsonb_build_object('ok',true,'audit',audit,'runtime_hash',sol_coordination.runtime_hash(),'workspace',w,'current_reuse_authorized',false); END IF;
 IF p_action='resolve' THEN RETURN sol_coordination.resolve(w,(p_input->>'anchor_task_id')::uuid,p_actor)||jsonb_build_object('source_journal_integrity_checked',true); END IF;
 IF p_action='list' THEN RETURN jsonb_build_object('ok',true,'workspace',w,'historical_result',true,'current_reuse_authorized',false,'bundles',coalesce((SELECT jsonb_agg(jsonb_build_object('bundle_id',id,'root_anchor_id',root_anchor_id,'purpose',definition->'purpose','actor',actor,'definition_hash',definition_hash,'created_at',created_at) ORDER BY created_at,id) FROM sol_coordination.bundles WHERE workspace=w AND (NOT p_input ? 'root_anchor_id' OR root_anchor_id=(p_input->>'root_anchor_id')::uuid)),'[]'::jsonb)); END IF;
 IF p_action='bundle_status' THEN
 SELECT * INTO b FROM sol_coordination.bundles WHERE id=(p_input->>'bundle_id')::uuid AND workspace=w; IF NOT FOUND THEN RAISE EXCEPTION 'BUNDLE_NOT_FOUND'; END IF;
 assembled:=sol_coordination.assembly(w,b.root_anchor_id,b.definition->'companion_anchor_ids',p_actor);
 RETURN jsonb_build_object('ok',true,'status','BUNDLE_RESOLVED_FOR_NAVIGATION_ONLY','bundle_id',b.id,'workspace',w,'coordination_runtime_hash',sol_coordination.runtime_hash(),'atelier_runtime_hash',sol_atelier.runtime_hash(),'historical_definition',b.definition,'definition_hash',b.definition_hash,'current_resolution',assembled,'source_journal_integrity_checked',true,'current_reuse_authorized',false,'needs_current_revalidation',true,'limit','NO_CURRENT_AUTHORITY','automatic_retry',false);
 END IF;
 req:=(p_input->>'request_id')::uuid; ih:=sol_coordination.hash(jsonb_build_object('action',p_action,'input',p_input,'actor',p_actor));
 SELECT * INTO prior FROM sol_coordination.requests WHERE workspace=w AND request_id=req;
 IF FOUND THEN
 IF prior.input_hash IS DISTINCT FROM ih OR prior.actor IS DISTINCT FROM p_actor THEN RAISE EXCEPTION 'REQUEST_ID_PAYLOAD_MISMATCH'; END IF;
 SELECT * INTO old FROM sol_coordination.outcomes WHERE workspace=w AND request_id=req;
 IF NOT FOUND THEN RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','error','OUTCOME_UNKNOWN','automatic_retry',false,'current_reuse_authorized',false); END IF;
 RETURN old.response||jsonb_build_object('status','HISTORICAL_NOT_CURRENT','deduplicated',true,'historical_result',true,'current_reuse_authorized',false,'needs_current_revalidation',true,'automatic_retry',false);
 END IF;
 IF EXISTS(SELECT 1 FROM sol_coordination.requests q WHERE q.workspace=w AND NOT EXISTS(SELECT 1 FROM sol_coordination.outcomes o WHERE o.workspace=q.workspace AND o.request_id=q.request_id)) THEN RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','error','UNRESOLVED_PRIOR_OUTCOME','automatic_retry',false,'current_reuse_authorized',false); END IF;
 INSERT INTO sol_coordination.requests(workspace,request_id,actor,input,input_hash) VALUES(w,req,p_actor,p_input,ih);
 PERFORM sol_coordination.append_event(w,'reservation',p_actor,jsonb_build_object('request_id',req,'input_hash',ih));
 BEGIN
 assembled:=sol_coordination.assembly(w,(p_input->>'root_anchor_id')::uuid,companions,p_actor); ident:=gen_random_uuid();
 d:=jsonb_build_object('version','SOL-COORDINATION/0.1.0','coordination_runtime_hash',sol_coordination.runtime_hash(),'atelier_runtime_hash',sol_atelier.runtime_hash(),'workspace',w,'purpose',p_input->'purpose','actor',p_actor,'root_anchor_id',(p_input->>'root_anchor_id')::uuid,'companion_anchor_ids',companions,'assembly',assembled,'association_basis','OPERATOR_DECLARED','semantic_truth','UNKNOWN','current_reuse_authorized',false,'limit','NO_CURRENT_AUTHORITY');
 INSERT INTO sol_coordination.bundles(id,workspace,request_id,actor,root_anchor_id,definition,definition_hash) VALUES(ident,w,req,p_actor,(p_input->>'root_anchor_id')::uuid,d,sol_coordination.hash(d));
 PERFORM sol_coordination.append_event(w,'bundle',p_actor,jsonb_build_object('bundle_id',ident,'request_id',req,'definition_hash',sol_coordination.hash(d)));
 result:=jsonb_build_object('ok',true,'status','BUNDLE_ASSEMBLED_FOR_NAVIGATION_ONLY','bundle_id',ident,'workspace',w,'definition',d,'definition_hash',sol_coordination.hash(d),'current_reuse_authorized',false,'needs_current_revalidation',true,'limit','NO_CURRENT_AUTHORITY','automatic_retry',false);
 EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS err=MESSAGE_TEXT,stmt=RETURNED_SQLSTATE;
 result:=jsonb_build_object('ok',false,'status','REJECTED','error',left(err,180),'sqlstate',stmt,'current_reuse_authorized',false,'automatic_retry',false);
 END;
 outcome:=gen_random_uuid(); result:=result||jsonb_build_object('request_id',req,'outcome_id',outcome);
 INSERT INTO sol_coordination.outcomes(id,workspace,request_id,response,response_hash) VALUES(outcome,w,req,result,sol_coordination.hash(result));
 PERFORM sol_coordination.append_event(w,CASE WHEN result->'ok'='true'::jsonb THEN 'result' ELSE 'error' END,p_actor,jsonb_build_object('request_id',req,'outcome_id',outcome,'response_hash',sol_coordination.hash(result))); RETURN result;
EXCEPTION WHEN OTHERS THEN GET STACKED DIAGNOSTICS err=MESSAGE_TEXT,stmt=RETURNED_SQLSTATE;
 RETURN jsonb_build_object('ok',false,'status','REJECTED','error',left(err,180),'sqlstate',stmt,'automatic_retry',false,'current_reuse_authorized',false,'limit','NO_CURRENT_AUTHORITY');
END $$;
CREATE FUNCTION public.sol_coordination_api(p_action text,p_input jsonb DEFAULT '{}',p_actor text DEFAULT 'connector:operator') RETURNS jsonb LANGUAGE sql SECURITY INVOKER SET search_path='' AS $$ SELECT sol_coordination.api(p_action,p_input,p_actor) $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA sol_coordination FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON FUNCTION public.sol_coordination_api(text,jsonb,text) FROM PUBLIC,anon,authenticated,service_role;
GRANT USAGE ON SCHEMA sol_coordination TO authenticated,service_role;
GRANT EXECUTE ON FUNCTION sol_coordination.api(text,jsonb,text) TO authenticated,service_role;
GRANT EXECUTE ON FUNCTION public.sol_coordination_api(text,jsonb,text) TO authenticated,service_role;
COMMENT ON SCHEMA sol_coordination IS 'SOL-Coordination 0.1.0. Immutable operator-declared bundles and checked successor navigation; no execution, completion, authority or semantic validation.';
COMMIT;
