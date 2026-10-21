-- Transactional smoke test; all new test rows ROLLBACK.
begin;
select set_config('request.jwt.claim.sub','11111111-1111-4111-8111-111111111111',true),
       set_config('request.jwt.claims','{"sub":"11111111-1111-4111-8111-111111111111","role":"authenticated","is_anonymous":false}',true);
set local role authenticated;
insert into public.sol_memory_bridge_events(event_type,claim_key,body,source_kind)
values('OBSERVATION','_smoke_memory_bridge','smoke: original','TEST');
insert into public.sol_memory_bridge_events(event_type,claim_key,body,source_kind,relates_to)
select 'CORRECTION',claim_key,'smoke: corrected','TEST',event_id
from public.sol_memory_bridge_events
where owner_id=auth.uid() and claim_key='_smoke_memory_bridge' and event_type='OBSERVATION';
select public.sol_memory_bridge_verify() as expected_ok_true_checked_2;
rollback;
select has_table_privilege('anon','public.sol_memory_bridge_events','SELECT') as anon_read_must_be_false,
has_table_privilege('authenticated','public.sol_memory_bridge_events','UPDATE') as update_must_be_false,
has_table_privilege('authenticated','public.sol_memory_bridge_events','DELETE') as delete_must_be_false,
(select count(*) from public.sol_memory_bridge_events) as persisted_test_rows_must_be_0;
-- NOT TESTED: browser signup/login, cross-user isolation, actual Railway /healthz.
