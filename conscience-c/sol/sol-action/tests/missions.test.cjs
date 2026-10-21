const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const crypto = require('node:crypto');
const process = require('node:process');
const ROOT = path.resolve(__dirname, '..');
const SOURCE = fs.readFileSync(path.join(ROOT, 'app/public/missions.js'), 'utf8');
const JOB = '10000000-0000-4000-8000-000000000001';
const MISSION = '20000000-0000-4000-8000-000000000001';
const KEY = 'sol-action-mission-session-v1';
const CAP = 'b'.repeat(64);
const HASH = 'a'.repeat(64);
const clone = value => JSON.parse(JSON.stringify(value));
const checks = [];
const rows = Array.from({length: 32}, (_, i) => ({compound_id: 'ensemble-' + (i < 16 ? 'principal' : 'complement'), task_id: 'task-' + i, anchor_task_id: 'ancrage-1', role: i < 16 ? 'root' : 'complement', requirement: {id: 'r-' + i, text: 'Exigence exacte ' + i + '\nDeuxième ligne intacte.', contract: {kind: 'journal_integrity', target: {}}}, mapping_basis: 'Déclaration de l’opérateur', validation: 'UNKNOWN'}));
const mission = () => ({mission_id: MISSION, definition_hash: HASH, definition: {job: {mandate: 'Demande CSV exacte', requirements: ['Contrat CSV original', 'Autre texte conservé'], source_sha256: HASH}, requirements_matrix: clone(rows)}, last_report: null});
function report(now) {
  return {status: 'TECHNICAL_RESULT_VERIFIED', technical_verdict: 'PASS', general_mandate: 'UNKNOWN', verified_at: new Date(now - 100).toISOString(), expires_at: new Date(now + 59900).toISOString(), requirements: clone(rows), checks: [{name: 'Source et résultat', verdict: 'PASS', reason: 'EXACT_MATCH', evidence: {source_sha256: HASH}}]};
}
class Element {
  constructor() { this.value = ''; this.textContent = ''; this.className = ''; this.children = []; this.hidden = false; this.disabled = false; this.events = {}; }
  addEventListener(type, callback) { this.events[type] = callback; }
  appendChild(child) { this.children.push(child); return child; }
  replaceChildren(...children) { this.children = children; }
}
function harness(options = {}) {
  const elements = new Map(), store = new Map(), requests = [], timers = [], events = {};
  let clock = Date.now(), elapsed = 0, uuidCount = 0;
  if (!options.noJob) store.set('sol-action-session-v1', JSON.stringify({version: 1, job_id: JOB, capability: CAP, source_csv: 'PRIVATE-RAW-CSV-SHOULD-NOT-BE-DISPLAYED'}));
  if (options.saved) store.set(KEY, JSON.stringify(options.saved));
  const $ = id => { if (!elements.has(id)) elements.set(id, new Element()); return elements.get(id); };
  class Clock extends Date { constructor(value) { super(value === undefined ? clock : value); } static now() { return clock; } }
  const context = {
    document: {getElementById: $, createElement: () => new Element(), addEventListener: (type, callback) => { events[type] = callback; }},
    addEventListener: (type, callback) => { events[type] = callback; },
    localStorage: {getItem: key => store.get(key) || null, setItem: (key, value) => { if (options.storageFails || (options.clearFails && JSON.parse(value).pending === null)) throw new Error('denied'); store.set(key, value); }},
    crypto: {randomUUID: () => '30000000-0000-4000-8000-' + String(++uuidCount).padStart(12, '0')},
    Date: Clock, performance: {now: () => elapsed}, AbortController, setTimeout, clearTimeout, setInterval: callback => timers.push(callback),
    fetch: async (url, init) => {
      assert.equal(url, '/api/mission');
      const body = JSON.parse(init.body); requests.push(body);
      if (body.action === 'verify') {
        const pending = JSON.parse(store.get(KEY)).pending;
        assert.equal(pending.input.request_id, body.input.request_id, 'verify UUID must be durable before network');
        assert.equal(pending.input.mission_id, body.input.mission_id);
        assert.equal('capability' in pending.input, false, 'capability remains under the existing job key only');
      }
      let base;
      if (body.action === 'status') base = {ok: true, job_id: body.input.job_id, status: 'HISTORICAL_NOT_CURRENT', found: true, missions: [mission()], current_reuse_authorized: false};
      if (body.action === 'verify') base = {ok: true, action: 'verify', status: 'TECHNICAL_RESULT_VERIFIED', job_id: body.input.job_id, mission_id: body.input.mission_id, request_id: body.input.request_id, report: report(clock), current_reuse_authorized: true};
      if (body.action === 'receipt') base = {ok: true, found: false, status: 'OUTCOME_UNKNOWN', job_id: body.input.job_id, mission_id: body.input.mission_id, target_request_id: body.input.target_request_id, receipt: null, current_reuse_authorized: false};
      let value = options.responder ? await options.responder(body, {base, clock, store}) : undefined;
      if (value === undefined) value = base;
      return {ok: true, json: () => Promise.resolve(value)};
    },
  };
  vm.createContext(context); vm.runInContext(SOURCE, context, {filename: 'missions.js'});
  async function click(id) { const e = $(id); if (!e.disabled) await e.events.click?.(); }
  async function select(id = MISSION) { $('mission-select').value = id; await $('mission-select').events.change?.(); }
  async function ready() { await click('mission-load'); await select(); }
  return {$, context, requests, store, click, ready, select, uuids: () => uuidCount, state: () => JSON.parse(store.get(KEY) || 'null'), advance(ms, wall = ms) { elapsed += ms; clock += wall; timers.forEach(callback => callback()); }, event(name) { events[name]?.(); }, text() { return [...elements.values()].map(function content(e) { return e.textContent + e.children.map(content).join(' '); }).join(' '); }};
}
async function test(name, fn) { try { await fn(); checks.push({name, status: 'PASS'}); } catch (error) { checks.push({name, status: 'FAIL', error: error.message}); } }
async function run() {
  await test('opening panel makes no request and a job is required without automatic mission registration', async () => {
    const app = harness({noJob: true}); assert.equal(app.requests.length, 0); await app.click('mission-load'); assert.equal(app.requests.length, 0); assert.match(app.$('mission-message').textContent, /d’abord un travail CSV/);
  });
  await test('status with no mission remains explicit and never calls register or verify', async () => {
    const app = harness({responder: (body, {base}) => body.action === 'status' ? {...base, found: false, missions: []} : base});
    await app.click('mission-load'); assert.equal(app.$('mission-verify').disabled, true); assert.equal(app.requests.length, 1); assert.match(app.$('mission-message').textContent, /opérateur/); assert.equal(app.uuids(), 0);
  });
  await test('all 32 matrix requirements, original CSV texts and exact roles remain separately visible', async () => {
    const app = harness(); await app.ready(); const items = app.$('mission-matrix').children; assert.equal(items.length, 32);
    for (let i = 0; i < rows.length; i++) { assert.equal(items[i].children[0].textContent, rows[i].requirement.text); assert.ok(items[i].children[1].textContent.includes(rows[i].requirement.id)); assert.ok(items[i].children[1].textContent.includes(rows[i].role)); }
    assert.equal(app.$('mission-job-mandate').textContent, 'Demande CSV exacte'); assert.equal(app.$('mission-job-requirements').children.length, 2); assert.match(app.$('mission-definition-summary').textContent, /32 lignes/);
    assert.match(app.$('mission-select').children[1].textContent, /Demande CSV exacte/); assert.ok(app.$('mission-select').children[1].textContent.includes(MISSION)); assert.equal(app.$('mission-select').children[1].value, MISSION);
    assert.equal(app.text().includes(CAP), false); assert.equal(app.text().includes('PRIVATE-RAW-CSV'), false);
  });
  await test('fresh exact technical verification keeps the general mandate UNKNOWN and expires without a reload', async () => {
    const app = harness(); await app.ready(); await app.click('mission-verify'); assert.equal(app.state().pending, null); assert.match(app.$('mission-freshness').textContent, /à cet instant/); assert.match(app.$('mission-freshness').textContent, /Demande générale : UNKNOWN/);
    const count = app.requests.length; app.advance(61000); assert.match(app.$('mission-freshness').textContent, /historique/); assert.equal(app.requests.length, count);
  });
  await test('status and reload never restore authority from a fresh looking historical PASS', async () => {
    const app = harness({responder: (body, {base, clock}) => { if (body.action === 'status') base.missions[0].last_report = report(clock); return base; }});
    await app.ready(); assert.match(app.$('mission-freshness').textContent, /historique/); await app.click('mission-verify'); await app.click('mission-load'); assert.match(app.$('mission-freshness').textContent, /historique/);
    const reloaded = harness({saved: app.state()}); assert.equal(reloaded.requests.length, 0); assert.doesNotMatch(reloaded.$('mission-freshness').textContent, /à cet instant/);
  });
  await test('delayed visibility and pageshow recheck expiry and monotonic time prevents clock rollback extension', async () => {
    const app = harness(); await app.ready(); await app.click('mission-verify'); app.advance(61000, -1000); app.event('visibilitychange'); app.event('pageshow'); assert.match(app.$('mission-freshness').textContent, /historique/); assert.equal(app.requests.length, 2);
  });
  await test('a historical report for only part of the matrix does not replace all preserved requirements', async () => {
    const app = harness({responder: (body, {base, clock}) => { if (body.action === 'status') { base.missions[0].last_report = report(clock); base.missions[0].last_report.requirements = base.missions[0].last_report.requirements.slice(0, 16); } return base; }});
    await app.ready(); assert.equal(app.$('mission-matrix').children.length, 32); assert.equal(app.$('mission-report-details').hidden, true); assert.doesNotMatch(app.$('mission-freshness').textContent, /à cet instant/);
  });
  await test('lost verify response after commit recovers by exact readonly receipt and never verifies again', async () => {
    let committed;
    const journal = [];
    const app = harness({responder: (body, {base}) => {
      if (body.action === 'verify') { committed = {...base, current_reuse_authorized: false}; journal.push(body.input.request_id); throw new Error('network lost after commit'); }
      if (body.action === 'receipt') return {...base, found: true, status: 'HISTORICAL_NOT_CURRENT', receipt: committed};
      return base;
    }});
    await app.ready(); await app.click('mission-verify'); const original = clone(app.state().pending); const uuids = app.uuids();
    await app.click('mission-verify'); assert.equal(app.requests.filter(r => r.action === 'verify').length, 1);
    await app.click('mission-receipt'); const lookup = app.requests.at(-1); assert.equal(lookup.action, 'receipt'); assert.equal(lookup.input.target_request_id, original.input.request_id); assert.equal(committed.status, 'TECHNICAL_RESULT_VERIFIED', 'SQL keeps the original nested status while removing current authority');
    assert.deepEqual(Object.keys(lookup.input).sort(), ['capability', 'job_id', 'mission_id', 'target_request_id']); assert.equal(app.uuids(), uuids); assert.equal(journal.length, 1); assert.equal(app.state().pending, null); assert.match(app.$('mission-freshness').textContent, /historique/);
  });
  await test('absent receipt retains the exact original pending across repeated readonly lookups', async () => {
    const app = harness({responder: (body, {base}) => { if (body.action === 'verify') throw new Error('network lost'); return base; }});
    await app.ready(); await app.click('mission-verify'); const pending = JSON.stringify(app.state().pending), uuids = app.uuids(); await app.click('mission-receipt'); await app.click('mission-receipt');
    assert.equal(JSON.stringify(app.state().pending), pending); assert.equal(app.uuids(), uuids); assert.equal(app.requests.filter(r => r.action === 'verify').length, 1); assert.match(app.$('mission-message').textContent, /UNKNOWN/);
  });
  await test('reload keeps a pending intention and retrieves its original receipt without loading or verifying again', async () => {
    let committed;
    const first = harness({responder: (body, {base}) => { if (body.action === 'verify') { committed = {...base, current_reuse_authorized: false}; throw new Error('lost'); } return base; }});
    await first.ready(); await first.click('mission-verify');
    const app = harness({saved: first.state(), responder: (_body, {base}) => ({...base, found: true, status: 'HISTORICAL_NOT_CURRENT', receipt: committed})});
    assert.equal(app.requests.length, 0); assert.ok(app.$('mission-message').textContent.includes(first.state().pending.input.request_id)); assert.ok(app.$('mission-pending-id').textContent.includes(JOB)); assert.ok(app.$('mission-pending-id').textContent.includes(MISSION)); assert.equal(app.$('mission-pending-id').textContent.includes(CAP), false); await app.click('mission-receipt'); assert.equal(app.requests.length, 1); assert.equal(app.requests[0].action, 'receipt'); assert.equal(app.uuids(), 0); assert.equal(app.state().pending, null); assert.equal(app.$('mission-matrix').children.length, 32); assert.match(app.$('mission-report-time').textContent, new RegExp(MISSION)); assert.match(app.$('mission-freshness').textContent, /historique/);
  });
  await test('a known technical FAIL is preserved without a general verdict or current badge', async () => {
    const app = harness({responder: (body, {base}) => { if (body.action === 'verify') { base.current_reuse_authorized = false; base.report.status = 'NOT_VERIFIED'; base.report.technical_verdict = 'FAIL'; base.report.checks[0].verdict = 'FAIL'; } return base; }});
    await app.ready(); await app.click('mission-verify'); assert.equal(app.state().pending, null); assert.match(app.$('mission-freshness').textContent, /FAIL/); assert.match(app.$('mission-freshness').textContent, /Demande générale : UNKNOWN/); assert.doesNotMatch(app.$('mission-freshness').textContent, /à cet instant/); assert.equal(app.requests.length, 2);
  });
  await test('wrong job, mission, request UUID or missing matrix in verification keeps the exact pending', async () => {
    for (const variant of ['job', 'mission', 'request', 'matrix', 'general']) {
      const app = harness({responder: (body, {base}) => { if (body.action === 'verify') {
        if (variant === 'job') base.job_id = '10000000-0000-4000-8000-000000000099';
        if (variant === 'mission') base.mission_id = '20000000-0000-4000-8000-000000000099';
        if (variant === 'request') base.request_id = '30000000-0000-4000-8000-000000000099';
        if (variant === 'matrix') base.report.requirements.pop();
        if (variant === 'general') base.report.general_mandate = 'PASS';
      } return base; }});
      await app.ready(); await app.click('mission-verify'); assert.ok(app.state().pending, variant); assert.equal(app.$('mission-verify').disabled, true); assert.doesNotMatch(app.$('mission-freshness').textContent, /à cet instant/);
    }
  });
  await test('wrong lookup envelope or nested receipt identity cannot erase pending or restore authority', async () => {
    for (const variant of ['outer-job', 'outer-mission', 'outer-target', 'nested-job', 'nested-mission', 'nested-request', 'current', 'malformed']) {
      let committed;
      const app = harness({responder: (body, {base}) => {
        if (body.action === 'verify') { committed = {...base, current_reuse_authorized: false}; throw new Error('network lost'); }
        if (body.action === 'receipt') {
          base.found = true; base.status = 'HISTORICAL_NOT_CURRENT'; base.receipt = clone(committed);
          const wrong = '10000000-0000-4000-8000-000000000099';
          if (variant === 'outer-job') base.job_id = wrong;
          if (variant === 'outer-mission') base.mission_id = wrong;
          if (variant === 'outer-target') base.target_request_id = wrong;
          if (variant === 'nested-job') base.receipt.job_id = wrong;
          if (variant === 'nested-mission') base.receipt.mission_id = wrong;
          if (variant === 'nested-request') base.receipt.request_id = wrong;
          if (variant === 'current') base.receipt.current_reuse_authorized = true;
          if (variant === 'malformed') base.receipt.report = {};
        } return base;
      }});
      await app.ready(); await app.click('mission-verify'); const pending = JSON.stringify(app.state().pending); await app.click('mission-receipt'); assert.equal(JSON.stringify(app.state().pending), pending, variant); assert.doesNotMatch(app.$('mission-freshness').textContent, /à cet instant/);
    }
  });
  await test('local storage failure prevents sending and clearing failure retains the durable pending', async () => {
    const denied = harness({storageFails: true}); await denied.ready(); await denied.click('mission-verify'); assert.equal(denied.requests.length, 1);
    const app = harness({clearFails: true}); await app.ready(); await app.click('mission-verify'); assert.ok(app.state().pending); assert.equal(app.$('mission-verify').disabled, true); await app.click('mission-verify'); assert.equal(app.requests.filter(r => r.action === 'verify').length, 1);
  });
  await test('failed list refresh keeps old provenance visible and blocks verification until a correlated refresh', async () => {
    let fail = false;
    const app = harness({responder: (body, {base}) => { if (body.action === 'status' && fail) throw new Error('status network unavailable'); return base; }});
    await app.ready(); fail = true; await app.click('mission-load'); assert.equal(app.$('mission-matrix').children.length, 32); assert.ok(app.$('mission-list-provenance').textContent.includes(JOB)); assert.match(app.$('mission-list-provenance').textContent, /Lecture actuelle non confirmée/); assert.equal(app.$('mission-verify').disabled, true); await app.click('mission-verify'); assert.equal(app.requests.filter(r => r.action === 'verify').length, 0);
    fail = false; await app.click('mission-load'); await app.select(); assert.equal(app.$('mission-verify').disabled, false); await app.click('mission-verify'); assert.equal(app.requests.filter(r => r.action === 'verify').length, 1);
  });
  await test('changing the browser job suspends the old copy without a secret request or another UUID', async () => {
    const app = harness(); await app.ready(); const before = app.requests.length;
    const differentJob = '10000000-0000-4000-8000-000000000099'; const differentCapability = 'c'.repeat(64);
    app.store.set('sol-action-session-v1', JSON.stringify({version: 1, job_id: differentJob, capability: differentCapability})); app.advance(1);
    assert.equal(app.requests.length, before); assert.equal(app.uuids(), 0); assert.equal(app.$('mission-verify').disabled, true); assert.ok(app.$('mission-list-provenance').textContent.includes(JOB)); assert.match(app.$('mission-list-provenance').textContent, /a changé/); assert.equal(app.text().includes(differentCapability), false); await app.click('mission-verify'); assert.equal(app.requests.length, before);
  });
  await test('untrusted labels render as literal text and raw evidence never prints capabilities or CSV', async () => {
    const attack = '<img src=x onerror=alert(1)>';
    const app = harness({responder: (body, {base}) => { if (body.action === 'status') base.missions[0].definition.requirements_matrix[0].requirement.text = attack; if (body.action === 'verify') { base.report.requirements[0].requirement.text = attack; base.report.checks[0].evidence = {capability: CAP, source_csv: 'PRIVATE-RAW-CSV-SHOULD-NOT-BE-DISPLAYED'}; } return base; }});
    await app.ready(); assert.equal(app.$('mission-matrix').children[0].children[0].textContent, attack); await app.click('mission-verify'); assert.equal(app.text().includes(CAP), false); assert.equal(app.text().includes('PRIVATE-RAW-CSV'), false); assert.equal(SOURCE.includes('innerHTML'), false);
  });
  const receipt = {schema: 'SOL_MISSION_UI_TEST/v1', observed_at: new Date().toISOString(), app_source_sha256: crypto.createHash('sha256').update(SOURCE).digest('hex'), scope: 'Synthetic DOM, storage and transport only; no browser or live mission proof', runtime: typeof Deno !== 'undefined' ? {runner: 'DENO_NODE_COMPATIBILITY', ...Deno.version} : {runner: 'NODE', node: process.version}, test_count: checks.length, passed: checks.filter(c => c.status === 'PASS').length, failed: checks.filter(c => c.status === 'FAIL').length, checks};
  fs.mkdirSync(path.join(ROOT, 'evidence'), {recursive: true}); fs.writeFileSync(path.join(ROOT, 'evidence/mission-ui-tests.json'), JSON.stringify(receipt, null, 2) + '\n'); return receipt;
}
module.exports = {run};
if (require.main === module) run().then(value => { console.log(JSON.stringify(value, null, 2)); process.exitCode = value.failed ? 1 : 0; });
