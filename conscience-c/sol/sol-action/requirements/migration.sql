-- SOL-Action-Requirements 0.1.0: additive canonical-contract guard; no old function or ACL changes.
BEGIN;
DO $$ BEGIN
 IF sol_action.runtime_hash()<>'c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0' OR sol_action_bridge.runtime_hash()<>'d7ee0d9d373978aa9e05892c491f6c115710bd6ad9c29923fba42ba3c64328f7' THEN RAISE EXCEPTION 'REVIEWED_PREDECESSOR_REQUIRED'; END IF;
END $$;
CREATE SCHEMA sol_action_requirements;
REVOKE ALL ON SCHEMA sol_action_requirements FROM PUBLIC,anon,authenticated,service_role;
CREATE FUNCTION sol_action_requirements.sha(p text) RETURNS text LANGUAGE sql IMMUTABLE STRICT SET search_path='' AS $$ SELECT encode(extensions.digest(convert_to(p,'UTF8'),'sha256'),'hex') $$;
CREATE FUNCTION sol_action_requirements.runtime_hash() RETURNS text LANGUAGE sql STABLE SET search_path='' AS $$ SELECT sol_action_requirements.sha(string_agg(pg_get_functiondef(p.oid),E'\n' ORDER BY n.nspname,p.proname,pg_get_function_identity_arguments(p.oid))) FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace WHERE p.prokind='f' AND (n.nspname='sol_action_requirements' OR (n.nspname='public' AND p.proname='sol_action_requirements_api')) $$;
CREATE TABLE sol_action_requirements.admissions(release_hash text PRIMARY KEY,guard_runtime_hash text NOT NULL DEFAULT sol_action_requirements.runtime_hash(),core_runtime_hash text NOT NULL DEFAULT sol_action.runtime_hash(),bridge_runtime_hash text NOT NULL DEFAULT sol_action_bridge.runtime_hash(),release_metadata_hash text NOT NULL,admitted_at timestamptz NOT NULL DEFAULT clock_timestamp(),admitted_by text NOT NULL DEFAULT session_user);
CREATE TABLE sol_action_requirements.requests(request_id uuid PRIMARY KEY,job_id uuid NOT NULL,action text NOT NULL CHECK(action IN ('bind','verify','complete')),payload_hash text NOT NULL,capability_hash bytea NOT NULL CHECK(octet_length(capability_hash)=32),binding_hash text NOT NULL,release_hash text NOT NULL,guard_runtime_hash text NOT NULL,core_runtime_hash text NOT NULL,bridge_runtime_hash text NOT NULL,created_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE UNIQUE INDEX one_guarded_bind_per_job ON sol_action_requirements.requests(job_id) WHERE action='bind';
CREATE TABLE sol_action_requirements.outcomes(request_id uuid PRIMARY KEY REFERENCES sol_action_requirements.requests(request_id),job_id uuid NOT NULL,receipt jsonb NOT NULL,receipt_sha256 text GENERATED ALWAYS AS (sol_action_requirements.sha(receipt::text)) STORED,recorded_at timestamptz NOT NULL DEFAULT clock_timestamp());
CREATE TABLE sol_action_requirements.events(sequence bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,id uuid UNIQUE NOT NULL,request_id uuid NOT NULL,job_id uuid NOT NULL,kind text NOT NULL CHECK(kind IN ('reservation','outcome')),at timestamptz NOT NULL,data jsonb NOT NULL,previous_hash text NOT NULL,event_hash text NOT NULL);
CREATE FUNCTION sol_action_requirements.no_change() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$ BEGIN RAISE EXCEPTION 'SOL_REQUIREMENTS_APPEND_ONLY' USING ERRCODE='42501'; END $$;
DO $$ DECLARE t text; BEGIN FOREACH t IN ARRAY ARRAY['admissions','requests','outcomes','events'] LOOP
 EXECUTE format('ALTER TABLE sol_action_requirements.%I ENABLE ROW LEVEL SECURITY',t);
 EXECUTE format('CREATE TRIGGER immutable_rows BEFORE UPDATE OR DELETE ON sol_action_requirements.%I FOR EACH ROW EXECUTE FUNCTION sol_action_requirements.no_change()',t);
 EXECUTE format('CREATE TRIGGER immutable_truncate BEFORE TRUNCATE ON sol_action_requirements.%I FOR EACH STATEMENT EXECUTE FUNCTION sol_action_requirements.no_change()',t);
END LOOP; END $$;
REVOKE ALL ON ALL TABLES IN SCHEMA sol_action_requirements FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA sol_action_requirements FROM PUBLIC,anon,authenticated,service_role;
CREATE FUNCTION sol_action_requirements.release_metadata(r sol_action_bridge.releases) RETURNS jsonb LANGUAGE sql IMMUTABLE SET search_path='' AS $$ SELECT jsonb_build_object('release_hash',r.release_hash,'manifest_hash',r.manifest_hash,'source_commit',r.source_commit,'source_files',r.source_files,'deployment_id',r.deployment_id,'deployment_url',r.deployment_url,'core_runtime_hash',r.core_runtime_hash,'bridge_runtime_hash',r.bridge_runtime_hash,'admitted_at',sol_action.utc(r.admitted_at),'admitted_by',r.admitted_by) $$;
CREATE FUNCTION sol_action_requirements.admission_check() RETURNS trigger LANGUAGE plpgsql SET search_path='' AS $$
DECLARE r sol_action_bridge.releases%ROWTYPE; h text;
BEGIN
 IF session_user NOT IN ('postgres','supabase_admin') THEN RAISE EXCEPTION 'SQL_OPERATOR_REQUIRED'; END IF;
 SELECT * INTO r FROM sol_action_bridge.releases x WHERE x.release_hash=NEW.release_hash;
 IF NOT FOUND OR r.core_runtime_hash<>sol_action.runtime_hash() OR r.bridge_runtime_hash<>sol_action_bridge.runtime_hash() OR NEW.guard_runtime_hash<>sol_action_requirements.runtime_hash() OR NEW.core_runtime_hash<>r.core_runtime_hash OR NEW.bridge_runtime_hash<>r.bridge_runtime_hash THEN RAISE EXCEPTION 'CURRENT_RELEASE_REQUIRED'; END IF;
 h:=sol_action_requirements.sha(sol_action_requirements.release_metadata(r)::text); IF NEW.release_metadata_hash IS NOT NULL AND NEW.release_metadata_hash<>h THEN RAISE EXCEPTION 'METADATA_MISMATCH'; END IF; NEW.release_metadata_hash:=h; RETURN NEW;
END $$;
CREATE TRIGGER validate_admission BEFORE INSERT ON sol_action_requirements.admissions FOR EACH ROW EXECUTE FUNCTION sol_action_requirements.admission_check();
CREATE FUNCTION sol_action_requirements.append_event(j uuid,q uuid,k text,d jsonb) RETURNS void LANGUAGE plpgsql SET search_path='' AS $$
DECLARE ident uuid:=gen_random_uuid(); stamp timestamptz:=clock_timestamp(); prev text;
BEGIN PERFORM pg_advisory_xact_lock(hashtextextended('sol_action_requirements:journal',0)); SELECT event_hash INTO prev FROM sol_action_requirements.events ORDER BY sequence DESC LIMIT 1; prev:=coalesce(prev,repeat('0',64)); INSERT INTO sol_action_requirements.events(id,request_id,job_id,kind,at,data,previous_hash,event_hash) VALUES(ident,q,j,k,stamp,d,prev,sol_action_requirements.sha(jsonb_build_object('id',ident,'request_id',q,'job_id',j,'kind',k,'at',sol_action.utc(stamp),'data',d,'previous_hash',prev)::text)); END $$;
-- Verify every legitimate core/Bridge overlap; a later legacy collision cannot mask history.
CREATE FUNCTION sol_action_requirements.coherent(q sol_action_requirements.requests,o sol_action_requirements.outcomes) RETURNS boolean LANGUAGE plpgsql STABLE SET search_path='' AS $$
DECLARE i sol_action.intents%ROWTYPE; c sol_action.outcomes%ROWTYPE; f sol_action_bridge.refusals%ROWTYPE; b sol_action_bridge.bindings%ROWTYPE; raw jsonb; coreph text;
BEGIN
 IF EXISTS(SELECT 1 FROM sol_action_bridge.recovery_outcomes x WHERE x.request_id=q.request_id) OR EXISTS(SELECT 1 FROM sol_creation_guard.requests x WHERE x.request_id=q.request_id) THEN RETURN false; END IF;
 SELECT * INTO i FROM sol_action.intents x WHERE x.request_id=q.request_id; SELECT * INTO c FROM sol_action.outcomes x WHERE x.request_id=q.request_id; SELECT * INTO f FROM sol_action_bridge.refusals x WHERE x.request_id=q.request_id;
 IF o.receipt->>'receipt_kind'='REQUIREMENTS_GUARD_REFUSAL' THEN RETURN i.request_id IS NULL AND c.request_id IS NULL AND f.request_id IS NULL AND NOT EXISTS(SELECT 1 FROM sol_action_bridge.bindings x WHERE x.production_request_id=q.request_id); END IF;
 IF q.action='bind' THEN
 IF f.request_id IS NOT NULL THEN RETURN false; END IF;
 IF o.receipt->>'status'='OUTCOME_UNKNOWN' AND i.request_id IS NULL AND c.request_id IS NULL THEN RETURN NOT EXISTS(SELECT 1 FROM sol_action_bridge.bindings x WHERE x.production_request_id=q.request_id); END IF;
 SELECT * INTO b FROM sol_action_bridge.bindings x WHERE x.production_request_id=q.request_id;
 coreph:=sol_action_requirements.sha(jsonb_build_object('action','begin','input',jsonb_build_object('job_id',q.job_id,'request_id',q.request_id,'expected_step_id','produce'))::text);
 RETURN coalesce(i.job_id=q.job_id AND i.action='begin' AND i.payload_hash=coreph AND c.job_id=q.job_id AND b.job_id=q.job_id AND b.release_hash=q.release_hash AND b.core_runtime_hash=q.core_runtime_hash AND b.bridge_runtime_hash=q.bridge_runtime_hash AND c.receipt=o.receipt->'begin_receipt',false);
 END IF;
 raw:=o.receipt-'requirements_guard'-'requirements_release_hash'-'requirements_guard_runtime_hash';
 IF f.request_id IS NOT NULL THEN RETURN i.request_id IS NULL AND c.request_id IS NULL AND f.job_id=q.job_id AND f.action=q.action AND f.payload_hash=q.payload_hash AND f.capability_hash=q.capability_hash AND f.receipt=raw; END IF;
 RETURN coalesce(i.job_id=q.job_id AND i.action=q.action AND i.payload_hash=q.payload_hash AND c.job_id=q.job_id AND c.receipt=raw,false);
END $$;
CREATE FUNCTION sol_action_requirements.audit() RETURNS jsonb LANGUAGE plpgsql STABLE SET search_path='' AS $$
DECLARE entry record; prev text:=repeat('0',64); bad bigint:=0; links bigint; total bigint:=0;
BEGIN
 FOR entry IN SELECT * FROM sol_action_requirements.events ORDER BY sequence LOOP
 IF entry.previous_hash IS DISTINCT FROM prev OR entry.event_hash IS DISTINCT FROM sol_action_requirements.sha(jsonb_build_object('id',entry.id,'request_id',entry.request_id,'job_id',entry.job_id,'kind',entry.kind,'at',sol_action.utc(entry.at),'data',entry.data,'previous_hash',entry.previous_hash)::text) THEN bad:=bad+1; END IF; prev:=entry.event_hash; total:=total+1; END LOOP;
 SELECT count(*) INTO links FROM sol_action_requirements.requests q WHERE q.binding_hash IS DISTINCT FROM sol_action_requirements.sha(encode(q.capability_hash,'hex')||':'||q.payload_hash||':'||q.job_id::text||':'||q.request_id::text||':'||q.action) OR (SELECT count(*) FROM sol_action_requirements.events e WHERE e.request_id=q.request_id AND e.job_id=q.job_id AND e.kind='reservation' AND e.data->>'payload_hash'=q.payload_hash AND e.data->>'binding_hash'=q.binding_hash)<>1;
 SELECT links+count(*) INTO links FROM sol_action_requirements.outcomes o WHERE NOT EXISTS(SELECT 1 FROM sol_action_requirements.requests q WHERE q.request_id=o.request_id AND q.job_id=o.job_id) OR o.receipt->>'job_id' IS DISTINCT FROM o.job_id::text OR o.receipt->>'request_id' IS DISTINCT FROM o.request_id::text OR NOT EXISTS(SELECT 1 FROM sol_action_requirements.requests q WHERE q.request_id=o.request_id AND sol_action_requirements.coherent(q,o)) OR (SELECT count(*) FROM sol_action_requirements.events e WHERE e.request_id=o.request_id AND e.job_id=o.job_id AND e.kind='outcome' AND e.data->>'receipt_sha256'=o.receipt_sha256)<>1;
 SELECT links+count(*) INTO links FROM sol_action_requirements.events e WHERE (e.kind='reservation' AND NOT EXISTS(SELECT 1 FROM sol_action_requirements.requests q WHERE q.request_id=e.request_id AND q.job_id=e.job_id AND q.payload_hash=e.data->>'payload_hash' AND q.binding_hash=e.data->>'binding_hash')) OR (e.kind='outcome' AND NOT EXISTS(SELECT 1 FROM sol_action_requirements.outcomes o WHERE o.request_id=e.request_id AND o.job_id=e.job_id AND o.receipt_sha256=e.data->>'receipt_sha256'));
 RETURN jsonb_build_object('valid',bad=0 AND links=0,'events',total,'head',prev,'invalid_events',bad,'incoherent_records',links,'owner_tamper_resistance','NOT_WORM','current_reuse_authorized',false);
END $$;
-- Strict SQL CSV parser for per-record constraints; oracle independently admits the whole source first.
CREATE FUNCTION sol_action_requirements.records(csv text) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE i integer:=1; st integer:=0; c text; v text:=''; fields text[]:=ARRAY[]::text[]; rows jsonb:='[]';
BEGIN
 PERFORM sol_action.oracle(csv);
 WHILE i<=length(csv) LOOP c:=substr(csv,i,1);
 IF st=2 THEN IF c='"' THEN IF substr(csv,i+1,1)='"' THEN v:=v||'"'; i:=i+1; ELSE st:=3; END IF; ELSE v:=v||c; END IF;
 ELSIF c=',' THEN fields:=array_append(fields,v); v:=''; st:=0;
 ELSIF c=E'\n' OR c=E'\r' THEN IF c=E'\r' THEN i:=i+1; END IF; rows:=rows||jsonb_build_array(to_jsonb(array_append(fields,v))); fields:=ARRAY[]::text[]; v:=''; st:=0;
 ELSIF c='"' THEN st:=2; ELSE v:=v||c; st:=1; END IF; i:=i+1; END LOOP;
 IF st<>0 OR v<>'' OR cardinality(fields)>0 THEN rows:=rows||jsonb_build_array(to_jsonb(array_append(fields,v))); END IF;
 RETURN rows-0;
END $$;
CREATE FUNCTION sol_action_requirements.contract(t text) RETURNS jsonb LANGUAGE plpgsql IMMUTABLE SET search_path='' AS $$
DECLARE m text[]; name text; params jsonb:='{}';
BEGIN
 IF t='Conserver chaque ligne d’entrée.' THEN name:='PRESERVE_ROW_IDS_ORDER';
 ELSIF t='Calculer exactement les totaux, sans arrondi intermédiaire.' THEN name:='EXACT_CENTS_TOTALS';
 ELSIF t='Séparer les devises et identifier le tableau source.' THEN name:='SEPARATE_CURRENCIES_AND_SOURCE_HASH';
 ELSIF t='Conserver le tableau source intact.' THEN name:='IMMUTABLE_SOURCE_HASH';
 ELSIF t='Interdire les montants négatifs.' THEN name:='NONNEGATIVE_RECORD_AMOUNTS';
 ELSE
 m:=regexp_match(t,'^Autoriser uniquement la devise ([A-Z]{3})[.]$');
 IF m IS NOT NULL AND t='Autoriser uniquement la devise '||m[1]||'.' THEN name:='ONLY_CURRENCY'; params:=jsonb_build_object('currency',m[1]);
 ELSE m:=regexp_match(t,'^Limiter le tableau à ([1-9][0-9]{0,2}) lignes[.]$');
 IF m IS NOT NULL AND t='Limiter le tableau à '||m[1]||' lignes.' AND m[1]::integer<=500 THEN name:='MAX_ROWS'; params:=jsonb_build_object('max_rows',m[1]::integer);
 ELSE m:=regexp_match(t,'^Limiter la valeur absolue de chaque montant à ((0|[1-9][0-9]{0,11})[.][0-9]{2})[.]$');
 IF m IS NOT NULL AND t='Limiter la valeur absolue de chaque montant à '||m[1]||'.' THEN name:='MAX_ABSOLUTE_RECORD_AMOUNT'; params:=jsonb_build_object('max_absolute_amount',m[1]); END IF;
 END IF; END IF; END IF;
 RETURN jsonb_build_object('contract',name,'parameters',params,'recognition',CASE WHEN name IS NULL THEN 'UNKNOWN' ELSE 'EXACT_WHOLE_CANONICAL_TEXT' END);
END $$;
CREATE FUNCTION sol_action_requirements.observe(j sol_action.jobs,phase text) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE expected jsonb; rows jsonb; actual sol_action.results%ROWTYPE; item jsonb; c jsonb; txt text; verdict text; reason text; report jsonb:='[]'; checks jsonb:='[]'; allstatus text:='PASS'; idx integer:=0; stamp timestamptz; source_ok boolean:=false; result_state text:='UNKNOWN'; rowv jsonb;
BEGIN
 IF phase NOT IN ('PRE_EFFECT_ADMISSION','RESULT_VERIFICATION') THEN RAISE EXCEPTION 'INVALID_PHASE'; END IF;
 IF j.runtime_hash<>sol_action.runtime_hash() OR sol_action.runtime_hash()<>'c054604ade238ab2f7381bb01b51648e7cafcd3513c73c77d203d0b65c58f0b0' OR sol_action_bridge.runtime_hash()<>'d7ee0d9d373978aa9e05892c491f6c115710bd6ad9c29923fba42ba3c64328f7' THEN allstatus:='UNKNOWN'; checks:=checks||jsonb_build_array(jsonb_build_object('name','PINNED_RUNTIME','verdict','UNKNOWN')); END IF;
 IF sol_action.audit_job(j.job_id)->>'status' IS DISTINCT FROM 'PASS' OR j.source_sha256 IS DISTINCT FROM sol_action_requirements.sha(j.source_csv) THEN allstatus:='FAIL'; checks:=checks||jsonb_build_array(jsonb_build_object('name','SOURCE_DEFINITION_AND_JOURNAL','verdict','FAIL')); ELSE checks:=checks||jsonb_build_array(jsonb_build_object('name','SOURCE_DEFINITION_AND_JOURNAL','verdict','PASS')); END IF;
 BEGIN expected:=sol_action.oracle(j.source_csv); rows:=sol_action_requirements.records(j.source_csv); source_ok:=true; EXCEPTION WHEN OTHERS THEN allstatus:='FAIL'; END;
 checks:=checks||jsonb_build_array(jsonb_build_object('name','INDEPENDENT_SQL_SOURCE_CONTRACT','verdict',CASE WHEN source_ok THEN 'PASS' ELSE 'FAIL' END));
 SELECT * INTO actual FROM sol_action.results x WHERE x.job_id=j.job_id;
 IF actual.job_id IS NOT NULL THEN result_state:=CASE WHEN source_ok AND actual.result=expected AND actual.result_sha256=sol_action_requirements.sha(actual.result::text) AND actual.runtime_hash=j.runtime_hash THEN 'PASS' ELSE 'FAIL' END; END IF;
 IF phase='RESULT_VERIFICATION' THEN checks:=checks||jsonb_build_array(jsonb_build_object('name','EXACT_SQL_RESULT_COMPARISON','verdict',result_state)); IF result_state='FAIL' THEN allstatus:='FAIL'; ELSIF result_state='UNKNOWN' AND allstatus<>'FAIL' THEN allstatus:='UNKNOWN'; END IF; END IF;
 IF jsonb_typeof(j.requirements) IS DISTINCT FROM 'array' OR jsonb_array_length(j.requirements) NOT BETWEEN 1 AND 32 THEN RAISE EXCEPTION 'INVALID_STORED_REQUIREMENTS'; END IF;
 FOR item IN SELECT value FROM jsonb_array_elements(j.requirements) LOOP
 txt:=CASE WHEN jsonb_typeof(item)='string' THEN item#>>'{}' ELSE NULL END; c:=sol_action_requirements.contract(txt); verdict:='PASS'; reason:='CANONICAL_SOURCE_ADMISSIBLE';
 IF c->>'contract' IS NULL THEN verdict:='UNKNOWN'; reason:='UNSUPPORTED_WHOLE_REQUIREMENT';
 ELSIF NOT source_ok THEN verdict:='FAIL'; reason:='SOURCE_OUTSIDE_SQL_CONTRACT';
 ELSE
 IF c->>'contract'='ONLY_CURRENCY' AND EXISTS(SELECT 1 FROM jsonb_array_elements(rows) x WHERE x->>1<>c->'parameters'->>'currency') THEN verdict:='FAIL'; reason:='FORBIDDEN_SOURCE_CURRENCY';
 ELSIF c->>'contract'='NONNEGATIVE_RECORD_AMOUNTS' AND EXISTS(SELECT 1 FROM jsonb_array_elements(rows) x WHERE (x->>2)::numeric<0) THEN verdict:='FAIL'; reason:='NEGATIVE_SOURCE_RECORD';
 ELSIF c->>'contract'='MAX_ROWS' AND (expected->>'rows')::integer>(c->'parameters'->>'max_rows')::integer THEN verdict:='FAIL'; reason:='SOURCE_ROW_BOUND_EXCEEDED';
 ELSIF c->>'contract'='MAX_ABSOLUTE_RECORD_AMOUNT' AND EXISTS(SELECT 1 FROM jsonb_array_elements(rows) x WHERE abs((x->>2)::numeric)>(c->'parameters'->>'max_absolute_amount')::numeric) THEN verdict:='FAIL'; reason:='SOURCE_ABSOLUTE_AMOUNT_BOUND_EXCEEDED'; END IF;
 IF verdict='PASS' AND phase='RESULT_VERIFICATION' THEN verdict:=result_state; reason:=CASE WHEN result_state='PASS' THEN 'EXACT_SQL_RESULT_AND_SOURCE_CONSTRAINT_MATCH' WHEN result_state='FAIL' THEN 'RESULT_DIFFERS_FROM_SQL_ORACLE' ELSE 'NO_STORED_RESULT' END; END IF;
 END IF;
 IF verdict='FAIL' THEN allstatus:='FAIL'; ELSIF verdict='UNKNOWN' AND allstatus<>'FAIL' THEN allstatus:='UNKNOWN'; END IF;
 report:=report||jsonb_build_array(jsonb_build_object('index',idx,'text',txt,'contract',c->'contract','parameters',c->'parameters','verdict',verdict,'reason',reason)); idx:=idx+1;
 END LOOP;
 stamp:=clock_timestamp();
 RETURN jsonb_build_object('status',allstatus,'phase',phase,'requirements',report,'checks',checks,'checked_at',sol_action.utc(stamp),'expires_at',sol_action.utc(stamp+interval '60 seconds'),'source_sha256',j.source_sha256,'result_sha256',actual.result_sha256,'definition_hash',j.definition_hash,'requirements_sha256',sol_action_requirements.sha(j.requirements::text),'guard_runtime_hash',sol_action_requirements.runtime_hash(),'core_runtime_hash',sol_action.runtime_hash(),'bridge_runtime_hash',sol_action_bridge.runtime_hash(),'claim_scope',CASE WHEN phase='PRE_EFFECT_ADMISSION' THEN 'CANONICAL_SOURCE_ADMISSION_ONLY_NOT_PRODUCTION_SATISFACTION' ELSE 'CANONICAL_CONTRACTS_AND_EXACT_CSV_RESULT_ONLY' END,'semantic_truth','UNKNOWN','general_mandate','UNKNOWN','natural_language_coverage','CANONICAL_WHOLE_TEXT_ONLY','current_reuse_authorized',false,'needs_current_revalidation',true);
END $$;
CREATE FUNCTION sol_action_requirements.authorize_release(rh text) RETURNS sol_action_bridge.releases LANGUAGE plpgsql SET search_path='' AS $$
DECLARE r sol_action_bridge.releases%ROWTYPE; a sol_action_requirements.admissions%ROWTYPE;
BEGIN
 SELECT * INTO r FROM sol_action_bridge.releases x WHERE x.release_hash=rh; SELECT * INTO a FROM sol_action_requirements.admissions x WHERE x.release_hash=rh;
 IF r.release_hash IS NULL OR a.release_hash IS NULL OR a.guard_runtime_hash<>sol_action_requirements.runtime_hash() OR r.core_runtime_hash<>sol_action.runtime_hash() OR r.bridge_runtime_hash<>sol_action_bridge.runtime_hash() OR a.core_runtime_hash<>r.core_runtime_hash OR a.bridge_runtime_hash<>r.bridge_runtime_hash OR a.release_metadata_hash<>sol_action_requirements.sha(sol_action_requirements.release_metadata(r)::text) THEN RAISE EXCEPTION 'INVALID'; END IF; RETURN r;
END $$;
CREATE FUNCTION sol_action_requirements.lookup(jid uuid,target uuid,cap text) RETURNS jsonb LANGUAGE plpgsql SET search_path='' AS $$
DECLARE j sol_action.jobs%ROWTYPE; q sol_action_requirements.requests%ROWTYPE; o sol_action_requirements.outcomes%ROWTYPE;
BEGIN
 SELECT * INTO j FROM sol_action.jobs x WHERE x.job_id=jid; IF NOT FOUND THEN RAISE EXCEPTION 'INVALID'; END IF; PERFORM sol_action.authorize(j,cap);
 SELECT * INTO q FROM sol_action_requirements.requests x WHERE x.request_id=target; IF NOT FOUND THEN RETURN sol_action_bridge.dispatch('lookup_receipt',jsonb_build_object('job_id',jid,'capability',cap,'target_request_id',target)); END IF; IF (q.job_id<>jid OR q.capability_hash<>j.capability_hash) THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF sol_action_requirements.audit()->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'INVALID'; END IF;
 SELECT * INTO o FROM sol_action_requirements.outcomes x WHERE x.request_id=target; IF FOUND AND (q.request_id IS NULL OR o.job_id<>jid) THEN RAISE EXCEPTION 'INVALID'; END IF;
 RETURN jsonb_build_object('ok',true,'action','lookup_receipt','job_id',jid,'target_request_id',target,'target_action',CASE WHEN q.action='bind' THEN 'produce' ELSE q.action END,'status',CASE WHEN o.request_id IS NULL THEN 'UNKNOWN' ELSE 'HISTORICAL_NOT_CURRENT' END,'found',o.request_id IS NOT NULL,'intent_found',q.request_id IS NOT NULL,'receipt_kind',o.receipt->'receipt_kind','receipt_status',o.receipt->'status','receipt',CASE WHEN o.request_id IS NULL THEN NULL ELSE sol_action_bridge.historical(o.receipt,cap) END,'current_reuse_authorized',false,'automatic_retry',false,'worker_reexecuted',false);
END $$;
CREATE FUNCTION sol_action_requirements.api(p_action text,p_input jsonb DEFAULT '{}') RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path='' AS $$
DECLARE a text; d jsonb; jid uuid; req uuid; cap text; j sol_action.jobs%ROWTYPE; rel sol_action_bridge.releases%ROWTYPE; b sol_action_bridge.bindings%ROWTYPE; q sol_action_requirements.requests%ROWTYPE; prior sol_action_requirements.requests%ROWTYPE; o sol_action_requirements.outcomes%ROWTYPE; base jsonb; guard jsonb; r jsonb; ph text; bh text; k text; stage text; deadline timestamptz; utcday timestamptz;
BEGIN
 IF jsonb_typeof(p_input) IS DISTINCT FROM 'object' OR octet_length(p_input::text)>20000 THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF p_action='health' THEN PERFORM sol_action.keys(p_input,ARRAY[]::text[],ARRAY[]::text[]); RETURN jsonb_build_object('ok',true,'module','SOL-Action-Requirements','version','0.1.0','runtime_hash',sol_action_requirements.runtime_hash(),'canonical_whole_text_only',true,'unknown_blocks_effect',true,'legacy_direct_paths_enforced',false,'general_mandate','UNKNOWN','current_reuse_authorized',false); END IF;
 IF p_action='execute' THEN PERFORM sol_action.keys(p_input,ARRAY['core_action','core_input'],ARRAY['core_action','core_input']); a:=sol_action.text_field(p_input,'core_action',1,20); IF a NOT IN ('verify','complete') THEN RAISE EXCEPTION 'INVALID'; END IF; d:=p_input->'core_input'; PERFORM sol_action.keys(d,ARRAY['job_id','capability','request_id','expected_step_id'],ARRAY['job_id','capability','request_id','expected_step_id']); IF sol_action.text_field(d,'expected_step_id',1,40)<>a THEN RAISE EXCEPTION 'INVALID'; END IF;
 ELSIF p_action='bind' THEN a:='bind'; d:=p_input; PERFORM sol_action.keys(d,ARRAY['job_id','capability','production_request_id','release_hash','manifest_hash','source_commit','self_hash','bridge_token'],ARRAY['job_id','capability','production_request_id','release_hash','manifest_hash','source_commit','self_hash','bridge_token']);
 ELSIF p_action IN ('status','lookup_receipt') THEN a:=p_action; d:=p_input; PERFORM sol_action.keys(d,CASE WHEN a='status' THEN ARRAY['job_id','capability'] ELSE ARRAY['job_id','capability','target_request_id'] END,CASE WHEN a='status' THEN ARRAY['job_id','capability'] ELSE ARRAY['job_id','capability','target_request_id'] END);
 ELSE RAISE EXCEPTION 'INVALID'; END IF;
 jid:=sol_action.text_field(d,'job_id',36,36)::uuid; cap:=sol_action.text_field(d,'capability',64,64); IF d->>'job_id'<>jid::text OR cap !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID'; END IF;
 SELECT * INTO j FROM sol_action.jobs x WHERE x.job_id=jid; IF NOT FOUND THEN RAISE EXCEPTION 'INVALID'; END IF; PERFORM sol_action.authorize(j,cap);
 IF a='lookup_receipt' THEN req:=sol_action.text_field(d,'target_request_id',36,36)::uuid; IF d->>'target_request_id'<>req::text THEN RAISE EXCEPTION 'INVALID'; END IF; RETURN sol_action_requirements.lookup(jid,req,cap); END IF;
 IF a='status' THEN base:=sol_action.dispatch('status',d); IF base->'ok' IS DISTINCT FROM 'true'::jsonb OR base->'requirements' IS DISTINCT FROM j.requirements OR base->>'source_sha256' IS DISTINCT FROM j.source_sha256 THEN RAISE EXCEPTION 'INVALID'; END IF; guard:=sol_action_requirements.observe(j,CASE WHEN EXISTS(SELECT 1 FROM sol_action.results x WHERE x.job_id=jid) THEN 'RESULT_VERIFICATION' ELSE 'PRE_EFFECT_ADMISSION' END); RETURN sol_action_bridge.redact(base,cap)||jsonb_build_object('requirements_guard',guard,'current_reuse_authorized',false,'needs_current_revalidation',true,'legacy_direct_paths_enforced',false); END IF;
 req:=sol_action.text_field(d,CASE WHEN a='bind' THEN 'production_request_id' ELSE 'request_id' END,36,36)::uuid; IF d->>(CASE WHEN a='bind' THEN 'production_request_id' ELSE 'request_id' END)<>req::text THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF a='bind' THEN
 FOREACH k IN ARRAY ARRAY['release_hash','manifest_hash','self_hash','bridge_token'] LOOP IF sol_action.text_field(d,k,64,64) !~ '^[0-9a-f]{64}$' THEN RAISE EXCEPTION 'INVALID'; END IF; END LOOP; IF sol_action.text_field(d,'source_commit',40,40) !~ '^[0-9a-f]{40}$' THEN RAISE EXCEPTION 'INVALID'; END IF;
 rel:=sol_action_requirements.authorize_release(d->>'release_hash'); IF NOT sol_action_bridge.token_matches(d->>'bridge_token',rel.token_sha256) OR rel.manifest_hash<>d->>'manifest_hash' OR rel.source_commit<>d->>'source_commit' OR rel.source_files->>'api/job.py'<>d->>'self_hash' THEN RAISE EXCEPTION 'INVALID'; END IF;
 ELSE SELECT * INTO b FROM sol_action_bridge.bindings x WHERE x.job_id=jid; IF NOT FOUND THEN RAISE EXCEPTION 'INVALID'; END IF; rel:=sol_action_requirements.authorize_release(b.release_hash); END IF;
 PERFORM pg_advisory_xact_lock(hashtextextended('sol_action:job:'||jid::text,0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol_action_bridge:request:'||req::text,0)); PERFORM pg_advisory_xact_lock(hashtextextended('sol_action_requirements:journal',0));
 SELECT * INTO j FROM sol_action.jobs x WHERE x.job_id=jid; PERFORM sol_action.authorize(j,cap); PERFORM sol_action_requirements.authorize_release(rel.release_hash);
 ph:=sol_action_requirements.sha(jsonb_build_object('action',a,'input',d-'capability'-'bridge_token')::text); bh:=sol_action_requirements.sha(encode(j.capability_hash,'hex')||':'||ph||':'||jid::text||':'||req::text||':'||a);
 SELECT * INTO q FROM sol_action_requirements.requests x WHERE x.request_id=req;
 IF FOUND THEN IF q.job_id<>jid OR q.action<>a OR q.payload_hash<>ph OR q.binding_hash<>bh OR q.guard_runtime_hash<>sol_action_requirements.runtime_hash() THEN RAISE EXCEPTION 'INVALID'; END IF; r:=sol_action_requirements.lookup(jid,req,cap); IF r->'found'='true'::jsonb THEN RETURN (r->'receipt')||jsonb_build_object('deduplicated',true); END IF; RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','action',CASE WHEN a='bind' THEN 'produce' ELSE a END,'job_id',jid,'request_id',req,'pending',true,'automatic_retry',false,'current_reuse_authorized',false); END IF;
 SELECT * INTO prior FROM sol_action_requirements.requests x WHERE x.job_id=jid AND ((a='bind' AND x.action='bind') OR NOT EXISTS(SELECT 1 FROM sol_action_requirements.outcomes z WHERE z.request_id=x.request_id)) ORDER BY x.created_at LIMIT 1;
 IF FOUND THEN RETURN jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','action',CASE WHEN a='bind' THEN 'produce' ELSE a END,'job_id',jid,'request_id',req,'original_request_id',prior.request_id,'pending',true,'automatic_retry',false,'current_reuse_authorized',false); END IF;
 IF EXISTS(SELECT 1 FROM sol_action.intents x WHERE x.request_id=req) OR EXISTS(SELECT 1 FROM sol_action.outcomes x WHERE x.request_id=req) OR EXISTS(SELECT 1 FROM sol_action_bridge.refusals x WHERE x.request_id=req) OR EXISTS(SELECT 1 FROM sol_action_bridge.recovery_outcomes x WHERE x.request_id=req) OR EXISTS(SELECT 1 FROM sol_creation_guard.requests x WHERE x.request_id=req) THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF a='bind' AND (EXISTS(SELECT 1 FROM sol_action_bridge.bindings x WHERE x.job_id=jid) OR EXISTS(SELECT 1 FROM sol_action.intents x WHERE x.job_id=jid AND x.action='begin') OR EXISTS(SELECT 1 FROM sol_action.results x WHERE x.job_id=jid)) THEN RAISE EXCEPTION 'INVALID'; END IF;
 IF sol_action_requirements.audit()->'valid' IS DISTINCT FROM 'true'::jsonb THEN RAISE EXCEPTION 'INVALID'; END IF;
 utcday:=date_trunc('day',clock_timestamp() AT TIME ZONE 'UTC') AT TIME ZONE 'UTC'; IF (SELECT count(*) FROM sol_action_requirements.requests x WHERE x.job_id=jid)>=64 OR (SELECT count(*) FROM sol_action_requirements.requests x WHERE x.created_at>=utcday)>=2048 THEN RETURN jsonb_build_object('ok',false,'status','REJECTED','action',CASE WHEN a='bind' THEN 'produce' ELSE a END,'job_id',jid,'request_id',req,'error','REQUIREMENTS_STORAGE_LIMIT','admission_recorded',false,'automatic_retry',false,'current_reuse_authorized',false); END IF;
 base:=sol_action.dispatch('status',jsonb_build_object('job_id',jid,'capability',cap)); IF base->'ok' IS DISTINCT FROM 'true'::jsonb OR base->'requirements' IS DISTINCT FROM j.requirements OR base->>'mandate' IS DISTINCT FROM j.mandate OR base->>'source_csv' IS DISTINCT FROM j.source_csv OR base->>'source_sha256' IS DISTINCT FROM j.source_sha256 THEN RAISE EXCEPTION 'INVALID'; END IF;
 stage:=CASE WHEN a='bind' THEN 'PRE_EFFECT_ADMISSION' ELSE 'RESULT_VERIFICATION' END; guard:=sol_action_requirements.observe(j,stage); deadline:=(guard->>'expires_at')::timestamptz;
 INSERT INTO sol_action_requirements.requests(request_id,job_id,action,payload_hash,capability_hash,binding_hash,release_hash,guard_runtime_hash,core_runtime_hash,bridge_runtime_hash) VALUES(req,jid,a,ph,j.capability_hash,bh,rel.release_hash,sol_action_requirements.runtime_hash(),sol_action.runtime_hash(),sol_action_bridge.runtime_hash());
 PERFORM sol_action_requirements.append_event(jid,req,'reservation',jsonb_build_object('payload_hash',ph,'binding_hash',bh,'release_hash',rel.release_hash));
 IF guard->>'status' IS DISTINCT FROM 'PASS' THEN
 r:=jsonb_build_object('ok',false,'status','REJECTED','action',CASE WHEN a='bind' THEN 'produce' ELSE a END,'job_id',jid,'request_id',req,'production_request_id',CASE WHEN a='bind' THEN req ELSE NULL END,'error','REQUIREMENTS_'||coalesce(guard->>'status','UNKNOWN'),'requirements_guard',guard,'receipt_kind','REQUIREMENTS_GUARD_REFUSAL','terminal',true,'durable_refusal',true,'effect_scope',CASE WHEN a='bind' THEN 'REQUIREMENTS_ADMISSION_BEFORE_BRIDGE_BIND_ONLY' ELSE 'REQUIREMENTS_VERIFICATION_BEFORE_CORE_DISPATCH_ONLY' END,'business_effect',CASE WHEN a='bind' THEN 'NO_BEGIN_OR_WORKER_STARTED_BY_THIS_CALL' ELSE 'NO_CORE_VERIFY_OR_COMPLETE_BY_THIS_CALL' END,'receipt_recording_effect','APPEND_ONLY_REQUIREMENTS_GUARD_RECEIPT_RECORDED','worker_reexecuted',false,'automatic_retry',false,'current_reuse_authorized',false);
 ELSE
 IF clock_timestamp()>=deadline THEN RAISE EXCEPTION 'EXPIRED_BEFORE_DISPATCH'; END IF;
 IF a='bind' THEN
 r:=sol_action_bridge.dispatch('bind',d);
 IF r->'ok'='true'::jsonb AND r->'binding_granted'='true'::jsonb AND r->>'job_id'=jid::text AND r->>'production_request_id'=req::text AND r->'binding_and_begin_atomic'='true'::jsonb AND r->'begin_receipt'->'begin_granted'='true'::jsonb AND EXISTS(SELECT 1 FROM sol_action_bridge.bindings x WHERE x.job_id=jid AND x.production_request_id=req AND x.release_hash=rel.release_hash) THEN r:=r||jsonb_build_object('request_id',req,'requirements_guard',guard,'requirements_and_begin_atomic',true);
 ELSE r:=jsonb_build_object('ok',false,'status','OUTCOME_UNKNOWN','action','produce','job_id',jid,'request_id',req,'production_request_id',req,'pending',true,'error','BIND_NOT_NEWLY_GRANTED','requirements_guard',guard,'automatic_retry',false,'current_reuse_authorized',false); END IF;
 ELSE r:=sol_action_bridge.dispatch('execute',jsonb_build_object('core_action',a,'core_input',d)); IF r->>'job_id' IS DISTINCT FROM jid::text OR r->>'request_id' IS DISTINCT FROM req::text OR r->>'action' IS DISTINCT FROM a THEN RAISE EXCEPTION 'UNCORRELATED_CORE_RESPONSE'; END IF; r:=r||jsonb_build_object('requirements_guard',guard); END IF;
 IF clock_timestamp()>=deadline THEN RAISE EXCEPTION 'EXPIRED_AFTER_DISPATCH'; END IF;
 END IF;
 r:=r||jsonb_build_object('requirements_release_hash',rel.release_hash,'requirements_guard_runtime_hash',sol_action_requirements.runtime_hash()); INSERT INTO sol_action_requirements.outcomes(request_id,job_id,receipt) VALUES(req,jid,r); PERFORM sol_action_requirements.append_event(jid,req,'outcome',jsonb_build_object('receipt_sha256',sol_action_requirements.sha(r::text))); IF guard->>'status'='PASS' AND clock_timestamp()>=deadline THEN RAISE EXCEPTION 'EXPIRED_BEFORE_RETURN'; END IF; RETURN r;
EXCEPTION WHEN OTHERS THEN RETURN jsonb_build_object('ok',false,'status','REJECTED','error','NOT_AUTHORIZED_OR_INVALID_REFERENCE','automatic_retry',false,'current_reuse_authorized',false);
END $$;
CREATE FUNCTION public.sol_action_requirements_api(p_action text,p_input jsonb DEFAULT '{}') RETURNS jsonb LANGUAGE sql SECURITY INVOKER SET search_path='' AS $$ SELECT sol_action_requirements.api(p_action,p_input) $$;
REVOKE ALL ON ALL FUNCTIONS IN SCHEMA sol_action_requirements FROM PUBLIC,anon,authenticated,service_role;
REVOKE ALL ON FUNCTION public.sol_action_requirements_api(text,jsonb) FROM PUBLIC,anon,authenticated,service_role;
GRANT USAGE ON SCHEMA sol_action_requirements TO anon,authenticated;
GRANT EXECUTE ON FUNCTION sol_action_requirements.api(text,jsonb) TO anon,authenticated;
GRANT EXECUTE ON FUNCTION public.sol_action_requirements_api(text,jsonb) TO anon,authenticated;
COMMENT ON SCHEMA sol_action_requirements IS 'Exact canonical requirement source admission before guarded begin and fresh result contracts before verify/complete. UNKNOWN blocks this path; legacy direct APIs remain outside it. General semantic mandate UNKNOWN; append-only is not WORM.';
COMMIT;
