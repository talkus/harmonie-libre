# SOL-Action-Requirements 0.1.0 — garde additive des exigences canoniques

Préparation seulement. `migration.sql` crée un schéma neuf et `public.sol_action_requirements_api(p_action text,p_input jsonb default '{}') returns jsonb`. Les anciens modules, wrappers, droits et admissions restent inchangés. Ce garde contrôle son propre parcours ; les API directes historiques restent en dehors de cette protection. Il ne résout pas le sens universel du mandat, qui demeure UNKNOWN.

## Expressions entières reconnues

| Texte exact | Contrat borné |
|---|---|
| `Conserver chaque ligne d’entrée.` | Identifiants et ordre des lignes dans le résultat SQL attendu |
| `Calculer exactement les totaux, sans arrondi intermédiaire.` | Sommes exactes en cents de chaque devise |
| `Séparer les devises et identifier le tableau source.` | Totaux séparés et empreinte de la source |
| `Conserver le tableau source intact.` | Empreinte actuelle égale à la définition immuable conservée |
| `Autoriser uniquement la devise EUR.` | Chaque ligne source possède cette devise ; paramètre de trois lettres A–Z |
| `Interdire les montants négatifs.` | **Chaque ligne** est ≥0, sans compensation par une autre ligne ; −0.00 vaut zéro |
| `Limiter le tableau à 100 lignes.` | Maximum 1..500 ; entier canonique sans zéro initial |
| `Limiter la valeur absolue de chaque montant à 100.00.` | abs(montant) ≤ borne, en cents ; borne canonique 0..999999999999.99 avec exactement deux décimales |

Ces textes utilisent une égalité entière, y compris les accents, apostrophes et points. Les paramètres sont reconnus puis reconstruits exactement. Préfixe/suffixe, nouvelle ligne, négation, approximation, traduction, espace ajouté ou combinaison dans une même chaîne restent UNKNOWN. `Limiter chaque montant à 100.00.` reste UNKNOWN car son sens signé est ambigu. Les placeholders HTML différents des trois DEFAULT_REQUIREMENTS ne sont pas implicitement promus. Toute exigence inconnue ajoutée aux trois défauts bloque l'effet. Un client ne soumet ni verdict ni masque de sélection ni contrat alternatif : le garde relit **toutes** les exigences déjà conservées dans le job et leur mandat/source par un status noyau authentifié.

## Actions et entrées exactes

- `health {}` : version, runtime_hash, périmètre canonique, unknown_blocks_effect et legacy_direct_paths_enforced=false ; pas de listing ni secret.
- `status {job_id,capability}` : état du noyau authentifié, source CSV retirée de la réponse, plus `requirements_guard` calculé maintenant. Réponse historique, current_reuse_authorized=false ; aucun droit de produire ou clore déduit de cette lecture.
- `bind {job_id,capability,production_request_id,release_hash,manifest_hash,source_commit,self_hash,bridge_token}` : **enveloppe Bridge bind existante inchangée**, injectée par le proxy serveur pour les champs de release/token. UUID préparé avant l'appel, capacités/tokens 64 hex, commits 40 hex, UUID canoniques. Le serveur exige une release Bridge admise et une admission nouvelle pour le runtime de cette garde.
- `execute {core_action:'verify'|'complete',core_input:{job_id,capability,request_id,expected_step_id}}` : expected_step_id égal exactement à core_action. Garde actuelle sur source **et résultat conservé** avant le dispatch Bridge existant ; aucune donnée résultat ni verdict client.
- `lookup_receipt {job_id,capability,target_request_id}` : lecture seule de l'UUID original, sans nouveau worker, intention ou calcul d'autorité courante. Nos reçus en premier ; si aucune requête propre n'existe, fallback à la lecture Bridge pour les jobs historiques, résultats worker et réconciliations existantes. Une requête propre sans outcome reste UNKNOWN et n'est pas substituée par un reçu voisin.

Seules ces clés/types sont acceptés. Enveloppes ≤20000 octets. Références absentes/croisées, mauvaise capacité, null, mauvais type, entrée non canonique, admission périmée et erreur inattendue retournent une enveloppe opaque uniforme : `ok:false,status:'REJECTED',error:'NOT_AUTHORIZED_OR_INVALID_REFERENCE',automatic_retry:false,current_reuse_authorized:false`. Elle ne démontre ni existence ni absence d'effet.

## Rapport requirements_guard

Le rapport comprend :

```text
status: PASS | FAIL | UNKNOWN
phase: PRE_EFFECT_ADMISSION | RESULT_VERIFICATION
requirements: [{index:0,text:<original exact>,contract:<code ou null>,parameters:{...},verdict:PASS|FAIL|UNKNOWN,reason:<code>}]
checks: [{name,verdict}]
checked_at, expires_at: UTC serveur, durée 60 secondes
source_sha256, result_sha256, definition_hash, requirements_sha256
guard_runtime_hash, core_runtime_hash, bridge_runtime_hash
claim_scope, semantic_truth:UNKNOWN, general_mandate:UNKNOWN
natural_language_coverage:CANONICAL_WHOLE_TEXT_ONLY
current_reuse_authorized:false, needs_current_revalidation:true
```

Une ligne FAIL impose FAIL au rapport, sinon une ligne UNKNOWN impose UNKNOWN. Les contrôles globaux de runtime, empreinte, définition, intégrité du journal, oracle SQL source et comparaison du résultat sont également obligatoires ; un PASS de ligne ne masque pas un échec global. Aucun PASS n'est hérité d'un reçu ou de l'UI.

PRE_EFFECT_ADMISSION signifie : la source conservée permet les seuls contrats canoniques reconnus. Cette étape n'affirme pas qu'un résultat futur est déjà produit ou satisfait. RESULT_VERIFICATION exige que le résultat SQL persisté soit **exactement égal** à l'oracle SQL indépendant du worker Python, avec ses empreintes et runtime cohérents ; pas de résultat => UNKNOWN. La source non négative est inspectée ligne par ligne par un parseur SQL, sans déduire son signe du total. Le calcul est repris à chaque nouvelle vérification/clôture. La vérité de la source, sa provenance déclarée et les autres exigences naturelles demeurent hors preuve.

## Succès, refus et récupération

Un bind admis retourne le reçu original `BOUND_RELEASE` avec binding_granted=true, binding_and_begin_atomic=true, begin_receipt, plus `request_id=production_request_id`, `requirements_guard`, `requirements_and_begin_atomic:true`, `requirements_release_hash` et `requirements_guard_runtime_hash`. Le garde et le begin Bridge sont dans **la même transaction**. Seul le proxy recevant ce nouveau bind exact avec garde PASS et délai valide peut appeler ensuite le worker une seule fois. Un reçu historique ne redémarre jamais le worker.

Un FAIL/UNKNOWN avant bind conserve un refus durable :

```json
{
  "ok": false, "status": "REJECTED", "action": "produce",
  "job_id": "job exact", "request_id": "UUID original", "production_request_id": "même UUID",
  "error": "REQUIREMENTS_FAIL ou REQUIREMENTS_UNKNOWN",
  "receipt_kind": "REQUIREMENTS_GUARD_REFUSAL", "terminal": true, "durable_refusal": true,
  "effect_scope": "REQUIREMENTS_ADMISSION_BEFORE_BRIDGE_BIND_ONLY",
  "business_effect": "NO_BEGIN_OR_WORKER_STARTED_BY_THIS_CALL",
  "receipt_recording_effect": "APPEND_ONLY_REQUIREMENTS_GUARD_RECEIPT_RECORDED",
  "requirements_guard": {}, "worker_reexecuted": false,
  "automatic_retry": false, "current_reuse_authorized": false
}
```

Aucun champ `effect` SQL rollback n'est ajouté : aucune action Bridge bind n'a été appelée sur ce chemin et l'écriture du refus est un effet réel. Cela ne prétend pas annuler un effet externe ou une tentative composite antérieure. Pour verify/complete bloqués, action conserve verify/complete, effect_scope devient `REQUIREMENTS_VERIFICATION_BEFORE_CORE_DISPATCH_ONLY`, business_effect `NO_CORE_VERIFY_OR_COMPLETE_BY_THIS_CALL` ; production_request_id est null.

Le même UUID/contenu avec outcome connu retourne seulement le reçu historique et deduplicated=true. UUID/contenu divergent refusé. Un autre UUID sur un job possédant déjà une intention bind gardée ne contourne pas son refus ou son ambiguïté : OUTCOME_UNKNOWN avec original_request_id et pending=true ; consulter le reçu original. Une requête propre sans outcome bloque aussi toute nouvelle mutation du job. Une correction explicite exige un nouveau job conservant l'historique ; jamais un replay automatique.

Le lookup propre retourne `ok:true,action:'lookup_receipt',found:true,status:'HISTORICAL_NOT_CURRENT',target_action:'produce'` pour bind, ou verify/complete ; `receipt_status` conserve le statut initial, et `receipt` est le reçu exact passé au helper historique (CSV/capacités/token retirés, flags d'autorité false, needs_current_revalidation=true). Les rapports conservent leur date d'origine et leur expiration, sans nouvel examen. Une intention sans résultat retourne found=false,status=UNKNOWN,intent_found=true. La lecture n'ajoute aucune ligne.

Si Bridge ne confirme pas un bind nouvellement accordé, le garde conserve un OUTCOME_UNKNOWN, jamais un reçu de non-effet. Un nouveau UUID ne le relance pas. Les verify/complete admis retournent le reçu Bridge original plus le rapport courant ; leurs refus SQL existants gardent leur portée existante. Une erreur inattendue est opaque, sans marqueur de refus durable. L'horloge est relue après calcul sous verrous, avant/après dispatch et avant retour ; si la garde expire dans cette transaction, toute la transaction est annulée et aucune réponse d'autorité n'est délivrée.

## Admission, sécurité et limites

Après migration unique et admission de la nouvelle release dans Bridge par l'opérateur autorisé, insertion explicite :

```sql
INSERT INTO sol_action_requirements.admissions(release_hash) VALUES ('RELEASE_HASH_ADMISE');
SELECT public.sol_action_requirements_api('health','{}');
SELECT sol_action_requirements.audit(); -- lecture opérateur SQL seulement
```

Le trigger d'admission exige session_user postgres/supabase_admin ; il fige son runtime et les runtimes noyau/Bridge, ainsi que les métadonnées publiques exactes de release (sans token ni son hash secret). Aucune mutation de release ancienne ; un changement du code crée une nouvelle version à revoir/admettre. Les dépendances connues sont épinglées sur les empreintes existantes. Les empreintes de fonctions ne certifient pas les ACL, tables ou machines.

Ordre exact des verrous : Action job → Bridge UUID → journal global Requirements → verrous internes du Bridge/noyau inchangés. Les quotas sérialisés bornent le stockage à 64 requêtes par job et 2048 globales par jour UTC. Dépassement : REQUIREMENTS_STORAGE_LIMIT/admission_recorded=false, sans reçu durable ni claim de non-effet ; perte de ce refus reste UNKNOWN.

RLS sans politique client, tables/séquences/helpers privés révoqués pour PUBLIC/anon/authenticated/service_role ; seul l'API SECURITY DEFINER et le wrapper SECURITY INVOKER sont exécutables par anon/authenticated, search_path vide partout. UPDATE/DELETE/TRUNCATE bloqués par triggers. Requêtes liées à capacité hachée+job+UUID+payload ; outcomes et événements append-only chaînés UTC. Le propriétaire PostgreSQL reste privilégié, ce registre n'est pas WORM. Les lectures coûteuses commencent après authentification job/capacité.

`tests-dml.sql` sera un harnais synthétique sans DDL/réseau, avec rollback des lignes de fixtures ; des compteurs d'identité peuvent garder des numéros sautés. Une revue statique et des noms de tests ne sont pas des résultats d'exécution. Aucune mutation distante par l'auteur de cette préparation. La reprise réseau, la création gardée et les exigences gardées sont des frontières distinctes ; elles ne confèrent aucune garantie universelle, mémoire native permanente ou évolution des poids de Codex.
