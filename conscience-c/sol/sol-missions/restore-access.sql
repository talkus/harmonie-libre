-- Prepared only. Review the installed code and mandate before an explicit restoration.
BEGIN;
GRANT USAGE ON SCHEMA sol_missions TO anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION sol_missions.api(text,jsonb,text) TO anon,authenticated,service_role;
GRANT EXECUTE ON FUNCTION public.sol_missions_api(text,jsonb,text) TO anon,authenticated,service_role;
COMMIT;
