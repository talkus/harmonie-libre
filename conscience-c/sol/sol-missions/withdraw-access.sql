-- Prepared only. Operator decision required to execute; preserve every table and receipt.
BEGIN;
REVOKE EXECUTE ON FUNCTION public.sol_missions_api(text,jsonb,text) FROM PUBLIC,anon,authenticated,service_role;
REVOKE EXECUTE ON FUNCTION sol_missions.api(text,jsonb,text) FROM PUBLIC,anon,authenticated,service_role;
REVOKE USAGE ON SCHEMA sol_missions FROM PUBLIC,anon,authenticated,service_role;
COMMIT;
