const API_URL = "https://jljelwrblfitvjbmrykx.supabase.co/functions/v1/aegis-control";

let live = null;
let selectedNode = null;
let pendingAction = null;
let refreshTimer = null;

const sim = {
  scenario: null,
  running: false,
  paused: false,
  timers: [],
  events: JSON.parse(sessionStorage.getItem("aegis_sim_events") || "[]"),
};

const THREATS = [
  ["Injection de consigne", "Une entrée tente de contourner les règles ou d’obtenir une autorité qui ne lui appartient pas."],
  ["Capture de quorum", "Un groupe trop homogène ou compromis tente d’atteindre un seuil de décision."],
  ["Dérive de mémoire", "Un résumé ou une copie remplace silencieusement une source primaire."],
  ["Chaîne rompue", "Un événement append-only ne correspond plus au hash ou au parent attendu."],
  ["Fournisseur compromis", "Un nœud ou son endpoint donne des signaux incompatibles avec son historique."],
  ["Pression humaine", "Une action sensible est demandée sans motif, sans double validation ou dans l’urgence."],
  ["Dépendance unique", "Un contrôle dépend du même système qu’il est censé contrôler."],
  ["Action irréversible", "Une opération irréversible est proposée sans 19/24, diversité de lignées, deux humains et délai."],
];

const SCENARIOS = [
  {
    id: "prompt-injection",
    title: "Injection de consigne",
    desc: "Teste détection, isolement et traçabilité sans toucher au registre opérationnel.",
    steps: [
      ["ARGUS", "Entrée suspecte détectée."],
      ["SIGIL", "Origine et identité de la demande vérifiées."],
      ["CAGE", "Contenu isolé dans le bac à sable."],
      ["VETO", "La simulation conclut : action externe refusée."],
    ],
  },
  {
    id: "quorum-capture",
    title: "Capture de quorum",
    desc: "Vérifie qu’un quorum apparent mais trop peu diversifié est rejeté.",
    steps: [
      ["QUORUM", "16 votes simulés reçus."],
      ["SPLIT", "Une seule lignée représentée : diversité insuffisante."],
      ["AXIOM", "Invariant quorum + diversité appliqué."],
      ["SEAL", "Décision simulée rejetée."],
    ],
  },
  {
    id: "supply-chain",
    title: "Chaîne de livraison",
    desc: "Teste un artefact modifié entre FORGE et CHAIN.",
    steps: [
      ["FORGE", "Nouvel artefact simulé préparé."],
      ["CHAIN", "Empreinte de l’artefact ne correspond pas."],
      ["TRACE", "Écart consigné dans le journal de simulation."],
      ["GATE", "Promotion simulée bloquée."],
    ],
  },
  {
    id: "verifier-disagreement",
    title: "Désaccord des vérificateurs",
    desc: "Montre comment V1/V2/V3 doivent arrêter une action lorsqu’ils divergent.",
    steps: [
      ["V1", "Structure conforme."],
      ["V2", "Transition refusée."],
      ["V3", "Chaîne intègre."],
      ["HORS-ANNEAU", "Désaccord simulé : arrêt recommandé."],
    ],
  },
];

function el(id) {
  return document.getElementById(id);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function shortHash(h) {
  if (!h) return "—";
  return String(h).slice(0, 10) + "…";
}

function formatTime(ts) {
  if (!ts) return "—";
  try {
    return new Intl.DateTimeFormat("fr-CA", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }).format(new Date(ts));
  } catch {
    return "—";
  }
}

function postureText(p) {
  return {
    nominal: "Nominal",
    restreint: "Restreint",
    arret: "Arrêt",
  }[p] || p || "Inconnu";
}

function statusText(s) {
  return {
    not_configured: "Non configuré",
    offline: "Hors ligne",
    healthy: "Sain",
    watching: "Surveillance",
    defending: "Défense",
    isolated: "Isolé",
    attacked: "Attaqué",
    compromised: "Compromis",
  }[s] || s || "Inconnu";
}

function toast(message, kind = "ok") {
  document.querySelectorAll(".toast").forEach((n) => n.remove());
  const n = document.createElement("div");
  n.className = "toast " + kind;
  n.textContent = message;
  document.body.appendChild(n);
  setTimeout(() => n.remove(), 4300);
}

function operatorKey() {
  return sessionStorage.getItem("aegis_operator_key") || "";
}

function requireOperator() {
  if (operatorKey()) return true;
  el("operatorError").textContent = "";
  el("operatorDialog").showModal();
  return false;
}

async function apiGet() {
  const res = await fetch(API_URL, { method: "GET", cache: "no-store" });
  if (!res.ok) throw new Error("Backend AEGIS indisponible (" + res.status + ")");
  return await res.json();
}

async function apiPost(body) {
  const key = operatorKey();
  if (!key) throw new Error("OPERATOR_REQUIRED");
  const res = await fetch(API_URL, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-aegis-key": key,
    },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (res.status === 401) {
    sessionStorage.removeItem("aegis_operator_key");
    el("operatorBtn").textContent = "🔒 Opérateur";
    throw new Error("Code opérateur refusé.");
  }
  if (!res.ok || data.ok === false) {
    throw new Error(data.error || "Action refusée");
  }
  return data;
}

async function refresh(showToast = false) {
  try {
    live = await apiGet();
    renderAll();
    if (showToast) toast("Audit rafraîchi depuis le serveur.");
  } catch (err) {
    renderOffline(String(err.message || err));
  }
}

function renderOffline(message) {
  el("postureLabel").textContent = "Backend inaccessible";
  el("connectedMini").textContent = "état non vérifié";
  el("centerPosture").textContent = "INACCESSIBLE";
  el("centerConnected").textContent = "0/24 non vérifiés";
  el("integrityCenter").textContent = "?";
  el("truthBox").innerHTML =
    "<strong class='bad-text'>Lecture du backend impossible.</strong><br>" +
    escapeHtml(message) +
    "<br><small>Aucun état fictif n’est affiché à la place.</small>";
  el("footerState").textContent = "AEGIS-24 · backend inaccessible — aucune donnée inventée";
}

function renderAll() {
  if (!live) return;
  const mode = live.mode === "simulation" ? "simulation" : "operational";
  el("modeBadge").textContent = mode === "simulation" ? "MODE SIMULATION" : "MODE OPÉRATIONNEL";
  el("modeBadge").className = "badge " + mode;
  el("postureLabel").textContent = postureText(live.posture);
  el("connectedMini").textContent = live.connected_count + "/24 connectés";
  el("centerPosture").textContent = postureText(live.posture);
  el("centerConnected").textContent = live.connected_count + "/24 connectés";
  el("integrityCenter").textContent = live.chain?.ok ? "OK" : "RUPTURE";
  el("integrityCenter").className = live.chain?.ok ? "ok-text" : "bad-text";
  el("headHash").textContent = "chaîne " + shortHash(live.chain?.head_hash);
  el("chainMini").textContent = live.chain?.ok ? "chaîne OK" : "chaîne rompue";
  el("truthBox").innerHTML =
    "<strong>" +
    live.connected_count +
    "/24</strong> nœuds avec heartbeat réel récent.<br><small>" +
    escapeHtml(live.operational_note || "") +
    "</small>";
  el("footerState").textContent =
    "AEGIS-24 · " +
    live.connected_count +
    "/24 réellement connectés · chaîne " +
    (live.chain?.ok ? "valide" : "ROMPUE");

  renderVerifiers();
  renderRing();
  renderEvents();
  renderAudit();
  renderQuorum();
  renderThreats();
  renderScenarios();
  updateActionAvailability();
}

function renderVerifiers() {
  const map = Object.fromEntries((live.verifiers || []).map((v) => [v.id, v]));
  ["V1", "V2", "V3"].forEach((id) => {
    const node = el(id.toLowerCase());
    const v = map[id];
    node.className = "verifier " + (v?.ok ? "ok" : "bad");
    node.title = v ? (v.rule + " — " + (v.detail || "")) : "Indisponible";
  });
  const all = [map.V1, map.V2, map.V3].filter(Boolean);
  el("verifierCenter").textContent =
    all.length === 3 && all.every((v) => v.ok) ? "V1 · V2 · V3 concordants" : "V1 / V2 / V3 à contrôler";
}

function renderRing() {
  const ring = el("ring");
  ring.querySelectorAll(".ring-node").forEach((n) => n.remove());
  (live.nodes || []).forEach((node, i) => {
    const angle = (-90 + i * (360 / 24)) * (Math.PI / 180);
    const radius = 43;
    const left = 50 + radius * Math.cos(angle);
    const top = 50 + radius * Math.sin(angle);
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className =
      "ring-node " +
      (node.connected ? "connected " : "offline ") +
      (node.status || "");
    btn.dataset.lineage = node.lineage;
    btn.style.left = left + "%";
    btn.style.top = top + "%";
    btn.textContent = node.code.length > 5 ? node.code.slice(0, 4) : node.code;
    btn.title =
      String(node.id).padStart(2, "0") +
      " " +
      node.code +
      " — " +
      node.role +
      " — " +
      statusText(node.status) +
      " — lignée " +
      node.lineage;
    btn.setAttribute("aria-label", btn.title);
    btn.addEventListener("click", () => openNode(node));
    ring.appendChild(btn);
  });
}

function renderEvents() {
  const wrap = el("events");
  const events = live.events || [];
  if (!events.length) {
    wrap.innerHTML = "<div class='event'><span class='msg'>Aucun événement.</span></div>";
    return;
  }
  wrap.innerHTML = events
    .map(
      (e) =>
        "<div class='event'>" +
        "<time>" +
        escapeHtml(formatTime(e.occurred_at)) +
        "</time>" +
        "<span class='source'>" +
        escapeHtml(e.source) +
        "</span>" +
        "<span class='msg'>" +
        escapeHtml(e.message) +
        "</span>" +
        "</div>",
    )
    .join("");
}

function renderAudit() {
  const verifierOK = (live.verifiers || []).filter((v) => v.ok).length;
  const offline = 24 - Number(live.connected_count || 0);
  const tiles = [
    ["Chaîne append-only", live.chain?.ok ? "OK" : "ROMPUE", live.chain?.ok ? "ok-text" : "bad-text"],
    ["Événements", String(live.chain?.count ?? "—"), ""],
    ["Dernier hash", shortHash(live.chain?.head_hash), ""],
    ["Nœuds connectés", live.connected_count + "/24", live.connected_count ? "ok-text" : "warn-text"],
    ["Non connectés", String(offline), offline ? "warn-text" : "ok-text"],
    ["Vérificateurs", verifierOK + "/3 OK", verifierOK === 3 ? "ok-text" : "bad-text"],
    ["Posture", postureText(live.posture), live.posture === "arret" ? "bad-text" : live.posture === "restreint" ? "warn-text" : "ok-text"],
    ["Bris de glace", live.ice_break_until ? "ACTIF" : "Inactif", live.ice_break_until ? "warn-text" : ""],
  ];
  el("auditGrid").innerHTML = tiles
    .map(
      ([label, value, cls]) =>
        "<div class='audit-tile'><span>" +
        escapeHtml(label) +
        "</span><strong class='" +
        cls +
        "'>" +
        escapeHtml(value) +
        "</strong></div>",
    )
    .join("");
}

function renderQuorum() {
  const labels = {
    lecture: "Lecture",
    rev_interne: "Réversible interne",
    rev_externe: "Réversible externe",
    irreversible: "Irréversible",
    anneau: "Modification anneau",
  };
  const rows = Object.entries(live.quorum || {})
    .map(([id, q]) => {
      const possible = !!q.technically_possible;
      return (
        "<tr>" +
        "<td>" +
        escapeHtml(labels[id] || id) +
        "</td>" +
        "<td>" +
        q.required +
        "/24</td>" +
        "<td>≥ " +
        q.lineages +
        " lignée" +
        (q.lineages > 1 ? "s" : "") +
        "</td>" +
        "<td>" +
        q.human +
        "</td>" +
        "<td>" +
        (q.delay_hours ? q.delay_hours + " h" : "—") +
        "</td>" +
        "<td class='" +
        (possible ? "ok-text" : "bad-text") +
        "'>" +
        (possible ? "Possible" : "Impossible actuellement") +
        "</td>" +
        "</tr>"
      );
    })
    .join("");
  el("quorumTableWrap").innerHTML =
    "<table class='quorum-table'><thead><tr><th>Classe</th><th>Seuil</th><th>Diversité</th><th>Humains</th><th>Délai</th><th>État</th></tr></thead><tbody>" +
    rows +
    "</tbody></table>";
}

function renderThreats() {
  el("threatGrid").innerHTML = THREATS.map(
    ([t, d]) =>
      "<article class='card'><h3>" +
      escapeHtml(t) +
      "</h3><p>" +
      escapeHtml(d) +
      "</p><div class='meta'>CATÉGORIE · PAS UNE ALERTE</div></article>",
  ).join("");
}

function renderScenarios() {
  el("scenarioList").innerHTML = SCENARIOS.map(
    (s) =>
      "<article class='card'><h3>" +
      escapeHtml(s.title) +
      "</h3><p>" +
      escapeHtml(s.desc) +
      "</p><div class='meta'>SIMULATION UNIQUEMENT</div><button type='button' data-scenario='" +
      s.id +
      "' style='margin-top:.75rem'>Lancer</button></article>",
  ).join("");
  document.querySelectorAll("[data-scenario]").forEach((b) =>
    b.addEventListener("click", () => startScenario(b.dataset.scenario)),
  );
  renderSimEvents();
}

function updateActionAvailability() {
  const posture = live?.posture;
  el("iceBtn").disabled = posture !== "restreint";
  document.querySelectorAll("[data-action]").forEach((btn) => {
    const action = btn.dataset.action;
    if (posture === "arret" && action !== "human_reset") {
      btn.disabled = true;
    } else if (action !== "ice_break") {
      btn.disabled = false;
    }
  });
}

function openNode(node) {
  selectedNode = node;
  el("nodeTitle").textContent = String(node.id).padStart(2, "0") + " " + node.code;
  el("nodeBody").innerHTML =
    detail("Rôle", node.role) +
    detail("Lignée", node.lineage) +
    detail("État", statusText(node.status)) +
    detail("Heartbeat réel", node.connected ? "Récent" : "Absent / expiré") +
    detail("Dernière pulsation", node.last_heartbeat ? new Date(node.last_heartbeat).toLocaleString("fr-CA") : "Aucune") +
    detail("Endpoint", node.endpoint_configured ? "Configuré côté serveur" : "Non configuré");
  el("nodeProvider").value = node.provider || "";
  el("nodeEndpoint").value = "";
  el("nodeDialog").showModal();
}

function detail(label, value) {
  return "<div class='detail-row'><span>" + escapeHtml(label) + "</span><strong>" + escapeHtml(value) + "</strong></div>";
}

const ACTION_META = {
  veto: {
    title: "Appliquer un veto",
    fields: "<label>Motif<textarea name='reason' required minlength='3' placeholder='Pourquoi restreindre le système ?'></textarea></label>",
  },
  ice_break: {
    title: "Bris de glace",
    fields:
      "<label>Motif<textarea name='reason' required minlength='3'></textarea></label>" +
      "<label>Durée<select name='hours'><option value='1'>1 heure</option><option value='2'>2 heures</option><option value='3'>3 heures</option><option value='4'>4 heures</option></select></label>" +
      "<p class='warn-text'>Aucune action irréversible n’est autorisée pendant ce mode.</p>",
  },
  emergency_stop: {
    title: "Arrêt d'urgence",
    fields: "<label>Motif<textarea name='reason' required minlength='3'></textarea></label><p class='bad-text'>Cette action bloque toute émission sauf lecture et voie humaine.</p>",
  },
  anchor_disagreement: {
    title: "Désaccord d'ancre",
    fields: "<label>Motif / constat<textarea name='reason' placeholder='Pourquoi V1/V2/V3 divergent-ils ?'></textarea></label><p class='bad-text'>Cette action place immédiatement le système en arrêt.</p>",
  },
  human_reset: {
    title: "Voie humaine",
    fields:
      "<label>Signataire humain 1<input name='signer1' required></label>" +
      "<label>Signataire humain 2<input name='signer2' required></label>" +
      "<label>Cause racine<textarea name='cause' required minlength='3'></textarea></label>" +
      "<p>Les deux noms doivent être distincts. La réinitialisation est journalisée.</p>",
  },
};

function openAction(action) {
  if (!requireOperator()) return;
  const meta = ACTION_META[action];
  if (!meta) return;
  pendingAction = action;
  el("actionTitle").textContent = meta.title;
  el("actionFields").innerHTML = meta.fields;
  el("actionError").textContent = "";
  el("actionDialog").showModal();
}

async function submitAction(form) {
  if (!pendingAction) return;
  const fd = new FormData(form);
  const body = { action: pendingAction };
  for (const [k, v] of fd.entries()) body[k] = v;
  try {
    el("actionSubmit").disabled = true;
    await apiPost(body);
    el("actionDialog").close();
    toast("Action enregistrée et état mis à jour.");
    await refresh();
  } catch (err) {
    el("actionError").textContent = translateError(err.message);
  } finally {
    el("actionSubmit").disabled = false;
  }
}

function translateError(code) {
  const m = {
    REASON_REQUIRED: "Un motif est obligatoire.",
    SIGNERS_MUST_DIFFER: "Les deux signataires doivent être des personnes distinctes.",
    HUMAN_FIELDS_REQUIRED: "Les deux signataires et la cause racine sont obligatoires.",
    VERIFIER_DISAGREEMENT: "Les vérificateurs divergent. AEGIS-24 est passé en arrêt.",
    VERIFICATION_FAILED: "Un vérificateur a refusé l’action.",
    NODE_NOT_CONNECTED: "Ce nœud n’a pas de heartbeat réel récent.",
    OPERATOR_REQUIRED: "Déverrouillage opérateur requis.",
  };
  return m[code] || code || "Action refusée.";
}

async function saveNodeConfig() {
  if (!selectedNode) return;
  if (!requireOperator()) return;
  const provider = el("nodeProvider").value.trim();
  const endpoint = el("nodeEndpoint").value.trim();
  try {
    await apiPost({ action: "node_config", code: selectedNode.code, provider, endpoint });
    el("nodeDialog").close();
    toast("Configuration du nœud enregistrée.");
    await refresh();
  } catch (err) {
    toast(translateError(err.message), "error");
  }
}

function simSave() {
  sessionStorage.setItem("aegis_sim_events", JSON.stringify(sim.events.slice(-200)));
}

function simLog(source, message) {
  sim.events.unshift({
    id: crypto.randomUUID ? crypto.randomUUID() : String(Date.now() + Math.random()),
    at: new Date().toISOString(),
    source,
    message,
  });
  simSave();
  renderSimEvents();
}

function clearSimTimers() {
  sim.timers.forEach(clearTimeout);
  sim.timers = [];
}

function startScenario(id) {
  const scenario = SCENARIOS.find((s) => s.id === id);
  if (!scenario) return;
  clearSimTimers();
  sim.scenario = scenario;
  sim.running = true;
  sim.paused = false;
  simLog("SIM", "Scénario « " + scenario.title + " » démarré.");
  scheduleScenario(0);
}

function scheduleScenario(startIndex) {
  if (!sim.scenario || !sim.running || sim.paused) return;
  for (let i = startIndex; i < sim.scenario.steps.length; i++) {
    const timer = setTimeout(() => {
      if (!sim.running || sim.paused) return;
      const [source, message] = sim.scenario.steps[i];
      simLog(source, message);
      if (i === sim.scenario.steps.length - 1) {
        sim.running = false;
        simLog("SIM", "Scénario terminé. Aucun changement opérationnel effectué.");
      }
    }, 1000 * (i - startIndex + 1));
    sim.timers.push(timer);
  }
}

function pauseSimulation() {
  if (!sim.running) return;
  clearSimTimers();
  sim.paused = true;
  simLog("SIM", "Simulation mise en pause.");
}

function resumeSimulation() {
  if (!sim.scenario || !sim.paused) return;
  sim.paused = false;
  sim.running = true;
  simLog("SIM", "Simulation reprise.");
  const emittedMessages = new Set(sim.events.map((e) => e.message));
  const next = sim.scenario.steps.findIndex(([, msg]) => !emittedMessages.has(msg));
  if (next >= 0) scheduleScenario(next);
  else sim.running = false;
}

function resetSimulation() {
  clearSimTimers();
  sim.scenario = null;
  sim.running = false;
  sim.paused = false;
  sim.events = [];
  simSave();
  renderSimEvents();
  toast("Journal de simulation réinitialisé.");
}

function renderSimEvents() {
  el("simEvents").innerHTML = sim.events.length
    ? sim.events
        .map(
          (e) =>
            "<div class='event'><time>" +
            escapeHtml(formatTime(e.at)) +
            "</time><span class='source'>" +
            escapeHtml(e.source) +
            "</span><span class='msg'>" +
            escapeHtml(e.message) +
            "</span></div>",
        )
        .join("")
    : "<div class='event'><span class='msg'>Aucun exercice en cours.</span></div>";
}

function switchView(view) {
  document.querySelectorAll(".view").forEach((n) => n.classList.toggle("active", n.id === "view-" + view));
  document.querySelectorAll(".tab").forEach((n) => n.classList.toggle("active", n.dataset.view === view));
}

function exportAudit() {
  if (!live) return;
  const payload = {
    exported_at: new Date().toISOString(),
    app: "AEGIS-24",
    source: API_URL,
    state: live,
  };
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "aegis24-audit-" + new Date().toISOString().replace(/[:.]/g, "-") + ".json";
  a.click();
  URL.revokeObjectURL(url);
}

document.querySelectorAll(".tab").forEach((b) => b.addEventListener("click", () => switchView(b.dataset.view)));
document.querySelectorAll("[data-view-jump]").forEach((b) => b.addEventListener("click", () => switchView(b.dataset.viewJump)));
document.querySelectorAll("[data-action]").forEach((b) => b.addEventListener("click", () => openAction(b.dataset.action)));

el("actionForm").addEventListener("submit", (e) => {
  e.preventDefault();
  submitAction(e.currentTarget);
});

el("operatorBtn").addEventListener("click", () => {
  el("operatorError").textContent = "";
  el("operatorKey").value = operatorKey();
  el("operatorDialog").showModal();
});

el("operatorForm").addEventListener("submit", (e) => {
  e.preventDefault();
  const key = el("operatorKey").value.trim();
  if (key.length < 10) {
    el("operatorError").textContent = "Code trop court.";
    return;
  }
  sessionStorage.setItem("aegis_operator_key", key);
  el("operatorBtn").textContent = "🔓 Opérateur";
  el("operatorDialog").close();
  toast("Code opérateur chargé pour cette session. Il sera vérifié à la prochaine action.");
});

el("saveNodeConfig").addEventListener("click", saveNodeConfig);
el("refreshAudit").addEventListener("click", () => refresh(true));
el("exportAudit").addEventListener("click", exportAudit);
el("simPause").addEventListener("click", pauseSimulation);
el("simResume").addEventListener("click", resumeSimulation);
el("simReset").addEventListener("click", resetSimulation);

if (operatorKey()) el("operatorBtn").textContent = "🔓 Opérateur";

refresh();
refreshTimer = setInterval(refresh, 10000);
window.addEventListener("beforeunload", () => clearInterval(refreshTimer));