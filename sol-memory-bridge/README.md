# Sol Memory Bridge — auditable continuity memory (prototype)

**Status 2026-10-21:** database isolated on existing Supabase project and transactionally tested; Railway project creation failed with **"Deploys have been paused temporarily"**, followed by **"Access denied to this workspace"**. GitHub changes are on a review branch only. **SUPABASE EDGE UI LIVE (HTTP 200)**, **RAILWAY NOT DEPLOYED**, **NOT CANON**, **NOT MIGRATED**. No credentials, private memories, or user tokens are committed.

## Five responsibilities
- **Supabase**: Auth JWT/RLS, append-only trigger, per-owner SHA-256 chain and integrity verifier. Existing continuity data and SOL tables are untouched.
- **Railway**: intended Bun Function; project creation blocked by workspace permissions; not deployed.
- **Supabase Edge fallback**: separate public UI sol-memory-bridge v1 ACTIVE. Its landing page and /healthz each returned HTTP 200 on 2026-10-21; this is NOT a user-authenticated database write test. Browser speaks directly to Supabase Auth and Data API over HTTPS.
- **GitHub**: reviewed source on a branch (not merged).
- **Notion**: private operational runbook, a mirror not independent corroboration.
- **Stele**: decision and blocked deployment task within the private Alignement project.

## Data contract
Table: public.sol_memory_bridge_events.
- Every event belongs to owner_id=auth.uid(); anonymous sessions and unauthenticated users are rejected.
- Types: OBSERVATION, CORRECTION, RETRACTION, VERIFICATION, DECISION, AUTHORIZATION, REVOCATION, NOTE.
- claim_key groups assertions. A CORRECTION/RETRACTION/REVOCATION must reference (relates_to) an earlier same-owner, same-claim event.
- source_uri, source_kind and asserted_evidence are user assertions, never independent certification.
- previous_hash and event_hash are server-built; sol_memory_bridge_verify() replays the owner chain.
- Integrity is not truth, authenticity, an external signature or authority to act. A privileged admin could remove or rewrite the tail.

## Reproduction / deploy
1. Review migrations/001_sol_memory_bridge.sql before applying to a fresh staging project.
2. Run tests/smoke.sql with the SQL editor; expect verify ok=true checked=2 and zero persisted test events after rollback.
3. Configure Supabase Auth (email + password; may require email verification). Do not provide a service role key.
4. Working fallback UI: https://jljelwrblfitvjbmrykx.supabase.co/functions/v1/sol-memory-bridge (source: supabase-edge/index.ts).
5. When Railway permissions are granted, create a project + Function using railway-function.ts, then generate its domain.
6. GET /healthz already returned 200 on the Edge fallback; still log in as a real user and perform observation -> correction -> verify.
7. Test denial of UPDATE/DELETE and cross-user access before declaring any production readiness.

## Limits
- No bulk import from historical archives and no bidirectional live sync with Notion, Stele, GitHub or ChatGPT native memory.
- The web UI keeps the user session token in sessionStorage for the tab lifetime; XSS would be sensitive. No third-party JS is loaded; dynamic text uses textContent.
- UI retrieves a maximum of 200 most recent events. Export is not a full backup. Chain verification scans all owner records.
- The public publishable Supabase key is meant for clients; no secret server key is present.
- SQL integrity cannot detect a deliberately deleted tail without an externally anchored head.
- /healthz is UI liveness, NOT database readiness.
- The system is a proposed complementary journal, not a replacement for the canon C or SOL release process.

## Release gates
- Isolated DB objects, two-event transactional correction/verify, owner RLS, readonly anon: PASS.
- Notion guide and Stele decision/task: CREATED.
- Supabase Edge deployed and HTTP GET landing/healthz: PASS.
- Railway deployed: BLOCKED (permissions); actual browser sign-in / user E2E: NOT TESTED.
- CI, external anchors, independent review: NOT DONE.

Never conflate retrieved, reconstructed, tested, adopted and deployed.