/* SOL Memory Bridge — verified write protocol, independent from the UI.
 * No service role, no automatic promotion, no claim of external truth.
 */
(function(root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.SolBridgeProtocol = api;
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';
  const FIELDS = ['event_type','claim_key','body','source_uri','source_kind','asserted_evidence','relates_to'];

  function samePayload(expected, row) {
    return FIELDS.every(field => (expected[field] ?? null) === (row?.[field] ?? null));
  }

  function validateReadback(payload, rows, owner, integrity) {
    if (!Array.isArray(rows) || rows.length !== 1) throw new Error('READBACK_ABSENT_OR_AMBIGUOUS');
    const row = rows[0];
    if (!samePayload(payload,row) || row.owner_id !== owner ||
        row.idempotency_key !== payload.idempotency_key ||
        !Number.isSafeInteger(Number(row.seq)) || Number(row.seq) < 1 ||
        !/^[0-9a-f]{64}$/.test(row.event_hash || '')) {
      throw new Error('READBACK_MISMATCH');
    }
    if (!integrity || integrity.ok !== true ||
        !Number.isSafeInteger(Number(integrity.checked)) || Number(integrity.checked) < 1 ||
        !/^[0-9a-f]{64}$/.test(integrity.head_hash || '')) {
      throw new Error('CHAIN_NOT_VERIFIED');
    }
    return row;
  }

  async function sha256Hex(text) {
    const bytes = new TextEncoder().encode(text);
    const hashed = await crypto.subtle.digest('SHA-256',bytes);
    return [...new Uint8Array(hashed)].map(b=>b.toString(16).padStart(2,'0')).join('');
  }

  /*
   * readByKey(key): independently GET the exact row from PostgREST.
   * write(data): POST with the SAME key.
   * verify(): RPC server hash replay.
   * intentStore: {get,set,clear}; persist only owner, key, fingerprint,
   *              NEVER store passwords, JWTs or plaintext event bodies.
   * A write timeout is AMBIGUOUS; reconciliation precedes any retry.
   */
  async function appendVerified({payload, owner, intentStore, readByKey, write, verify, uuid, fingerprint}) {
    if (!owner || !payload || !fingerprint || !intentStore || !readByKey || !write || !verify || !uuid)
      throw new Error('MISSING_REQUIRED_INPUT');
    const pending = intentStore.get();
    if (pending && (pending.owner !== owner || pending.fingerprint !== fingerprint))
      throw new Error('UNRESOLVED_PREVIOUS_INTENT');
    const key = pending ? pending.id : uuid();
    if (!/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(key))
      throw new Error('INVALID_INTENT_ID');
    intentStore.set({owner,id:key,fingerprint});
    const expected = {...payload,idempotency_key:key};
    let rows = await readByKey(key);
    if (!Array.isArray(rows)) throw new Error('READBACK_INVALID');
    if (rows.length === 0) {
      try {
        await write(expected);
      } catch (error) {
        // A lost acknowledgement is not a proof that the write failed.
        // Re-read by the same idempotency key; never generate a second one.
        rows = await readByKey(key);
        if (!Array.isArray(rows) || rows.length === 0) throw new Error('WRITE_UNCONFIRMED_RETRY_SAME_INTENT');
      }
      if (rows.length === 0) rows = await readByKey(key);
    }
    const chain = await verify();
    const accepted = validateReadback(expected,rows,owner,chain);
    intentStore.clear();
    return {event_id:accepted.event_id,event_hash:accepted.event_hash,
            seq:accepted.seq,integrity:chain,duplicate_prevented:!!pending};
  }

  return {FIELDS,samePayload,validateReadback,sha256Hex,appendVerified};
});
