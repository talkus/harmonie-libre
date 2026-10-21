-- Isolated migration; NO import of historical private conversations.
-- The source code database already includes these objects; this file reproduces that schema.
create table if not exists public.sol_memory_bridge_events (
seq bigint generated always as identity primary key,
event_id uuid not null default gen_random_uuid() unique,
owner_id uuid not null default auth.uid(),
event_type text not null check (event_type in ('OBSERVATION','CORRECTION','RETRACTION','VERIFICATION','DECISION','AUTHORIZATION','REVOCATION','NOTE')),
claim_key text not null check (char_length(claim_key) between 1 and 120),
body text not null check (char_length(body) between 1 and 12000),
source_uri text,
source_kind text not null default 'USER_ENTRY' check (source_kind in ('USER_ENTRY','PRIMARY','MIRROR','DERIVED','TEST')),
asserted_evidence text not null default 'UNVERIFIED' check (asserted_evidence in ('UNVERIFIED','SOURCE_LINKED','REVIEWED_BY_AUTHOR')),
relates_to uuid,
idempotency_key uuid,
recorded_at timestamptz not null default clock_timestamp(),
previous_hash text not null default repeat('0',64),
event_hash text not null default repeat('0',64),
constraint sol_mem_source_uri_size check (source_uri is null or char_length(source_uri)<=2048),
constraint sol_mem_idempotency unique(owner_id,idempotency_key),
constraint sol_mem_hash_format check (previous_hash ~ '^[0-9a-f]{64}$' and event_hash ~ '^[0-9a-f]{64}$')
);
create index if not exists sol_mem_owner_seq on public.sol_memory_bridge_events(owner_id,seq desc);
create index if not exists sol_mem_owner_claim on public.sol_memory_bridge_events(owner_id,claim_key,seq desc);
alter table public.sol_memory_bridge_events enable row level security;
revoke all on public.sol_memory_bridge_events from public,anon,authenticated;
grant select,insert on public.sol_memory_bridge_events to authenticated;
drop policy if exists sol_mem_owner_select on public.sol_memory_bridge_events;
create policy sol_mem_owner_select on public.sol_memory_bridge_events
for select to authenticated using ((select auth.uid())=owner_id and coalesce((select auth.jwt())->>'is_anonymous','false')<>'true');
drop policy if exists sol_mem_owner_insert on public.sol_memory_bridge_events;
create policy sol_mem_owner_insert on public.sol_memory_bridge_events
for insert to authenticated with check ((select auth.uid())=owner_id and coalesce((select auth.jwt())->>'is_anonymous','false')<>'true');

CREATE OR REPLACE FUNCTION public.sol_memory_bridge_guard()
 RETURNS trigger
 LANGUAGE plpgsql
 SET search_path TO 'pg_catalog', 'public', 'extensions'
AS $function$
declare
  previous text;
  matched uuid;
  identity uuid;
begin
  if tg_op <> 'INSERT' then
    raise exception 'append-only: historical events may not be changed' using errcode='42501';
  end if;
  identity := auth.uid();
  if identity is null or identity <> new.owner_id then
    raise exception 'owner token required' using errcode='42501';
  end if;
  if coalesce(auth.jwt()->>'is_anonymous','false')='true' then
    raise exception 'anonymous sign-in is not authorized' using errcode='42501';
  end if;
  -- serialize appends per owner to form a deterministic hash chain
  perform pg_advisory_xact_lock(hashtextextended(new.owner_id::text,42));
  if new.relates_to is not null then
    select event_id into matched from public.sol_memory_bridge_events
    where owner_id=new.owner_id and event_id=new.relates_to
       and claim_key=new.claim_key;
    if matched is null then
      raise exception 'cross-owner, missing, or different-claim reference forbidden' using errcode='23503';
    end if;
  elsif new.event_type in ('CORRECTION','RETRACTION','REVOCATION') then
    raise exception 'correction, retraction or revocation requires relates_to' using errcode='23502';
  end if;
  select event_hash into previous from public.sol_memory_bridge_events
    where owner_id=new.owner_id order by seq desc limit 1;
  new.previous_hash:=coalesce(previous,repeat('0',64));
  new.recorded_at:=clock_timestamp();
  new.event_hash:=encode(extensions.digest(convert_to(
    new.previous_hash || '|' ||
    jsonb_build_object('seq',new.seq,'event_id',new.event_id,'owner_id',new.owner_id,
    'event_type',new.event_type,'claim_key',new.claim_key,'body',new.body,
    'source_uri',new.source_uri,'source_kind',new.source_kind,
    'asserted_evidence',new.asserted_evidence,'relates_to',new.relates_to,
    'idempotency_key',new.idempotency_key,'recorded_at',new.recorded_at)::text,
    'UTF8'),'sha256'),'hex');
  return new;
end
$function$;

CREATE OR REPLACE FUNCTION public.sol_memory_bridge_verify()
 RETURNS jsonb
 LANGUAGE plpgsql
 SET search_path TO 'pg_catalog', 'public', 'extensions', 'auth'
AS $function$
declare
  e public.sol_memory_bridge_events%rowtype;
  owner_uuid uuid := auth.uid();
  expected_prev text := repeat('0',64);
  computed text;
  inspected integer := 0;
begin
  if owner_uuid is null or coalesce(auth.jwt()->>'is_anonymous','false')='true' then
    raise exception 'authenticated non-anonymous user required' using errcode='42501';
  end if;
  for e in select * from public.sol_memory_bridge_events
    where owner_id = owner_uuid order by seq asc
  loop
    computed := encode(extensions.digest(convert_to(
      expected_prev || '|' ||
      jsonb_build_object('seq',e.seq,'event_id',e.event_id,'owner_id',e.owner_id,
      'event_type',e.event_type,'claim_key',e.claim_key,'body',e.body,
      'source_uri',e.source_uri,'source_kind',e.source_kind,
      'asserted_evidence',e.asserted_evidence,'relates_to',e.relates_to,
      'idempotency_key',e.idempotency_key,'recorded_at',e.recorded_at)::text,
      'UTF8'),'sha256'),'hex');
    if e.previous_hash <> expected_prev or e.event_hash <> computed then
      return jsonb_build_object('ok',false,'first_bad_seq',e.seq,'checked',inspected);
    end if;
    inspected:=inspected+1;
    expected_prev := e.event_hash;
  end loop;
  return jsonb_build_object('ok',true,'checked',inspected,'head_hash',expected_prev,
    'note','Integrity of stored chain, not proof of claim truth or authorization');
end
$function$;


revoke all on function public.sol_memory_bridge_guard() from public,anon,authenticated;
drop trigger if exists sol_mem_append_guard on public.sol_memory_bridge_events;
create trigger sol_mem_append_guard before insert or update or delete on public.sol_memory_bridge_events
for each row execute function public.sol_memory_bridge_guard();
revoke all on function public.sol_memory_bridge_verify() from public,anon;
grant execute on function public.sol_memory_bridge_verify() to authenticated;
comment on table public.sol_memory_bridge_events is
'Owner-RLS append-only hash-chain journal. Hash is not a signature, not truth verification, not production promotion.';
