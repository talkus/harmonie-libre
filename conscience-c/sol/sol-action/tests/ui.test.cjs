const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const ROOT = path.resolve(__dirname, '..');
const SOURCE_PATH = process.env.SOL_ACTION_UI_SOURCE || path.join(ROOT, 'app/public/app.js');
const SOURCE = fs.readFileSync(SOURCE_PATH, 'utf8');
const tests = [];
const RESULT = {source_sha256: 'a'.repeat(64), rows: 2, row_ids: ['a', 'b'], totals: [{currency: 'EUR', amount: '0.30'}]};
const tick = () => new Promise(resolve => setImmediate(resolve));
async function settle() { for (let i = 0; i < 8; i++) await tick(); }
class Element {
  constructor() { this.value = ''; this.hidden = false; this.disabled = false; this.textContent = ''; this.className = ''; this.events = {}; this.children = []; }
  addEventListener(name, listener) { this.events[name] = listener; }
  appendChild(element) { this.children.push(element); }
  replaceChildren() { this.children = []; }
  focus() {}
  click() { if (!this.disabled && this.events.click) return this.events.click({preventDefault() {}}); }
}
function harness(options = {}) {
  const elements = new Map();
  const store = new Map();
  if (options.saved) store.set('sol-action-session-v1', JSON.stringify(options.saved));
  const requests = [];
  const intervals = [];
  let clock = 1792560000000;
  let monotonic = 0;
  let count = 1;
  let capCount = 170;
  let stage = 'produce';
  let completed = null;
  const element = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
  class FakeDate extends Date { constructor(value) { super(value === undefined ? clock : value); } static now() { return clock; } }
  const context = {
    document: {getElementById: element, createElement: () => new Element()},
    localStorage: {getItem: key => store.get(key) || null, setItem: (key, value) => { if (options.storageFails) throw new Error('denied'); store.set(key, value); }},
    crypto: {getRandomValues: bytes => { bytes.fill(++capCount); return bytes; }, randomUUID: () => '10000000-0000-4000-8000-' + String(count++).padStart(12, '0')},
    Date: FakeDate, performance: {now: () => monotonic}, AbortController, Uint8Array, TextEncoder,
    setTimeout, clearTimeout, setInterval: callback => intervals.push(callback), Blob, URL,
    fetch: async (url, request) => {
      if (url === '/provider-observation.json') return {ok: false};
      const intent = JSON.parse(request.body);
      const saved = JSON.parse(store.get('sol-action-session-v1'));
      requests.push(intent);
      if (!['status', 'audit', 'receipt'].includes(intent.action)) {
        assert.ok(saved.pending, 'intent must be durable before network');
        if (intent.action !== 'reconcile') assert.equal(saved.pending.intent.input.request_id, intent.input.request_id);
        else assert.equal(saved.pending.reconciliation.intent.input.request_id, intent.input.request_id);
      }
      if (options.responder) {
        const custom = await options.responder(intent, {saved, clock});
        if (custom) return {ok: true, json: async () => custom};
      }
      const action = intent.action;
      if (action === 'create') { stage = 'produce'; completed = null; }
      const base = {ok: true, status: action === 'status' ? 'HISTORICAL_NOT_CURRENT' : 'RECORDED', action, job_id: intent.input.job_id, request_id: action === 'produce' ? intent.input.result_request_id : intent.input.request_id, next_step_id: stage, pending: false, source_sha256: RESULT.source_sha256, result: stage === 'produce' ? null : RESULT, current_reuse_authorized: false};
      if (action === 'produce') { stage = 'verify'; base.action = 'result'; base.result = RESULT; base.next_step_id = stage; }
      if (action === 'verify') { stage = 'complete'; base.next_step_id = stage; base.verification = {status: 'PASS', expires_at: new FakeDate(clock + 60000).toISOString()}; }
      if (action === 'complete') { base.status = 'COMPLETED_BOUNDED'; base.current_reuse_authorized = true; completed = {status: 'COMPLETED_BOUNDED', scope: 'CSV_EXACT_CENTS_ONLY', expires_at: new FakeDate(clock + 60000).toISOString()}; base.completion = completed; }
      if (action === 'status' && completed) base.completion = completed;
      if (action === 'audit') base.audit = {status: 'PASS', chain_valid: true, relations_valid: true, source_hash_valid: true, definition_hash_valid: true};
      return {ok: true, json: async () => base};
    }
  };
  vm.createContext(context);
  vm.runInContext(SOURCE, context, {filename: 'app.js'});
  async function click(id) { element(id).click(); await settle(); }
  async function create() { await click('sample'); element('job-form').events.submit({preventDefault() {}}); await settle(); }
  function state() { return JSON.parse(store.get('sol-action-session-v1')); }
  return {element, requests, context, create, click, state, advance: (milliseconds, wall = milliseconds) => { monotonic += milliseconds; clock += wall; intervals.forEach(callback => callback()); }, store};
}
async function test(name, callback) { try { await callback(); tests.push({name, status: 'PASS'}); } catch (error) { tests.push({name, status: 'FAIL', error: error.message}); } }
async function run() {
  await test('actual output displayed after produce with durable ids', async () => {
    const app = harness(); await app.create(); assert.equal(app.requests.length, 1); assert.equal(app.requests[0].action, 'create'); assert.equal(app.element('produce').disabled, false);
    await app.click('produce'); assert.equal(app.requests[1].action, 'produce'); assert.ok(app.requests[1].input.result_request_id); assert.equal(app.state().pending, null); assert.equal(app.element('totals').children[0].children[1].textContent, '0.30');
  });
  await test('complete freshness degrades without reload', async () => {
    const app = harness(); await app.create(); await app.click('produce'); await app.click('verify'); await app.click('complete'); assert.match(app.element('freshness').textContent, /actuelle/); app.advance(61000); assert.match(app.element('freshness').textContent, /historique/); assert.equal(app.element('message').className, 'message unknown'); assert.equal(app.element('verify').disabled, false);
  });
  await test('status never restores current authority', async () => {
    const app = harness(); await app.create(); await app.click('produce'); await app.click('verify'); await app.click('complete'); await app.click('status'); assert.match(app.element('freshness').textContent, /historique/);
  });
  await test('network loss preserves original intention and no replay on status', async () => {
    const app = harness({responder: intent => { if (intent.action === 'produce') throw new Error('network lost'); }}); await app.create(); await app.click('produce'); const original = app.state().pending.intent; await app.click('status'); assert.equal(app.state().pending.intent.input.request_id, original.input.request_id); await app.click('produce'); assert.equal(app.requests.filter(x => x.action === 'produce').length, 1); assert.equal(app.element('adapt').disabled, true);
  });
  await test('missing reconciliation remains blocked with same identity', async () => {
    const app = harness({responder: intent => { if (intent.action === 'produce') throw new Error('network lost'); if (intent.action === 'reconcile') return {ok: true, job_id: intent.input.job_id, request_id: intent.input.request_id, status: 'RECORDED', pending: true, reconciled_outcome: null}; }}); await app.create(); await app.click('produce'); const original = app.state().pending.intent.input.request_id; await app.click('reconcile'); assert.equal(app.state().pending.intent.input.request_id, original); await app.click('reconcile'); assert.equal(app.requests.filter(x => x.action === 'reconcile').length, 1);
  });
  await test('unrelated request response cannot close intention', async () => {
    const app = harness({responder: intent => intent.action === 'create' ? {ok: true, job_id: intent.input.job_id, request_id: '20000000-0000-4000-8000-000000000001', status: 'RECORDED', next_step_id: 'produce'} : null}); await app.create(); assert.ok(app.state().pending); assert.equal(app.element('produce').disabled, true);
  });
  await test('reload keeps completed proof historical', async () => {
    const first = harness(); await first.create(); await first.click('produce'); await first.click('verify'); await first.click('complete'); const second = harness({saved: first.state()}); assert.match(second.element('freshness').textContent, /historique/); assert.equal(second.requests.length, 0);
  });
  await test('correction retains old requirements and parent capability without inheriting result', async () => {
    const app = harness(); await app.create(); await app.click('produce'); const parent = app.state(); await app.click('adapt'); app.element('source-csv').value += 'c,EUR,1\n'; app.element('job-form').events.submit({preventDefault() {}}); await settle(); const intent = app.requests[2]; assert.equal(intent.action, 'create'); assert.equal(intent.input.parent_job_id, parent.job_id); assert.equal(intent.input.parent_capability, parent.capability); assert.equal(JSON.stringify(intent.input.requirements), JSON.stringify(parent.requirements)); assert.equal(app.state().result, undefined);
  });
  await test('audit success requires all exact server predicates', async () => { const app = harness(); await app.create(); await app.click('audit'); assert.match(app.element('journal-status').textContent, /Journal contrôlé/); });
  await test('failed local persistence prevents remote effects', async () => { const app = harness({storageFails: true}); await app.create(); assert.equal(app.requests.length, 0); assert.match(app.element('message').textContent, /sauvegarde locale/); });
  await test('freshness refuses broad scope or deduplicated receipt', async () => {
    const app = harness(); const response = {ok: true, status: 'COMPLETED_BOUNDED', current_reuse_authorized: true, completion: {status: 'COMPLETED_BOUNDED', scope: 'CSV_EXACT_CENTS_ONLY', expires_at: '2099-01-01T00:00:00Z'}}; const now = Date.now(); assert.equal(app.context.SolAction.currentCompletion(response, now, now, 59999), true); assert.equal(app.context.SolAction.currentCompletion(response, now, now, 60000), false); response.completion.scope = 'ALL_TASKS'; assert.equal(app.context.SolAction.currentCompletion(response, now, now, 1), false); response.completion.scope = 'CSV_EXACT_CENTS_ONLY'; response.deduplicated = true; assert.equal(app.context.SolAction.currentCompletion(response, now, now, 1), false);
  });
  await test('lost reconciliation response after commit is recovered by exact read-only receipt without producer replay', async () => {
    let durableReceipt = null;
    const remoteJournal = [];
    const app = harness({responder: intent => {
      if (intent.action === 'create') { remoteJournal.push({action: 'create'}); return null; }
      if (intent.action === 'produce') { remoteJournal.push({action: 'begin'}); throw new Error('network lost after result committed'); }
      if (intent.action === 'reconcile') {
        remoteJournal.push({action: 'reconcile', request_id: intent.input.request_id});
        durableReceipt = {
          ok: true, action: 'reconcile', job_id: intent.input.job_id, request_id: intent.input.request_id,
          status: 'HISTORICAL_NOT_CURRENT', current_reuse_authorized: false, automatic_retry: false,
          pending: false, outcome_known: true, worker_reexecuted: false, next_step_id: 'verify',
          production_request_id: intent.input.production_request_id, source_sha256: RESULT.source_sha256, result: RESULT,
          reconciled_outcome: {ok: true, action: 'begin', job_id: intent.input.job_id, request_id: intent.input.target_request_id, production_request_id: intent.input.production_request_id, source_sha256: RESULT.source_sha256, status: 'HISTORICAL_NOT_CURRENT', current_reuse_authorized: false, pending: true}
        };
        throw new Error('network lost after reconciliation committed');
      }
      if (intent.action === 'receipt') return {ok: true, status: 'HISTORICAL_NOT_CURRENT', found: true, job_id: intent.input.job_id, target_request_id: intent.input.target_request_id, receipt: durableReceipt, current_reuse_authorized: false, automatic_retry: false};
      return null;
    }});
    await app.create(); await app.click('produce'); await app.click('reconcile');
    const pending = app.state().pending;
    assert.ok(pending.reconciliation);
    assert.equal(app.element('reconcile').disabled, false, 'read-only recovery must remain available');
    assert.match(app.element('reconcile').textContent, /Consulter/);
    const journalBefore = JSON.stringify(remoteJournal);
    await app.click('reconcile');
    const read = app.requests.at(-1);
    assert.equal(read.action, 'receipt');
    assert.deepEqual(Object.keys(read.input).sort(), ['capability', 'job_id', 'target_request_id']);
    assert.equal(read.input.target_request_id, pending.reconciliation.intent.input.request_id);
    assert.equal(JSON.stringify(remoteJournal), journalBefore, 'lookup cannot append to the remote journal');
    assert.equal(app.requests.filter(x => x.action === 'produce').length, 1);
    assert.equal(app.requests.filter(x => x.action === 'reconcile').length, 1);
    assert.equal(app.state().pending, null);
    assert.deepEqual(app.state().result, RESULT);
    assert.equal(app.element('verify').disabled, false);
    assert.equal(app.state().last_response.current_reuse_authorized, false);
  });
  await test('absent lookup keeps original production and reconciliation identities unchanged across reload and repeated reads', async () => {
    const first = harness({responder: intent => { if (intent.action === 'produce' || intent.action === 'reconcile') throw new Error('network lost'); }});
    await first.create(); await first.click('produce'); await first.click('reconcile');
    const saved = first.state(), originalPending = JSON.stringify(saved.pending);
    const remoteJournal = ['begin', 'reconcile'];
    const app = harness({saved, responder: intent => {
      assert.equal(intent.action, 'receipt', 'reload recovery must only read the prior receipt');
      return {ok: true, status: 'OUTCOME_UNKNOWN', found: false, job_id: intent.input.job_id, target_request_id: intent.input.target_request_id, receipt: null, current_reuse_authorized: false, automatic_retry: false};
    }});
    await app.click('reconcile'); await app.click('reconcile');
    assert.equal(JSON.stringify(app.state().pending), originalPending);
    assert.equal(app.requests.length, 2);
    assert.ok(app.requests.every(x => x.action === 'receipt' && !('request_id' in x.input)));
    assert.deepEqual(remoteJournal, ['begin', 'reconcile']);
    assert.match(app.element('message').textContent, /absent ou inconnu/);
    assert.equal(app.element('produce').disabled, true);
  });
  await test('malformed lookup and wrong envelope job or target UUID cannot erase production pending', async () => {
    const seed = harness({responder: intent => { if (intent.action === 'produce' || intent.action === 'reconcile') throw new Error('network lost'); }});
    await seed.create(); await seed.click('produce'); await seed.click('reconcile');
    const saved = seed.state(), originalPending = JSON.stringify(saved.pending);
    for (const patch of [{job_id: '20000000-0000-4000-8000-000000000001'}, {target_request_id: '20000000-0000-4000-8000-000000000002'}, {receipt: null}, {found: 'true'}, {current_reuse_authorized: true}]) {
      const app = harness({saved, responder: intent => Object.assign({ok: true, status: 'HISTORICAL_NOT_CURRENT', found: true, job_id: intent.input.job_id, target_request_id: intent.input.target_request_id, receipt: {}, current_reuse_authorized: false, automatic_retry: false}, patch)});
      await app.click('reconcile');
      assert.equal(JSON.stringify(app.state().pending), originalPending);
      assert.equal(app.requests.length, 1);
      assert.equal(app.requests[0].action, 'receipt');
      assert.equal(app.state().result, undefined);
    }
  });
  await test('recovered reconciliation and nested original outcome require their own exact job and UUID correlations', async () => {
    const seed = harness({responder: intent => { if (intent.action === 'produce' || intent.action === 'reconcile') throw new Error('network lost'); }});
    await seed.create(); await seed.click('produce'); await seed.click('reconcile');
    const saved = seed.state(), originalPending = JSON.stringify(saved.pending);
    for (const variant of ['reconcile-id', 'reconcile-job', 'nested-id', 'nested-job', 'nested-production-id', 'nested-action', 'wrapper-source', 'nested-source', 'result-source']) {
      const app = harness({saved, responder: intent => {
        const original = saved.pending.intent;
        const receipt = {ok: true, action: 'reconcile', job_id: saved.job_id, request_id: intent.input.target_request_id, status: 'HISTORICAL_NOT_CURRENT', current_reuse_authorized: false, pending: false, outcome_known: true, worker_reexecuted: false, production_request_id: original.input.request_id, source_sha256: RESULT.source_sha256, result: {...RESULT}, next_step_id: 'verify', reconciled_outcome: {ok: true, action: 'begin', job_id: saved.job_id, request_id: original.input.request_id, production_request_id: original.input.request_id, source_sha256: RESULT.source_sha256, status: 'HISTORICAL_NOT_CURRENT', pending: true}};
        const wrong = '20000000-0000-4000-8000-000000000001';
        if (variant === 'reconcile-id') receipt.request_id = wrong;
        if (variant === 'reconcile-job') receipt.job_id = wrong;
        if (variant === 'nested-id') receipt.reconciled_outcome.request_id = wrong;
        if (variant === 'nested-job') receipt.reconciled_outcome.job_id = wrong;
        if (variant === 'nested-production-id') receipt.reconciled_outcome.production_request_id = wrong;
        if (variant === 'nested-action') receipt.reconciled_outcome.action = 'verify';
        if (variant === 'wrapper-source') receipt.source_sha256 = 'b'.repeat(64);
        if (variant === 'nested-source') receipt.reconciled_outcome.source_sha256 = 'b'.repeat(64);
        if (variant === 'result-source') receipt.result.source_sha256 = 'b'.repeat(64);
        return {ok: true, status: 'HISTORICAL_NOT_CURRENT', found: true, job_id: saved.job_id, target_request_id: intent.input.target_request_id, receipt, current_reuse_authorized: false, automatic_retry: false};
      }});
      await app.click('reconcile');
      assert.equal(JSON.stringify(app.state().pending), originalPending, variant);
      assert.equal(app.state().result, undefined);
      assert.equal(app.requests.length, 1);
    }
  });
  await test('receipt helper generates no UUID and recovered completion remains historical', async () => {
    const app = harness();
    let ids = 0;
    const intent = app.context.SolAction.newIntent('receipt', {job_id: 'job', capability: 'cap', target_request_id: 'prior'}, () => { ids++; return 'new-id'; });
    assert.equal(ids, 0);
    assert.deepEqual(Object.keys(intent.input).sort(), ['capability', 'job_id', 'target_request_id']);
    const completion = {status: 'COMPLETED_BOUNDED', scope: 'CSV_EXACT_CENTS_ONLY', expires_at: new Date(Date.now() + 60000).toISOString()};
    const original = {action: 'complete', input: {job_id: '30000000-0000-4000-8000-000000000001', capability: 'a'.repeat(64), request_id: '30000000-0000-4000-8000-000000000002'}};
    const reconcile = {action: 'reconcile', input: {job_id: original.input.job_id, capability: original.input.capability, request_id: '30000000-0000-4000-8000-000000000003', target_request_id: original.input.request_id}};
    const saved = {version: 1, job_id: original.input.job_id, capability: original.input.capability, mandate: 'Clore', requirements: ['CSV'], source_csv: 'id,currency,amount\na,EUR,0.30\n', pending: {intent: original, reconciliation: {intent: reconcile}}, history: []};
    const recovered = harness({saved, responder: input => ({ok: true, status: 'HISTORICAL_NOT_CURRENT', found: true, job_id: saved.job_id, target_request_id: input.input.target_request_id, current_reuse_authorized: false, automatic_retry: false, receipt: {ok: true, action: 'reconcile', job_id: saved.job_id, request_id: reconcile.input.request_id, status: 'HISTORICAL_NOT_CURRENT', current_reuse_authorized: false, pending: false, outcome_known: true, worker_reexecuted: false, completion, next_step_id: 'complete', reconciled_outcome: {ok: true, action: 'complete', job_id: saved.job_id, request_id: original.input.request_id, status: 'HISTORICAL_NOT_CURRENT', pending: false, completion}}})});
    await recovered.click('reconcile');
    assert.equal(recovered.state().pending, null);
    assert.match(recovered.element('freshness').textContent, /historique/);
  });
  const receipt = {schema: 'SOL_ACTION_UI_TEST/v1', observed_at: new Date().toISOString(), app_source_sha256: crypto.createHash('sha256').update(SOURCE).digest('hex'), environment: 'NODE_VM_SYNTHETIC_DOM_AND_NETWORK_NOT_REAL_BROWSER', runtime: typeof Deno !== 'undefined' ? {runner: 'DENO_NODE_COMPATIBILITY', ...Deno.version} : {runner: 'NODE', node: process.version}, test_count: tests.length, passed: tests.filter(x => x.status === 'PASS').length, failed: tests.filter(x => x.status === 'FAIL').length, tests};
  fs.mkdirSync(path.join(ROOT, 'evidence/reproduction'), {recursive: true});
  fs.writeFileSync(path.join(ROOT, 'evidence/reproduction/ui-tests-' + new Date().toISOString().replace(/[:.]/g, '-') + '.json'), JSON.stringify(receipt, null, 2) + '\n');
  return receipt;
}
module.exports = {run};
if (require.main === module) run().then(receipt => { console.log(JSON.stringify(receipt, null, 2)); process.exitCode = receipt.failed ? 1 : 0; });
