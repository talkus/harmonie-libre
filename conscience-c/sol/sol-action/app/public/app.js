(function (root) {
  'use strict';
  const STORAGE_KEY = 'sol-action-session-v1';
  const SAMPLE = 'id,currency,amount\ncommande-1,EUR,120.50\ncommande-2,EUR,-20.25\ncommande-3,USD,35.10\ncommande-4,EUR,0.05\ncommande-5,USD,4.90\n';
  const DEFAULT_REQUIREMENTS = ['Conserver chaque ligne d’entrée.', 'Calculer exactement les totaux, sans arrondi intermédiaire.', 'Séparer les devises et identifier le tableau source.'];
  function capability(cryptoProvider) {
    return Array.from(cryptoProvider.getRandomValues(new Uint8Array(32)), x => x.toString(16).padStart(2, '0')).join('');
  }
  function validResult(value) {
    return Boolean(value && typeof value === 'object' && /^[a-f0-9]{64}$/.test(value.source_sha256) && Number.isInteger(value.rows) && value.rows > 0 && value.rows <= 500 && Array.isArray(value.row_ids) && value.row_ids.length === value.rows && Array.isArray(value.totals) && value.totals.every(x => x && /^[A-Z]{3}$/.test(x.currency) && /^-?[0-9]+\.[0-9]{2}$/.test(x.amount)));
  }
  function currentCompletion(response, now, receivedAt, elapsed) {
    const completion = response && response.completion;
    return Boolean(response && response.ok === true && response.status === 'COMPLETED_BOUNDED' && response.current_reuse_authorized === true && !response.deduplicated && completion && completion.status === 'COMPLETED_BOUNDED' && completion.scope === 'CSV_EXACT_CENTS_ONLY' && Number.isFinite(Date.parse(completion.expires_at)) && Date.parse(completion.expires_at) > now && now >= receivedAt && elapsed >= 0 && elapsed < 60000);
  }
  function newIntent(action, input, uuidProvider) {
    const copy = Object.assign({}, input);
    if (!['status', 'audit', 'receipt'].includes(action)) copy.request_id = uuidProvider();
    if (action === 'produce') copy.result_request_id = uuidProvider();
    return {action, input: copy};
  }
  const helpers = {capability, currentCompletion, newIntent, validResult, SAMPLE, STORAGE_KEY};
  if (typeof module !== 'undefined' && module.exports) module.exports = helpers;
  root.SolAction = helpers;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  let state = null;
  let busy = false;
  let authority = null;
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
        if (notify) message = {text: state && state.pending ? 'Reprise partagée : l’intention ' + state.pending.intent.input.request_id + ' attend son reçu. Aucun calcul n’a été relancé.' : 'La tâche partagée a changé. Consultez son état ; les reçus restent historiques.', kind: 'unknown'};
      }
      return changed;
    } catch (error) {
      storageBlocked = true; authority = null;
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
    if (typeof response.source_sha256 === 'string') state.source_sha256 = response.source_sha256;
    appendHistory(action, response);
  }
  async function post(intent) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 27000);
    try {
      const response = await fetch('/api/job', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(intent), signal: controller.signal, cache: 'no-store'});
      const result = await response.json();
      if (!result || typeof result !== 'object' || Array.isArray(result)) throw new Error('Réponse illisible.');
      return result;
    } finally { clearTimeout(timeout); }
  }
  async function mutate(action, additions = {}, creation = null) {
    if (busy) return;
    const expectedView = state && {job_id: state.job_id, capability: state.capability};
    authority = null; busy = true;
    try {
      const reservation = await requireSlots().withKeys(slotKeys, () => {
        const latest = readState();
        assertNoMissionPending();
        if (latest && latest.pending) throw new Error('Une intention attend déjà son reçu exact : ' + latest.pending.intent.input.request_id + '. Aucun nouvel identifiant ne sera créé.');
        if (action === 'create') {
          if (expectedView ? !slots.identity(latest, expectedView) || !latest.adaptation_draft : latest !== null) throw new Error('Un travail est déjà conservé ou a changé. Relisez sa reprise avant un nouvel enregistrement.');
          const previous = latest;
          const parent = previous && !previous.create_rejected ? previous : null;
          if (parent && JSON.stringify(creation.requirements) !== JSON.stringify(parent.requirements)) throw new Error('Les exigences antérieures restent conservées exactement pour cette correction.');
          state = {version: 1, job_id: crypto.randomUUID(), capability: capability(crypto), mandate: creation.mandate, requirements: creation.requirements, source_csv: creation.source_csv, next_step_id: null, history: [], pending: null,
            ancestors: previous ? (previous.ancestors || []).concat([{job_id: previous.job_id, capability: previous.capability, mandate: previous.mandate, requirements: previous.requirements, history: previous.create_rejected ? previous.history : undefined, source_csv: previous.create_rejected ? previous.source_csv : undefined, rejected_intents: previous.rejected_intents || []}]) : []};
          additions = {mandate: creation.mandate, requirements: creation.requirements, source_csv: creation.source_csv, source_origin: {kind: 'declared'}};
          if (parent) { additions.parent_job_id = parent.job_id; additions.parent_capability = parent.capability; }
        } else {
          if (!slots.identity(latest, expectedView)) throw new Error('La tâche ou sa clé a changé. Consultez le travail conservé avant une nouvelle action.');
          if (latest.adaptation_draft) throw new Error('Une correction est en préparation. Enregistrez-la ou annulez-la explicitement.');
          state = latest;
        }
        const intent = newIntent(action, Object.assign(credentials(), additions), () => crypto.randomUUID());
        state.pending = {intent, prepared_at: new Date().toISOString()};
        persist();
        return {intent, pending: state.pending, expected: credentials()};
      });
      render();
      const sentMonotonic = performance.now();
      const response = await send(reservation.intent, reservation.expected, reservation.pending);
      const outcome = await commit(reservation.expected, reservation.pending, () => {
        if (!correlated(reservation.intent, response)) {
          appendHistory(action, response);
          return 'UNRELATED';
        }
        adopt(response, action);
        if (response.ok === false && response.status === 'REJECTED' && response.effect === 'NONE_SQL_TRANSACTION_ROLLED_BACK') {
          state.rejected_intents = (state.rejected_intents || []).concat([{intent: reservation.intent, response, received_at: new Date().toISOString()}]);
          state.pending = null;
          if (action === 'create') { state.create_rejected = true; state.adaptation_draft = true; }
          return 'REJECTED';
        }
        if (response.ok !== true || response.status === 'OUTCOME_UNKNOWN' || response.pending) return 'UNKNOWN';
        state.pending = null;
        if (action === 'complete' && response.current_reuse_authorized === true && !response.deduplicated) authority = {response, receivedAt: Date.now(), monotonic: sentMonotonic};
        return 'RECORDED';
      });
      if (outcome === 'UNRELATED') throw new Error('L’issue de la demande n’est pas corrélée. Consultez son reçu sans la relancer.');
      if (outcome === 'REJECTED') { show('La demande a été refusée sans effet pour cet appel. Le refus est conservé. ' + (action === 'create' ? 'Corrigez les entrées avant un nouvel enregistrement explicite.' : 'Consultez les contrôles et préparez une action explicite.'), 'error'); return; }
      if (outcome === 'UNKNOWN') { show('L’issue reste inconnue ou bloquée. L’intention et ses identifiants sont conservés ; aucun calcul ne sera rejoué.', 'unknown'); return; }
      const messages = {create: 'Demande conservée. Vous pouvez maintenant produire le résultat.', produce: 'Le calcul a produit un résultat. Lancez la vérification séparée.', verify: response.status === 'PASS' || (response.verification && response.verification.status === 'PASS') ? 'Le vérificateur a confirmé les contrats CSV. La clôture demandera une nouvelle observation.' : 'La vérification est conservée. Consultez sa portée avant de poursuivre.', complete: response.status === 'COMPLETED_BOUNDED' ? 'Clôture bornée reçue. Sa validité actuelle est affichée ci-dessous.' : 'La clôture ne confirme pas tous les contrôles. La tâche reste visible.'};
      show(messages[action] || 'Reçu conservé.', response.status === 'COMPLETED_BOUNDED' ? 'success' : 'neutral');
    } catch (error) {
      authority = null; refreshState();
      show(error.message && !/fetch|abort|network/i.test(error.message) ? error.message : 'La réponse n’est pas arrivée. Son issue reste inconnue : consultez le reçu, sans relancer l’action.', 'unknown');
    } finally { busy = false; render(); }
  }
  async function read(action) {
    if (busy) return;
    readOnlyView = null; refreshState();
    if (!state || storageBlocked) { render(); return; }
    const expected = credentials();
    const observedPending = state.pending;
    if (action === 'status') authority = null;
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
    authority = null; busy = true;
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
      if (applied) show('Issue rapprochée sans relancer le calcul. Toute clôture retrouvée reste historique.', 'neutral');
    } catch (error) { authority = null; refreshState(); show(error.message || 'Lecture du reçu indisponible : issue inconnue.', 'unknown'); }
    finally { busy = false; render(); }
  }
  async function reconcile() {
    if (busy) return;
    refreshState();
    if (!state || !state.pending || storageBlocked) { render(); return; }
    if (state.pending.reconciliation) { await lookupReconciliation(state.pending); return; }
    const expected = credentials(), original = state.pending;
    authority = null; busy = true;
    try {
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
      if (applied) show('Issue rapprochée sans relancer le calcul. Toute clôture retrouvée reste historique.', 'neutral');
    } catch (error) { authority = null; refreshState(); show(error.message || 'Rapprochement sans réponse : issue inconnue.', 'unknown'); }
    finally { busy = false; render(); }
  }
  function renderFreshness() {
    const element = $('freshness');
    const completion = state && state.completion;
    if (!completion) { element.hidden = true; return; }
    element.hidden = false;
    const now = Date.now();
    const current = authority && currentCompletion(authority.response, now, authority.receivedAt, performance.now() - authority.monotonic);
    element.className = 'freshness' + (current ? '' : ' expired');
    if (current) {
      const seconds = Math.max(0, Math.min(60, Math.ceil((Date.parse(completion.expires_at) - now) / 1000), Math.ceil((60000 - (performance.now() - authority.monotonic)) / 1000)));
      element.textContent = 'Clôture bornée actuelle · ' + seconds + ' s restantes · contrats CSV seulement · sens : UNKNOWN.';
    } else {
      element.textContent = 'Clôture historique : sa validité actuelle a expiré ou n’est pas établie dans cette session. Demandez une nouvelle clôture pour la revalider.';
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
    try { missionPending = Boolean(otherPending()); } catch (error) { storageBlocked = true; authority = null; message = {text: error.message, kind: 'unknown'}; $('message').textContent = message.text; $('message').className = 'message unknown'; }
    const mutable = Boolean(slots && slots.available() && !storageBlocked && !missionPending);
    $('job-meta').hidden = !hasJob;
    const drafting = hasJob && state.adaptation_draft;
    ['mandate', 'source-csv', 'sample', 'create'].forEach(id => { $(id).disabled = busy || (hasJob && !drafting); });
    $('requirements').disabled = busy || hasJob;
    $('create').textContent = drafting ? 'Enregistrer la correction →' : 'Enregistrer cette demande →';
    ['status', 'audit'].forEach(id => { $(id).disabled = busy || !hasJob; });
    ['produce', 'verify', 'complete'].forEach(action => {
      const next = hasJob && state.next_step_id;
      $(action).disabled = !mutable || busy || !hasJob || pending || drafting || !(next === action || (action === 'complete' && state.completion) || (action === 'verify' && validResult(state.result)));
      const ordered = ['produce', 'verify', 'complete'];
      const index = ordered.indexOf(next);
      const done = hasJob && (index > ordered.indexOf(action) || (action === 'produce' && validResult(state.result)) || (action === 'complete' && state.completion));
      $('step-' + action).className = done ? 'done' : next === action ? 'active' : '';
    });
    $('recovery').hidden = !pending;
    $('reconcile').disabled = busy || !pending || storageBlocked || (!(slots && slots.available()) && !state.pending.reconciliation);
    $('reconcile').textContent = pending && state.pending.reconciliation ? 'Consulter le reçu du rapprochement' : 'Rapprocher le reçu';
    $('adapt').disabled = !mutable || busy || !hasJob || pending || drafting;
    $('adapt').hidden = drafting;
    $('cancel-adapt').hidden = !drafting;
    $('cancel-adapt').disabled = !mutable || busy;
    $('create').disabled = $('create').disabled || !mutable;
    if (hasJob) {
      $('saved-mandate').textContent = state.mandate;
      $('job-id').textContent = 'Tâche ' + state.job_id;
      $('saved-requirements').replaceChildren();
      (state.requirements || []).forEach(text => { const item = document.createElement('li'); item.textContent = text + ' — portée sémantique non vérifiée'; $('saved-requirements').appendChild(item); });
    }
    const result = hasJob && state.result;
    $('result').hidden = !validResult(result);
    if (validResult(result)) {
      $('row-count').textContent = result.rows + (result.rows > 1 ? ' lignes' : ' ligne');
      $('totals').replaceChildren();
      result.totals.forEach(total => { const row = document.createElement('tr'); [total.currency, total.amount].forEach(value => { const cell = document.createElement('td'); cell.textContent = value; row.appendChild(cell); }); $('totals').appendChild(row); });
      const verification = state.verification;
      $('result-proof').textContent = 'Source SHA-256 : ' + result.source_sha256 + '. ' + (verification && verification.status === 'PASS' ? 'Contrats CSV vérifiés à la date du reçu ; une clôture actuelle réexécute les contrôles.' : 'Résultat produit ; vérification distincte à consulter.') + ' Source déclarée par l’utilisateur ; vérité sémantique : UNKNOWN.';
    }
    renderFreshness();
  }
  $('job-form').addEventListener('submit', async event => {
    event.preventDefault();
    if (busy) return;
    const mandate = $('mandate').value.trim();
    const requirements = $('requirements').value.split(/\r?\n/).map(x => x.trim()).filter(Boolean);
    const source = $('source-csv').value;
    if (!mandate || !requirements.length || requirements.length > 32 || requirements.some(x => x.length > 2000) || new TextEncoder().encode(source).length > 32768) { show('Vérifiez la demande, 1 à 32 exigences et un CSV de 32 Kio maximum.', 'error'); return; }
    await mutate('create', {}, {mandate, requirements, source_csv: source});
  });
  $('sample').addEventListener('click', () => { $('mandate').value = 'Calculer les totaux de ce tableau fictif par devise et conserver chaque ligne.'; if (!state) $('requirements').value = DEFAULT_REQUIREMENTS.join('\n'); $('source-csv').value = SAMPLE; $('source-csv').focus(); });
  async function draft(enabled) {
    if (busy) return;
    refreshState();
    if (!state || storageBlocked) { render(); return; }
    const expected = credentials();
    busy = true;
    try {
      await requireSlots().withKeys(slotKeys, () => {
        state = requireCurrent(expected);
        assertNoMissionPending();
        if (state.pending) throw new Error('Une intention attend son reçu exact. La reprise ne sera pas remplacée par une correction.');
        state.adaptation_draft = enabled; persist();
      });
      if (enabled) { $('mandate').value = state.mandate; $('requirements').value = state.requirements.join('\n'); $('source-csv').value = state.source_csv; }
      show(enabled ? 'Préparez une correction. Elle créera un nouvel objet lié au précédent, avec les mêmes exigences et de nouveaux contrôles. L’historique reste conservé.' : 'Correction abandonnée. La tâche précédente reste conservée.', 'neutral');
      if (enabled) $('mandate').focus();
    } catch (error) { refreshState(); show(error.message, 'unknown'); }
    finally { busy = false; render(); }
  }
  $('adapt').addEventListener('click', () => draft(true));
  $('cancel-adapt').addEventListener('click', () => draft(false));
  ['produce', 'verify', 'complete'].forEach(action => $(action).addEventListener('click', () => mutate(action, {expected_step_id: action})));
  $('status').addEventListener('click', () => read('status'));
  $('audit').addEventListener('click', () => read('audit'));
  $('reconcile').addEventListener('click', reconcile);
  function download(contents, type, suffix) {
    const url = URL.createObjectURL(new Blob([contents], {type}));
    const anchor = document.createElement('a'); anchor.href = url; anchor.download = 'agir-' + state.job_id + '.' + suffix; anchor.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  $('download-json').addEventListener('click', () => {
    if (!state || !validResult(state.result)) return;
    const value = {schema: 'SOL_ACTION_EXPORT/v1', job_id: state.job_id, mandate: state.mandate, requirements: state.requirements, result: state.result, verification: state.verification || null, completion: state.completion || null, source_origin: 'CLIENT_DECLARED_NOT_AUTHENTICATED', semantic_truth: 'UNKNOWN', current_reuse_authorized: false, export_status: 'HISTORICAL_DOCUMENT_ONLY'};
    download(JSON.stringify(value, null, 2), 'application/json;charset=utf-8', 'json');
  });
  $('download-csv').addEventListener('click', () => { if (state && validResult(state.result)) download('currency,amount\r\n' + state.result.totals.map(x => x.currency + ',' + x.amount).join('\r\n') + '\r\n', 'text/csv;charset=utf-8', 'csv'); });
  // A dated public snapshot, if provided, is evidence of a connector read only.
  fetch('/provider-observation.json', {cache: 'no-store'}).then(response => response.ok ? response.json() : null).then(snapshot => {
    if (snapshot && snapshot.provider === 'StorageChain' && snapshot.connector_read_executed === true && typeof snapshot.observed_at === 'string' && typeof snapshot.public_summary === 'string') $('storagechain-status').textContent = 'StorageChain · lecture observée le ' + snapshot.observed_at + ' : ' + snapshot.public_summary + ' Cette observation datée ne prouve pas un accès actuel.';
  }).catch(() => {});
  function sharedChanged(event) {
    if (event && event.type === 'storage' && event.key !== null && !slotKeys.includes(event.key)) return;
    authority = null; readOnlyView = null; refreshState(true); render();
  }
  root.addEventListener('storage', sharedChanged);
  root.addEventListener('pageshow', sharedChanged);
  document.addEventListener('visibilitychange', sharedChanged);
  setInterval(() => { if (refreshState(true)) render(); else renderFreshness(); }, 500);
  if (state) { $('mandate').value = state.mandate; $('requirements').value = state.requirements.join('\n'); $('source-csv').value = state.source_csv; }
  render();
})(typeof globalThis === 'undefined' ? this : globalThis);
