(function (root) {
  'use strict';
  const JOB_KEY = 'sol-action-session-v1';
  const KEY = 'sol-action-mission-session-v1';
  const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[1-8][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i;
  const HASH = /^[a-f0-9]{64}$/;
  const object = value => Boolean(value && typeof value === 'object' && !Array.isArray(value));
  function canonical(value) {
    if (Array.isArray(value)) return '[' + value.map(canonical).join(',') + ']';
    if (object(value)) return '{' + Object.keys(value).sort().map(key => JSON.stringify(key) + ':' + canonical(value[key])).join(',') + '}';
    return JSON.stringify(value);
  }
  function matrix(value) {
    return Array.isArray(value) && value.length > 0 && value.every(row => object(row) &&
      typeof row.compound_id === 'string' && typeof row.task_id === 'string' && typeof row.role === 'string' &&
      object(row.requirement) && typeof row.requirement.id === 'string' && typeof row.requirement.text === 'string' &&
      object(row.requirement.contract) && row.validation === 'UNKNOWN');
  }
  function validReport(report) {
    return Boolean(object(report) && ['TECHNICAL_RESULT_VERIFIED', 'NOT_VERIFIED'].includes(report.status) &&
      ['PASS', 'FAIL', 'UNKNOWN'].includes(report.technical_verdict) && report.general_mandate === 'UNKNOWN' &&
      matrix(report.requirements) && Array.isArray(report.checks) && report.checks.length > 0 &&
      report.checks.every(check => object(check) && typeof check.name === 'string' && typeof check.reason === 'string' &&
        ['PASS', 'FAIL', 'UNKNOWN'].includes(check.verdict) && object(check.evidence)) &&
      (report.status !== 'TECHNICAL_RESULT_VERIFIED' || (report.technical_verdict === 'PASS' && report.checks.every(check => check.verdict === 'PASS'))));
  }
  function currentTechnical(response, now, receivedAt, elapsed) {
    if (!object(response) || response.ok !== true || response.current_reuse_authorized !== true || response.deduplicated ||
        response.status === 'HISTORICAL_NOT_CURRENT' || !validReport(response.report) || response.report.status !== 'TECHNICAL_RESULT_VERIFIED') return false;
    const verified = Date.parse(response.report.verified_at), expires = Date.parse(response.report.expires_at);
    return Number.isFinite(verified) && Number.isFinite(expires) && verified <= now + 1000 && expires > now &&
      expires > verified && expires - verified <= 60000 && now >= receivedAt && elapsed >= 0 && elapsed < 60000;
  }
  const helpers = {KEY, JOB_KEY, canonical, matrix, validReport, currentTechnical};
  if (typeof module !== 'undefined' && module.exports) module.exports = helpers;
  root.SolMissions = helpers;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  let saved = {version: 1, job_id: null, mission_id: null, pending: null};
  let storageBlocked = false;
  let busy = false;
  let missions = [];
  let listedJob = null;
  let listedAt = null;
  let listValidated = false;
  let jobChanged = false;
  let authority = null;
  let shownReport = null;
  function message(text, kind = 'neutral') {
    $('mission-message').textContent = text;
    $('mission-message').className = 'message ' + kind;
  }
  try {
    const raw = localStorage.getItem(KEY);
    if (raw) {
      const data = JSON.parse(raw);
      if (!object(data) || data.version !== 1 || (data.job_id !== null && !UUID.test(data.job_id)) ||
          (data.mission_id !== null && !UUID.test(data.mission_id))) throw new Error('invalid');
      if (data.pending && (!object(data.pending) || data.pending.action !== 'verify' || !object(data.pending.input) ||
          !UUID.test(data.pending.input.job_id) || !UUID.test(data.pending.input.mission_id) || !UUID.test(data.pending.input.request_id))) throw new Error('invalid');
      saved = data;
      if (saved.pending) message('Une vérification attend son reçu exact. UUID conservé : ' + saved.pending.input.request_id + '. Consultez-le sans créer une autre intention.', 'unknown');
    }
  } catch (_) {
    storageBlocked = true;
    message('La reprise des liens est illisible ou indisponible. Aucune nouvelle vérification ne sera envoyée ; les données locales restent conservées.', 'unknown');
  }
  function save(value = saved) {
    if (storageBlocked) throw new Error('La reprise locale est indisponible. Aucune nouvelle intention ne peut être envoyée.');
    try { localStorage.setItem(KEY, JSON.stringify(value)); }
    catch (_) { throw new Error('La sauvegarde de l’intention a échoué. Aucune nouvelle requête de vérification ne sera envoyée.'); }
  }
  function clearPending() {
    const next = Object.assign({}, saved, {pending: null});
    save(next);
    saved = next;
  }
  function job() {
    let value;
    try { value = JSON.parse(localStorage.getItem(JOB_KEY) || 'null'); } catch (_) { value = null; }
    if (!object(value) || !UUID.test(value.job_id) || typeof value.capability !== 'string' || !HASH.test(value.capability)) {
      throw new Error('Enregistrez ou reprenez d’abord un travail CSV dans ce navigateur. Aucun lien n’est créé automatiquement.');
    }
    return {job_id: value.job_id, capability: value.capability};
  }
  function selected() { return missions.find(item => item.mission_id === $('mission-select').value) || null; }
  function copyProvenance(reason) {
    $('mission-list-provenance').textContent = listedJob
      ? 'Copie conservée pour la tâche ' + listedJob + ', consultée le ' + listedAt + '. ' + reason
      : 'Aucune liste de liens confirmée dans cette session. ' + reason;
  }
  function checkJobChange() {
    if (!listedJob) return false;
    let current = null;
    try { const value = JSON.parse(localStorage.getItem(JOB_KEY) || 'null'); if (object(value) && UUID.test(value.job_id)) current = value.job_id; } catch (_) { /* Reading metadata grants no action. */ }
    if (current === listedJob) return false;
    const changed = !jobChanged || listValidated;
    listValidated = false; jobChanged = true; authority = null;
    copyProvenance('Le travail du navigateur a changé ou est indisponible. Consulter ses liens avant toute nouvelle vérification.');
    if (changed) message('La copie affichée appartient à une autre tâche conservée. Consultez les liens du travail actuel ; aucun appel n’a été envoyé.', 'unknown');
    return changed;
  }
  function controls() {
    checkJobChange();
    $('mission-load').disabled = busy;
    $('mission-select').disabled = busy || Boolean(saved.pending) || missions.length === 0;
    $('mission-verify').disabled = busy || !listValidated || storageBlocked || Boolean(saved.pending) || !selected();
    $('mission-receipt').hidden = !saved.pending;
    $('mission-receipt').disabled = busy || !saved.pending || storageBlocked;
    $('mission-pending-id').hidden = !saved.pending;
    $('mission-pending-id').textContent = saved.pending ? 'Tâche ' + saved.pending.input.job_id + ' · Mission ' + saved.pending.input.mission_id + ' · UUID de vérification conservé : ' + saved.pending.input.request_id : '';
  }
  function text(tag, value, className) {
    const element = document.createElement(tag);
    element.textContent = value;
    if (className) element.className = className;
    return element;
  }
  function renderMatrix(rows) {
    $('mission-matrix').replaceChildren();
    rows.forEach(row => {
      const item = document.createElement('li');
      item.appendChild(text('p', row.requirement.text, 'mission-verbatim'));
      item.appendChild(text('p', 'Exigence ' + row.requirement.id + ' · rôle ' + row.role + ' · tâche ' + row.task_id + ' · ensemble ' + row.compound_id, 'identifier'));
      if (typeof row.anchor_task_id === 'string') item.appendChild(text('p', 'Tâche d’ancrage : ' + row.anchor_task_id, 'identifier'));
      item.appendChild(text('p', 'Contrat : ' + JSON.stringify(row.requirement.contract), 'mission-contract'));
      if (typeof row.mapping_basis === 'string') item.appendChild(text('p', 'Base du lien déclarée : ' + row.mapping_basis, 'field-note'));
      item.appendChild(text('p', 'Validation sémantique du lien : UNKNOWN.', 'field-note'));
      $('mission-matrix').appendChild(item);
    });
    $('mission-definition-summary').textContent = 'Toutes les exigences conservées — ' + rows.length + ' lignes';
    $('mission-definition').hidden = false;
  }
  function definition(item) {
    $('mission-job-mandate').textContent = item.definition.job.mandate;
    $('mission-job-requirements').replaceChildren();
    item.definition.job.requirements.forEach(value => $('mission-job-requirements').appendChild(text('li', value)));
    $('mission-source').textContent = 'Empreinte du tableau conservé : ' + item.definition.job.source_sha256;
    renderMatrix(item.definition.requirements_matrix);
  }
  function report(value, provenance, missionId) {
    shownReport = value;
    $('mission-report-details').hidden = false;
    $('mission-checks').replaceChildren();
    value.checks.forEach(check => $('mission-checks').appendChild(text('li', check.name + ' · ' + check.verdict + ' · ' + check.reason)));
    $('mission-report-time').textContent = 'Mission ' + missionId + '. ' + (provenance === 'LIVE_VERIFY' ? 'Reçu de la vérification demandée. ' : 'Lecture historique. ') + 'Observation conservée : ' + (typeof value.verified_at === 'string' ? value.verified_at : 'date inconnue') +
      '. Échéance d’origine : ' + (typeof value.expires_at === 'string' ? value.expires_at : 'inconnue') + '. La lecture ne modifie pas ces dates.';
    if (!selected()) {
      $('mission-job-mandate').textContent = 'Définition à relire avec « Consulter les liens enregistrés ». Cette matrice provient du reçu historique.';
      $('mission-job-requirements').replaceChildren(); $('mission-source').textContent = '';
      renderMatrix(value.requirements);
    }
    freshness();
  }
  function freshness() {
    if (checkJobChange()) controls();
    const fresh = authority && currentTechnical(authority.response, Date.now(), authority.receivedAt, performance.now() - authority.monotonic);
    if (fresh) {
      const seconds = Math.max(0, Math.min(60, Math.ceil((Date.parse(shownReport.expires_at) - Date.now()) / 1000), Math.ceil((60000 - (performance.now() - authority.monotonic)) / 1000)));
      $('mission-freshness').textContent = 'Résultat technique et liens contrôlés à cet instant · ' + seconds + ' s restantes. Demande générale : UNKNOWN.';
    } else {
      $('mission-freshness').textContent = shownReport
        ? 'Reçu historique — aucune validité actuelle déduite. Contrôle technique conservé : ' + shownReport.technical_verdict + '. Demande générale : UNKNOWN.'
        : 'Aucune vérification de ces liens n’est actuelle. Demande générale : UNKNOWN.';
      if (authority) { authority = null; message('La vérification conservée est désormais historique. Une nouvelle vérification explicite est nécessaire pour observer l’état présent.', 'unknown'); }
    }
    $('mission-freshness').className = fresh ? 'field-note' : 'field-note mission-historical';
  }
  async function post(action, input) {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), 15000);
    try {
      const response = await fetch('/api/mission', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({action, input}), signal: controller.signal, cache: 'no-store'});
      const value = await response.json();
      if (!response.ok || !object(value)) throw new Error('Réponse illisible ou refusée. L’intention éventuelle reste conservée.');
      return value;
    } finally { clearTimeout(timeout); }
  }
  function matching(value, input) {
    return object(value) && value.ok === true && value.job_id === input.job_id && value.mission_id === input.mission_id &&
      value.request_id === input.request_id && validReport(value.report);
  }
  function sameMatrix(value, missionId) {
    const item = missions.find(item => item.mission_id === missionId);
    return !item || canonical(value.report.requirements) === canonical(item.definition.requirements_matrix);
  }
  async function load() {
    if (busy) return;
    authority = null; listValidated = false; busy = true; controls(); freshness();
    try {
      const credentials = job();
      const response = await post('status', credentials);
      if (response.ok !== true || response.job_id !== credentials.job_id || response.status !== 'HISTORICAL_NOT_CURRENT' || response.current_reuse_authorized !== false || !Array.isArray(response.missions)) throw new Error('La liste des missions n’est pas corrélée à cette tâche. Aucun lien n’est adopté.');
      if (!response.missions.every(item => object(item) && UUID.test(item.mission_id) && HASH.test(item.definition_hash) && object(item.definition) && object(item.definition.job) &&
          typeof item.definition.job.mandate === 'string' && Array.isArray(item.definition.job.requirements) && item.definition.job.requirements.every(value => typeof value === 'string') &&
          HASH.test(item.definition.job.source_sha256) && matrix(item.definition.requirements_matrix))) throw new Error('Une définition reçue est incomplète. Aucune vérification ne sera préparée depuis cette réponse.');
      missions = response.missions; listedJob = credentials.job_id; listedAt = new Date().toISOString(); listValidated = true; jobChanged = false;
      copyProvenance('Lecture historique corrélée à cette tâche. Une vérification explicite demande un nouveau contrôle.');
      shownReport = null; $('mission-report-details').hidden = true; freshness();
      $('mission-select').replaceChildren(text('option', missions.length ? 'Choisir une mission enregistrée' : 'Aucune mission enregistrée'));
      $('mission-select').children[0].value = '';
      missions.forEach(item => {
        const label = Array.from(item.definition.job.mandate.replace(/\s+/g, ' ').trim()).slice(0, 60).join('');
        const option = text('option', (label || 'Mission enregistrée') + ' · ' + item.definition.requirements_matrix.length + ' exigences · ' + item.mission_id);
        option.value = item.mission_id; $('mission-select').appendChild(option);
      });
      const prior = missions.find(item => item.mission_id === saved.mission_id && saved.job_id === listedJob);
      $('mission-select').value = prior ? prior.mission_id : '';
      if (prior) { definition(prior); if (validReport(prior.last_report) && sameMatrix({report: prior.last_report}, prior.mission_id)) report(prior.last_report, 'HISTORICAL_STATUS', prior.mission_id); }
      else { $('mission-definition').hidden = true; $('mission-report-details').hidden = true; shownReport = null; freshness(); }
      message(missions.length ? 'Liens enregistrés consultés. Choisissez la mission exacte ; les rapports de cette lecture restent historiques.' : 'Aucun lien enregistré n’a été trouvé. Un opérateur doit enregistrer la mission ; cette page ne le fait pas automatiquement.', missions.length ? 'neutral' : 'unknown');
    } catch (error) { listValidated = false; copyProvenance('Lecture actuelle non confirmée. Cette copie ne permet pas une nouvelle vérification ; consulter les liens à nouveau.'); message(error.message || 'Lecture indisponible.', 'unknown'); }
    finally { busy = false; controls(); }
  }
  async function verify() {
    if (busy || !listValidated || saved.pending || storageBlocked) return;
    const item = selected();
    if (!item) return;
    authority = null; busy = true;
    try {
      const credentials = job();
      if (credentials.job_id !== listedJob) throw new Error('La tâche du navigateur a changé. Consultez ses liens avant de préparer une vérification.');
      const input = {job_id: credentials.job_id, mission_id: item.mission_id, request_id: crypto.randomUUID()};
      saved = {version: 1, job_id: input.job_id, mission_id: input.mission_id, pending: {action: 'verify', input, prepared_at: new Date().toISOString()}};
      save(); controls(); freshness();
      const monotonic = performance.now();
      const response = await post('verify', Object.assign({}, input, {capability: credentials.capability}));
      if (!matching(response, input) || !sameMatrix(response, input.mission_id)) throw new Error('Le reçu ne correspond pas à l’intention et à toutes ses exigences. Conservez l’identifiant et consultez son reçu sans relancer.');
      clearPending();
      if (currentTechnical(response, Date.now(), Date.now(), performance.now() - monotonic)) authority = {response, receivedAt: Date.now(), monotonic};
      report(response.report, 'LIVE_VERIFY', input.mission_id);
      message(response.report.technical_verdict === 'PASS' ? 'Contrôles techniques reçus. La demande générale reste UNKNOWN ; les dates et toutes les exigences restent visibles.' : 'Le contrôle technique ne confirme pas le résultat et ses liens. Le reçu est conservé, sans décision sur le mandat général.', response.report.technical_verdict === 'PASS' ? 'neutral' : 'unknown');
    } catch (error) { message((error.message || 'Réponse indisponible.') + (saved.pending ? ' Intention conservée : ' + saved.pending.input.request_id + '. Aucun nouvel envoi automatique.' : ''), 'unknown'); }
    finally { busy = false; controls(); }
  }
  async function receipt() {
    if (busy || !saved.pending || storageBlocked) return;
    const pending = saved.pending;
    authority = null; busy = true; controls(); freshness();
    try {
      const credentials = job();
      if (credentials.job_id !== pending.input.job_id) throw new Error('L’intention appartient à une autre tâche. Son identifiant reste conservé.');
      const input = {job_id: pending.input.job_id, mission_id: pending.input.mission_id, target_request_id: pending.input.request_id, capability: credentials.capability};
      const response = await post('receipt', input);
      if (response.ok !== true || response.job_id !== input.job_id || response.mission_id !== input.mission_id || response.target_request_id !== input.target_request_id || response.current_reuse_authorized !== false) throw new Error('Consultation du reçu non corrélée. L’intention originale reste inconnue.');
      if (response.found !== true) { message('Reçu absent : issue UNKNOWN. L’intention et son UUID restent conservés ; aucune vérification n’est rejouée.', 'unknown'); return; }
      // SQL preserves the original receipt status. The read-only wrapper and
      // disabled authority make it historical; its text is not a current grant.
      if (response.status !== 'HISTORICAL_NOT_CURRENT' || !matching(response.receipt, pending.input) || response.receipt.current_reuse_authorized !== false || !sameMatrix(response.receipt, input.mission_id)) throw new Error('Le reçu historique est incomplet ou lié à une autre intention. L’intention originale reste conservée.');
      clearPending();
      report(response.receipt.report, 'HISTORICAL_RECEIPT', input.mission_id);
      message('Reçu exact retrouvé en lecture seule. Il reste historique ; aucune vérification n’a été rejouée. Demande générale : UNKNOWN.', 'neutral');
    } catch (error) { message(error.message || 'Reçu indisponible ; intention conservée.', 'unknown'); }
    finally { busy = false; controls(); }
  }
  $('mission-load').addEventListener('click', load);
  $('mission-verify').addEventListener('click', verify);
  $('mission-receipt').addEventListener('click', receipt);
  $('mission-select').addEventListener('change', () => {
    authority = null; shownReport = null;
    const item = selected();
    if (item) {
      definition(item);
      if (validReport(item.last_report) && sameMatrix({report: item.last_report}, item.mission_id)) report(item.last_report, 'HISTORICAL_STATUS', item.mission_id);
      else { $('mission-report-details').hidden = true; freshness(); }
    } else { $('mission-definition').hidden = true; $('mission-report-details').hidden = true; freshness(); }
    controls();
  });
  setInterval(freshness, 500);
  document.addEventListener('visibilitychange', freshness);
  root.addEventListener('pageshow', freshness);
  controls();
})(typeof globalThis === 'undefined' ? this : globalThis);
