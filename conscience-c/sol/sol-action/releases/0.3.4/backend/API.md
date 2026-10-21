# SOL-Creation-Guard 0.1.0 — candidat pour SOL-Action 0.3.4

Source : `migration.sql`. Ce module est additif : aucune définition, permission, admission ou donnée Action/Bridge/Atelier/Preuve existante n'est remplacée. Il ne démarre aucun worker. La migration n'est pas rejouable et n'est pas exécutée par son auteur.

## Interface proxy

RPC `public.sol_action_creation_api(p_action text, p_input jsonb default '{}') → jsonb`.

`create_guarded` reçoit exactement :

```json
{
  "core_input": {
    "job_id": "uuid préparé avant appel", "request_id": "uuid préparé avant appel",
    "capability": "64 caractères hexadécimaux minuscules",
    "mandate": "mandat conservé", "requirements": ["exigence conservée"],
    "source_csv": "id,currency,amount\na,EUR,1.00\n", "source_origin": {"kind": "declared"}
  },
  "release_hash": "64 hex", "manifest_hash": "64 hex", "source_commit": "40 hex",
  "self_hash": "64 hex", "bridge_token": "secret injecté par le serveur"
}
```

Les seuls champs optionnels de `core_input` sont `parent_job_id` et `parent_capability`, ensemble ; le parent doit exister et être autorisé. `source_origin` admet `kind` (`declared` ou `connector-retrieved`) et les champs optionnels `provider`/`reference` (1..512 caractères). Le proxy navigateur conserve sa restriction à `declared` ; ce champ n'authentifie aucune provenance. Mandat 1..10000 caractères non blancs, exigences 1..32 chaînes non blanches de 1..2000, CSV 1..32768 caractères **et** octets UTF-8. Enveloppe ≤200000 octets, entrée noyau ≤180000. UUID de création canoniques, clés inconnues/types incorrects refusés. Le garde ne préjuge pas du CSV : l'oracle SQL existant l'admet ou le refuse.

Le proxy lit la release et le token de son environnement déjà installé ; aucun champ runtime ne vient du navigateur. Une release doit être admise dans Bridge **et** dans la nouvelle table d'admissions. Le token authentifie le détenteur de cette release ; il n'est ni une identité utilisateur ni une attestation machine. Une capacité neuve lie seulement l'intention et son futur reçu avant l'existence d'un job.

`lookup_receipt` reçoit exactement `{"job_id":"uuid","capability":"64 hex","target_request_id":"uuid ORIGINAL"}`. Lecture seule ; pas de nouvel UUID, worker, intention, réconciliation ou relecture de preuve courante. `health` reçoit `{}` et retourne version, empreinte runtime propre, limites et absence de remplacement des modules existants.

## Résultats

Une création réussie retourne le reçu original du noyau : `ok:true, action:"create", status:"RECORDED"`, identifiants exacts et état du job. Cette réponse n'est pas une preuve de production ni d'achèvement du mandat.

Un refus SQL contrôlé **enregistré** retourne `ok:false, status:"REJECTED", action:"create"`, `job_id`, `request_id`, erreur SQL bornée, et ces marqueurs exacts :

```json
{
  "receipt_kind": "CONTROLLED_CREATION_REFUSAL",
  "terminal": true, "durable_refusal": true,
  "effect": "NONE_SQL_TRANSACTION_ROLLED_BACK",
  "effect_scope": "CONTROLLED_CORE_DISPATCH_SUBTRANSACTION_ONLY",
  "core_effect_scope": "THIS_RPC_SQL_TRANSACTION_ONLY",
  "business_effect": "NONE_CORE_ACTION_ROLLED_BACK",
  "receipt_recording_effect": "APPEND_ONLY_CREATION_GUARD_RECEIPT_RECORDED",
  "capability_activated_by_this_call": false,
  "automatic_retry": false, "current_reuse_authorized": false,
  "worker_reexecuted": false
}
```

Le reçu comporte aussi `payload_hash`, `refused_at`, `release_hash` et les trois empreintes runtime (garde/noyau/Bridge). Ces marqueurs sont différents des anciens refus Bridge et ne doivent pas être mélangés dans une condition frontend. L'absence d'effet concerne exclusivement la sous-transaction du dispatch SQL **create**. L'écriture du reçu est un effet réel ; ce reçu n'affirme rien sur une tentative composite externe ou sur une exception réseau.

La récupération trouvée retourne `ok:true, action:"lookup_receipt", status:"HISTORICAL_NOT_CURRENT", found:true, target_action:"create", job_id, target_request_id, receipt_kind, receipt`. Le reçu imbriqué a le même UUID original, les marqueurs historiques ajoutés (`status:"HISTORICAL_NOT_CURRENT"`, `current_reuse_authorized:false`, `needs_current_revalidation:true`, `begin_granted:false`, `automatic_retry:false`) et conserve le verdict initial. Le helper historique existant retire CSV/capacités/token. Le statut original est dans `receipt_status`. Aucune donnée secrète de release n'est retournée.

Une réservation autorisée sans résultat connu retourne `found:false, status:"UNKNOWN", intent_found:true, receipt:null`. Un nouvel UUID sur le même job réservé retourne `OUTCOME_UNKNOWN`, `original_request_id`, `pending:true`, `automatic_retry:false` : consulter le reçu original, sans relancer create. Le même UUID avec un contenu modifié est refusé ; un replay exact avec reçu connu renvoie uniquement ce reçu historique avec `deduplicated:true`.

Sans job autorisé ni réservation exacte liée à la capacité, les références absentes, croisées ou de mauvaise capacité retournent la **même** enveloppe opaque : `ok:false, status:"REJECTED", error:"NOT_AUTHORIZED_OR_INVALID_REFERENCE", current_reuse_authorized:false, automatic_retry:false`. Aucun identifiant, résultat, existence ou absence d'effet n'en est déduit. Un UUID legacy absent n'est pas une preuve de refus.

Le quota retourne `REJECTED/CREATION_ADMISSION_LIMIT`, identifiants, `admission_recorded:false`, sans marqueurs de refus durable ni absence d'effet. Sa réponse perdue reste UNKNOWN. Les entrées malformées, accès invalides, admissions/runtime périmés et erreurs inattendues ont l'enveloppe opaque et n'obtiennent aucun reçu contrôlé. Une réponse noyau non reconnue conserve une réservation + événement UNKNOWN ; elle ne devient jamais un no-effect.

## Installation opérateur et contrôle

Après installation unique, admission de la release Bridge par le parcours opérateur existant puis, dans une transaction explicitement autorisée :

```sql
INSERT INTO sol_creation_guard.admissions(release_hash) VALUES ('RELEASE_HASH_ADMISE');
SELECT public.sol_action_creation_api('health','{}');
SELECT sol_creation_guard.audit(); -- opérateur SQL uniquement
```

Le trigger d'admission exige `session_user` postgres/supabase_admin, vérifie les runtimes actuels, fige leur empreinte et celle des métadonnées publiques exactes de release ; le token et son hash restent exclus. Aucun argument client ne peut admettre un runtime. Une modification de code impose une nouvelle revue et une nouvelle release/admission ; les admissions existantes restent conservées. Les empreintes couvrent les fonctions, pas une attestation des tables/ACL/machine.

Les tables nouvelles admissions/requests/refusals/events sont RLS sans politique client ; accès tables/séquences/helper privés refusé à anon/authenticated/service_role. Seuls API/wrapper sont exécutables par anon/authenticated ; API privée SECURITY DEFINER, wrapper SECURITY INVOKER, tous avec search_path vide. UPDATE/DELETE/TRUNCATE bloqués par triggers. Registre de requêtes/capacités hachées, chaîne d'événements UTC et liens réciproques audités. Le propriétaire PostgreSQL reste privilégié : ce n'est pas WORM.

Ordre de verrous : job Action → UUID Bridge → journal global du garde → verrous du dispatch Action inchangé. Quotas UTC sérialisés : 128 réservations globales/jour et 32 par hash de capacité/jour ; les refus malformés/pré-authentification n'en consomment pas. Les lectures utilisent une photographie transactionnelle : une intention encore non commise peut rester invisible et UNKNOWN ; cela n'autorise aucun replay.

## Tests et limites

`tests-dml.sql` est un harnais synthétique sans DDL ni réseau, pour exécution opérateur après installation. Releases/admissions, jobs, requêtes/refus et événements de test sont annulés par une sous-transaction ; les résultats et le contrôle de nettoyage sont retournés. Les séquences d'identité PostgreSQL peuvent conserver des numéros sautés après rollback ; aucune ligne de fixture ne persiste. Il teste succès, refus avant existence, récupération historique, anti-sonde, collisions, réserve ambiguë, quotas, ACL, triggers et conservation des runtimes. Le fichier est une préparation, pas un résultat de test exécuté.

Les anciennes API restent utilisables et peuvent contourner ce nouveau garde ; les anciens refus non archivés restent UNKNOWN. Un nouveau job/capacité est nécessaire pour corriger une création gardée refusée, avec décision explicite ; un nouvel UUID du même job ne contourne pas l'intention. Aucun replay automatique, retry réseau, worker, satisfaction sémantique générale, mémoire interne permanente ou apprentissage de poids n'est ajouté. Le retrait du parcours proxy peut rendre le garde inactif en conservant son historique ; aucune suppression automatique du registre n'est prévue.
