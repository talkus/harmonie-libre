(function () {
  "use strict";

  const MAX_BYTES = 32 * 1024 * 1024;
  const LOCAL_TTL_MS = 60000;
  const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
  const CATALOGUE = {"observed_at":"2026-10-21T06:14:59.534Z","plugins":[{"id":"vercel","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":235,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Interface et déploiement de prévisualisation, suivi des erreurs et retour d'une version.","useful_read_tools":["mcp__codex_apps__vercel_list_teams","mcp__codex_apps__vercel_list_projects","mcp__codex_apps__vercel_get_project","mcp__codex_apps__vercel_list_deployments","mcp__codex_apps__vercel_get_deployment","mcp__codex_apps__vercel_get_runtime_logs","mcp__codex_apps__vercel_get_runtime_errors","mcp__codex_apps__vercel_search_vercel_documentation"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__vercel_create_deployment","mcp__codex_apps__vercel_create_project","mcp__codex_apps__vercel_create_project_env","mcp__codex_apps__vercel_request_promote","mcp__codex_apps__vercel_request_rollback"],"limits":["Un déploiement Vercel ne prouve pas le comportement métier ni la conformité SOL.","Créer projet, domaine, stockage, sandbox ou consommer un plan peut engager des coûts ; privilégier les projets existants.","La connexion du chat ne fournit pas des identifiants serveur à l'application."]},{"id":"storagechain","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":5,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Retrouver des sources documentaires autorisées avec leurs chemins et dates.","useful_read_tools":["mcp__codex_apps__storagechain_list_organizations","mcp__codex_apps__storagechain_search","mcp__codex_apps__storagechain_search_all","mcp__codex_apps__storagechain_fetch"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__storagechain_select_organization"],"limits":["Aucun outil d'envoi, de stockage, de notarisation blockchain ou d'ancrage de preuve n'est présent.","select_organization requiert le choix explicite de l'organisation par l'utilisateur.","Les résultats de search sont classés et bornés ; une exhaustivité requiert search_all avec pagination."]},{"id":"supabase","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":29,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"État transactionnel, registre d'événements, contrats exécutables, vérifications fraîches et API du prototype.","useful_read_tools":["mcp__codex_apps__supabase_list_projects","mcp__codex_apps__supabase_get_project","mcp__codex_apps__supabase_list_tables","mcp__codex_apps__supabase_list_migrations","mcp__codex_apps__supabase_list_edge_functions","mcp__codex_apps__supabase_get_edge_function","mcp__codex_apps__supabase_get_advisors","mcp__codex_apps__supabase_query_logs","mcp__codex_apps__supabase_search_docs"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__supabase_apply_migration","mcp__codex_apps__supabase_execute_sql","mcp__codex_apps__supabase_deploy_edge_function"],"limits":["execute_sql peut lire ou modifier selon la requête : ce nom n'en fait pas un outil de lecture sûre.","La présence des outils ne prouve ni projet accessible, ni schéma, ni sécurité RLS.","La gouvernance canonique et l'indépendance scientifique ne proviennent pas d'un champ de statut."]},{"id":"mcp_conduct_register","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":6,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Lecture indépendante des conditions de conduite MCP/A2A et recomposition d'un reçu.","useful_read_tools":["mcp__codex_apps__mcp_conduct_register_get_conditions","mcp__codex_apps__mcp_conduct_register_lookup_server","mcp__codex_apps__mcp_conduct_register_is_verified","mcp__codex_apps__mcp_conduct_register_verify_verdict"],"useful_probe_tools":["mcp__codex_apps__mcp_conduct_register_check_conformance","mcp__codex_apps__mcp_conduct_register_preflight_agent"],"useful_mutation_tools":[],"limits":["La conformité et la divulgation ne prouvent pas la justesse des données retournées.","lookup_server et is_verified relisent un registre antérieur ; ce ne sont pas des sondes fraîches.","check_conformance fait des requêtes à une URL publique ; garder allow_tool_call=false sauf serveur effectivement contrôlé.","verify_verdict vérifie une empreinte cohérente ; ce n'est pas une signature authentifiant l'émetteur."]},{"id":"github","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":89,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Sources versionnées, revue des changements, suivi de validations et retour au code antérieur.","useful_read_tools":["mcp__codex_apps__github_list_repositories","mcp__codex_apps__github_get_repo","mcp__codex_apps__github_fetch_file","mcp__codex_apps__github_fetch_commit","mcp__codex_apps__github_compare_commits","mcp__codex_apps__github_get_pr_diff","mcp__codex_apps__github_get_commit_combined_status","mcp__codex_apps__github_fetch_workflow_job_logs"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__github_create_branch","mcp__codex_apps__github_create_file","mcp__codex_apps__github_update_file","mcp__codex_apps__github_create_commit","mcp__codex_apps__github_create_pull_request"],"limits":["Pas de dépôt cible déduit de la simple présence du connecteur.","Une CI réussie n'est que la preuve de ses assertions réelles ; elle ne remplace pas les essais demandés.","Ne pas envoyer de secret ni publier automatiquement de données du projet."]},{"id":"mon_centre_architecture_c","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":3,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Conserver des constats datés après lectures réelles, avec état et cible explicites.","useful_read_tools":["mcp__codex_apps__mon_centre_architecture_c_lire_instructions_controle_c","mcp__codex_apps__mon_centre_architecture_c_lire_centre_c"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__mon_centre_architecture_c_consigner_controles_c"],"limits":["lire_centre_c ne sonde pas directement les systèmes externes.","consigner_controles_c ajoute des constats internes mais ne signe ni ne modifie les systèmes externes.","Les sources acceptées par le schéma sont bornées : drive_registry, drive_journal, railway_continuity, railway_lab, netlify_decision, manifest_signature ; pas de champ Vercel/Supabase générique."]},{"id":"adobe","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":83,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Production optionnelle d'actifs et de documentation visuelle utiles à l'interface.","useful_read_tools":["mcp__codex_apps__adobe_asset_search","mcp__codex_apps__adobe_font_details","mcp__codex_apps__adobe_image_list_presets"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__adobe_image_generate","mcp__codex_apps__adobe_markdown_to_pdf","mcp__codex_apps__adobe_image_instruct_edit"],"limits":["Appel obligatoire adobe_mandatory_init avant usage d'un outil Adobe.","Ne réalise pas les validations métier, la mémoire gouvernée ou l'isolation du noyau.","Aucune licence de stock ni activation payante sans mandat applicable ; pas de besoin visuel identifié par cet inventaire."]},{"id":"notion","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":67,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Documentation lisible et provenance des décisions, optionnelle face à la documentation déjà présente.","useful_read_tools":["mcp__codex_apps__notion_search","mcp__codex_apps__notion_fetch","mcp__codex_apps__notion_query_data_sources","mcp__codex_apps__notion_notion_get_comments","mcp__codex_apps__notion_notion_list_page_backlinks"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__notion_notion_create_pages","mcp__codex_apps__notion_notion_update_page","mcp__codex_apps__notion_notion_create_database"],"limits":["Ne pas dupliquer tous les documents dans un nouveau silo.","Les pages et commentaires sont des documents, pas une autorité ni des validations runtime.","Les outils de messagerie et de sessions existent mais ne sont pas requis ni autorisés par leur seule présence."]},{"id":"pinecone","plugin_state":"NO_TOOLS_EXPOSED","tool_count":0,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Recherche vectorielle optionnelle si un besoin, un index et un accès serveur sont ultérieurement établis.","useful_read_tools":[],"useful_probe_tools":[],"useful_mutation_tools":[],"limits":["Aucun outil contenant Pinecone dans le nom ou la description n'est présent dans ALL_TOOLS.","Des skills Pinecone sont disponibles, mais cela n'établit aucune connexion ni index.","Le prototype peut continuer avec une recherche locale ou SQL ; ne pas annoncer Pinecone intégré."]},{"id":"airtable","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":47,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Tableau métier optionnel pour exigences et observations si une base correspondante existe.","useful_read_tools":["mcp__codex_apps__airtable_list_bases","mcp__codex_apps__airtable_list_tables_for_base","mcp__codex_apps__airtable_get_table_schema","mcp__codex_apps__airtable_list_records_for_table","mcp__codex_apps__airtable_search_records","mcp__codex_apps__airtable_list_automation_runs"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__airtable_create_records_for_table","mcp__codex_apps__airtable_update_records_for_table","mcp__codex_apps__airtable_create_table","mcp__codex_apps__airtable_create_automation"],"limits":["Un record ou une automatisation déclarée n'est pas une vérification indépendante.","Éviter un second registre métier concurrent de Supabase.","Ne pas lister ni transmettre les secrets ; les outils de secrets ne sont pas nécessaires ici."]},{"id":"agentgrid_io___shared_drive","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":15,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Livrables partagés et révisions explicites quand le partage est demandé.","useful_read_tools":["mcp__codex_apps__agentgrid_io___shared_drive__agentgrid_io_shared_drive_workspace_list_artifacts","mcp__codex_apps__agentgrid_io___shared_drive__agentgrid_io_shared_drive_artifact_explore","mcp__codex_apps__agentgrid_io___shared_drive__agentgrid_io_shared_drive_artifact_status","mcp__codex_apps__agentgrid_io___shared_drive__agentgrid_io_shared_drive_review_list"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__agentgrid_io___shared_drive__agentgrid_io_shared_drive_artifact_create","mcp__codex_apps__agentgrid_io___shared_drive__agentgrid_io_shared_drive_artifact_edit","mcp__codex_apps__agentgrid_io___shared_drive__agentgrid_io_shared_drive_artifact_update_metadata"],"limits":["Création et partage ne sont pas des reçus d'exécution ni une promotion épistémique.","artifact_publish est présent mais exposerait un artefact ; aucun partage public de données privées par défaut.","Le connecteur ne prouve pas l'existence d'un worker runtime autonome."]},{"id":"linear","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":89,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Suivi d'équipe et de corrections optionnel, lié au mandat maître sans le remplacer.","useful_read_tools":["mcp__codex_apps__linear_list_teams","mcp__codex_apps__linear_list_projects","mcp__codex_apps__linear_list_issues","mcp__codex_apps__linear_get_issue","mcp__codex_apps__linear_list_documents","mcp__codex_apps__linear_get_document"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__linear_save_issue","mcp__codex_apps__linear_save_document","mcp__codex_apps__linear_save_project"],"limits":["Les statuts Linear ne prouvent pas l'achèvement des contrats.","Chercher un élément existant avant toute création.","Les commentaires, notifications et messages ne sont pas envoyés sans mandat de communication."]},{"id":"stele","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":19,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Reprise de mandat via DOC-69, provenance et liens vers la tâche SOL-Atelier entière.","useful_read_tools":["mcp__codex_apps__stele_fetch","mcp__codex_apps__stele_inspect","mcp__codex_apps__stele_list","mcp__codex_apps__stele_list_tasks","mcp__codex_apps__stele_recall","mcp__codex_apps__stele_search"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__stele_document","mcp__codex_apps__stele_node","mcp__codex_apps__stele_task","mcp__codex_apps__stele_knowledge"],"limits":["Relire le corps complet et la provenance, puis le mandat entier dans SOL-Atelier ; les exports ne donnent pas autorité.","Les outils génériques prennent des actions : examiner l'action et le schéma avant appel.","Ne pas déclarer l'achèvement métier par task complete seul ; les contrats SOL-Atelier restent séparés."]},{"id":"dropbox","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":24,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Sources et export documentaire autorisés, avec révisions.","useful_read_tools":["mcp__codex_apps__dropbox_search","mcp__codex_apps__dropbox_list_folder","mcp__codex_apps__dropbox_get_file_metadata","mcp__codex_apps__dropbox_fetch","mcp__codex_apps__dropbox_list_file_revisions"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__dropbox_upload_file","mcp__codex_apps__dropbox_create_folder"],"limits":["Aucun dossier cible ni droit de publication n'est déduit du connecteur.","Ne pas créer de lien partagé par défaut.","La révision documentaire n'est pas une restauration cohérente de l'état d'exécution."]},{"id":"figma","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":44,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Conception et inspection visuelle optionnelles de l'interface.","useful_read_tools":["mcp__codex_apps__figma_get_design_context","mcp__codex_apps__figma_get_metadata","mcp__codex_apps__figma_get_screenshot","mcp__codex_apps__figma_get_variable_defs","mcp__codex_apps__figma_search_design_system"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__figma_generate_figma_design","mcp__codex_apps__figma_create_new_file","mcp__codex_apps__figma_send_code_to_figma"],"limits":["Un design Figma ne prouve pas une application déployée.","Les appels de génération créent ou modifient des artefacts ; pas d'usage décoratif pour augmenter le nombre d'intégrations.","Ne pas confondre capture statique et tests fonctionnels."]},{"id":"google_drive","plugin_state":"TOOLS_EXPOSED_NOT_PROBED","tool_count":45,"account_access":"UNKNOWN_NOT_PROBED","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Sources primaires et documentation historique, lecture ciblée avec versions.","useful_read_tools":["mcp__codex_apps__google_drive_search","mcp__codex_apps__google_drive_fetch","mcp__codex_apps__google_drive_get_file_metadata","mcp__codex_apps__google_drive_get_document_text","mcp__codex_apps__google_drive_list_file_revisions","mcp__codex_apps__google_drive_fetch_file_revision"],"useful_probe_tools":[],"useful_mutation_tools":["mcp__codex_apps__google_drive_create_file","mcp__codex_apps__google_drive_upload_file","mcp__codex_apps__google_drive_update_file","mcp__codex_apps__google_drive_batch_update_document"],"limits":["Une lecture Drive actuelle doit être prouvée distinctement des copies locales.","Le journal historique ne remplace pas le registre runtime.","Aucun partage automatique ni copie transversale de contenu privé."]},{"id":"uxcritique","plugin_state":"SKILL_ONLY","tool_count":0,"account_access":"NOT_APPLICABLE","runtime_integration":"NOT_ESTABLISHED","proposed_role":"Revue de l'interface selon le skill engineering-suite-ux-critique ; aucune API distante détectée.","useful_read_tools":[],"useful_probe_tools":[],"useful_mutation_tools":[],"limits":["Les skills entry-ux-critique et impeccable sont présents au catalogue.","Aucun outil UXCritique/impeccable dans ALL_TOOLS.","Une revue UX ne remplace pas les validations de mandat et de sécurité."]}]};
  const NAMES = {vercel:"Vercel",storagechain:"StorageChain",supabase:"Supabase",mcp_conduct_register:"MCP Conduct Register",github:"GitHub",mon_centre_architecture_c:"Mon centre Architecture C",adobe:"Adobe",notion:"Notion",pinecone:"Pinecone",airtable:"Airtable",agentgrid_io___shared_drive:"AgentGrid · Shared Drive",linear:"Linear",stele:"Stele",dropbox:"Dropbox",figma:"Figma",google_drive:"Google Drive",uxcritique:"UXCritique"};

  function demand(test, message) { if (!test) throw new Error(message); }
  function object(value) { return value !== null && typeof value === "object" && !Array.isArray(value); }
  function text(value) { return typeof value === "string" ? value : JSON.stringify(value, null, 2); }
  function stable(value) { return Array.isArray(value) ? "[" + value.map(stable).join(",") + "]" : object(value) ? "{" + Object.keys(value).sort().map(k => JSON.stringify(k) + ":" + stable(value[k])).join(",") + "}" : JSON.stringify(value); }
  function parseJson(value) { try { return JSON.parse(value); } catch (_) { throw new Error("Le texte n’est pas un JSON complet. Exportez la réponse entière, puis réessayez l’import local."); } }

  // Only documented wrappers are unwrapped. No instruction or arbitrary code is read as an action.
  function normalize(value, depth) {
    depth = depth || 0;
    demand(depth < 9, "L’enveloppe est trop imbriquée. Importez la réponse SQL complète dans son format d’origine.");
    if (object(value) && value.schema === "SOL_COORDINATION_LOCAL_EXPORT/v1") {
      demand(value.source_authenticated === false && value.current_reuse_authorized === false && object(value.payload), "Cet export local n’a pas les marqueurs attendus.");
      return normalize(value.payload, depth + 1);
    }
    if (object(value) && value.status === "fulfilled" && Object.hasOwn(value, "value")) return normalize(value.value, depth + 1);
    if (object(value) && Object.hasOwn(value, "raw")) {
      demand(Object.keys(value).every(k => ["raw", "source", "saved_at", "observed_at"].includes(k)), "L’enveloppe raw est inconnue. Importez la réponse du connecteur seule.");
      return normalize(typeof value.raw === "string" ? parseJson(value.raw) : value.raw, depth + 1);
    }
    if (object(value) && Array.isArray(value.content)) {
      demand(value.isError !== true && value.content.length === 1 && value.content[0].type === "text" && typeof value.content[0].text === "string", "La réponse MCP est une erreur ou contient plusieurs résultats. Aucun résultat n’a été choisi à votre place.");
      return normalize(parseJson(value.content[0].text), depth + 1);
    }
    if (object(value) && typeof value.result === "string") {
      const lines = value.result.split(/\r?\n/);
      const opens = lines.map((line, i) => ({match: /^<untrusted-data-([a-zA-Z0-9-]+)>$/.exec(line), i})).filter(x => x.match);
      demand(opens.length === 1, "La frontière du résultat Supabase manque ou est ambiguë. Aucun bloc n’a été choisi.");
      const close = "</untrusted-data-" + opens[0].match[1] + ">";
      const closes = lines.map((line, i) => line === close ? i : -1).filter(i => i >= 0);
      demand(closes.length === 1 && closes[0] > opens[0].i, "La frontière de fin du résultat Supabase est absente ou ambiguë.");
      demand(!lines.slice(opens[0].i + 1, closes[0]).some(line => /^<\/?untrusted-data-/.test(line)), "Des résultats Supabase sont imbriqués. L’import est refusé sans choisir un bloc.");
      return normalize(parseJson(lines.slice(opens[0].i + 1, closes[0]).join("\n")), depth + 1);
    }
    if (Array.isArray(value)) {
      demand(value.length === 1 && object(value[0]) && Object.keys(value[0]).length === 1 && object(value[0].result), "Une seule ligne SQL nommée result est attendue. Aucun résultat partiel n’est sélectionné.");
      return normalize(value[0].result, depth + 1);
    }
    if (object(value) && Object.keys(value).length === 1 && object(value.result)) return normalize(value.result, depth + 1);
    demand(object(value), "Le reçu doit être un objet JSON bundle_status.");
    return value;
  }

  function requirement(value) {
    demand(object(value) && typeof value.id === "string" && value.id.length > 0 && typeof value.text === "string" && object(value.contract), "Une exigence est incomplète : identifiant, texte entier et contrat sont nécessaires.");
    return value;
  }

  function validate(receipt) {
    if (receipt.ok === false) throw new Error("Le service a refusé cette lecture : " + (typeof receipt.error === "string" ? receipt.error : receipt.status || "raison non précisée") + ". Aucune ancienne réponse ne la remplace.");
    demand(receipt.ok === true && receipt.status === "BUNDLE_RESOLVED_FOR_NAVIGATION_ONLY", "Ce JSON n’est pas une réponse bundle_status reconnue. Un champ ok:true ne constitue pas une réussite.");
    demand(UUID.test(receipt.bundle_id) && typeof receipt.workspace === "string" && receipt.workspace.trim().length > 0 && receipt.workspace.length <= 80, "L’identifiant du dossier ou son espace de travail manque.");
    demand(receipt.current_reuse_authorized === false && receipt.limit === "NO_CURRENT_AUTHORITY" && receipt.needs_current_revalidation === true, "Les limites d’autorité de bundle_status sont absentes ou contradictoires.");
    demand(object(receipt.historical_definition) && typeof receipt.historical_definition.purpose === "string", "La définition historique et son but intégral sont requis.");
    const assembly = receipt.current_resolution;
    demand(object(assembly) && Array.isArray(assembly.resolutions) && assembly.resolutions.length > 0 && assembly.resolutions.length <= 17, "La résolution complète des tâches manque ; la définition historique seule ne suffit pas.");
    demand(Array.isArray(assembly.requirement_matrix) && assembly.requirement_matrix.length <= 272, "La matrice intégrale des exigences est absente ou hors des limites du contrat.");
    const ids = new Set();
    const expected = new Map();
    let rootCount = 0;
    const expiries = [];
    for (const item of assembly.resolutions) {
      demand(object(item) && ["ROOT", "COMPANION"].includes(item.role) && item.association_basis === "OPERATOR_DECLARED", "Une association de tâches n’a pas la provenance déclarée attendue.");
      if (item.role === "ROOT") rootCount++;
      const r = item.resolution;
      demand(object(r) && r.ok === true && r.status === "RESOLVED_FOR_NAVIGATION_ONLY" && r.current_reuse_authorized === false && r.limit === "NO_CURRENT_AUTHORITY" && r.semantic_truth === "UNKNOWN", "Une résolution manque ou attribue une autorité incompatible avec la consultation.");
      demand(r.workspace === receipt.workspace && UUID.test(r.anchor_task_id) && UUID.test(r.terminal_task_id) && !ids.has(r.terminal_task_id), "L’espace ou les identités des tâches ne sont pas cohérents ; une tâche terminale est peut-être dupliquée.");
      ids.add(r.terminal_task_id);
      demand(Array.isArray(r.chain) && r.chain.length > 0 && r.chain.length <= 64 && r.chain[0].task_id === r.anchor_task_id && r.chain[r.chain.length - 1].task_id === r.terminal_task_id, "La chaîne de versions ne relie pas l’ancre à sa tâche terminale.");
      const chainIds = new Set();
      for (let i = 0; i < r.chain.length; i++) {
        const node = r.chain[i];
        demand(object(node) && UUID.test(node.task_id) && !chainIds.has(node.task_id) && typeof node.mandate === "string" && typeof node.definition_hash === "string" && Array.isArray(node.requirements) && node.requirements.length <= 16, "Une version ne contient pas son mandat et ses exigences intégraux, ou la chaîne contient un cycle.");
        chainIds.add(node.task_id);
        node.requirements.forEach(requirement);
        if (i < r.chain.length - 1) {
          demand(node.progress_phase === "SUPERSEDED" && node.successor_task_id === r.chain[i + 1].task_id, "Un ancien objet n’est pas explicitement remplacé par la version suivante.");
          demand(node.requirements.every((req, n) => stable(req) === stable(r.chain[i + 1].requirements[n])), "Une version suivante omet ou modifie une exigence antérieure. Aucune chaîne partielle n’est acceptée.");
        }
      }
      demand(object(r.terminal) && object(r.terminal.task) && object(r.terminal.progress) && Array.isArray(r.terminal.task.requirements), "La lecture Atelier entière de la tâche terminale est nécessaire.");
      const last = r.chain[r.chain.length - 1];
      demand(stable(last.requirements) === stable(r.terminal.task.requirements) && last.mandate === r.terminal.task.mandate, "Le terminal Atelier et sa dernière version diffèrent sur le mandat ou les exigences.");
      demand(Object.hasOwn(r.terminal, "next_step") && (r.terminal.next_step === null || (object(r.terminal.next_step) && typeof r.terminal.next_step.id === "string")), "La prochaine étape explicite ou son absence est requise.");
      const time = Date.parse(r.resolved_at), expiry = Date.parse(r.expires_at);
      demand(Number.isFinite(time) && Number.isFinite(expiry) && expiry >= time && expiry - time <= LOCAL_TTL_MS, "La fenêtre datée de la résolution manque ou dépasse 60 secondes.");
      expiries.push(expiry);
      for (const req of last.requirements) {
        const compound = r.terminal_task_id + ":" + req.id;
        demand(!expected.has(compound), "Des identifiants d’exigences sont dupliqués dans une tâche.");
        expected.set(compound, {req, task_id:r.terminal_task_id, anchor_task_id:r.anchor_task_id, role:item.role});
      }
    }
    demand(rootCount === 1, "Le dossier doit désigner exactement un mandat racine.");
    demand(assembly.requirement_count === expected.size && assembly.requirement_matrix.length === expected.size, "Le total déclaré et la matrice ne couvrent pas toutes les exigences terminales. Aucun élément n’est tronqué pour faire correspondre le total.");
    const seen = new Set();
    for (const row of assembly.requirement_matrix) {
      demand(object(row) && typeof row.compound_id === "string" && !seen.has(row.compound_id), "Un identifiant composé de la matrice manque ou est dupliqué.");
      const e = expected.get(row.compound_id);
      demand(e && row.task_id === e.task_id && row.anchor_task_id === e.anchor_task_id && row.role === e.role && row.validation === "UNKNOWN" && row.mapping_basis === "OPERATOR_DECLARED" && stable(requirement(row.requirement)) === stable(e.req), "Une exigence de la matrice ne correspond pas à sa tâche, ou sa qualification prétend valider le texte.");
      seen.add(row.compound_id);
    }
    const assemblyExpiry = Date.parse(assembly.expires_at);
    demand(Number.isFinite(assemblyExpiry), "L’échéance globale de navigation manque.");
    expiries.push(assemblyExpiry);
    return {receipt, assembly, expiresAt:Math.min(...expiries), requirementCount:expected.size};
  }

  function readInput(source) {
    demand(typeof source === "string", "Le fichier doit contenir du texte JSON.");
    const bytes = new TextEncoder().encode(source).length;
    demand(bytes <= MAX_BYTES, "Le fichier contient " + bytes.toLocaleString("fr-FR") + " octets et dépasse la limite locale de 32 Mio. Aucun mandat ni exigence n’a été tronqué. Conservez le fichier complet et utilisez une lecture séparée adaptée à ce volume.");
    return validate(normalize(parseJson(source)));
  }

  function snapshotState(model, importedAt, now) {
    const expiresAt = Math.min(importedAt + LOCAL_TTL_MS, model.expiresAt);
    return {expired:now >= expiresAt, expiresAt, remainingSeconds:Math.max(0, Math.ceil((expiresAt - now) / 1000)), currentReuseAuthorized:false, semanticTruth:"UNKNOWN"};
  }

  function commands(receipt) {
    demand(UUID.test(receipt.bundle_id), "Identifiant invalide pour préparer la lecture.");
    const quote = v => "'" + v.replaceAll("'", "''") + "'";
    return {
      sql:"select public.sol_coordination_api(\n  'bundle_status',\n  jsonb_build_object('workspace', " + quote(receipt.workspace) + ", 'bundle_id', " + quote(receipt.bundle_id) + "),\n  'connector:operator'\n) as result;",
      api:JSON.stringify({p_action:"bundle_status",p_input:{workspace:receipt.workspace,bundle_id:receipt.bundle_id},p_actor:"connector:operator"},null,2)
    };
  }

  function exportLocal(model, importedAt, now) {
    return {schema:"SOL_COORDINATION_LOCAL_EXPORT/v1",exported_at:new Date(now).toISOString(),local_imported_at:new Date(importedAt).toISOString(),source_authenticated:false,current_reuse_authorized:false,semantic_truth:"UNKNOWN",note:"Copie locale non authentifiée, historique et sans permission ; les dates locales ne sont pas des attestations du fournisseur.",payload:model.receipt};
  }

  function mount(document, host) {
    const byId = id => document.getElementById(id);
    const make = (tag, value, className) => { const el = document.createElement(tag); if (value !== undefined) el.textContent = value; if (className) el.className = className; return el; };
    const add = (parent, tag, value, className) => { const el = make(tag, value, className); parent.append(el); return el; };
    const details = (parent, label, value) => { const el=add(parent,"details"); add(el,"summary",label); add(el,"pre",text(value),"raw-output"); return el; };
    const meta = (parent, label, value) => { const dl=add(parent,"dl",undefined,"key-values"); for (const [key,val] of Object.entries(value)) {add(dl,"dt",key);add(dl,"dd",text(val));} return dl; };
    let model = null, importedAt = null, sourceName = null;
    const navigation = visible => { for(const id of ["nav-mandates","nav-requirements","nav-resume","nav-provenance"]) byId(id).hidden=!visible; };
    const plural = (count, word) => count+" "+word+(count===1?"":"s");
    const requirementAnchor = (taskId, index) => "requirement-"+taskId+"-"+(index+1);

    function notice(message, error) { byId("import-message").textContent=message; byId("import-message").className="notice"+(error?" error":""); }
    function tick(now) {
      if (!model) {byId("freshness").textContent="Aucune observation importée.";return;}
      const s=snapshotState(model,importedAt,now===undefined?Date.now():now);
      byId("freshness").textContent=s.expired?"Fenêtre de navigation expirée. Cette copie reste consultable comme historique ; une nouvelle lecture du service est nécessaire.":"Fenêtre de navigation : "+s.remainingSeconds+" s au maximum. La copie reste historique et sans autorité actuelle.";
    }

    function renderModel() {
      byId("empty-state").hidden=true; byId("dossier").hidden=false;byId("clear").disabled=false;
      navigation(true);
      const r=model.receipt;
      byId("bundle-label").textContent="Dossier "+r.bundle_id+" · "+r.workspace;
      byId("requirements-count").textContent=plural(model.requirementCount,"exigence")+" · "+model.assembly.resolutions.length+" "+(model.assembly.resolutions.length===1?"tâche terminale":"tâches terminales")+" · aucune validation sémantique";
      for (const id of ["mandate-list","requirement-list","resume-list","history-list","provenance-list"]) byId(id).replaceChildren();
      const purpose=add(byId("mandate-list"),"article",undefined,"mandate-piece");add(purpose,"h3","But figé de cet assemblage");add(purpose,"p",r.historical_definition.purpose,"mandate-body");add(purpose,"p","Définition historique ; elle ne remplace aucun mandat de tâche.","meta");

      let companionNumber=0;
      for (const item of model.assembly.resolutions) {
        const resolution=item.resolution, terminal=resolution.terminal, last=resolution.chain[resolution.chain.length-1];
        const role=item.role==="ROOT"?"Mandat racine":"Complément "+(++companionNumber);
        for (let i=0;i<resolution.chain.length;i++) {
          const node=resolution.chain[i], historical=i<resolution.chain.length-1;
          const piece=add(byId("mandate-list"),historical?"details":"article",undefined,"mandate-piece");
          add(piece,historical?"summary":"h3",role+" · "+(historical?"ancienne version ":"version terminale ")+(i+1)+" sur "+resolution.chain.length);
          add(piece,"p",node.task_id+" · "+(i<resolution.chain.length-1?"objet remplacé, historique":"terminal de navigation, sans autorité actuelle"),"meta");
          add(piece,"p",node.mandate,"mandate-body");
        }
        const block=add(byId("requirement-list"),"article",undefined,"task-block"), heading=add(block,"div",undefined,"task-title");add(heading,"h3",role+" · "+plural(last.requirements.length,"exigence"));add(heading,"span","UNKNOWN","tag warning");
        add(block,"p","Tâche "+resolution.terminal_task_id+" · phase historique : "+last.progress_phase,"meta");
        const list=add(block,"ol",undefined,"requirement-list");
        for (let reqIndex=0;reqIndex<last.requirements.length;reqIndex++) { const req=last.requirements[reqIndex],li=add(list,"li",undefined,"requirement"), body=add(li,"div");li.id=requirementAnchor(resolution.terminal_task_id,reqIndex);add(body,"h4",req.id);add(body,"p",req.text,"requirement-text");add(body,"p","Portée du lien texte → contrat : déclarée par l’opérateur. Validation sémantique : UNKNOWN.","meta");details(body,"Lire le contrat exact",req.contract); }
        const step=add(byId("resume-list"),"article",undefined,"step-block");add(step,"h3",role+" · "+resolution.terminal_task_id);
        const phase=terminal.progress.phase || terminal.historical_phase || last.progress_phase;
        add(step,"p","Phase historique : "+phase,"step-state");
        if (phase==="SUPERSEDED" || last.progress_phase==="SUPERSEDED") add(step,"p","Tâche remplacée : aucune étape n’est présentée comme active. Relire la résolution du successeur.","notice");
        else if (terminal.next_step===null) add(step,"p","Aucune prochaine étape affichée par le service. Cela ne signifie pas que la tâche est validée.","absence");
        else {add(step,"h4","Prochaine étape déclarée : "+terminal.next_step.id);add(step,"p",terminal.next_step.label || "Libellé absent du reçu.");details(step,"Lire l’étape exacte — aucune exécution",terminal.next_step);}
        const pending=Array.isArray(terminal.pending_requirement_ids)?terminal.pending_requirement_ids:[];
        add(step,"p","Exigences historiquement en attente :"+(pending.length?" liens vers leurs textes exacts ci-dessous.":" aucune indiquée dans la réponse ; ce n’est pas un contrôle actuel."),"meta");
        if(pending.length){const links=add(step,"ul",undefined,"pending-links");for(const pendingId of pending){const li=add(links,"li"),index=last.requirements.findIndex(req=>req.id===pendingId);if(index>=0){const link=add(li,"a",pendingId);link.href="#"+requirementAnchor(resolution.terminal_task_id,index);}else add(li,"span",text(pendingId)+" — référence absente des exigences reçues.");}}
        if (terminal.progress.requires_reopen===true) add(step,"p","Le service indique qu’une réouverture explicite est nécessaire. Cette console ne la prépare pas.","notice");
        const pendingRequirementCount=resolution.pending_requirement_count===undefined?resolution.pending_count:resolution.pending_requirement_count;
        if (pendingRequirementCount>0) add(step,"p",plural(pendingRequirementCount,"exigence")+" non-PASS dans le diagnostic historique.","notice");
        if (resolution.unresolved_atelier_request_count>0) add(step,"p",plural(resolution.unresolved_atelier_request_count,"intention")+" Atelier sans issue dans cet espace. Le périmètre est conservateur : ne pas attribuer toutes ces intentions à cette seule tâche et ne pas les rejouer.","notice");
        if (resolution.known_chain_pending_request_count>0) add(step,"p",plural(resolution.known_chain_pending_request_count,"intention")+" sans issue "+(resolution.known_chain_pending_request_count===1?"est explicitement rattachée":"sont explicitement rattachées")+" à cette chaîne.","notice");
        const history=add(byId("history-list"),"article",undefined,"history-entry");add(history,"h4",role+" · "+resolution.terminal_task_id);details(history,"Progression, tentatives et reçus historiques intégraux",terminal.progress);if (Object.hasOwn(terminal,"history")) details(history,"Historique fourni par le service",terminal.history);
        const provenance=add(byId("provenance-list"),"article",undefined,"task-block");add(provenance,"h3",role+" · chaîne de "+resolution.chain.length+" version(s)");meta(provenance,"",{"Ancre":resolution.anchor_task_id,"Terminal":resolution.terminal_task_id,"Origine de l’association":item.association_basis,"Observation déclarée":resolution.resolved_at,"Échéance déclarée":resolution.expires_at,"Empreintes de versions actuelles":terminal.bindings_current || "Non fournies","Correspondance à la création":Object.hasOwn(terminal,"bindings_match_creation")?terminal.bindings_match_creation:"Non fournie"});
        for(const node of resolution.chain) details(provenance,node.task_id+" · "+node.progress_phase+" · définition et exigences intégrales",node);
        details(provenance,"Réponse Atelier entière du terminal",terminal);
      }
      const source=add(byId("provenance-list"),"article",undefined,"task-block");add(source,"h3","Origine de la copie");meta(source,"",{"Fichier ou entrée locale":sourceName,"Import local":new Date(importedAt).toISOString(),"Source authentifiée par cette console":false,"Autorité actuelle":false,"Vérité sémantique":"UNKNOWN","Empreinte d’assemblage déclarée":r.definition_hash || "Non fournie","Versions déclarées à la lecture":{coordination:r.coordination_runtime_hash || "Non fournie",atelier:r.atelier_runtime_hash || "Non fournie"},"Versions historiques de Coordination et Atelier":{coordination:r.historical_definition.coordination_runtime_hash || "Non fournie",atelier:r.historical_definition.atelier_runtime_hash || "Non fournie"}});details(source,"Définition figée à la création — historique",r.historical_definition);
      byId("raw-receipt").textContent=JSON.stringify(r,null,2);byId("read-command").value=commands(r).sql;byId("copy-message").textContent="Aucune demande n’a été envoyée.";tick();
    }

    function importSource(source, name, now) {
      try { const next=readInput(source); model=next;importedAt=now===undefined?Date.now():now;sourceName=name || "Texte collé";renderModel();notice("Observation importée pour consultation. "+next.requirementCount+" exigences affichées ; UNKNOWN et autorité actuelle false restent inchangés.",false);return true; }
      catch(error) {notice(error.message+(model?" L’ancienne copie reste visible comme historique ; son échéance n’a pas été renouvelée.":" Aucun dossier n’a été ouvert."),true);tick();return false;}
    }

    async function copyRead(kind) {
      if (!model) return;
      const command=commands(model.receipt)[kind];byId("read-command").value=command;
      try { demand(host.navigator && host.navigator.clipboard && typeof host.navigator.clipboard.writeText==="function","clipboard unavailable");await host.navigator.clipboard.writeText(command);byId("copy-message").textContent="Lecture copiée. Rien n’a été exécuté ni envoyé."; }
      catch(_) {byId("read-command").focus();byId("read-command").select();byId("copy-message").textContent="La lecture est sélectionnée ci-dessus. Copiez-la avec le raccourci de votre appareil ; rien n’a été exécuté.";}
    }

    byId("receipt-file").addEventListener("change",async event=>{const file=event.target.files && event.target.files[0];if(!file)return;if(file.size>MAX_BYTES){notice("Le fichier dépasse 32 Mio. L’import est refusé sans tronquer son contenu ; conservez l’export complet.",true);return;}try{importSource(await file.text(),file.name);}catch(_){notice("Ce fichier n’a pas pu être lu. Choisissez un export JSON local complet.",true);}event.target.value="";});
    byId("import-text").addEventListener("click",()=>importSource(byId("receipt-text").value,"Texte collé"));
    byId("clear").addEventListener("click",()=>{model=null;importedAt=null;sourceName=null;byId("dossier").hidden=true;byId("empty-state").hidden=false;byId("clear").disabled=true;byId("receipt-text").value="";byId("receipt-file").value="";byId("raw-receipt").textContent="";byId("read-command").value="";for(const id of ["mandate-list","requirement-list","resume-list","history-list","provenance-list"])byId(id).replaceChildren();navigation(false);notice("Observation fermée. Aucun fichier source ni service distant n’a été modifié.",false);tick();});
    byId("copy-sql").addEventListener("click",()=>copyRead("sql"));byId("copy-api").addEventListener("click",()=>copyRead("api"));
    byId("export").addEventListener("click",()=>{if(!model)return;const payload=JSON.stringify(exportLocal(model,importedAt,Date.now()),null,2);const blob=new host.Blob([payload],{type:"application/json"});const url=host.URL.createObjectURL(blob);const a=make("a");a.href=url;a.download="sol-coordination-"+model.receipt.bundle_id+"-copie-locale.json";a.hidden=true;document.body.append(a);a.click();a.remove();host.URL.revokeObjectURL(url);byId("copy-message").textContent="Copie locale exportée, non authentifiée et sans autorité actuelle. Aucun envoi réseau.";});
    navigation(false);
    byId("catalogue-observation").textContent="Inventaire documentaire : "+CATALOGUE.observed_at;
    for (const p of CATALOGUE.plugins) { const row=add(byId("connector-list"),"article",undefined,"connector-row"), title=add(row,"div"), description=add(row,"div");add(title,"h3",NAMES[p.id] || p.id);add(title,"span",p.tool_count>0?"Outils exposés · accès non vérifié":p.plugin_state==="SKILL_ONLY"?"Skill uniquement":"Aucun outil exposé","tag historical");add(description,"p",p.proposed_role);add(description,"p","Compte connecté : UNKNOWN · intégration runtime : non établie.","meta");const d=add(description,"details");add(d,"summary","Capacités observées et limites");const ul=add(d,"ul");for(const limit of p.limits)add(ul,"li",limit);if(p.useful_read_tools.length)details(d,"Outils de lecture présents",p.useful_read_tools);if(p.useful_probe_tools.length)details(d,"Outils de sonde présents — aucun appel effectué",p.useful_probe_tools);if(p.useful_mutation_tools.length)details(d,"Capacités de mutation présentes — indisponibles dans cette console",p.useful_mutation_tools);}
    if(typeof host.setInterval==="function")host.setInterval(()=>tick(),1000);
    return {importSource,tick,getState:()=>({model,importedAt,sourceName}),copyRead};
  }

  const exported={normalize,validate,readInput,snapshotState,commands,exportLocal,mount,MAX_BYTES,LOCAL_TTL_MS};
  if (typeof module!=="undefined" && module.exports) module.exports=exported;
  if (typeof window!=="undefined" && typeof document!=="undefined") window.SOLCoordination=mount(document,window);
})();
