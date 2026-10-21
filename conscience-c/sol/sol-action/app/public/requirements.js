(function (root) {
  'use strict';
  const DEFAULTS = ['Conserver chaque ligne d’entrée.', 'Calculer exactement les totaux, sans arrondi intermédiaire.', 'Séparer les devises et identifier le tableau source.'];
  const object = value => Boolean(value && typeof value === 'object' && !Array.isArray(value));
  function canonical(kind, currency) {
    if (/^[0-2]$/.test(kind)) return DEFAULTS[Number(kind)];
    if (kind === 'nonnegative') return 'Interdire les montants négatifs.';
    if (kind === 'currency' && typeof currency === 'string' && /^[A-Z]{3}$/.test(currency)) return 'Autoriser uniquement la devise ' + currency + '.';
    return null;
  }
  function appendExact(value, line) {
    if (typeof value !== 'string' || typeof line !== 'string' || !line || line.includes('\n') || line.includes('\r')) return null;
    if (value.split(/\r?\n/).filter(item => item.length > 0).length >= 32) return null;
    return value + (value && !value.endsWith('\n') ? '\n' : '') + line;
  }
  function reasonLabel(code) {
    const labels = {
      CANONICAL_SOURCE_ADMISSIBLE: 'La source permet ce contrat explicite, avant calcul.',
      UNSUPPORTED_WHOLE_REQUIREMENT: 'Le texte entier ne correspond à aucun contrat pris en charge.',
      SOURCE_OUTSIDE_SQL_CONTRACT: 'La source sort du format contrôlé.',
      FORBIDDEN_SOURCE_CURRENCY: 'Une ligne contient une devise interdite.',
      NEGATIVE_SOURCE_RECORD: 'Une ligne contient un montant négatif.',
      SOURCE_ROW_BOUND_EXCEEDED: 'Le nombre de lignes dépasse la limite demandée.',
      SOURCE_ABSOLUTE_AMOUNT_BOUND_EXCEEDED: 'La valeur absolue d’un montant dépasse la limite demandée.',
      EXACT_SQL_RESULT_AND_SOURCE_CONSTRAINT_MATCH: 'Le résultat conservé correspond au calcul SQL de référence et aux contraintes de source.',
      RESULT_DIFFERS_FROM_SQL_ORACLE: 'Le résultat conservé diffère du calcul SQL de référence.',
      NO_STORED_RESULT: 'Aucun résultat conservé ne permet ce contrôle.'
    };
    return Object.prototype.hasOwnProperty.call(labels, code) ? labels[code] + ' (' + code + ')' : 'Motif reçu : ' + code;
  }
  function validGuard(guard, requirements) {
    return Boolean(object(guard) && guard.semantic_truth === 'UNKNOWN' && guard.general_mandate === 'UNKNOWN' && ['PASS', 'FAIL', 'UNKNOWN'].includes(guard.status) && ['PRE_EFFECT_ADMISSION', 'RESULT_VERIFICATION'].includes(guard.phase) &&
      Array.isArray(requirements) && Array.isArray(guard.requirements) && guard.requirements.length === requirements.length &&
      guard.requirements.every((row, index) => object(row) && row.index === index && row.text === requirements[index] && ['PASS', 'FAIL', 'UNKNOWN'].includes(row.verdict) && typeof row.reason === 'string') &&
      (guard.status !== 'PASS' || guard.requirements.every(row => row.verdict === 'PASS')));
  }
  function controlledRefusal(intent, response, historical = false, requirements) {
    const produce = intent && intent.action === 'produce';
    return Boolean(intent && ['produce', 'verify', 'complete'].includes(intent.action) && intent.input && object(response) && response.ok === false && response.action === intent.action &&
      response.job_id === intent.input.job_id && response.request_id === intent.input.request_id && response.production_request_id === (produce ? intent.input.request_id : null) &&
      (historical ? response.status === 'HISTORICAL_NOT_CURRENT' && response.historical_status === 'REJECTED' && response.needs_current_revalidation === true : response.status === 'REJECTED') &&
      response.receipt_kind === 'REQUIREMENTS_GUARD_REFUSAL' && response.effect_scope === (produce ? 'REQUIREMENTS_ADMISSION_BEFORE_BRIDGE_BIND_ONLY' : 'REQUIREMENTS_VERIFICATION_BEFORE_CORE_DISPATCH_ONLY') &&
      response.business_effect === (produce ? 'NO_BEGIN_OR_WORKER_STARTED_BY_THIS_CALL' : 'NO_CORE_VERIFY_OR_COMPLETE_BY_THIS_CALL') && response.receipt_recording_effect === 'APPEND_ONLY_REQUIREMENTS_GUARD_RECEIPT_RECORDED' &&
      response.terminal === true && response.durable_refusal === true && response.worker_reexecuted === false && response.current_reuse_authorized === false && response.automatic_retry === false &&
      object(response.requirements_guard) && response.requirements_guard.phase === (produce ? 'PRE_EFFECT_ADMISSION' : 'RESULT_VERIFICATION') && ['FAIL', 'UNKNOWN'].includes(response.requirements_guard.status) &&
      (!requirements || validGuard(response.requirements_guard, requirements)));
  }
  function historical(value, secrets = []) {
    if (Array.isArray(value)) return value.map(item => historical(item, secrets));
    if (object(value)) {
      const out = {};
      for (const [key, item] of Object.entries(value)) {
        if (['capability', 'parent_capability', 'capability_hash', 'bridge_token', 'token', 'token_sha256', 'source_csv', 'authorization', 'apikey', 'service_role_key'].includes(key)) continue;
        if (['current_reuse_authorized', 'begin_granted', 'binding_granted'].includes(key)) out[key] = false;
        else if (key === 'needs_current_revalidation') out[key] = true;
        else out[key] = historical(item, secrets);
      }
      return out;
    }
    if (typeof value === 'string') return secrets.filter(secret => typeof secret === 'string' && secret.length === 64).reduce((text, secret) => text.split(secret).join('[REDACTED]'), value).replace(/https?:\/\/[^\s"<>]*(?:capability|token|secret)=[^\s"<>]*/gi, '[REDACTED_URL]');
    return value;
  }
  function exportBundle(state, exportedAt) {
    const last = object(state.last_response) ? state.last_response : {};
    const value = {
      schema: 'SOL_ACTION_RESULT_AND_PROOF/v2', export_status: 'HISTORICAL_DOCUMENT_ONLY', historical_only: true, exported_at: exportedAt,
      job_id: state.job_id, mandate: state.mandate, requirements: state.requirements,
      source_sha256: state.source_sha256 || (state.result && state.result.source_sha256) || null,
      result_sha256: state.result_sha256 || last.result_sha256 || null,
      result: state.result || null, release: {binding: state.release_binding || last.release_binding || null, requirements_release_hash: state.requirements_release_hash || last.requirements_release_hash || null, requirements_guard_runtime_hash: state.requirements_guard_runtime_hash || last.requirements_guard_runtime_hash || (state.requirements_guard && state.requirements_guard.guard_runtime_hash) || null},
      requirements_guard: state.requirements_guard || last.requirements_guard || null,
      verification: state.verification || null, completion: state.completion || null,
      scope: 'CSV_EXACT_CENTS_ONLY_AND_EXPLICIT_REQUIREMENTS_CONTRACTS', general_mandate: 'UNKNOWN', semantic_truth: 'UNKNOWN',
      current_reuse_authorized: false, needs_current_revalidation: true,
      provenance: 'DOCUMENTARY_EXPORT_OF_PRESERVED_RECEIPTS_NOT_CURRENT_PROVIDER_OR_SEMANTIC_PROOF'
    };
    const secrets = [state.capability].concat((state.ancestors || []).map(item => item.capability));
    return historical(value, secrets);
  }
  const helpers = {DEFAULTS, canonical, appendExact, reasonLabel, validGuard, controlledRefusal, historical, exportBundle};
  if (typeof module !== 'undefined' && module.exports) module.exports = helpers;
  root.SolRequirements = helpers;
  if (typeof document === 'undefined') return;
  const $ = id => document.getElementById(id);
  function preview() {
    const kind = $('requirement-template').value;
    $('requirement-currency-field').hidden = kind !== 'currency';
    $('requirement-template-preview').textContent = canonical(kind, $('requirement-currency').value) || (kind === 'currency' ? 'Saisissez trois lettres majuscules, par exemple EUR. Aucun texte libre ne sera converti.' : 'Choisissez une formulation ; son texte intégral sera affiché ici avant ajout.');
  }
  $('requirement-template').addEventListener('change', preview);
  $('requirement-currency').addEventListener('input', preview);
  $('requirement-add').addEventListener('click', () => {
    if ($('requirements').disabled) return;
    const line = canonical($('requirement-template').value, $('requirement-currency').value);
    const next = appendExact($('requirements').value, line);
    $('requirement-helper-message').textContent = next === null ? 'Choisissez une formulation valide et gardez au plus 32 lignes. Vos textes restent inchangés.' : 'Formulation ajoutée explicitement. Les lignes déjà saisies restent inchangées ; le serveur effectuera son propre contrôle avant tout calcul.';
    if (next !== null) { $('requirements').value = next; $('requirements').focus(); }
  });
  function paragraph(text, className) { const p = document.createElement('p'); p.textContent = text; if (className) p.className = className; return p; }
  helpers.render = (guard, requirements) => {
    const list = $('requirements-guard-lines'); list.replaceChildren();
    $('requirements-guard').hidden = !Array.isArray(requirements);
    if (!Array.isArray(requirements)) return;
    const known = validGuard(guard, requirements);
    $('requirements-guard-summary').textContent = known ? 'Contrôle des exigences conservé : ' + guard.status + ' · portée bornée' : 'Exigences à contrôler avant le calcul · issue UNKNOWN';
    $('requirements-guard-date').textContent = known ? 'Phase : ' + (guard.phase === 'PRE_EFFECT_ADMISSION' ? 'admission avant calcul' : 'vérification du résultat conservé') + '. Observation : ' + (typeof guard.checked_at === 'string' ? guard.checked_at : 'date inconnue') + '. Échéance d’origine : ' + (typeof guard.expires_at === 'string' ? guard.expires_at : 'inconnue') + '. Copie de reçu ; aucune autorisation actuelle n’est déduite de cet affichage.' : 'Aucun contrôle corrélé n’est disponible dans cette vue. Le serveur devra examiner chaque ligne avant le début du calcul ; les textes libres ne sont pas convertis automatiquement.';
    requirements.forEach((value, index) => {
      const row = known ? guard.requirements[index] : null;
      const item = document.createElement('li');
      item.appendChild(paragraph(value, 'requirement-exact'));
      item.appendChild(paragraph('Ligne ' + (index + 1) + ' · ' + (row ? row.verdict : 'UNKNOWN') + ' · ' + (row ? reasonLabel(row.reason) : 'Contrat non observé'), 'field-note'));
      item.appendChild(paragraph('Portée : cette ligne et le tableau lié au reçu, à la date conservée ; aucun jugement sur le mandat général.', 'field-note'));
      item.appendChild(paragraph(row && row.verdict === 'PASS' ? 'Ce contrôle ne vaut que pour le contrat explicite indiqué par le reçu ; le mandat général reste UNKNOWN.' : row && row.verdict === 'FAIL' ? 'Corriger la source ou préparer une correction explicite ; conserver cette exigence et le refus.' : 'Préciser un contrat pris en charge ou traiter cette exigence avec une autre capacité. La conserver ; aucun calcul ne doit contourner ce point.', 'field-note'));
      list.appendChild(item);
    });
  };
  helpers.controls = () => {
    const disabled = $('requirements').disabled;
    ['requirement-template', 'requirement-currency', 'requirement-add'].forEach(id => { $(id).disabled = disabled; });
  };
  preview();
})(typeof globalThis === 'undefined' ? this : globalThis);
