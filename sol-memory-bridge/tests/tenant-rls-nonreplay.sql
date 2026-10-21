-- SOL Memory Bridge — owner isolation / non-replay smoke.
-- Run in Supabase SQL editor with privileged testing access.
-- ALL synthetic rows are inside BEGIN/ROLLBACK. Does not provision an Auth user.
-- This is a JWT-claims simulation, NOT a real browser Auth E2E test.
BEGIN;
SELECT set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true),
       set_config('request.jwt.claims','{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","is_anonymous":false}',true);
SET LOCAL ROLE authenticated;
INSERT INTO public.sol_memory_bridge_events(event_id,event_type,claim_key,body,source_kind,idempotency_key)
VALUES('aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','OBSERVATION','_e2e_provenance_r1','synthetic A','TEST','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb');
INSERT INTO public.sol_memory_bridge_events(event_type,claim_key,body,source_kind,relates_to,idempotency_key)
VALUES('CORRECTION','_e2e_provenance_r1','synthetic A corrected','TEST','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa','cccccccc-cccc-4ccc-8ccc-cccccccccccc');
DO $$
DECLARE v jsonb; n integer;
BEGIN
  SELECT public.sol_memory_bridge_verify() INTO v;
  IF v->>'ok' <> 'true' OR (v->>'checked')::integer < 2 THEN
    RAISE EXCEPTION 'failed valid owner chain: %',v;
  END IF;
  SELECT count(*) INTO n FROM public.sol_memory_bridge_events WHERE claim_key='_e2e_provenance_r1';
  IF n <> 2 THEN RAISE EXCEPTION 'expected two owner A records'; END IF;
END $$;
DO $$
BEGIN
  INSERT INTO public.sol_memory_bridge_events(event_type,claim_key,body,source_kind,idempotency_key)
  VALUES('NOTE','_e2e_provenance_r1','duplicate UUID','TEST','bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb');
  RAISE EXCEPTION 'DUPLICATE_NOT_REJECTED';
EXCEPTION WHEN unique_violation THEN NULL;
END $$;
SELECT set_config('request.jwt.claim.sub','22222222-2222-4222-8222-222222222222',true),
       set_config('request.jwt.claims','{"sub":"22222222-2222-4222-8222-222222222222","role":"authenticated","is_anonymous":false}',true);
DO $$
DECLARE n integer;
BEGIN
  SELECT count(*) INTO n FROM public.sol_memory_bridge_events WHERE claim_key='_e2e_provenance_r1';
  IF n <> 0 THEN RAISE EXCEPTION 'TENANT_LEAK_FOUND'; END IF;
END $$;
DO $$
BEGIN
  INSERT INTO public.sol_memory_bridge_events(event_type,claim_key,body,source_kind,relates_to)
  VALUES('CORRECTION','_e2e_provenance_r1','wrong owner','TEST','aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa');
  RAISE EXCEPTION 'CROSS_OWNER_REFERENCE_ACCEPTED';
EXCEPTION WHEN foreign_key_violation THEN NULL;
END $$;
ROLLBACK;
SELECT count(*) AS synthetic_rows_after_rollback
FROM public.sol_memory_bridge_events WHERE claim_key='_e2e_provenance_r1';
-- Expected: 0, and no DO exception.
