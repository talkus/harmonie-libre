'use strict';
// Executes the unmodified shipped UI; transport responses below are controlled
// models, not a PostgreSQL interpreter or an external provider observation.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const KEY = 'sol-action-session-v1';
const JOB = '10000000-0000-4000-8000-000000000001';
const WRONG = '90000000-0000-4000-8000-000000000009';
const CAP = 'b'.repeat(64), HASH = 'a'.repeat(64);
const clone = x => JSON.parse(JSON.stringify(x));

class Element {
  constructor() { this.value = ''; this.textContent = ''; this.className = ''; this.children = []; this.hidden = false; this.disabled = false; this.events = {}; }
  addEventListener(type, fn) { (this.events[type] ||= []).push(fn); }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = children; }
  focus() {}
  async dispatch(type, event = {}) { for (const fn of this.events[type] || []) await fn(event); }
}
class World {
  constructor(sourceDir, mode) {
    this.sourceDir = sourceDir; this.mode = mode; this.now = Date.now(); this.elapsed = 0;
    this.store = new Map(); this.calls = []; this.model = []; this.outcomes = new Map(); this.uuidCount = 0; this.tabs = [];
    this.store.set(KEY, JSON.stringify({version: 1, job_id: JOB, capability: CAP, mandate: 'Synthetic bounded CSV', requirements: ['Exact cents'], source_csv: 'id,currency,amount\none,EUR,0.10\n', source_sha256: HASH, next_step_id: 'complete', history: [], pending: null, result: {source_sha256: HASH, rows: 1, row_ids: ['one'], totals: [{currency: 'EUR', amount: '0.10'}]}, verification: {status: 'PASS', observed_at: new Date(this.now - 1000).toISOString(), expires_at: new Date(this.now + 59000).toISOString()}}));
  }
  state() { return JSON.parse(this.store.get(KEY)); }
  safeState() {
    const s = this.state();
    return {job_id: s.job_id, next_step_id: s.next_step_id, pending_request_id: s.pending?.intent?.input?.request_id || null,
      reconciliation_request_id: s.pending?.reconciliation?.intent?.input?.request_id || null,
      history_actions: (s.history || []).map(x => x.action), rejected: (s.rejected_intents || []).map(x => ({request_id: x.intent.input.request_id, error: x.response.error, status: x.response.status})),
      verification: s.verification || null, completion: s.completion || null};
  }
  response(value, code = 200) { return Promise.resolve({ok: code >= 200 && code < 300, status: code, json: async () => clone(value)}); }
  async fetch(url, init) {
    if (url === '/provider-observation.json') return this.response(null);
    assert.equal(url, '/api/job');
    const {action, input} = JSON.parse(init.body);
    this.calls.push({action, request_id: input.request_id || null, target_request_id: input.target_request_id || null, expected_step_id: input.expected_step_id || null});
    const common = {action, job_id: input.job_id, request_id: input.request_id, automatic_retry: false, current_reuse_authorized: false};
    if (action === 'complete') {
      if (this.mode === 'refusal-delivered') {
        this.model.push({event: 'SQL_REJECTION_RETURNED_WITHOUT_DURABLE_OUTCOME', request_id: input.request_id});
        return this.response({...common, ok: false, status: 'REJECTED', error: 'FRESH_VERIFICATION_REQUIRED', sqlstate: 'P0001', effect: 'NONE_SQL_TRANSACTION_ROLLED_BACK', effect_scope: 'THIS_RPC_SQL_TRANSACTION_ONLY'});
      }
      if (this.mode === 'refusal-lost') {
        this.model.push({event: 'SQL_REJECTION_MODEL_NO_INTENT_OR_OUTCOME_THEN_REPLY_LOST', request_id: input.request_id});
        throw new Error('network: controlled response lost after SQL rejection');
      }
      if (this.mode === 'unknown-500') return this.response({...common, ok: false, status: 'OUTCOME_UNKNOWN', error: 'OUTCOME_UNKNOWN'}, 500);
      if (this.mode === 'wrong-direct') return this.response({...common, ok: false, status: 'REJECTED', request_id: WRONG, error: 'FRESH_VERIFICATION_REQUIRED', effect: 'NONE_SQL_TRANSACTION_ROLLED_BACK'});
      if (this.mode === 'success-lost' || this.mode === 'wrong-recovery') {
        const receipt = {...common, ok: true, status: 'COMPLETED_BOUNDED', current_reuse_authorized: true, pending: false, next_step_id: 'complete', completion: {status: 'COMPLETED_BOUNDED', scope: 'CSV_EXACT_CENTS_ONLY', source_sha256: HASH, observed_at: new Date(this.now).toISOString(), expires_at: new Date(this.now + 60000).toISOString()}};
        this.outcomes.set(input.request_id, receipt);
        this.model.push({event: 'SUCCESS_OUTCOME_MODEL_STORED_THEN_REPLY_LOST', request_id: input.request_id});
        throw new Error('network: controlled response lost after stored success');
      }
      return this.response({...common, ok: true, status: 'RECORDED'});
    }
    if (action === 'reconcile') {
      const original = this.outcomes.get(input.target_request_id);
      const nested = original ? {...clone(original), status: 'HISTORICAL_NOT_CURRENT', current_reuse_authorized: false} : null;
      if (nested && this.mode === 'wrong-recovery') nested.request_id = WRONG;
      const r = {...common, ok: true, status: 'RECORDED', pending: false, outcome_known: Boolean(nested), worker_reexecuted: false, reconciled_outcome: nested, next_step_id: 'complete'};
      this.outcomes.set(input.request_id, clone(r));
      return this.response(r);
    }
    if (action === 'receipt') {
      const known = this.outcomes.get(input.target_request_id);
      const receipt = known ? {...clone(known), status: 'HISTORICAL_NOT_CURRENT', current_reuse_authorized: false} : null;
      return this.response({...common, ok: true, status: known ? 'HISTORICAL_NOT_CURRENT' : 'UNKNOWN', target_request_id: input.target_request_id, found: Boolean(known), receipt});
    }
    throw new Error('Unexpected modeled action: ' + action);
  }
  tab(name = 'A') {
    const w = this, elements = new Map(), intervals = [], listeners = {};
    const $ = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
    class Clock extends Date { constructor(value) { super(value === undefined ? w.now : value); } static now() { return w.now; } }
    const ctx = {document: {getElementById: $, createElement: () => new Element(), addEventListener: (type, fn) => (listeners[type] ||= []).push(fn)},
      addEventListener: (type, fn) => (listeners[type] ||= []).push(fn), navigator: {locks: {request: async (_name, _options, fn) => fn({mode: 'exclusive'})}},
      localStorage: {getItem: key => w.store.get(key) ?? null, setItem: (key, value) => w.store.set(key, String(value))},
      crypto: {randomUUID: () => '30000000-0000-4000-8000-' + String(++w.uuidCount).padStart(12, '0'), getRandomValues: v => v.fill(17)},
      Date: Clock, performance: {now: () => w.elapsed}, AbortController, TextEncoder, setTimeout, clearTimeout, setInterval: fn => intervals.push(fn),
      fetch: (url, init) => w.fetch(url, init), console: {log() {}, warn() {}, error() {}}};
    ctx.window = ctx; vm.createContext(ctx);
    for (const file of ['intent-slot.js', 'app.js']) { const p = path.join(w.sourceDir, file); vm.runInContext(fs.readFileSync(p, 'utf8'), ctx, {filename: p}); }
    const tab = {name, $, click: async id => { const e = $(id); if (!e.disabled && !e.hidden) await e.dispatch('click'); },
      advance: ms => { w.now += ms; w.elapsed += ms; intervals.forEach(fn => fn()); },
      view: () => ({complete_disabled: $('complete').disabled, verify_disabled: $('verify').disabled, recovery_hidden: $('recovery').hidden, message: $('message').textContent, freshness: $('freshness').textContent})};
    this.tabs.push(tab); return tab;
  }
}

async function run(sourceDir) {
  const results = [];
  async function probe(id, title, fn) {
    try { results.push({id, title, ...await fn()}); }
    catch (e) { results.push({id, title, harness_status: 'ERROR', error: String(e.message).split(CAP).join('[SYNTHETIC_CAPABILITY]')}); }
  }
  await probe('E01', 'Expired verify still permits complete in baseline UI', async () => {
    const w = new World(sourceDir, 'refusal-delivered'), t = w.tab(); t.advance(61000);
    const before = t.view(); await t.click('complete');
    assert.equal(w.calls.filter(x => x.action === 'complete').length, 1);
    return {harness_status: 'OBSERVED', corrected_predicate: 'FAIL', before, calls: w.calls, after: w.safeState(), view: t.view()};
  });
  await probe('R01', 'Correlated delivered rejection resolves its own pending and is retained', async () => {
    const w = new World(sourceDir, 'refusal-delivered'), t = w.tab(); await t.click('complete');
    assert.equal(w.state().pending, null); assert.equal(w.state().rejected_intents.length, 1);
    assert.equal(w.state().rejected_intents[0].response.error, 'FRESH_VERIFICATION_REQUIRED');
    return {harness_status: 'OBSERVED', corrected_predicate: 'PARTIAL', reason: 'Identity/error retained; visible generic rejection omits machine code.', calls: w.calls, after: w.safeState(), view: t.view()};
  });
  await probe('R02', 'Lost rejection remains unresolved after reconcile, reload, repeated receipt reads', async () => {
    const w = new World(sourceDir, 'refusal-lost'), a = w.tab(); a.advance(61000); await a.click('complete');
    const original = w.state().pending.intent.input.request_id;
    await a.click('reconcile'); const afterReconcile = w.safeState();
    const b = w.tab('B'); await b.click('reconcile'); await b.click('reconcile');
    assert.equal(w.state().pending.intent.input.request_id, original);
    assert.equal(w.calls.filter(x => x.action === 'complete').length, 1);
    assert.equal(w.calls.filter(x => x.action === 'reconcile').length, 1);
    assert.equal(w.calls.filter(x => x.action === 'receipt').length, 2);
    assert.equal(w.state().pending.reconciliation.intent.input.target_request_id, original);
    return {harness_status: 'OBSERVED', corrected_predicate: 'FAIL', original_request_id: original, calls: w.calls, modeled_server: w.model, after_reconcile: afterReconcile, after_reload_and_reads: w.safeState(), view: b.view()};
  });
  await probe('U01', 'Ambiguous500 preserves original pending and does not fabricate no-effect', async () => {
    const w = new World(sourceDir, 'unknown-500'), t = w.tab(); await t.click('complete'); const id = w.state().pending.intent.input.request_id; await t.click('reconcile');
    assert.equal(w.state().pending.intent.input.request_id, id); assert.equal(w.calls.filter(x => x.action === 'complete').length, 1);
    assert.equal((w.state().rejected_intents || []).length, 0);
    return {harness_status: 'OBSERVED', corrected_predicate: 'PASS_BOUNDED', calls: w.calls, after: w.safeState(), view: t.view()};
  });
  await probe('S01', 'Lost success recovered as historical without reexecution', async () => {
    const w = new World(sourceDir, 'success-lost'), t = w.tab(); await t.click('complete'); await t.click('reconcile');
    assert.equal(w.state().pending, null); assert.equal(w.calls.filter(x => x.action === 'complete').length, 1);
    assert.ok(!t.view().freshness.includes('Clôture bornée actuelle'));
    return {harness_status: 'OBSERVED', corrected_predicate: 'PASS_BOUNDED', calls: w.calls, after: w.safeState(), view: t.view()};
  });
  await probe('I01a', 'Wrong direct request identity cannot resolve pending', async () => {
    const w = new World(sourceDir, 'wrong-direct'), t = w.tab(); await t.click('complete'); assert.ok(w.state().pending); assert.equal(w.state().pending.intent.input.request_id, w.calls[0].request_id);
    return {harness_status: 'OBSERVED', corrected_predicate: 'PASS_BOUNDED', calls: w.calls, after: w.safeState(), view: t.view()};
  });
  await probe('I01b', 'Wrong recovered request identity cannot resolve pending', async () => {
    const w = new World(sourceDir, 'wrong-recovery'), t = w.tab(); await t.click('complete'); const id = w.state().pending.intent.input.request_id; await t.click('reconcile'); assert.equal(w.state().pending.intent.input.request_id, id);
    return {harness_status: 'OBSERVED', corrected_predicate: 'PASS_BOUNDED', calls: w.calls, after: w.safeState(), view: t.view()};
  });
  return {schema: 'SOL_COMPLETION_RECOVERY_LOCAL_PROBE/v1', observed_at_utc: new Date().toISOString(), scope: 'Unmodified shipped UI executed in JavaScript VM with synthetic DOM/storage/Web Locks and controlled transport. SQL rejection/commit behavior is modeled from source, not executed. No provider calls, no actual packet loss, no external account mutations.', source_dir: sourceDir, source_hashes: Object.fromEntries(['app.js','intent-slot.js'].map(f => [f, crypto.createHash('sha256').update(fs.readFileSync(path.join(sourceDir,f))).digest('hex')])), corpus_sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,'corpus-frozen.json'))).digest('hex'), results,
    not_executed: [{id: 'D01', reason: 'Requires actual durable wrapper binding contract; source/runtime comparison stays a frozen correction predicate.'}, {id: 'Q01', reason: 'UI never intentionally retransmits same mutation UUID; server deduplication/negative durability requires separate SQL test.'}], external_network_calls: 0, model_weights_changed: false};
}
if (require.main === module) {
  const source = process.argv[2], receipt = process.argv[3];
  if (!source || !receipt || fs.existsSync(receipt)) throw new Error('Explicit source dir and new receipt path required; refuse overwrite.');
  run(source).then(r => { fs.writeFileSync(receipt, JSON.stringify(r, null, 2) + '\n'); process.stdout.write(JSON.stringify({receipt, probes: r.results.length, harness_errors: r.results.filter(x => x.harness_status === 'ERROR').length, corrected_predicates: r.results.map(x => ({id:x.id,status:x.corrected_predicate || x.harness_status}))}) + '\n'); }).catch(e => { process.stderr.write(String(e) + '\n'); process.exitCode = 1; });
}
module.exports = {run};
