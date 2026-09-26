# Audit des revérifications — 26 septembre 2026 (UTC)

**Base examinée :** `62aa3eeae0340450c773d3e7c1e5561b4b987cfc`.  
**Portée :** admission et consultation des comptes rendus de revérification dans l'API publique de Conscience C. Aucun changement au telos, à l'ordre des capteurs ou à la phénoménalité INDETERMINATE.

## Écart démontré

Le commit de reproduction `1a96ae55f119ebf828592200886f97633264ec0d` n'ajoute que neuf tests. La CI `36213227535`, job `108323955028`, exécute 171 tests : les 162 tests existants passent et les neuf nouveaux échouent.

La fonction `validate_revalidation_item()` acceptait notamment un identifiant d'événement inexistant, un type d'événement substitué, une classe choisie par l'appelant, une référence de source vide ou une provenance composée d'espaces. Un événement documentaire ou même `BOOTSTRAP_T0` pouvait ainsi être présenté comme une tâche de revérification externe.

Elle annonçait `revalidated_with_fresh_evidence` à partir d'un objet fourni par l'appelant, sans consulter la source. Pour `requires_current_canon_check`, elle annonçait une comparaison au canon sans la réaliser. Ces libellés dépassaient les contrôles effectivement exécutés.

[Reproduction CI](https://github.com/talkus/harmonie-libre/actions/runs/36213227535)

## Correction ciblée

La nouvelle entrée recommandée est :

```python
record_revalidation_review(item, review, provenance)
```

Elle vérifie le journal local, la cohérence de ses pointeurs avec l'état, l'existence de l'événement exact et la correspondance de son type et de sa classe calculée. L'appelant ne peut pas imposer une autre classe. La classe `requires_current_canon_check` reste bloquée dans cette API : une comparaison explicite distincte est nécessaire.

Le compte rendu exige `source_ref` et `result`, textes non vides. Les seuls champs facultatifs sont `observed_at` et `notes`, également textuels. Une date déclarée n'est pas vérifiée comme date d'observation. Les champs qui prétendraient injecter une autorisation ou un verdict sont refusés.

Le résultat et le nouvel événement portent :

```text
status = recorded_not_verified
outcome = review_recorded_not_verified
verification_status = not_performed
automatic_replay_allowed = false
```

Les contrôles effectués et non effectués sont séparés. Le code ne consulte pas la source, n'authentifie pas le déclarant, ne prouve pas son indépendance et ne certifie ni la vérité ni la fraîcheur du résultat. Une contradiction déclarée est conservée comme déclaration : elle ne réécrit pas les preuves et n'invalide pas automatiquement les hypothèses.

## Compatibilité et histoire

L'ancienne méthode `validate_revalidation_item()` reste un adaptateur de compatibilité. Son champ historique `status=resolved` est conservé **uniquement pour signifier dépôt enregistré**, avec `legacy_status_semantics=submission_recorded_only`, `recording_status=recorded_not_verified` et `verification_status=not_performed`. Il ne faut jamais l'utiliser comme autorisation ou preuve. Les nouveaux clients doivent employer `record_revalidation_review()`.

Le nom historique d'événement `REVALIDATE_HISTORICAL_EVENT` et le champ `fresh_evidence` sont conservés pour lire l'histoire, sans revendiquer de fraîcheur. Les nouveaux événements portent `recording_version=2` et `record_type=declared_review`. Les anciennes lignes ne sont pas modifiées ; la vue courante les distingue comme `legacy_declaration_not_verified` et indique si leur événement cible existe réellement.

Les revues successives restent reliées par `supersedes_revalidation_event_hash`. La dernière revue n'est pas automatiquement la vérité. La tâche de revérification reste en attente et aucun replay n'est autorisé par le seul dépôt d'un compte rendu.

## Tests et intégration

Neuf tests reproduisent les écarts initiaux. Vingt-trois tests supplémentaires couvrent l'API explicite, la compatibilité, les champs mal formés, la non-injection d'autorité, l'absence de modification des preuves, les comptes rendus contradictoires, les copies détachées, l'historique hérité, la corruption du journal, l'instance périmée et la récupération après interruption.

L'intégration utilise la frontière de commit coordonné déjà présente. Le modèle historique `_state_model.py` et les 162 tests préexistants restent inchangés. Les classes privées de ce modèle ne constituent pas une alternative prise en charge à l'API publique.

```sh
cd conscience-c/brain
python -m unittest discover -s tests -p 'test_revalidation*.py' -v
python -m unittest discover -s tests -v
python ../verify_reprise.py
```

Les résultats complets doivent être lus dans la CI du commit d'intégration ; la présence des tests n'établit pas leur réussite.

## Limites maintenues

Cette passe corrige l'admission des revues et le sens de leur enregistrement. Elle n'implémente pas un service indépendant de vérification. Les mécanismes `verify_repair()` et les autres références de source restent, hors de ce périmètre, des enregistrements de données déclarées ; leurs libellés ne prouvent pas une réparation réelle, une identité authentifiée ou une indépendance du vérificateur.

Les garanties du journal sont locales. Un remplacement coordonné de tous les fichiers nécessite un point d'appui extérieur. L'appelant autorisé peut déposer un compte rendu faux : le système le marque déclaré, il ne prétend pas le détecter comme faux.

La reprise après panne termine seulement le dépôt préparé ; elle ne réexécute pas de vérification externe. Deux appels volontaires identiques restent deux dépôts distincts : ce correctif n'introduit pas d'identifiant de requête dédupliqué.
