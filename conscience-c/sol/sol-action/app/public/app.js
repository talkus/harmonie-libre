(function (root) {
  'use strict';
  const STORAGE_KEY = 'sol-action-session-v1';
  const SAMPLE = 'id,currency,amount\ncommande-1,EUR,120.50\ncommande-2,EUR,-20.25\ncommande-3,USD,35.10\ncommande-4,EUR,0.05\ncommande-5,USD,4.90\n';
  const DEFAULT_REQUIREMENTS = ['Conserver chaque ligne d’entrée.', 'Calculer exactement les totaux, sans arrondi intermédiaire.', 'Séparer les devises et identifier le tableau source.'];
  const DIAGNOSTICS = {
    INVALID_MANDATE: ['mandate', 'Écrivez une demande de 1 à 10 000 caractères.'],
    INVALID_REQUIREMENTS: ['requirements', 'Indiquez 1 à 32 exigences, une par ligne, de 2 000 caractères maximum chacune.'],
    CSV_SIZE: ['source-csv', 'Le tableau doit contenir entre 1 octet et 32 Kio.'],
    CSV_ENCODING: ['source-csv', 'Retirez les caractères NUL et les marques BOM du tableau.'],
    CSV_LINE_ENDING: ['source-csv', 'Utilisez des fins de ligne LF ou CRLF ; un retour CR isolé n’est pas accepté.'],
    CSV_QUOTING: ['source-csv', 'Fermez les champs entre guillemets et doublez chaque guillemet intérieur.'],
    CSV_HEADER: ['source-csv', 'La première ligne doit contenir exactement id,currency,amount.'],
    CSV_ROWS: ['source-csv', 'Ajoutez 1 à 500 lignes de données après l’en-tête.'],
    CSV_COLUMNS: ['source-csv', 'Chaque ligne doit contenir exactement trois champs, séparés par des virgules.'],
    CSV_ID: ['source-csv', 'Utilisez un identifiant unique de 1 à 80 caractères : lettres, chiffres, puis . _ : ou - autorisés.'],
    CSV_DUPLICATE_ID: ['source-csv', 'Cet identifiant apparaît déjà ; attribuez un identifiant différent à chaque ligne.'],
    CSV_CURRENCY: ['source-csv', 'Écrivez la devise avec trois lettres majuscules, par exemple EUR.'],
    CSV_AMOUNT: ['source-csv', 'Écrivez un montant avec 1 à 12 chiffres avant le point et au plus 2 décimales, par exemple -12.50.']
  };
  const DIAGNOSTIC_ALIASES = {
    REQUIREMENTS: 'INVALID_REQUIREMENTS', REQUIREMENT_TEXT: 'INVALID_REQUIREMENTS',
    'STRING_REQUIRED:mandate': 'INVALID_MANDATE', 'STRING_BOUNDS:mandate': 'INVALID_MANDATE',
    'MISSING_FIELD:mandate': 'INVALID_MANDATE', 'STRING_REQUIRED:source_csv': 'CSV_SIZE', 'STRING_BOUNDS:source_csv': 'CSV_SIZE',
    CSV_LONE_CR: 'CSV_LINE_ENDING', CSV_AFTER_QUOTE: 'CSV_QUOTING', CSV_QUOTE_IN_UNQUOTED: 'CSV_QUOTING',
    CSV_UNCLOSED_QUOTE: 'CSV_QUOTING', CSV_ROW_LIMIT: 'CSV_ROWS', CSV_ROW_COUNT: 'CSV_ROWS'
  };
  function diagnosticFor(response, line) {
    const rawCode = response && response.error;
    if (typeof rawCode !== 'string') return null;
    const code = Object.prototype.hasOwnProperty.call(DIAGNOSTICS, rawCode) ? rawCode : Object.prototype.hasOwnProperty.call(DIAGNOSTIC_ALIASES, rawCode) ? DIAGNOSTIC_ALIASES[rawCode] : null;
    const item = code && DIAGNOSTICS[code];
    if (!item) return null;
    return {code, field: item[0], line: Number.isInteger(line) && line > 0 && line <= 32769 ? line : null, message: item[1]};
  }
  function fullMatch(pattern, value) {
    if (typeof value !== 'string') return false;
    const match = pattern.exec(value);
    return Boolean(match && match[0] === value);
  }
  function validateCsv(source) {
    const fail = (error, line) => ({ok: false, scope: 'INPUT_FORMAT_ONLY', errors: [diagnosticFor({error}, line)]});
    if (typeof source !== 'string' || new TextEncoder().encode(source).length < 1 || new TextEncoder().encode(source).length > 32768) return fail('CSV_SIZE');
    if (/[\u0000\ufeff]/.test(source)) return fail('CSV_ENCODING');
    const records = [], starts = [];
    let fields = [], value = '', mode = 'start', line = 1, start = 1, quoteStart = 1;
    const field = () => { fields.push(value); value = ''; mode = 'start'; };
    const record = () => { field(); records.push(fields); starts.push(start); fields = []; };
    for (let i = 0; i < source.length; i++) {
      const char = source[i];
      if (mode === 'quoted') {
        if (char === '"') {
          if (source[i + 1] === '"') { value += '"'; i++; } else mode = 'after_quote';
        } else { value += char; if (char === '\n') line++; }
      } else if (char === ',') field();
      else if (char === '\n' || char === '\r') {
        if (char === '\r') { if (source[i + 1] !== '\n') return fail('CSV_LINE_ENDING', line); i++; }
        record(); line++; start = line;
      } else if (mode === 'after_quote') return fail('CSV_QUOTING', line);
      else if (char === '"') {
        if (mode !== 'start') return fail('CSV_QUOTING', line);
        mode = 'quoted'; quoteStart = line;
      } else { value += char; mode = 'unquoted'; }
    }
    if (mode === 'quoted') return fail('CSV_QUOTING', quoteStart);
    if (mode !== 'start' || value !== '' || fields.length) record();
    if (!records.length || records[0].length !== 3 || records[0].some((x, i) => x !== ['id', 'currency', 'amount'][i])) return fail('CSV_HEADER', 1);
    if (records.length < 2 || records.length > 501) return fail('CSV_ROWS');
    const seen = new Set();
    for (let i = 1; i < records.length; i++) {
      const row = records[i];
      if (row.length !== 3) return fail('CSV_COLUMNS', starts[i]);
      if (!fullMatch(/^[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}$/, row[0])) return fail('CSV_ID', starts[i]);
      if (seen.has(row[0])) return fail('CSV_DUPLICATE_ID', starts[i]);
      if (!fullMatch(/^[A-Z]{3}$/, row[1])) return fail('CSV_CURRENCY', starts[i]);
      if (!fullMatch(/^[+-]?[0-9]{1,12}(?:\.[0-9]{1,2})?$/, row[2])) return fail('CSV_AMOUNT', starts[i]);
      seen.add(row[0]);
    }
    return {ok: true, scope: 'INPUT_FORMAT_ONLY', errors: [], rows: records.length - 1};
  }
  function validateCreation(mandate, requirements, source) {
    const errors = [];
    if (typeof mandate !== 'string' || !mandate.trim() || Array.from(mandate).length > 10000) errors.push(diagnosticFor({error: 'INVALID_MANDATE'}));
    if (!Array.isArray(requirements) || !requirements.length || requirements.length > 32 || requirements.some(x => typeof x !== 'string' || !x.trim() || Array.from(x).length > 2000)) errors.push(diagnosticFor({error: 'INVALID_REQUIREMENTS'}));
    const csv = validateCsv(source); errors.push(...csv.errors);
    return {ok: errors.length === 0, scope: 'INPUT_FORMAT_ONLY', errors};
  }
  function capability(cryptoProvider) {
    return Array.from(cryptoProvider.getRandomValues(new Uint8Array(32)), x => x.toString(16).padStart(2, '0')).join('');
  }
  function validResult(value) {
    return Boolean(value && typeof value === 'object' && fullMatch(/^[a-f0-9]{64}$/, value.source_sha256) && Number.isInteger(value.rows) && value.rows > 0 && value.rows <= 500 && Array.isArray(value.row_ids) && value.row_ids.length === value.rows && Array.isArray(value.totals) && value.totals.every(x => x && fullMatch(/^[A-Z]{3}$/, x.currency) && fullMatch(/^-?[0-9]+\.[0-9]{2}$/, x.amount)));
  }
  function currentCompletion(response, now, receivedAt, elapsed) {
    const completion = response && response.completion;
    return Boolean(response && response.ok === true && response.status === 'COMPLETED_BOUNDED' && response.current_reuse_authorized === true && !response.deduplicated && completion && completion.status === 'COMPLETED_BOUNDED' && completion.scope === 'CSV_EXACT_CENTS_ONLY' && Number.isFinite(Date.parse(completion.expires_at)) && Date.parse(completion.expires_at) > now && now >= receivedAt && elapsed >= 0 && elapsed < 60000);
  }
  function verificationWindow(response, receivedAt, receivedMonotonic, sentMonotonic, sentAt = receivedAt) {
    const verification = response && response.verification;
    if (!response || response.ok !== true || response.action !== 'verify' || response.deduplicated || response.historical_status || response.status === 'HISTORICAL_NOT_CURRENT' || response.pending || !verification || verification.status !== 'PASS' || verification.current_reuse_authorized !== true) return null;
    const serverTime = verification.verified_at === undefined ? verification.observed_at : verification.verified_at;
    if (typeof serverTime !== 'string' || typeof verification.expires_at !== 'string') return null;
    const verifiedAt = Date.parse(serverTime);
    const observedAt = Date.parse(verification.observed_at);
    const explicitVerifiedAt = Date.parse(verification.verified_at);
    const expiresAt = Date.parse(verification.expires_at);
    const lifetime = expiresAt - verifiedAt;
    const roundtrip = receivedMonotonic - sentMonotonic;
    if (![receivedAt, receivedMonotonic, sentMonotonic, sentAt, verifiedAt, expiresAt, roundtrip].every(Number.isFinite) || receivedAt < sentAt || roundtrip < 0 || lifetime <= 0 || lifetime > 60000 ||
        (verification.verified_at !== undefined && verification.observed_at !== undefined && (typeof verification.observed_at !== 'string' || !Number.isFinite(observedAt) || !Number.isFinite(explicitVerifiedAt) || verification.observed_at !== verification.verified_at))) return null;
    // Server time bounds the lifetime. Subtract the whole request duration, so a
    // delayed response cannot start a new sixty-second window on receipt.
    const budget = Math.min(lifetime - roundtrip, expiresAt - receivedAt);
    if (budget <= 0) return null;
    return {response, receivedAt, receivedMonotonic, lastWall: receivedAt, lastMonotonic: receivedMonotonic, deadline: receivedMonotonic + budget, revoked: false};
  }
  function currentVerification(window, now, monotonic) {
    if (!window || window.revoked) return false;
    const valid = Number.isFinite(now) && Number.isFinite(monotonic) && now >= window.lastWall && monotonic >= window.lastMonotonic && monotonic < window.deadline && now < Date.parse(window.response.verification.expires_at);
    window.lastWall = now; window.lastMonotonic = monotonic;
    if (!valid) window.revoked = true;
    return valid;
  }
  function controlledRefusal(intent, response, historical = false, requirements) {
    if (root.SolRequirements && root.SolRequirements.controlledRefusal(intent, response, historical, requirements)) return true;
    const receiptOrigin = response && (
      response.receipt_kind === 'CONTROLLED_REFUSAL' && response.receipt_recording_effect === 'APPEND_ONLY_BRIDGE_RECEIPT_RECORDED' ||
      intent && intent.action === 'create' && response.receipt_kind === 'CONTROLLED_CREATION_REFUSAL' && response.receipt_recording_effect === 'APPEND_ONLY_CREATION_GUARD_RECEIPT_RECORDED');
    return Boolean(intent && intent.input && ['create', 'verify', 'complete'].includes(intent.action) && response && typeof response === 'object' && !Array.isArray(response) &&
      response.ok === false && response.action === intent.action && response.job_id === intent.input.job_id && response.request_id === intent.input.request_id &&
      (historical ? response.status === 'HISTORICAL_NOT_CURRENT' && response.historical_status === 'REJECTED' && response.needs_current_revalidation === true : response.status === 'REJECTED') &&
      response.effect === 'NONE_SQL_TRANSACTION_ROLLED_BACK' && response.effect_scope === 'CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY' && response.core_effect_scope === 'THIS_RPC_SQL_TRANSACTION_ONLY' &&
      receiptOrigin && response.business_effect === 'NONE_CORE_ACTION_ROLLED_BACK' && response.terminal === true && response.durable_refusal === true &&
      response.worker_reexecuted === false && response.current_reuse_authorized === false && response.automatic_retry === false);
  }
  function liveCreateRefusal(intent, response) {
    // Only the response to this live create call can establish its rollback.
    // This is not a durable receipt and is never accepted during recovery.
    return Boolean(intent && intent.action === 'create' && intent.input && response && typeof response === 'object' && !Array.isArray(response) &&
      response.ok === false && response.status === 'REJECTED' && response.sqlstate === 'P0001' && response.action === 'create' && response.job_id === intent.input.job_id && response.request_id === intent.input.request_id &&
      response.effect === 'NONE_SQL_TRANSACTION_ROLLED_BACK' && response.effect_scope === 'THIS_RPC_SQL_TRANSACTION_ONLY' && response.current_reuse_authorized === false && response.automatic_retry === false &&
      !response.deduplicated && !response.historical_status && !response.durable_refusal);
  }
  function refusalCode(response) {
    // Only a stable, understood code is displayed. Arbitrary server text is not
    // a user-facing error or an inferred diagnosis.
    return response && response.error === 'FRESH_VERIFICATION_REQUIRED' ? 'FRESH_VERIFICATION_REQUIRED' : null;
  }
  function newIntent(action, input, uuidProvider) {
    const copy = Object.assign({}, input);
    if (!['status', 'audit', 'receipt', 'creation_receipt'].includes(action)) copy.request_id = uuidProvider();
    if (action === 'produce') copy.result_request_id = uuidProvider();
    return {action, input: copy};
  }
  const helpers = {capability, currentCompletion, verificationWindow, currentVerification, controlledRefusal, liveCreateRefusal, refusalCode, diagnosticFor, validateCsv, validateCreation, newIntent, validResult, SAMPLE, STORAGE_KEY};
  if (typeof module !== 'undefined' && module.exports) module.exports = helpers;
  root.SolAction = helpers;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  function aria(element, name, value) {
    if (typeof element.setAttribute === 'function') element.setAttribute(name, value);
    else element[name === 'aria-busy' ? 'ariaBusy' : 'ariaInvalid'] = value;
  }
  // Shared by CSV and Mission preparation/transports. Busy never establishes
  // that an effect succeeded or that a missing response is known.
  const activities = new Map(); let activitySequence = 0;
  const preparations = new Map();
  root.SolUiActivity = {begin(channel, action) {
    const labels = {prepare: 'Préparation de la demande : attente du verrou de reprise…', create: 'Enregistrement de la demande en cours…', produce: 'Calcul en cours…', verify: channel === 'mission' ? 'Vérification des liens en cours…' : 'Vérification du résultat en cours…', complete: 'Clôture en cours…', status: 'Consultation de l’état en cours…', audit: 'Contrôle du journal en cours…', receipt: 'Recherche du reçu en cours…', creation_receipt: 'Recherche de l’issue de création en cours…', reconcile: 'Recherche de l’issue de la demande en cours…'};
    if (preparations.has(channel)) { activities.delete(preparations.get(channel)); preparations.delete(channel); }
    const key = ++activitySequence; activities.set(key, labels[action] || 'Demande en cours…');
    if (action === 'prepare') preparations.set(channel, key);
    function update() {
      aria($('work-area'), 'aria-busy', activities.size ? 'true' : 'false');
      const text = activities.size ? Array.from(activities.values()).join(' ') : '';
      if ($('operation-status').textContent !== text) $('operation-status').textContent = text;
    }
    update(); return () => { activities.delete(key); if (preparations.get(channel) === key) preparations.delete(channel); update(); };
  }};
  let fieldDiagnostics = [];
  function setDiagnostics(items) {
    fieldDiagnostics = items.filter(Boolean);
    ['mandate', 'requirements', 'source-csv'].forEach(field => {
      const item = fieldDiagnostics.find(x => x.field === field);
      aria($(field), 'aria-invalid', item ? 'true' : 'false');
      $(field + '-error').hidden = !item;
      $(field + '-error').textContent = item ? (item.line ? 'Ligne ' + item.line + ' : ' : '') + item.message : '';
    });
  }
  let state = null;
  let busy = false;
  let authority = null;
  let verificationAuthority = null;
  let message = {text: 'Votre demande sera conservée avant tout calcul.', kind: 'neutral'};
  const slots = root.SolIntentSlot;
  const MISSION_KEY = 'sol-action-mission-session-v1';
  const slotKeys = [STORAGE_KEY, MISSION_KEY];
  let storageBlocked = false;
  let readOnlyView = null;
  function requireSlots() {
    if (!slots) throw new Error('Le contrôle de reprise entre onglets n’est pas chargé. Aucune nouvelle action ne sera envoyée.');
    return slots;
  }
  function readState() { return requireSlots().read(STORAGE_KEY, slots.validJob); }
  function refreshState(notify = false) {
    try {
      const latest = readState();
      if (readOnlyView && (slots.available() || !slots.same(latest, readOnlyView.base))) readOnlyView = null;
      const visible = readOnlyView ? readOnlyView.value : latest;
      const changed = !slots.same(state, visible);
      state = visible; storageBlocked = false;
      if (changed) {
        authority = null;
        verificationAuthority = null;
        if (notify) message = {text: state && state.pending ? 'Reprise partagée : l’intention ' + state.pending.intent.input.request_id + ' attend son reçu. Aucun calcul n’a été relancé.' : 'La tâche partagée a changé. Consultez son état ; les reçus restent historiques.', kind: 'unknown'};
      }
      return changed;
    } catch (error) {
      storageBlocked = true; authority = null; verificationAuthority = null;
      message = {text: error.message || 'La reprise locale est illisible et reste conservée.', kind: 'unknown'};
      return false;
    }
  }
  function otherPending() {
    const mission = requireSlots().read(MISSION_KEY, slots.validMission);
    return mission && mission.pending;
  }
  function assertNoMissionPending() {
    const pending = otherPending();
    if (pending) throw new Error('Une vérification de mission attend son reçu exact : ' + pending.input.request_id + '. Retrouvez ce reçu avant une nouvelle action CSV.');
  }
  function requireCurrent(expected, pending) {
    const latest = readState();
    if (!slots.identity(latest, expected)) throw new Error('La tâche ou sa clé a changé dans un autre onglet. Aucun ancien reçu ne remplace la reprise partagée.');
    if (pending !== undefined && !slots.same(latest.pending, pending)) throw new Error('Une autre intention est conservée. L’ancien retour ne peut pas l’effacer ni autoriser une suite.');
    return latest;
  }
  function persist() {
    slots.write(STORAGE_KEY, state);
    state = readState();
  }
  async function commit(expected, pending, callback) {
    return requireSlots().withKeys(slotKeys, () => {
      state = requireCurrent(expected, pending);
      const result = callback();
      persist();
      return result;
    });
  }
  async function send(intent, expected, pending, blockMission = true) {
    const packet = await requireSlots().withKeys(slotKeys, () => {
      state = requireCurrent(expected, pending);
      if (blockMission) assertNoMissionPending();
      // Fetch starts under the lock. The promise is boxed so the durable pending,
      // rather than a long-held network lock, excludes a second reservation.
      return {response: post(intent)};
    });
    return packet.response;
  }
  refreshState(true);
  if (slots && !slots.available()) message = {text: slots.unavailable().message, kind: 'unknown'};
  function appendHistory(action, response) {
    state.history = (state.history || []).concat([{action, received_at: new Date().toISOString(), response}]).slice(-40);
  }
  function show(text, kind = 'neutral') { message = {text, kind}; render(); }
  function verificationIsCurrent() {
    if (!verificationAuthority || !state || verificationAuthority.response.job_id !== state.job_id || !slots.same(verificationAuthority.response.verification, state.verification) || verificationAuthority.response.source_sha256 !== state.source_sha256) { verificationAuthority = null; return false; }
    return currentVerification(verificationAuthority, Date.now(), performance.now());
  }
  function showRefusal(response, known) {
    if (response && response.receipt_kind === 'REQUIREMENTS_GUARD_REFUSAL') {
      const scope = response.action === 'produce' ? 'Aucun begin ni calculateur n’a été lancé par cet appel.' : 'Aucune vérification ni clôture noyau n’a été lancée par cet appel ; le résultat antérieur reste conservé.';
      show(known ? 'Le contrôle des exigences a refusé cette action. ' + scope + ' Le refus est enregistré. Consultez chaque ligne ci-dessous, puis préparez une correction explicite. Le mandat général reste UNKNOWN.' : 'Le contrôle des exigences annoncé ne suffit pas à établir l’issue. L’intention reste conservée ; retrouvez son reçu exact sans relancer le calcul.', known ? 'error' : 'unknown');
      return;
    }
    const code = refusalCode(response);
    const diagnosis = diagnosticFor(response);
    if (diagnosis) setDiagnostics([diagnosis]);
    const detail = code ? ' Code : ' + code + '.' : ' Aucun code reconnu n’est disponible dans cette vue.';
    const scope = known ? ' L’action refusée est sans effet métier ; son reçu reste enregistré.' : ' L’issue globale reste inconnue ; l’intention est conservée.';
    const next = code === 'FRESH_VERIFICATION_REQUIRED' ? (known ? ' Cliquez sur « Vérifier », puis sur « Clore » lorsque la vérification est actuelle.' : ' Rapprochez d’abord le reçu. Si le refus est confirmé, cliquez sur « Vérifier » avant de clore.') : ' Consultez le reçu et ses contrôles avant une nouvelle action explicite.';
    show('Le serveur a refusé cette demande.' + (diagnosis ? ' ' + diagnosis.message : detail) + scope + next, known ? 'error' : 'unknown');
  }
  function recordRefusal(original, response, reconciliation) {
    state.rejected_intents = (state.rejected_intents || []).concat([{intent: original.intent, response, reconciliation: reconciliation || undefined, proof_origin: response.durable_refusal === true ? 'DURABLE_SERVER_RECEIPT' : 'LIVE_CREATE_RPC_RESPONSE_ONLY', received_at: new Date().toISOString()}]);
    state.pending = null;
    verificationAuthority = null;
    if (original.intent.action === 'create') { state.create_rejected = true; state.adaptation_draft = true; }
    if (original.intent.action === 'produce' && response.receipt_kind === 'REQUIREMENTS_GUARD_REFUSAL') state.requirements_refused = true;
  }
  function knownRequirementsRefusal(value) {
    return Boolean(value && value.requirements_refused === true && (value.rejected_intents || []).some(item =>
      controlledRefusal(item.intent, item.response, item.response && item.response.status === 'HISTORICAL_NOT_CURRENT', value.requirements)));
  }
  function credentials() { return {job_id: state.job_id, capability: state.capability}; }
  function responseJob(response) {
    // The server envelope itself is the only operational response shape.
    if (!response || typeof response !== 'object' || response.job_id !== state.job_id) return false;
    return true;
  }
  function correlated(intent, response) {
    if (!responseJob(response)) return false;
    if (['status', 'audit'].includes(intent.action)) return true;
    const expected = intent.action === 'produce' && response.action === 'result' ? intent.input.result_request_id : intent.input.request_id;
    return response.request_id === expected;
  }
  function adopt(response, action) {
    if (!responseJob(response)) throw new Error('Le reçu reçu ne correspond pas à cette tâche. L’intention reste conservée.');
    state.last_response = response;
    if (typeof response.next_step_id === 'string' || response.next_step_id === null) state.next_step_id = response.next_step_id;
    if (validResult(response.result)) state.result = response.result;
    if (response.verification) state.verification = response.verification;
    if (response.completion) state.completion = response.completion;
    if (root.SolRequirements && root.SolRequirements.validGuard(response.requirements_guard, state.requirements)) state.requirements_guard = response.requirements_guard;
    if (response.release_binding && typeof response.release_binding === 'object') state.release_binding = response.release_binding;
    if (typeof response.result_sha256 === 'string') state.result_sha256 = response.result_sha256;
    if (typeof response.requirements_release_hash === 'string') state.requirements_release_hash = response.requirements_release_hash;
    if (typeof response.requirements_guard_runtime_hash === 'string') state.requirements_guard_runtime_hash = response.requirements_guard_runtime_hash;
    if (typeof response.source_sha256 === 'string') state.source_sha256 = response.source_sha256;
    appendHistory(action, response);
  }
  async function post(intent) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 27000);
    const finish = root.SolUiActivity.begin('csv', intent.action);
    try {
      const response = await fetch('/api/job', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(intent), signal: controller.signal, cache: 'no-store'});
      const result = await response.json();
      if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('Réponse illisible.');
      return result;
    } finally { clearTimeout(timeout); finish(); }
  }
  async function mutate(action, additions = {}, creation = null) {
    if (busy) return;
    const expectedView = state && {job_id: state.job_id, capability: state.capability};
    authority = null; busy = true;
    if (action !== 'complete') verificationAuthority = null;
    const sentMonotonic = performance.now(), sentAt = Date.now();
    const finishPreparation = root.SolUiActivity.begin('csv', 'prepare');
    try {
      render();
      const reservation = await requireSlots().withKeys(slotKeys, () => {
        const latest = readState();
        assertNoMissionPending();
        if (latest && latest.pending) throw new Error('Une intention attend déjà son reçu exact : ' + latest.pending.intent.input.request_id + '. Aucun nouvel identifiant ne sera créé.');
        if (action === 'create') {
          const format = validateCreation(creation.mandate, creation.requirements, creation.source_csv);
          if (!format.ok) { setDiagnostics(format.errors); throw new Error('Les entrées doivent être corrigées avant l’enregistrement. Aucun envoi n’a eu lieu.'); }
          if (expectedView ? !slots.identity(latest, expectedView) || !latest.adaptation_draft : latest !== null) throw new Error('Un travail est déjà conservé ou a changé. Relisez sa reprise avant un nouvel enregistrement.');
          const previous = latest;
          const parent = previous && !previous.create_rejected && !previous.independent_draft ? previous : null;
          if (parent && JSON.stringify(creation.requirements) !== JSON.stringify(parent.requirements)) throw new Error('Les exigences antérieures restent conservées exactement pour cette correction.');
          state = {version: 1, job_id: crypto.randomUUID(), capability: capability(crypto), mandate: creation.mandate, requirements: creation.requirements, source_csv: creation.source_csv, next_step_id: null, history: [], pending: null,
            ancestors: previous ? (previous.ancestors || []).concat([{job_id: previous.job_id, capability: previous.capability, mandate: previous.mandate, requirements: previous.requirements, history: previous.create_rejected || previous.independent_draft ? previous.history : undefined, source_csv: previous.create_rejected || previous.independent_draft ? previous.source_csv : undefined, rejected_intents: previous.rejected_intents || [], relation: previous.independent_draft ? 'INDEPENDENT_RESTART_AFTER_KNOWN_REFUSAL' : 'CORRECTION_REFERENCE_ONLY'}]) : []};
          additions = {mandate: creation.mandate, requirements: creation.requirements, source_csv: creation.source_csv, source_origin: {kind: 'declared'}};
          if (parent) { additions.parent_job_id = parent.job_id; additions.parent_capability = parent.capability; }
        } else {
          if (!slots.identity(latest, expectedView)) throw new Error('La tâche ou sa clé a changé. Consultez le travail conservé avant une nouvelle action.');
          if (latest.adaptation_draft) throw new Error('Une correction est en préparation. Enregistrez-la ou annulez-la explicitement.');
          state = latest;
        }
        if (action === 'complete' && !verificationIsCurrent()) throw new Error('La vérification n’est plus actuelle dans cette session. Cliquez sur « Vérifier » avant de clore. Aucune demande de clôture n’a été envoyée.');
        const intent = newIntent(action, Object.assign(credentials(), additions), () => crypto.randomUUID());
        state.pending = {intent, prepared_at: new Date().toISOString()};
        if (['produce', 'verify', 'complete'].includes(action)) state.pending.requirements_guard_flow = true;
        persist();
        // Complete is checked, reserved and sent under this same exclusive lock.
        // The promise is boxed, so the network never holds the browser lock.
        return {intent, pending: state.pending, expected: credentials(), response: action === 'complete' ? post(intent) : null};
      });
      render();
      const response = reservation.response ? await reservation.response : await send(reservation.intent, reservation.expected, reservation.pending);
      const receivedAt = Date.now(), receivedMonotonic = performance.now();
      const outcome = await commit(reservation.expected, reservation.pending, () => {
        if (!correlated(reservation.intent, response)) {
          appendHistory(action, response);
          return 'UNRELATED';
        }
        adopt(response, action);
        if (controlledRefusal(reservation.intent, response, false, state.requirements)) {
          recordRefusal({intent: reservation.intent}, response);
          return 'REJECTED';
        }
        if (liveCreateRefusal(reservation.intent, response)) {
          recordRefusal({intent: reservation.intent}, response);
          return 'REJECTED_CREATE_LIVE';
        }
        if (response.ok !== true || response.status === 'OUTCOME_UNKNOWN' || response.pending) return 'UNKNOWN';
        state.pending = null;
        if (action === 'verify') verificationAuthority = verificationWindow(response, receivedAt, receivedMonotonic, sentMonotonic, sentAt);
        if (action === 'complete') {
          verificationAuthority = null;
          if (response.current_reuse_authorized === true && !response.deduplicated) authority = {response, receivedAt, monotonic: sentMonotonic, lastWall: receivedAt, lastMonotonic: receivedMonotonic};
        }
        return 'RECORDED';
      });
      if (outcome === 'UNRELATED') throw new Error('L’issue de la demande n’est pas corrélée. Consultez son reçu sans la relancer.');
      if (outcome === 'REJECTED') { showRefusal(response, true); return; }
      if (outcome === 'REJECTED_CREATE_LIVE') { const diagnosis = diagnosticFor(response); if (diagnosis) setDiagnostics([diagnosis]); show('La création a été refusée sans modification métier. ' + (diagnosis ? diagnosis.message + ' ' : '') + 'Sa réponse est conservée dans ce navigateur ; aucun reçu durable de ce refus n’est établi. Corrigez les entrées, puis enregistrez explicitement la correction.', 'error'); return; }
      if (outcome === 'UNKNOWN') { if (response.ok === false && response.status === 'REJECTED') showRefusal(response, false); else show('L’issue reste inconnue ou bloquée. L’intention et ses identifiants sont conservés ; aucun calcul ne sera rejoué.', 'unknown'); return; }
      const messages = {create: 'Demande conservée. Vous pouvez maintenant produire le résultat.', produce: 'Le calcul a produit un résultat. Lancez la vérification séparée.', verify: response.status === 'PASS' || (response.verification && response.verification.status === 'PASS') ? 'Le vérificateur a confirmé les contrats CSV. La clôture demandera une nouvelle observation.' : 'La vérification est conservée. Consultez sa portée avant de poursuivre.', complete: response.status === 'COMPLETED_BOUNDED' ? 'Clôture bornée reçue. Sa validité actuelle est affichée ci-dessous.' : 'La clôture ne confirme pas tous les contrôles. La tâche reste visible.'};
      show(messages[action] || 'Reçu conservé.', response.status === 'COMPLETED_BOUNDED' ? 'success' : 'neutral');
    } catch (error) {
      authority = null; verificationAuthority = null; refreshState();
      show(error.message && !/fetch|abort|network/i.test(error.message) ? error.message : 'La réponse n’est pas arrivée. Son issue reste inconnue : consultez le reçu, sans relancer l’action.', 'unknown');
    } finally { busy = false; finishPreparation(); render(); }
  }
  async function read(action) {
    if (busy) return;
    readOnlyView = null; refreshState();
    if (!state || storageBlocked) { render(); return; }
    const expected = credentials();
    const observedPending = state.pending;
    authority = null; verificationAuthority = null;
    busy = true;
    try {
      render();
      requireCurrent(expected, observedPending);
      const response = await post({action, input: expected});
      if (response.ok !== true || response.job_id !== expected.job_id) throw new Error('Lecture non confirmée. L’état actuel reste inconnu.');
      const apply = () => {
        if (action === 'audit') appendHistory(action, response);
        else adopt(response, action);
      };
      if (slots.available()) await commit(expected, observedPending, apply);
      else {
        state = requireCurrent(expected, observedPending);
        const base = JSON.parse(JSON.stringify(state));
        apply();
        readOnlyView = {base, value: state};
      }
      if (action === 'audit') {
        const audit = response.audit || response;
        $('journal-status').textContent = audit.status === 'PASS' && audit.chain_valid === true && audit.relations_valid === true && audit.source_hash_valid === true && audit.definition_hash_valid === true ? 'Journal contrôlé par le serveur pour cette tâche.' : 'Contrôle du journal reçu ; intégrité non confirmée dans cette vue.';
      }
      show((state.pending ? 'État consulté. L’intention conservée attend toujours son rapprochement ; cette lecture ne l’a pas rejouée.' : 'État consulté. Les reçus antérieurs restent historiques ; Clore demande une nouvelle preuve.') + (slots.available() ? '' : ' Verrou entre onglets indisponible : cette lecture ne modifie pas la reprise partagée.'), 'neutral');
    } catch (error) { authority = null; refreshState(); show(error.message || 'Lecture indisponible.', 'unknown'); }
    finally { busy = false; render(); }
  }
  function originalOutcome(original, response) {
    if (!response || typeof response !== 'object' || Array.isArray(response) || !responseJob(response) || response.ok !== true || response.status === 'OUTCOME_UNKNOWN') return null;
    const intent = original.intent;
    if (!intent || !intent.input) return null;
    if (intent.action === 'produce') {
      if (response.action === 'begin' && response.request_id === intent.input.request_id && response.production_request_id === intent.input.request_id) return response;
      if (response.action === 'result' && response.request_id === intent.input.result_request_id && response.production_request_id === intent.input.request_id && !response.pending) return response;
      return null;
    }
    return response.action === intent.action && response.request_id === intent.input.request_id && !response.pending ? response : null;
  }
  function applyReconciliation(original, intent, response, source) {
    if (!correlated(intent, response) || response.action !== 'reconcile') throw new Error('Rapprochement non corrélé. L’intention reste inconnue.');
    if (response.ok !== true || response.pending !== false || response.status === 'OUTCOME_UNKNOWN' || response.outcome_known !== true || response.worker_reexecuted !== false) {
      message = {text: 'Le reçu ne permet pas d’établir l’issue. La tâche reste bloquée ; aucun calcul n’est relancé.', kind: 'unknown'}; return false;
    }
    const refusal = response.reconciled_outcome;
    if (response.receipt_kind === 'REFUSAL_RECONCILIATION') {
      if (response.current_reuse_authorized !== false || response.automatic_retry !== false || response.target_request_id !== original.intent.input.request_id || response.target_action !== original.intent.action || !controlledRefusal(original.intent, refusal, true, state.requirements)) {
        message = {text: 'Le refus historique ne correspond pas exactement à l’intention originale et à sa portée. L’issue reste inconnue.', kind: 'unknown'}; return false;
      }
      adopt(response, source);
      recordRefusal(original, refusal, {intent, response});
      return 'REJECTED';
    }
    // The recovered reconciliation is a wrapper, never a replacement for the
    // original production identity. Its nested outcome must match that identity.
    const outcome = originalOutcome(original, response.reconciled_outcome);
    const expectedSource = state.source_sha256;
    const productionRecovered = original.intent.action === 'produce' && response.production_request_id === original.intent.input.request_id && validResult(response.result) &&
      typeof expectedSource === 'string' && /^[a-f0-9]{64}$/.test(expectedSource) && response.source_sha256 === expectedSource && response.result.source_sha256 === expectedSource && outcome && outcome.source_sha256 === expectedSource;
    if (!outcome || (original.intent.action === 'produce' && !productionRecovered) || (!productionRecovered && outcome.pending)) {
      message = {text: 'L’issue originale n’est pas confirmée. L’intention reste conservée.', kind: 'unknown'}; return false;
    }
    adopt(response, source);
    if (validResult(outcome.result) && !state.result) state.result = outcome.result;
    state.pending = null;
    return true;
  }
  async function lookupReconciliation(original) {
    const intent = original.reconciliation && original.reconciliation.intent;
    if (!intent || intent.action !== 'reconcile' || !intent.input || typeof intent.input.request_id !== 'string') { show('L’identifiant du rapprochement conservé est illisible. L’intention originale reste conservée.', 'unknown'); return; }
    const expected = {job_id: intent.input.job_id, capability: intent.input.capability};
    authority = null; verificationAuthority = null; busy = true;
    try {
      render();
      state = requireCurrent(expected, original);
      const response = await post({action: 'receipt', input: Object.assign({}, expected, {target_request_id: intent.input.request_id})});
      if (response.job_id !== expected.job_id || response.ok !== true || response.target_request_id !== intent.input.request_id || response.current_reuse_authorized !== false || response.automatic_retry !== false) throw new Error('Lecture du reçu non corrélée. L’intention originale reste conservée.');
      if (response.found !== true) { show('Le reçu du rapprochement reste absent ou inconnu. L’intention originale est conservée ; aucun calcul n’est relancé.', 'unknown'); return; }
      const receipt = response.receipt;
      if (!receipt || typeof receipt !== 'object' || Array.isArray(receipt) || receipt.status !== 'HISTORICAL_NOT_CURRENT' || receipt.current_reuse_authorized !== false) throw new Error('Reçu historique illisible. L’intention originale reste conservée.');
      if (!slots.available()) { state = requireCurrent(expected, original); show('Reçu historique retrouvé. Le verrou entre onglets est indisponible : l’intention reste conservée, sans nouveau calcul ni nouvel envoi.', 'unknown'); return; }
      const applied = await commit(expected, original, () => applyReconciliation(original, intent, receipt, 'receipt-reconcile-observation'));
      if (applied === 'REJECTED') showRefusal(receipt.reconciled_outcome, true);
      else if (applied) show('Issue rapprochée sans relancer le calcul. Toute clôture retrouvée reste historique.', 'neutral');
      else render();
    } catch (error) { authority = null; refreshState(); show(error.message || 'Lecture du reçu indisponible : issue inconnue.', 'unknown'); }
    finally { busy = false; render(); }
  }
  async function lookupRequirementsGuard(original) {
    const intent = original.intent;
    const expected = {job_id: intent.input.job_id, capability: intent.input.capability};
    authority = null; verificationAuthority = null; busy = true;
    try {
      render(); state = requireCurrent(expected, original);
      const response = await post({action: 'receipt', input: Object.assign({}, expected, {target_request_id: intent.input.request_id})});
      if (response.ok !== true || response.action !== 'lookup_receipt' || response.job_id !== expected.job_id || response.target_request_id !== intent.input.request_id || response.current_reuse_authorized !== false || response.automatic_retry !== false) throw new Error('Lecture préalable non corrélée. L’intention originale reste conservée.');
      if (response.found !== true) { show('Le reçu préalable reste absent : issue UNKNOWN. L’UUID est conservé, sans nouveau calcul ni nouveau rapprochement automatique.', 'unknown'); return; }
      const receipt = response.receipt;
      if (!receipt || receipt.job_id !== expected.job_id || receipt.request_id !== intent.input.request_id || receipt.status !== 'HISTORICAL_NOT_CURRENT' || receipt.current_reuse_authorized !== false) throw new Error('Le reçu ne correspond pas à la production conservée. L’intention reste inconnue.');
      const refused = response.target_action === intent.action && controlledRefusal(intent, receipt, true, state.requirements);
      const completed = intent.action !== 'produce' && response.target_action === intent.action && originalOutcome(original, receipt);
      const admitted = intent.action === 'produce' && receipt.ok === true && ((response.target_action === 'produce' && receipt.production_request_id === intent.input.request_id && receipt.historical_status === 'BOUND_RELEASE' && receipt.requirements_and_begin_atomic === true && receipt.binding_and_begin_atomic === true && root.SolRequirements && root.SolRequirements.validGuard(receipt.requirements_guard, state.requirements) && receipt.requirements_guard.status === 'PASS') ||
        (response.target_action === 'begin' && receipt.action === 'begin' && receipt.production_request_id === intent.input.request_id));
      if (!refused && !admitted && !completed) throw new Error('Ce reçu n’établit pas un refus contrôlé, une admission ou une issue corrélée. L’intention reste conservée.');
      if (!slots.available()) { show('Reçu historique retrouvé. Le verrou entre onglets est indisponible ; l’intention reste conservée, sans nouvel effet.', 'unknown'); return; }
      await commit(expected, original, () => {
        if (root.SolRequirements && root.SolRequirements.validGuard(receipt.requirements_guard, state.requirements)) state.requirements_guard = receipt.requirements_guard;
        appendHistory('requirements-admission-receipt', response);
        if (refused) { adopt(receipt, 'requirements-refusal-observation'); recordRefusal(original, receipt); }
        else if (completed) { adopt(receipt, 'requirements-outcome-observation'); state.pending = null; }
        else state.pending.admission_receipt_observed = true;
      });
      if (refused) showRefusal(receipt, true);
      else if (completed) show('Le reçu exact de cette action a été retrouvé sans nouvel envoi. Son observation reste historique ; aucune vérification actuelle ni clôture générale n’en est déduite.', 'neutral');
      else show('L’admission a été retrouvée comme historique ; elle ne prouve pas la fin du calcul. Cliquez à nouveau sur « Retrouver l’issue » pour demander explicitement son rapprochement, sans relancer le calculateur.', 'unknown');
    } catch (error) { refreshState(); show(error.message || 'Reçu préalable indisponible ; issue inconnue.', 'unknown'); }
    finally { busy = false; render(); }
  }
  async function lookupCreation(original) {
    const intent = original.intent;
    const expected = {job_id: intent.input.job_id, capability: intent.input.capability};
    authority = null; verificationAuthority = null; busy = true;
    try {
      render();
      state = requireCurrent(expected, original);
      const response = await post({action: 'creation_receipt', input: Object.assign({}, expected, {target_request_id: intent.input.request_id})});
      if (response.ok !== true || response.action !== 'lookup_receipt' || response.job_id !== expected.job_id || response.target_request_id !== intent.input.request_id || response.current_reuse_authorized !== false || response.automatic_retry !== false) throw new Error('Lecture de création non corrélée. L’intention originale reste conservée.');
      if (response.found !== true) { show('L’issue de l’enregistrement reste inconnue. La demande et son identifiant sont conservés ; aucun nouvel envoi n’est effectué.', 'unknown'); return; }
      const receipt = response.receipt;
      if (!receipt || response.target_action !== 'create' || receipt.status !== 'HISTORICAL_NOT_CURRENT' || receipt.current_reuse_authorized !== false || receipt.job_id !== expected.job_id || receipt.request_id !== intent.input.request_id || receipt.action !== 'create') throw new Error('Le reçu ne correspond pas à la création conservée. L’issue reste inconnue.');
      const refused = controlledRefusal(intent, receipt, true);
      const accepted = !refused && originalOutcome(original, receipt);
      if (!refused && !accepted) throw new Error('Le reçu ne prouve ni une création acceptée ni un refus contrôlé. L’intention reste conservée.');
      await commit(expected, original, () => {
        if (refused) recordRefusal(original, receipt);
        else { adopt(receipt, 'creation-receipt-observation'); state.pending = null; }
        appendHistory('creation-receipt', response);
      });
      if (refused) show('Le refus d’enregistrement a été retrouvé. Aucun travail n’a été lancé par cette demande refusée. Sa preuve et la demande originale sont conservées ; vous pouvez préparer une demande corrigée.', 'error');
      else show('La demande enregistrée a été retrouvée sans nouvel envoi. ' + (receipt.next_step_id === 'produce' ? 'Étape suivante : Produire. ' : '') + 'Cette lecture historique ne vérifie pas le résultat et ne permet pas de clore.', 'neutral');
    } catch (error) { refreshState(); show(error.message || 'Lecture de création indisponible : issue inconnue.', 'unknown'); }
    finally { busy = false; render(); }
  }
  async function reconcile() {
    if (busy) return;
    refreshState();
    if (!state || !state.pending || storageBlocked) { render(); return; }
    if (state.pending.intent && state.pending.intent.action === 'create') { await lookupCreation(state.pending); return; }
    if (state.pending.intent && state.pending.requirements_guard_flow && !state.pending.admission_receipt_observed && !state.pending.reconciliation) { await lookupRequirementsGuard(state.pending); return; }
    if (state.pending.reconciliation) { await lookupReconciliation(state.pending); return; }
    const expected = credentials(), original = state.pending;
    authority = null; verificationAuthority = null; busy = true;
    const finishPreparation = root.SolUiActivity.begin('csv', 'prepare');
    try {
      render();
      const reservation = await requireSlots().withKeys(slotKeys, () => {
        state = requireCurrent(expected, original);
        const target = original.intent.input.request_id;
        const addition = {target_request_id: target};
        if (original.intent.action === 'produce') addition.production_request_id = target;
        const intent = newIntent('reconcile', Object.assign(credentials(), addition), () => crypto.randomUUID());
        state.pending.reconciliation = {intent, prepared_at: new Date().toISOString()};
        persist();
        return {intent, pending: state.pending};
      });
      render();
      const response = await send(reservation.intent, expected, reservation.pending, false);
      const applied = await commit(expected, reservation.pending, () => {
        const result = applyReconciliation(original, reservation.intent, response, 'reconcile-observation');
        if (!result) appendHistory('reconcile', response);
        return result;
      });
      if (applied === 'REJECTED') showRefusal(response.reconciled_outcome, true);
      else if (applied) show('Issue rapprochée sans relancer le calcul. Toute clôture retrouvée reste historique.', 'neutral');
      else render();
    } catch (error) { authority = null; refreshState(); show(error.message || 'Rapprochement sans réponse : issue inconnue.', 'unknown'); }
    finally { busy = false; finishPreparation(); render(); }
  }
  function renderVerification() {
    const current = verificationIsCurrent();
    const element = $('verification-freshness');
    const text = current ? 'Vérification actuelle dans cette session. Vous pouvez cliquer sur « Clore ».' : 'Clore exige une vérification actuelle dans cette session. Cliquez sur « Vérifier » pour la demander.';
    if (element.textContent !== text) element.textContent = text;
    element.hidden = !state || !validResult(state.result);
    if (!current) $('complete').disabled = true;
    return current;
  }
  function renderFreshness() {
    const element = $('freshness');
    const completion = state && state.completion;
    if (!completion) { element.hidden = true; return; }
    element.hidden = false;
    const now = Date.now();
    const monotonic = performance.now();
    const current = authority && now >= authority.lastWall && monotonic >= authority.lastMonotonic && currentCompletion(authority.response, now, authority.receivedAt, monotonic - authority.monotonic);
    if (authority) { authority.lastWall = now; authority.lastMonotonic = monotonic; }
    if (!current) authority = null;
    element.className = 'freshness' + (current ? '' : ' expired');
    if (current) {
      const text = 'Clôture bornée actuelle · contrats CSV seulement · sens : UNKNOWN.';
      if (element.textContent !== text) element.textContent = text;
    } else {
      const text = 'Clôture historique : sa validité actuelle a expiré ou n’est pas établie dans cette session. Cliquez sur « Vérifier », puis sur « Clore » pour la revalider.';
      if (element.textContent !== text) element.textContent = text;
      if (message.kind === 'success') { message = {text: 'La clôture conservée est désormais historique. Le résultat et ses preuves restent consultables.', kind: 'unknown'}; $('message').className = 'message unknown'; $('message').textContent = message.text; }
    }
  }
  function render() {
    refreshState();
    $('message').textContent = message.text;
    $('message').className = 'message ' + message.kind;
    const hasJob = Boolean(state);
    const pending = hasJob && Boolean(state.pending);
    let missionPending = false;
    try { missionPending = Boolean(otherPending()); } catch (error) { storageBlocked = true; authority = null; verificationAuthority = null; message = {text: error.message, kind: 'unknown'}; $('message').textContent = message.text; $('message').className = 'message unknown'; }
    const mutable = Boolean(slots && slots.available() && !storageBlocked && !missionPending);
    $('job-meta').hidden = !hasJob;
    const drafting = hasJob && state.adaptation_draft;
    ['mandate', 'source-csv', 'sample', 'create'].forEach(id => { $(id).disabled = !mutable || busy || pending || (hasJob && !drafting); });
    $('requirements').disabled = !mutable || busy || (hasJob && !(drafting && (state.create_rejected === true || state.independent_draft === true) && !pending));
    $('requirements-help').textContent = drafting && state.independent_draft ? 'Nouvelle demande indépendante : vos modifications ne satisfont pas rétroactivement l’ancien mandat. L’ancien travail et son refus restent conservés.' : hasJob && !state.create_rejected ? 'Les exigences d’une demande acceptée restent conservées exactement, y compris dans une correction.' : 'Une exigence par ligne, 1 à 32 au total ; 2 000 caractères maximum chacune.';
    $('mission-panel').hidden = !(missionPending || (hasJob && state.create_rejected !== true && validResult(state.result)));
    $('create').textContent = drafting && state.independent_draft ? 'Enregistrer la demande indépendante →' : drafting ? 'Enregistrer la correction →' : 'Enregistrer cette demande →';
    ['status', 'audit'].forEach(id => { $(id).disabled = busy || !hasJob; });
    ['produce', 'verify', 'complete'].forEach(action => {
      const next = hasJob && state.next_step_id;
      $(action).disabled = !mutable || busy || !hasJob || pending || drafting || !(next === action || (action === 'complete' && state.completion) || (action === 'verify' && validResult(state.result))) || (action === 'complete' && !verificationIsCurrent());
      if (action === 'produce' && hasJob && state.requirements_refused === true) $(action).disabled = true;
      const ordered = ['produce', 'verify', 'complete'];
      const index = ordered.indexOf(next);
      const done = hasJob && (index > ordered.indexOf(action) || (action === 'produce' && validResult(state.result)) || (action === 'complete' && state.completion));
      $('step-' + action).className = done ? 'done' : next === action ? 'active' : '';
    });
    $('recovery').hidden = !pending;
    const guardLookup = pending && state.pending.requirements_guard_flow && !state.pending.admission_receipt_observed && !state.pending.reconciliation;
    $('reconcile').disabled = busy || !pending || storageBlocked || (!(slots && slots.available()) && !state.pending.reconciliation && !guardLookup);
    $('reconcile').textContent = guardLookup ? 'Consulter le reçu préalable' : pending && state.pending.reconciliation ? 'Consulter l’issue recherchée' : 'Retrouver l’issue de la demande';
    $('independent-request').hidden = !hasJob || !knownRequirementsRefusal(state) || drafting;
    $('independent-request').disabled = !mutable || busy || pending || drafting;
    $('independent-warning').hidden = $('independent-request').hidden;
    $('adapt').disabled = !mutable || busy || !hasJob || pending || drafting;
    $('adapt').hidden = drafting;
    $('cancel-adapt').hidden = !drafting;
    $('cancel-adapt').disabled = !mutable || busy;
    $('create').disabled = $('create').disabled || !mutable;
    if (root.SolRequirements) root.SolRequirements.controls();
    if (hasJob) {
      $('saved-mandate').textContent = state.mandate;
      $('job-id').textContent = 'Tâche ' + state.job_id;
      $('saved-requirements').replaceChildren();
      (state.requirements || []).forEach(text => { const item = document.createElement('li'); item.textContent = text + ' — portée sémantique non vérifiée'; $('saved-requirements').appendChild(item); });
    }
    if (root.SolRequirements) root.SolRequirements.render(hasJob ? state.requirements_guard : null, hasJob ? state.requirements : null);
    const result = hasJob && state.result;
    $('result').hidden = !validResult(result);
    if (validResult(result)) {
      $('row-count').textContent = result.rows + (result.rows > 1 ? ' lignes' : ' ligne');
      $('totals').replaceChildren();
      result.totals.forEach(total => { const row = document.createElement('tr'); [total.currency, total.amount].forEach(value => { const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell); }); $('totals').appendChild(row); });
      const verification = state.verification;
      $('result-proof').textContent = 'Source SHA-256 : ' + result.source_sha256 + '. ' + (verification && verification.status === 'PASS' ? 'Contrats CSV vérifiés à la date du reçu ; Clore exige une vérification actuelle dans cette session.' : 'Résultat produit ; vérification distincte à consulter.') + ' Source déclarée par l’utilisateur ; vérité sémantique : UNKNOWN.';
    }
    renderVerification();
    renderFreshness();
  }
  $('job-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (busy) return;
    const mandate = $('mandate').value;
    const requirements = $('requirements').value.split(/\r?\n/).filter(value => value.length > 0);
    const source = $('source-csv').value;
    const format = validateCreation(mandate, requirements, source);
    setDiagnostics(format.errors);
    if (!format.ok) { const first = format.errors[0]; show((first.line ? 'Ligne ' + first.line + ' : ' : '') + first.message + ' Les données restent dans le formulaire ; aucun envoi n’a eu lieu.', 'error'); $(first.field).focus(); return; }
    await mutate('create', {}, {mandate, requirements, source_csv: source});
  });
  ['mandate', 'requirements', 'source-csv'].forEach(field => $(field).addEventListener('input', () => setDiagnostics(fieldDiagnostics.filter(x => x.field !== field))));
  $('sample').addEventListener('click', () => { $('mandate').value = 'Calculer les totaux de ce tableau fictif par devise et conserver chaque ligne.'; if (!state) $('requirements').value = DEFAULT_REQUIREMENTS.join('\n'); $('source-csv').value = SAMPLE; $('source-csv').focus(); });
  async function draft(enabled, independent = false) {
    if (busy) return;
    refreshState();
    if (!state || storageBlocked) { render(); return; }
    const expected = credentials();
    busy = true;
    const finishPreparation = root.SolUiActivity.begin('csv', 'prepare');
    try {
      render();
      await requireSlots().withKeys(slotKeys, () => {
        state = requireCurrent(expected);
        assertNoMissionPending();
        if (state.pending) throw new Error('Une intention attend son reçu exact. La reprise ne sera pas remplacée par une correction.');
        if (independent && !knownRequirementsRefusal(state)) throw new Error('Une demande indépendante ne peut être préparée ici sans refus préalable durable connu.');
        state.adaptation_draft = enabled; state.independent_draft = Boolean(enabled && independent); persist();
      });
      if (enabled) { $('mandate').value = state.mandate; $('requirements').value = state.requirements.join('\n'); $('source-csv').value = state.source_csv; }
      show(enabled && independent ? 'Préparez une nouvelle demande indépendante. L’ancien travail et son refus restent conservés ; aucun résultat, permission ou contrôle n’est hérité. Modifier les exigences ne satisfait pas rétroactivement l’ancien mandat.' : enabled ? 'Préparez une correction. Elle créera un nouvel objet lié au précédent, avec les mêmes exigences et de nouveaux contrôles. L’historique reste conservé.' : 'Correction abandonnée. La tâche précédente reste conservée.', 'neutral');
      if (enabled) $('mandate').focus();
    } catch (error) { refreshState(); show(error.message, 'unknown'); }
    finally { busy = false; finishPreparation(); render(); }
  }
  $('adapt').addEventListener('click', () => draft(true));
  $('independent-request').addEventListener('click', () => draft(true, true));
  $('cancel-adapt').addEventListener('click', () => draft(false));
  ['produce', 'verify', 'complete'].forEach(action => $(action).addEventListener('click', () => mutate(action, {expected_step_id: action})));
  $('status').addEventListener('click', () => read('status'));
  $('audit').addEventListener('click', () => read('audit'));
  $('reconcile').addEventListener('click', reconcile);
  function download(contents, type, suffix) {
    const url = URL.createObjectURL(new Blob([contents], {type}));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'agir-' + state.job_id + '.' + suffix; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function downloadProof() {
    if (!state) return;
    if (!root.SolRequirements) { show('Le module d’export de la portée n’est pas chargé. Aucun export incomplet n’est créé.', 'unknown'); return; }
    const value = root.SolRequirements.exportBundle(state, new Date().toISOString());
    download(JSON.stringify(value, null, 2), 'application/json;charset=utf-8', 'json');
  }
  $('download-json').addEventListener('click', downloadProof);
  $('download-proof').addEventListener('click', downloadProof);
  $('download-csv').addEventListener('click', () => { if (state && validResult(state.result)) download('currency,amount\r\n' + state.result.totals.map(x => x.currency + ',' + x.amount).join('\r\n') + '\r\n', 'text/csv;charset=utf-8', 'csv'); });
  // A dated public snapshot, if provided, is evidence of a connector read only.
  fetch('/provider-observation.json', {cache: 'no-store'}).then(response => response.ok ? response.json() : null).then(snapshot => {
    if (snapshot && snapshot.provider === 'StorageChain' && snapshot.connector_read_executed === true && typeof snapshot.observed_at === 'string' && typeof snapshot.public_summary === 'string') $('storagechain-status').textContent = 'StorageChain · lecture observée le ' + snapshot.observed_at + ' : ' + snapshot.public_summary + ' Cette observation datée ne prouve pas un accès actuel.';
  }).catch(() => {});
  function sharedChanged(event) {
    if (event && event.type === 'storage' && event.key !== null && !slotKeys.includes(event.key)) return;
    authority = null; verificationAuthority = null; readOnlyView = null; refreshState(true); render();
  }
  root.addEventListener('storage', sharedChanged);
  root.addEventListener('pageshow', sharedChanged);
  document.addEventListener('visibilitychange', sharedChanged);
  setInterval(() => { if (refreshState(true)) render(); else { renderVerification(); renderFreshness(); } }, 500);
  if (state) { $('mandate').value = state.mandate; $('requirements').value = state.requirements.join('\n'); $('source-csv').value = state.source_csv; }
  render();
})(typeof globalThis === 'undefined' ? this : globalThis);
