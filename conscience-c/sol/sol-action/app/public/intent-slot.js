(function (root) {
  'use strict';
  const JOB_KEY = 'sol-action-session-v1';
  const MISSION_KEY = 'sol-action-mission-session-v1';
  const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const HASH = /^[a-f0-9]{64}$/;
  const object = value => Boolean(value && typeof value === 'object' && !Array.isArray(value));
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (object(value)) return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
    return JSON.stringify(value);
  }
  const same = (a, b) => canonical(a) === canonical(b);
  function available() { return Boolean(root.navigator && root.navigator.locks && typeof root.navigator.locks.request === 'function'); }
  function unavailable() { return new Error('Ce navigateur ne fournit pas le verrou entre onglets. Les lectures restent possibles ; aucune nouvelle action ne sera envoyée.'); }
  async function withKeys(keys, callback) {
    if (!available()) throw unavailable();
    const ordered = Array.from(new Set(keys)).sort();
    if (!ordered.length || ordered.some(key => ![JOB_KEY, MISSION_KEY].includes(key))) throw new Error('Emplacement de reprise inconnu.');
    function acquire(index) {
      if (index === ordered.length) return callback();
      return root.navigator.locks.request('sol-intent-slot:' + ordered[index], {mode: 'exclusive'}, lock => {
        if (!lock) throw unavailable();
        return acquire(index + 1);
      });
    }
    return acquire(0);
  }
  function read(key, validate) {
    let raw;
    try { raw = root.localStorage.getItem(key); }
    catch (_) { throw new Error('La reprise locale est indisponible. Aucune nouvelle action ne sera envoyée.'); }
    if (raw === null) return null;
    let value;
    try { value = JSON.parse(raw); }
    catch (_) { throw new Error('La reprise locale est illisible. Ses octets restent conservés ; aucune nouvelle action ne sera envoyée.'); }
    if (!validate(value)) throw new Error('La reprise locale est incohérente. Elle reste conservée sans être remplacée.');
    return value;
  }
  function write(key, value) {
    const serialized = JSON.stringify(value);
    try {
      root.localStorage.setItem(key, serialized);
      if (root.localStorage.getItem(key) !== serialized) throw new Error('readback mismatch');
    } catch (_) { throw new Error('La sauvegarde exacte de l’intention a échoué. Aucune nouvelle requête ne sera envoyée ; relisez la reprise conservée.'); }
    return value;
  }
  function identity(a, b) { return Boolean(a && b && a.job_id === b.job_id && a.capability === b.capability); }
  function validIntent(intent, job) {
    return object(intent) && ['create', 'produce', 'verify', 'complete', 'reconcile'].includes(intent.action) && object(intent.input) &&
      intent.input.job_id === job.job_id && intent.input.capability === job.capability && UUID.test(intent.input.request_id) &&
      (intent.action !== 'produce' || UUID.test(intent.input.result_request_id));
  }
  function validJob(value) {
    if (!object(value) || value.version !== 1 || !UUID.test(value.job_id) || !HASH.test(value.capability) ||
        typeof value.mandate !== 'string' || typeof value.source_csv !== 'string' || !Array.isArray(value.requirements) ||
        !value.requirements.length || value.requirements.length > 32 || !value.requirements.every(x => typeof x === 'string')) return false;
    if (value.pending !== undefined && value.pending !== null) {
      if (!object(value.pending) || !validIntent(value.pending.intent, value)) return false;
      if (value.pending.reconciliation && (!object(value.pending.reconciliation) || !validIntent(value.pending.reconciliation.intent, value) ||
          value.pending.reconciliation.intent.action !== 'reconcile' || value.pending.reconciliation.intent.input.target_request_id !== value.pending.intent.input.request_id)) return false;
    }
    return true;
  }
  function validMission(value) {
    if (!object(value) || value.version !== 1 || (value.job_id !== null && !UUID.test(value.job_id)) || (value.mission_id !== null && !UUID.test(value.mission_id))) return false;
    if (value.pending !== undefined && value.pending !== null) {
      const p = value.pending;
      if (!object(p) || p.action !== 'verify' || !object(p.input) || !UUID.test(p.input.job_id) || !UUID.test(p.input.mission_id) ||
          !UUID.test(p.input.request_id) || p.input.job_id !== value.job_id || p.input.mission_id !== value.mission_id) return false;
    }
    return true;
  }
  const api = {JOB_KEY, MISSION_KEY, UUID, HASH, object, canonical, same, available, unavailable, withKeys, read, write, identity, validJob, validMission};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  root.SolIntentSlot = api;
})(typeof globalThis === 'undefined' ? this : globalThis);
