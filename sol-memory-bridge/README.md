# Sol Memory Bridge — auditable continuity memory (prototype)

**Status 2026-10-21:** database isolated on existing Supabase project and transactionally tested; Railway project creation failed with **"Deploys have been paused temporarily"**. GitHub changes are on a review branch only. **NOT LIVE**, **NOT CANON**, **NOT MIGRATED**. No credentials, private memories, or user tokens are committed.

## Five responsibilities
- **Supabase**: Auth JWT/RLS, append-only trigger, per-owner SHA-256 chain and integrity verifier. Existing continuity data and SOL tables are untouched.
- **Railway**: intended Bun Function hosting the web UI and /healthz; deploy currently blocked. Browser speaks directly to Supabase Auth and Data API via HTTPS.
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
4. When Railway resumes deploying, create a project + Function using the entire railway-function.ts, then generate a service domain.
5. Verify GET /healthz, then log in as a real user and perform observation -> correction -> verify.
6. Test denial of UPDATE/DELETE and cross-user access before declaring any production readiness.

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
- Railway deployed / actual browser sign-in / user E2E: BLOCKED or NOT TESTED.
- CI, external anchors, independent review: NOT DONE.

Never conflate retrieved, reconstructed, tested, adopted and deployed.