'use strict';
// Independent shared-origin schedule tests. No external network or dependencies.
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const JOB_KEY = 'sol-action-session-v1';
const MISSION_KEY = 'sol-action-mission-session-v1';
const JOB = '10000000-0000-4000-8000-000000000001';
const MISSION = '20000000-0000-4000-8000-000000000001';
const OTHER_UUID = '90000000-0000-4000-8000-000000000009';
const CAP = 'b'.repeat(64), HASH = 'a'.repeat(64);
const clone = value => JSON.parse(JSON.stringify(value));
const delay = () => new Promise(resolve => setTimeout(resolve, 0));
async function tick() { for (let i = 0; i < 4; i++) await delay(); }
class Element {
  constructor() { this.value = ''; this.textContent = ''; this.className = ''; this.children = []; this.hidden = false; this.disabled = false; this.events = {}; }
  addEventListener(type, callback) { (this.events[type] ||= []).push(callback); }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = children; }
  focus() {}
  async dispatch(type, event = {}) { for (const callback of this.events[type] || []) await callback(event); }
}
class Locks {
  constructor() { this.held = new Set(); this.queues = new Map(); this.calls = []; }
  request(name, options, callback) {
    if (typeof options === 'function') { callback = options; options = {}; }
    options ||= {}; this.calls.push({name, ifAvailable: Boolean(options.ifAvailable)});
    if (options.ifAvailable && this.held.has(name)) return Promise.resolve().then(() => callback(null));
    return new Promise((resolve, reject) => {
      const queue = this.queues.get(name) || []; queue.push({resolve, reject, callback}); this.queues.set(name, queue); this.next(name);
    });
  }
  next(name) {
    if (this.held.has(name)) return;
    const item = (this.queues.get(name) || []).shift(); if (!item) return;
    this.held.add(name);
    Promise.resolve().then(() => item.callback({name, mode: 'exclusive'})).then(item.resolve, item.reject).finally(() => { this.held.delete(name); this.next(name); });
  }
  async query() { return {held: [...this.held].map(name => ({name, mode: 'exclusive'})), pending: []}; }
}
function rows() { return Array.from({length: 32}, (_, i) => ({compound_id: JOB + ':r' + i, task_id: JOB, anchor_task_id: JOB, role: i < 16 ? 'ROOT' : 'COMPANION', requirement: {id: 'r' + i, text: 'Exact requirement ' + i, contract: {kind: 'semantic_claim', target: {claim: 'UNKNOWN'}}}, mapping_basis: 'OPERATOR_DECLARED', validation: 'UNKNOWN'})); }
function definition() { return {mission_id: MISSION, definition_hash: HASH, definition: {job: {mandate: 'Bounded synthetic CSV only', requirements: ['Exact cents'], source_sha256: HASH}, requirements_matrix: rows()}, last_report: null}; }
function report(now) { return {status: 'TECHNICAL_RESULT_VERIFIED', technical_verdict: 'PASS', general_mandate: 'UNKNOWN', verified_at: new Date(now - 100).toISOString(), expires_at: new Date(now + 59900).toISOString(), requirements: rows(), checks: [{name: 'synthetic_control', verdict: 'PASS', reason: 'CONTROLLED_FIXTURE', evidence: {scope: 'NOT_PROVIDER_PROOF'}}]}; }
function initialJob() { return {version: 1, job_id: JOB, capability: CAP, mandate: 'Bounded synthetic CSV only', requirements: ['Exact cents'], source_csv: 'id,currency,amount\none,EUR,0.10\n', source_sha256: HASH, next_step_id: 'verify', result: {source_sha256: HASH, rows: 1, row_ids: ['one'], totals: [{currency: 'EUR', amount: '0.10'}]}, history: [], pending: null}; }
class World {
  constructor(sourceDir) {
    this.sourceDir = sourceDir; this.store = new Map([[JOB_KEY, JSON.stringify(initialJob())]]); this.tabs = []; this.events = []; this.calls = []; this.waiting = []; this.committed = new Map(); this.locks = new Locks(); this.clock = Date.now(); this.elapsed = 0;
  }
  seed(key, value, notify = false) { const previous = this.store.get(key) ?? null; this.store.set(key, value); if (notify) this.queueEvents(null, key, previous, value); }
  queueEvents(sender, key, oldValue, newValue) { for (const tab of this.tabs) if (tab !== sender) this.events.push({tab, key, oldValue, newValue}); }
  async deliverEvents() { while (this.events.length) { const event = this.events.shift(); await event.tab.emit('storage', {...event, storageArea: event.tab.context.localStorage}); } await tick(); }
  callsFor(action, route) { return this.calls.filter(x => x.body.action === action && (!route || x.url === route)); }
  response(call) {
    const {body} = call, input = body.input;
    if (call.url === '/api/mission') {
      if (body.action === 'status') return {ok: true, action: 'status', job_id: input.job_id, status: 'HISTORICAL_NOT_CURRENT', current_reuse_authorized: false, missions: [definition()]};
      if (body.action === 'verify') return {ok: true, action: 'verify', job_id: input.job_id, mission_id: input.mission_id, request_id: input.request_id, report_id: '40000000-0000-4000-8000-000000000001', status: 'TECHNICAL_RESULT_VERIFIED', technical_verdict: 'PASS', report: report(this.clock), general_mandate: 'UNKNOWN', current_reuse_authorized: true};
      const committed = this.committed.get(input.target_request_id);
      const receipt = committed ? clone(committed) : null;
      if (receipt) { receipt.current_reuse_authorized = false; receipt.report.current_reuse_authorized = false; }
      return {ok: true, action: 'receipt', job_id: input.job_id, mission_id: input.mission_id, target_request_id: input.target_request_id, found: Boolean(receipt), status: receipt ? 'HISTORICAL_NOT_CURRENT' : 'UNKNOWN', current_reuse_authorized: false, receipt};
    }
    return {ok: true, action: body.action, job_id: input.job_id, request_id: input.request_id, status: 'PASS', next_step_id: 'complete', verification: {status: 'PASS'}, source_sha256: HASH, current_reuse_authorized: false};
  }
  fetch(tab, url, init) {
    if (url === '/provider-observation.json') return Promise.resolve({ok: true, json: async () => null});
    assert.ok(['/api/mission', '/api/job'].includes(url), 'Unexpected network destination');
    const call = {tab: tab.name, url, body: JSON.parse(init.body)}; this.calls.push(call);
    if (call.body.action === 'verify') return new Promise((resolve, reject) => this.waiting.push({call, resolve, reject, done: false}));
    return Promise.resolve({ok: true, json: async () => this.response(call)});
  }
  release(record, lose = false) {
    if (record.done) return; record.done = true;
    const value = this.response(record.call); this.committed.set(record.call.body.input.request_id, clone(value));
    if (lose) record.reject(new Error('Controlled reply absent after synthetic commit'));
    else record.resolve({ok: true, json: async () => clone(value)});
  }
  async drain(promises = []) {
    for (let i = 0; i < 8; i++) { this.waiting.forEach(item => this.release(item)); await tick(); }
    await Promise.race([Promise.allSettled(promises), new Promise(resolve => setTimeout(resolve, 100))]);
  }
  tab(name, mode = 'mission', options = {}) {
    const world = this, elements = new Map(), listeners = {}, intervals = [];
    const tab = {name, uuidCount: 0, mode};
    const $ = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
    class Clock extends Date { constructor(value) { super(value === undefined ? world.clock : value); } static now() { return world.clock; } }
    tab.context = {
      document: {getElementById: $, createElement: () => new Element(), addEventListener: (type, callback) => (listeners[type] ||= []).push(callback), visibilityState: 'visible'},
      addEventListener: (type, callback) => (listeners[type] ||= []).push(callback), navigator: options.noLocks ? {} : {locks: world.locks},
      localStorage: {getItem: key => world.store.get(key) ?? null, setItem: (key, value) => { if (options.writeFails) throw new Error('Controlled storage refusal'); const old = world.store.get(key) ?? null; world.store.set(key, String(value)); world.queueEvents(tab, key, old, String(value)); }},
      crypto: {randomUUID: () => { tab.uuidCount++; return (name === 'A' ? '30000000' : '50000000') + '-0000-4000-8000-' + String(tab.uuidCount).padStart(12, '0'); }, getRandomValues: value => { value.fill(17); return value; }},
      Date: Clock, performance: {now: () => world.elapsed}, AbortController, setTimeout, clearTimeout, setInterval: callback => intervals.push(callback), TextEncoder,
      fetch: (url, init) => world.fetch(tab, url, init), console: {log() {}, warn() {}, error() {}}
    };
    tab.context.window = tab.context; tab.context.self = tab.context;
    vm.createContext(tab.context);
    const helper = path.join(this.sourceDir, 'public/intent-slot.js'); if (fs.existsSync(helper)) vm.runInContext(fs.readFileSync(helper, 'utf8'), tab.context, {filename: helper});
    const file = path.join(this.sourceDir, 'public', mode === 'mission' ? 'missions.js' : 'app.js'); vm.runInContext(fs.readFileSync(file, 'utf8'), tab.context, {filename: file});
    tab.$ = $; tab.emit = async (type, event = {}) => { for (const callback of listeners[type] || []) await callback(event); };
    tab.click = async id => { const element = $(id); if (!element.disabled && !element.hidden) await element.dispatch('click'); };
    tab.ready = async () => { if (mode !== 'mission') return; await tab.click('mission-load'); $('mission-select').value = MISSION; await $('mission-select').dispatch('change'); };
    tab.state = () => JSON.parse(world.store.get(mode === 'mission' ? MISSION_KEY : JOB_KEY) || 'null');
    tab.advance = ms => { world.clock += ms; world.elapsed += ms; intervals.forEach(callback => callback()); };
    tab.hasCurrent = () => /à cet instant/.test($('mission-freshness').textContent);
    this.tabs.push(tab); return tab;
  }
}
async function run({sourceDir, receiptPath} = {}) {
  assert.ok(sourceDir && receiptPath, 'Explicit source and new receipt path required');
  assert.ok(!fs.existsSync(receiptPath), 'Refuse overwriting an old test receipt');
  const results = [];
  async function test(name, fn) { try { await fn(); results.push({name, status: 'PASS'}); } catch (error) { results.push({name, status: 'FAIL', error: String(error.message).split(CAP).join('[SYNTHETIC_CAPABILITY]')}); } }
  await test('T01_two_stale_Mission_tabs_cannot_reserve_two_verify_UUIDs', async () => {
    const w = new World(sourceDir), a = w.tab('A'), b = w.tab('B'); await a.ready(); await b.ready();
    const pa = a.click('mission-verify'); await tick(); const original = w.store.get(MISSION_KEY); const pb = b.click('mission-verify'); await tick();
    try { assert.equal(w.callsFor('verify').length, 1); assert.equal(b.uuidCount, 0); assert.equal(w.store.get(MISSION_KEY), original); }
    finally { await w.drain([pa, pb]); }
    assert.equal(w.callsFor('verify').length, 1, 'A waiting click must not become a later second verification');
  });
  await test('T02_Mission_response_cannot_clear_a_foreign_durable_pending', async () => {
    const w = new World(sourceDir), a = w.tab('A'); await a.ready(); const pa = a.click('mission-verify'); await tick();
    const other = JSON.parse(w.store.get(MISSION_KEY)); other.pending.input.request_id = OTHER_UUID; const bytes = JSON.stringify(other); w.seed(MISSION_KEY, bytes);
    await w.drain([pa]); assert.equal(w.store.get(MISSION_KEY), bytes); assert.equal(a.hasCurrent(), false);
  });
  await test('T03_other_open_tab_recovers_exact_shared_pending_by_receipt_only', async () => {
    const w = new World(sourceDir), a = w.tab('A'), b = w.tab('B'); await a.ready(); await b.ready();
    const pa = a.click('mission-verify'); await tick(); const id = w.callsFor('verify')[0].body.input.request_id; w.release(w.waiting[0], true); await pa;
    await w.deliverEvents(); await b.click('mission-receipt');
    assert.equal(w.callsFor('verify').length, 1); assert.equal(w.callsFor('receipt').length, 1); assert.equal(w.callsFor('receipt')[0].body.input.target_request_id, id); assert.equal(b.uuidCount, 0); assert.equal(b.state().pending, null); assert.equal(b.hasCurrent(), false);
  });
  await test('T04_reload_recovers_same_pending_without_verify_or_new_UUID', async () => {
    const w = new World(sourceDir), a = w.tab('A'); await a.ready(); const pa = a.click('mission-verify'); await tick(); const id = w.callsFor('verify')[0].body.input.request_id; w.release(w.waiting[0], true); await pa;
    const b = w.tab('B'); await b.click('mission-receipt'); assert.equal(w.callsFor('verify').length, 1); assert.equal(w.callsFor('receipt')[0].body.input.target_request_id, id); assert.equal(b.uuidCount, 0); assert.equal(b.hasCurrent(), false);
  });
  await test('T05_stale_storage_refusal_does_not_generate_foreign_intent', async () => {
    const w = new World(sourceDir), a = w.tab('A'), b = w.tab('B', 'mission', {writeFails: true}); await a.ready(); await b.ready(); const pa = a.click('mission-verify'); await tick(); const bytes = w.store.get(MISSION_KEY); await b.click('mission-verify');
    try { assert.equal(w.callsFor('verify').length, 1); assert.equal(b.uuidCount, 0); assert.equal(w.store.get(MISSION_KEY), bytes); } finally { await w.drain([pa]); }
  });
  await test('T06_without_exclusive_coordination_Mission_refuses_mutation', async () => {
    const w = new World(sourceDir), a = w.tab('A', 'mission', {noLocks: true}); await a.ready(); const pa = a.click('mission-verify'); await tick();
    try { assert.equal(w.callsFor('verify').length, 0); assert.equal(a.uuidCount, 0); } finally { await w.drain([pa]); }
  });
  await test('T07_single_tab_preserves_full_matrix_and_expires', async () => {
    const w = new World(sourceDir), a = w.tab('A'); await a.ready(); const pa = a.click('mission-verify'); await tick(); await w.drain([pa]);
    assert.equal(w.callsFor('verify').length, 1); assert.equal(a.state().pending, null); assert.equal(a.$('mission-matrix').children.length, 32); assert.equal(a.hasCurrent(), true); a.advance(61000); assert.equal(a.hasCurrent(), false);
  });
  await test('S09_corrupt_durable_Mission_slot_is_preserved_by_stale_tab', async () => {
    const w = new World(sourceDir), a = w.tab('A'); await a.ready(); w.seed(MISSION_KEY, '{not valid JSON'); const pa = a.click('mission-verify'); await tick();
    try { assert.equal(w.callsFor('verify').length, 0); assert.equal(a.uuidCount, 0); assert.equal(w.store.get(MISSION_KEY), '{not valid JSON'); } finally { await w.drain([pa]); }
  });
  await test('S10_two_stale_Action_tabs_cannot_replace_durable_pending', async () => {
    const w = new World(sourceDir), a = w.tab('A', 'action'), b = w.tab('B', 'action'); const pa = a.click('verify'); await tick(); const original = w.store.get(JOB_KEY); const pb = b.click('verify'); await tick();
    try { assert.equal(w.callsFor('verify', '/api/job').length, 1); assert.equal(b.uuidCount, 0); assert.equal(w.store.get(JOB_KEY), original); } finally { await w.drain([pa, pb]); }
    assert.equal(w.callsFor('verify', '/api/job').length, 1);
  });
  await test('S11_Action_response_cannot_clear_foreign_durable_pending', async () => {
    const w = new World(sourceDir), a = w.tab('A', 'action'); const pa = a.click('verify'); await tick(); const other = JSON.parse(w.store.get(JOB_KEY)); other.pending.intent.input.request_id = OTHER_UUID; const bytes = JSON.stringify(other); w.seed(JOB_KEY, bytes);
    await w.drain([pa]); assert.equal(w.store.get(JOB_KEY), bytes);
  });
  await test('S12_without_exclusive_coordination_Action_refuses_mutation', async () => {
    const w = new World(sourceDir), a = w.tab('A', 'action', {noLocks: true}); const pa = a.click('verify'); await tick();
    try { assert.equal(w.callsFor('verify', '/api/job').length, 0); assert.equal(a.uuidCount, 0); } finally { await w.drain([pa]); }
  });
  const sourceHashes = {};
  for (const name of ['missions.js', 'app.js', 'intent-slot.js']) { const file = path.join(sourceDir, 'public', name); if (fs.existsSync(file)) sourceHashes[name] = crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex'); }
  const receipt = {schema: 'SOL_SHARED_BROWSER_INDEPENDENT_TEST_RESULT/v1', observed_at: new Date().toISOString(), source_dir: sourceDir, source_hashes: sourceHashes, test_source_sha256: crypto.createHash('sha256').update(fs.readFileSync(__filename)).digest('hex'), scope: 'Two separate JavaScript VM contexts sharing one storage Map, exclusive-lock simulator and controlled transport. Storage events intentionally delayed. No real browser, remote call or provider proof.', base_corpus: 'work/reussite-20261021/audit/next-gap-shared-browser-corpus.json', base_case_ids_covered: ['T01','T02','T03','T04','T05','T06','T07'], secondary_T08: 'NOT_EXECUTED_BY_THIS_SUITE', supplementary_cases_timing: 'S09-S12 added before reviewer executed baseline, while correction author could already be working; no inherited measurements', tests: results.length, passed: results.filter(x => x.status === 'PASS').length, failed: results.filter(x => x.status === 'FAIL').length, results, external_network_calls: 0};
  fs.mkdirSync(path.dirname(receiptPath), {recursive: true}); fs.writeFileSync(receiptPath, JSON.stringify(receipt, null, 2) + '\n'); return receipt;
}
module.exports = {run};
