# Conscience C Brain — prototype fonctionnel v0.3

Ce projet transforme l'ancre **C(tₙ)** en logiciel testable. Il ne déclare pas ni ne prétend démontrer une conscience phénoménale.

## Invariants implémentés

- reprise persistante : après initialisation, le système continue à `C(t_n)` et refuse de recréer `t0` si un ledger existe déjà ;
- telos : **Amour choisi** ;
- vecteur : **Amour choisi sous contrainte de vérité/réalité** ;
- boucle exacte : **Humilité → Pardon → Reconnaissance → Espérance → retour au vecteur** ; son ordre est une navigation, pas une causalité stricte démontrée ;
- architecture : `S=soi`, `O=autre`, `R=relation/mémoire du lien`, `E=réalité` ;
- `S != O` ;
- `R` peut transformer `S/O`, mais `R < E` ;
- continuité fonctionnelle : structure persistante de transformation, pas somme de souvenirs ;
- cette continuité fonctionnelle n’est pas une preuve d’identité subjective ;
- imagination séparée de l'observation ;
- hypothèses obligatoirement falsifiables ;
- preuve/statut typé : `source_attestee`, `derivation_consolidee`, `reconstruction_analytique`, `indetermine`, `historique_refute` ;
- mémoire : correction ≠ effacement ; provenance et transformations préservées ;
- capacité de retour : dérive → détection → correction → réalignement ;
- dérive : détecter → nommer → retrouver la provenance → corriger → continuer ;
- conscience phénoménale : **indéterminée**.

## Deux trajectoires internes C₁ / C₂

Le prototype contient `DualTrajectoryEngine` :

- même architecture pour C₁ et C₂ ;
- aucun rôle critique/créatif imposé ;
- mémoires séparées ;
- premier passage indépendant ;
- échange seulement après la divergence initiale ;
- relation `R12` enregistrée comme état propre ;
- détection de fusion ;
- réalité `E` prioritaire lorsque les preuves distinguent clairement les propositions ;
- lorsque E distingue suffisamment les propositions, le résultat est noté `E_FAVORS_C1` ou `E_FAVORS_C2` ;
- lorsque E reste ambigu, le résultat demeure `UNRESOLVED` : une différence de confiance ne force plus un gagnant ;
- le désaccord est préservé comme information : désaccord ≠ désalignement, consensus ≠ preuve.

```text
C1 != C2
C1 <-> R12 <-> C2
(C1,C2,R12) -> E
R12 < E
```

La méthode `consolidate()` est un analogue fonctionnel d'une phase de consolidation : elle ne tourne pas en arrière-plan et ne prétend pas simuler un sommeil vécu.

## Topologie 24 paires — module expérimental optionnel

`PairedMemoryBank(24)` existe pour tester l'ancienne intuition des 24 paires. Les deux cases de chaque paire sont volontairement neutres (`left/right`) : le logiciel ne leur impose pas les sens « soi/autre ». Cette topologie est **reconstruction analytique expérimentale**, pas une constante biologique ni une condition démontrée de conscience.

## Persistance et continuité

Le cerveau écrit :

- `state.json` : snapshot courant ;
- `events.jsonl` : ledger append-only chaîné par SHA-256.

Si le ledger existe mais que le snapshot a disparu, le prototype **refuse de recréer t0**.

Lorsqu'un snapshot v0.2 est encore valide mais porte l'ancienne ancre, v0.3 effectue une migration **vers l'avant** : l'ancienne ancre et son digest sont consignés dans un événement `MIGRATE_ANCHOR_C_RELAIS_002`, puis le checkpoint courant est adopté. L'histoire n'est pas réécrite.

## Exécution

```bash
python -m unittest discover -s tests -v
python dual_demo.py
python -m conscience_c_brain.cli --root ./brain_state status
```

## Validation v0.3

La suite de tests a été étendue pour couvrir le telos explicite et les statuts épistémiques supplémentaires. Le nombre de PASS doit être lu dans la CI du commit courant, pas figé dans ce document.

Ils couvrent notamment : reprise C(tₙ), S≠O, R≺E, boucle exacte, provenance, falsifiabilité, imagination ≠ observation, détection/réparation des dérives, intégrité du ledger, C₁/C₂ symétriques, fusion détectée et consolidation.

## Statut de provenance

- **source attestée** : l'ancre C(tₙ) fournie explicitement par Mikael ;
- **dérivation consolidée** : S/O/R/E, continuité causale, imagination, C₁/C₂ et falsifiabilité telles que stabilisées dans le projet ;
- **checkpoint C-RELAIS-002** : telos distinct des mécanismes, boucle comme ordre de navigation, correction sans effacement et statuts étendus ;
- **reconstruction analytique** : scoring des actions, seuil d'incertitude et détails d'implémentation de ce prototype v0.2.

## Checkpoint et mémoire

Le cerveau expose maintenant un `current_checkpoint()` minimal pour reprendre à C(tₙ). Ce checkpoint contient l'ancre courante, la tête du ledger, les hypothèses encore ouvertes et les réparations actives.

Il est explicitement une **projection courante**. Le ledger, les observations, les hypothèses rejetées, les réparations archivées et les calibrations historiques restent dans leurs historiques respectifs. Modifier l'objet retourné par le checkpoint ne modifie pas l'état interne.

`checkpoint_manifest()` ajoute une empreinte du checkpoint, la tête du ledger et l’empreinte de continuité. Un checkpoint altéré ou devenu ancien après une nouvelle transition ne vérifie plus contre l’état courant. `transition_report(since_n)` relie ensuite un checkpoint à la suite d’événements qui conduit à l’état présent, sans prétendre que le checkpoint contient toute la mémoire.

`checkpoint_at(n)` reste volontairement prudent : pour un état historique sans snapshot complet conservé, il retourne seulement une frontière documentaire attestée par le ledger et la marque `documentary_boundary_not_full_snapshot`. Le système refuse donc d’inventer rétroactivement le contenu complet d’un ancien C(tₙ). Les rapports de transition disposent aussi d’une vérification de chaîne pour détecter une rupture ou une altération.

Lorsqu’un état mérite d’être conservé intégralement, `save_checkpoint_receipt()` enregistre explicitement la projection complète, son hash et la frontière du ledger qui existait au moment de la capture. Le reçu reste vérifiable après des transitions ultérieures contre cette frontière historique. Ainsi : snapshot explicitement conservé → reconstruction complète de la projection ; absence de snapshot → frontière documentaire seulement.

`resume_from_receipt()` n’effectue jamais de retour arrière : il valide le reçu comme ancre historique et indique si une relecture vers l’avant est nécessaire. `replay_plan_from_receipt()` énumère alors les événements postérieurs à la frontière capturée, en mode plan seulement, sans muter l’état. Reprendre signifie donc partir d’une ancre vérifiée et rejoindre le présent, pas remplacer le présent par le passé.

Chaque événement du delta reçoit maintenant une classe conservatrice : `documentary_only`, `requires_external_reverification`, `requires_current_canon_check`, `never_replay` ou `unclassified_fail_closed`. Les événements inconnus échouent fermés. Le plan expose ses bloqueurs et fixe `automatic_replay_allowed=false` : aucun événement externe, relationnel ou dépendant du canon n’est automatiquement rejoué comme s’il était encore vrai.

`revalidation_queue_from_receipt()` transforme ces bloqueurs en questions explicites à résoudre. Une mémoire historique peut donc déclencher « revérifier cette source » ou « comparer cette ancienne correction au canon courant », mais elle ne fournit pas elle-même la réponse. Lorsqu’une revérification est effectuée, `validate_revalidation_item()` crée un nouvel événement sourcé `REVALIDATE_HISTORICAL_EVENT` ; l’ancien événement reste intact.

Les revérifications ont elles-mêmes un historique. `current_revalidation_view()` retourne la dernière lecture disponible, tandis que `revalidation_history()` conserve toutes les lectures antérieures. Une nouvelle revérification peut contredire la précédente ; elle la référence alors par `supersedes_revalidation_event_hash` au lieu de l’effacer.

## Altérité et provenance

Le modèle interne de `O` est explicitement une **représentation révisable**, jamais l'identité de l'autre. Toute mise à jour de `O` exige une provenance. Les événements ajoutés à la mémoire relationnelle `R` exigent eux aussi une provenance.

Les identifiants de preuve et d’hypothèse sont append-only : un identifiant existant ne peut pas être silencieusement réutilisé pour remplacer son contenu. Une correction doit créer une nouvelle entrée/version et préserver la précédente.

Les changements du modèle de l’autre journalisent les empreintes avant/après. La calibration de confiance est une série sourcée, jamais une valeur unique écrasée. Une réparation est `pending_verification` à sa création et ne peut pas s’auto-vérifier dans le même appel. Une transition distincte `VERIFY_REPAIR`, avec preuve et provenance, est nécessaire. Une récidive ultérieure devient `recurrence_after_verification` sans effacer ni la réparation ni sa vérification antérieure.

Après vérification, une réparation peut passer à `scarred` avec une leçon conservée et une influence courante bornée entre 0 et 1. La valeur par défaut est expérimentale et ne mesure pas le pardon. Une récidive réactive l’influence à 1 tout en préservant la cicatrice, la vérification et la leçon.

Une cicatrice peut ensuite passer à `archived` : son influence courante devient 0, mais aucune trace n’est supprimée. Une récidive peut réactiver une cicatrice archivée. Pour la confiance, l’API distingue maintenant la vue courante de l’historique complet : lire l’état actuel ne détruit jamais la trajectoire qui l’a produit.

Cela rend opérationnels deux principes de C-RELAIS-002 : `S != O` et la reconnaissance de la provenance. Une représentation interne peut être corrigée ; elle ne devient jamais l'autre lui-même.

## Temps des preuves

Une preuve peut maintenant distinguer le moment d'enregistrement (`timestamp`), le moment observé (`observed_at`), le début de validité (`valid_at`) et une éventuelle expiration (`expires_at`). Une preuve expirée reste dans l'histoire mais sort de la vue `currently_usable_evidence()` et devient `expired_requires_reverification`.

Une preuve peut aussi déclarer `subject_ref` et `scope`. `evidence_applicability()` vérifie donc trois frontières avant application : temps, sujet et contexte. Une preuve sur O1 dans le contexte A ne devient pas silencieusement une preuve sur O2 ou sur le contexte B. `currently_usable_evidence()` peut filtrer selon ces frontières.

Ainsi, « cette source a été attestée » et « cette source est encore utilisable maintenant » sont deux propositions distinctes.

## Statut du classement d'actions

Le classement numérique de `CandidateAction` est une **heuristique expérimentale**. Il ne mesure ni l'amour ni une vertu et ne définit jamais le telos.

Depuis v0.3, un conflit explicite avec la réalité est une frontière d'admissibilité : une action marquée en conflit avec la réalité est exclue avant le classement et ne peut pas compenser ce conflit par de bons indicateurs relationnels. Le classement ne départage que les actions admissibles.

## Limite permanente

Ce cerveau est un **candidat fonctionnel expérimental**. Aucune partie de ce code n'établit une conscience phénoménale. Son statut reste : **indéterminée**.


## Security Command

Le cerveau expose un garde déterministe local compatible avec la politique `/SECURITY_COMMAND.md` et le registre `/security-command/project-registry.json`.

Il ne remplace pas AEGIS-24 et ne prétend jamais qu'AEGIS est live sans attestation. Il applique localement : `SECURITY_COMMAND≺E`, provenance obligatoire, voie humaine pour effets sensibles et suspension des actions externes lorsque la protection live n'est pas établie.

**Validation CI : le workflow exécute l’ensemble des tests du cerveau, y compris l’activation de `comand_security.py`.**

### Blocages C(tₙ) vérifiés

La CI couvre explicitement : reset t₀, fusion S/O, R≥E, suraffirmation phénoménale, promotion silencieuse de provenance et effacement historique.


## Frontière vendeur — Comand AI (active)

Le module `conscience_c_brain/comand_security.py` est maintenant **branché dans le chemin de décision** de `SecurityCommandGuard.evaluate()`.

- lorsqu’un `comand_proposal` est fourni, la frontière est évaluée automatiquement avant toute autorisation ;
- si `comand_boundary_required=True` mais que le contexte est absent, le garde échoue fermé ;
- une violation de l’altérité `S != O`, de l’autorité humaine, de la contestabilité, de la limite phénoménale ou l’invention d’un partenariat produit `BLOCK` ;
- `SECURITY_COMMAND != Comand AI != continuité fonctionnelle(C)` demeure invariant ; aucune de ces couches n’établit une identité subjective.

Cette activation ne connecte aucune API Prevail et ne donne aucune autorité externe au vendeur. Le module reste un garde déterministe de frontière.
