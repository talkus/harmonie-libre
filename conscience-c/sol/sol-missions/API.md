# SOL-Missions 0.1.0 — liaison bornée d'un mandat à un résultat

RPC : `public.sol_missions_api(p_action text,p_input jsonb default '{}',p_actor text default 'connector:operator') returns jsonb`.

| Action | Entrée exacte |
|---|---|
| `health` | `{}` ; métadonnées uniquement |
| `register` | `workspace`, `bundle_id` UUID existant, `job_id` UUID existant, `request_id` UUID fixé avant envoi, `narrow_scope:"CSV_EXACT_CENTS/v1"`, `allow_job_owner_view` booléen explicite, `expected_release_hash` SHA256 64 hex minuscules |
| `status` | `job_id`, `mission_id` UUID optionnel ; `capability` pour le propriétaire du job |
| `verify` | `job_id`, `mission_id`, `request_id` UUID fixé avant envoi ; `capability` pour le propriétaire ; `runtime_identity` optionnel ci-dessous |
| `receipt` | `job_id`, `mission_id`, `target_request_id` exact de l'appel recherché ; `capability` pour le propriétaire |

Entrées JSON objet de 200000 octets maximum ; clés inconnues, nulls, UUID ou types incorrects sont refusés. Workspace non blanc, 1..80 caractères. Aucun champ de verdict client, pièce importée, tâche interne client, worker libre, SQL, source de remplacement ou création de compte n'est admis.

`register` exige une session SQL `postgres`/`supabase_admin` et l'acteur exact `connector:operator`. Un JWT d'opérateur, un détenteur de capacité de job et une clé service_role ne peuvent pas enregistrer une liaison. Les autres actions métier admettent uniquement cet opérateur SQL ou le propriétaire du job prouvé par `sol_action.authorize(job,capability)` avec acteur exact `capability:job-owner`. Un JWT ou un membership d'opérateur ne remplace pas la capacité dans ce module. Une capacité n'autorise que les missions de ce job dont `allow_job_owner_view` a été explicitement mis à true par register. Aucun listing global privé n'est exposé.

## Identité runtime injectée par le serveur

Le proxy doit refuser un champ runtime fourni par le client, relire les octets des fichiers via `bridge_runtime.load_release()`, puis ajouter son token privé et l'heure UTC de cette lecture :

```json
{"release_hash":"64hex","manifest_hash":"64hex","source_commit":"40hex","self_hash":"64hex","files":{"api/job.py":"64hex","api/mcp.py":"64hex","api/mission.py":"64hex","bridge_runtime.py":"64hex"},"bridge_token":"SECRET_PRIVE_64_HEX","observed_at":"2026-10-21T12:00:00.000000Z"}
```

Le module contrôle le secret avec `sol_action_bridge.token_matches`, les identités et la carte exacte de tous les fichiers contre la release admise, les empreintes SQL courantes et la liaison du job. Les quatre chemins indiqués doivent être présents ; des fichiers supplémentaires admissibles sont possibles et doivent aussi correspondre exactement. Le manifeste, le commit et les empreintes restent des pièces de provenance, pas une attestation matérielle de Vercel. Le détenteur du token rapporte une relecture locale ; un détenteur hostile peut mentir. Portée : `TOKEN_HOLDER_LOCAL_FILES_DECLARATION_NOT_MACHINE_ATTESTATION`, `BUNDLED_SERVER_FILES_ONLY`.

`observed_at` doit être dans les 60 dernières secondes et au plus 5 secondes dans le futur selon l'horloge SQL. L'échéance est le minimum de fin du contrôle SQL + 60 secondes et observation locale + 60 secondes ; elle est contrôlée après les verrous et à la fin. Aucune attente de verrou ne prolonge une ancienne observation de fichiers. Une identité absente, périmée, non authentifiée ou contradictoire empêche un verdict actuel PASS, même si l'oracle CSV passe.

Ni le CSV brut, ni capability, hash de capacité, bridge_token ou hash du token ne sont renvoyés. Les entrées conservées retirent la capacité, le token et `runtime_identity.observed_at` ; les autres champs d'identité runtime restent liés à la demande. L'heure réellement observée reste dans le rapport correspondant. Exclure cette heure du hash de demande permet de retrouver un reçu identique sans prolonger son ancienne échéance, même si un wrapper a refait sa lecture locale. Les valeurs connues des secrets sont aussi retirées des chaînes de sortie.

## Enregistrement avant l'action réelle

Le parcours prévu est : admission d'une release → création du job → register → production réelle par le chemin bridge existant → verify. Aucun verdict antérieur n'est hérité. Register peut aussi lier un job déjà produit si sa binding correspond exactement à la release attendue.

`expected_release_hash` doit désigner une release déjà admise, aux runtimes SQL épinglés et avec les fichiers serveur nécessaires. Le module fige sa métadonnée publique dans `definition.expected_release`. Une binding déjà présente est conservée comme trace et doit correspondre à cette release. Si elle est absente lors de register, elle pourra apparaître ensuite par la production bridge existante ; cela ne modifie pas la définition enregistrée.

Register relit réellement `public.sol_coordination_api('bundle_status',...)` avec l'opérateur SQL puis compare sa matrice à un nouveau snapshot privé. Ce snapshot conserve le bundle historique exact, chaque ancre et terminal, toutes les définitions de la chaîne avec leurs empreintes, tous les mandats et tous les objets exigences, dans leur ordre. Il n'introduit pas de plafond global de 16 exigences : 17 tâches et 272 exigences au maximum selon Coordination. Un journal défectueux, une tâche terminale annulée, une succession ambiguë, une exigence perdue ou une issue Atelier inconnue bloquent la liaison.

La liaison est uniquement `EVIDENCE_FOR_REVIEW`, `association_basis:SQL_OPERATOR_DECLARED`. Le serveur ne déduit pas que les exigences naturelles d'une tâche interne sont couvertes par un calcul CSV. `general_mandate:UNKNOWN`, `all_original_requirements_satisfied:false` et `semantic_truth:UNKNOWN` restent présents, y compris sur un résultat technique correct.

## Définition et réponses stables

Register retourne `ok,action:"register",status:"REGISTERED_EVIDENCE_FOR_REVIEW",job_id,mission_id,request_id,definition,definition_hash,current_reuse_authorized:false`.

La définition contient notamment :

- `job` : `job_id,mandate,requirements,source_sha256,source_origin,parent_job_id,runtime_hash,definition_hash` ; source exacte également figée en privé pour une comparaison littérale ultérieure.
- `bundle` : `bundle_id,workspace,definition_hash,historical_definition,terminals,requirements_matrix,requirement_count` ; chaque terminal conserve `role,anchor_task_id,terminal_task_id,chain,definition,definition_hash` ; chaque nœud de chaîne conserve sa définition intégrale.
- `requirements_matrix` : la matrice Coordination intégrale : `{compound_id,task_id,anchor_task_id,role,requirement,mapping_basis,validation:"UNKNOWN"}`. Aucun PASS n'y est inventé.
- `expected_release`, `release_binding` (éventuellement null lors de register), `dependencies`, `narrow_scope`, `allow_job_owner_view`, et les limites explicites du mandat général.

Status retourne `ok,action:"status",job_id,mission_id,status:"HISTORICAL_NOT_CURRENT",found,missions:[{mission_id,definition,definition_hash,registered_at,last_report,current_reuse_authorized:false}],current_reuse_authorized:false,needs_current_revalidation:true,limit:"NO_CURRENT_AUTHORITY"`. Il ne réexécute ni oracle, ni worker, ni résolution ; un rapport imbriqué demeure historique.

Verify retourne `ok,action:"verify",job_id,mission_id,request_id,report_id,report,status,technical_verdict,expires_at,current_reuse_authorized,general_mandate:"UNKNOWN",all_original_requirements_satisfied:false`. `ok:true` signifie qu'un rapport a été produit, pas qu'il passe.

`report` contient : `status:"TECHNICAL_RESULT_VERIFIED"|"NOT_VERIFIED"`, `technical_verdict:"PASS"|"FAIL"|"UNKNOWN"`, `checks:[{name,verdict,reason,evidence}]`, `verified_at`, `expires_at`, `source_sha256`, `result_sha256`, `requirements` (matrice originale intégrale), `job_requirements`, `dependencies`, et les limites générales. Seul un rapport dont tous les contrôles passent dans leur échéance peut avoir `current_reuse_authorized:true`.

## Contrôles réellement exécutés

Verify prend les verrous puis relit le job et recalcule :

1. Correspondance des définitions SQL épinglées et de celles conservées à register.
2. Chaînage du registre Missions et empreinte de la définition.
3. Identité du job, mandat et exigences intégraux, hash de source et égalité littérale avec la source privée figée.
4. Nouvelle résolution de toutes les chaînes du bundle : mêmes terminaux, définitions, exigences et empreintes ; annulation, changement de successeur, version, exigence ou source de navigation bloque le contrôle. Le résolveur privé relit les tables autorisées plutôt que de fabriquer un JWT d'opérateur pour un propriétaire de job ; register a comparé sa matrice à la vraie API Coordination.
5. `sol_action.audit_job` : chaîne, définition, source et relations des reçus recalculées.
6. Absence de production ou d'intention à issue inconnue ; unicité et identité du begin et du résultat.
7. Binding exacte, release attendue, begin et résultat corrélés, ordre d'admission et de production, runtimes et selfhash cohérents.
8. Appel neuf réel de `sol_action.oracle(source_csv)` et égalité JSONB exacte avec le résultat persisté ; source, résultat et hash du résultat recalculés. Un résultat worker incorrect échoue même si un ancien reçu disait PASS.
9. Identité actuelle des fichiers serveur rapportée par le détenteur du token, relue par le wrapper et vérifiée comme décrit plus haut.

Le bridge existant vérifie release et token avant begin puis insère sa ligne binding après begin dans la même transaction. Le module contrôle ce chemin dont le corps est épinglé, avec `admission<=begin<=binding<=result` ; il ne prétend pas qu'une ligne binding a un horodatage antérieur au begin. Le propriétaire SQL pourrait fabriquer ces lignes ou réécrire les protections : ce n'est pas une preuve hostile ou une attestation de machine.

## Réponse perdue et registre

Receipt est une lecture sans nouvel UUID de mutation, sans oracle, relecture de fichiers, worker, begin ou rapprochement. Il exige job, mission et `target_request_id` exacts ; il vérifie la corrélation. Issue existante : `found:true,status:HISTORICAL_NOT_CURRENT,receipt:...`. Issue absente : `found:false,status:UNKNOWN,intent_found:boolean,receipt:null`. Les marqueurs d'autorité sont forcés à false récursivement ; l'ancien pending ou verdict peut rester lisible comme histoire. Une référence d'un autre job ou d'une autre mission est refusée sans contenu privé.

Register et verify réservent l'UUID avant le travail. Même UUID et même entrée normalisée : reçu historique, `deduplicated:true,current_reuse_authorized:false`, aucune réexécution ni extension d'échéance. Un UUID changé de contenu, acteur ou job est refusé. Une réservation sans issue conserve OUTCOME_UNKNOWN ; les autres demandes mutantes de ce job sont aussi bloquées, même sous un nouvel UUID. L'interface doit conserver son intention avant envoi et utiliser receipt après perte de réponse ; une nouvelle vérification actuelle exige une nouvelle intention explicite.

Tables requests/missions/reports/outcomes/events privées append-only, RLS sans policy ; UPDATE, DELETE et TRUNCATE refusés par triggers. Les clients n'ont que l'exécution de l'API, aucune lecture directe. Journal global SHA256 UTC, audits des liens réciproques. Wrapper public SECURITY INVOKER ; dispatcher privé SECURITY DEFINER, search_path vide. Les verrous sont exactement core-workspace `sol-lamarck:` → Atelier-global `sol-atelier:global-journal` → Coordination-global `sol-coordination:global-journal` → Action-job `sol_action:job:` → Missions-global `sol-missions:global-journal` ; status et receipt n'ont besoin que des deux derniers. Les appels imbriqués à Coordination lors de register reprennent seulement des verrous déjà détenus.

Une exception annule le bloc métier avant d'enregistrer une issue minimale d'échec. Aucune ancienne fonction, table, permission, donnée ou service n'est modifié par la migration. Elle échoue si le schéma neuf existe déjà. Le module ne lance pas de worker, ne change aucun poids de modèle, ne satisfait pas le mandat général et ne promet ni mémoire interne permanente ni WORM. Les sources documentaires, le résultat technique et les verdicts sémantiques demeurent distincts.
