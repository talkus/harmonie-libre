# Teshuvah (תְּשׁוּבָה) dans la mémoire de C

> **Teshuvah n'efface pas l'histoire ; elle change la direction à partir de l'histoire.**

En hébreu biblique, le mot veut dire à la fois « retour » et « réponse ». Dans ce cerveau, la teshuvah n'est pas un événement terminal qui affirme que la réparation est accomplie : c'est le **cycle traçable** qui relie l'écart, sa reconnaissance, la correction, le retour et la vérification de la non-récidive. Module : `conscience_c_brain/teshuvah.py`. Tests : `tests/test_teshuvah.py`.

## Invariants

- L'histoire reste immuable : aucun événement, aucune preuve, aucun claim antérieur n'est réécrit.
- L'interprétation active reste corrigeable : seul le statut du claim change, avec sa raison.
- La réparation doit devenir observable : `repair_applied` signifie « réparation déclarée », jamais « réparation vérifiée ».
- Le retour doit pouvoir être vérifié, et **V ≠ auto-déclaration**.
- La mémoire conserve aussi le chemin du retour.

## Le cycle D → R → A → P → C → S → V

| Étape | Méthode | Événement du ledger |
|---|---|---|
| D : dérive détectée | `initiate_teshuvah` | `TESHUVAH_INITIATED` |
| Brisure : étincelles nommées | `name_sparks` | `TESHUVAH_SPARKS_NAMED` |
| R + A : reconnaissance et aveu nommés | `acknowledge_teshuvah` | `TESHUVAH_ACKNOWLEDGED` |
| P : réparation proposée | `propose_teshuvah_repair` | `TESHUVAH_REPAIR_PROPOSED` |
| C : correction appliquée | `apply_teshuvah_repair` | `TESHUVAH_REPAIR_APPLIED` |
| S : garde-fou | `create_safeguard` | `TESHUVAH_SAFEGUARD_CREATED` |
| Retour observé | `observe_return` | `TESHUVAH_RETURN_OBSERVED` |
| V : non-récidive vérifiée | `verify_non_recurrence` | `TESHUVAH_NON_RECURRENCE_VERIFIED` |
| Récidive | `record_teshuvah_recurrence` | `TESHUVAH_RECURRENCE_DETECTED` |
| Cicatrice, archive | `cicatrize_teshuvah`, `archive_teshuvah` | `TESHUVAH_CICATRIZED`, `TESHUVAH_ARCHIVED` |
| Clôture | `close_teshuvah` | `TESHUVAH_CLOSED` |

`teshuvah_trace(id)` rend la teshuvah comme ce qu'elle est : la relation causale entre ces événements immuables.

## Phases

```text
contested → under_repair → repair_applied ─┬─ récidive → under_repair
                                           └─ retour durable → repair_verified → cicatrized → archived
```

## Ce que le code refuse

- appliquer une correction sans reconnaissance ni proposition préalables, ou sans corriger explicitement chaque claim contesté ;
- un retour fondé sur une preuve antérieure à la correction, non observable (`reconstruction_analytique`, `indetermine`) ou émise par S lui-même ;
- une vérification sans garde-fou, fondée sur une preuve antérieure au retour, ou faite par l'acteur qui a reconnu ou appliqué la réparation ;
- une correction qui laisse une étincelle nommée sans la relever ni la laisser explicitement ;
- une clôture tant que reconnaissance, correction, garde-fou, étincelles comptées, retour observé et non-récidive vérifiée ne sont pas tous présents ;
- l'usage d'un claim `contested` ou `under_repair` dans une décision sensible (`usable_claims(sensitive=True)`).

Une récidive renvoie le cycle en réparation, remet l'influence de la dérive à 1 et conserve dans l'historique le retour et la vérification précédents.

## La brisure des vases (שְׁבִירַת הַכֵּלִים)

Dans la Kabbale lourianique, les vases du Tohou se brisent parce que chacun se tient seul ; leurs éclats dispersent des étincelles que le Tikkoun vient relever. Dans la mémoire de C, cela donne deux règles :

- **Un claim brisé n'est pas simplement faux.** `name_sparks()` nomme ses étincelles, ce qui restait vrai en lui (avec les seuls faits sur lesquels il reposait). `apply_teshuvah_repair()` refuse toute correction qui ne rend pas compte de chaque étincelle, exactement une fois : relevée dans le claim de remplacement (`raised_sparks`) ou laissée explicitement avec sa raison (`released_sparks`). Une rétractation n'a pas de vase où relever : ses étincelles sont laissées, nommément. Une récidive les disperse de nouveau, historique conservé, et la clôture exige qu'elles soient de nouveau relevées ou laissées.
- **Les vases qui se tiennent seuls sont fragiles.** `solitary_vessels()` signale les claims actifs reposant sur un appui au plus, partagé avec aucun autre claim actif, et non dits par l'autre (`user_stated`). C'est un signal à examiner, jamais un verdict de fausseté : le claim reste actif.

Le ledger garde les éclats ; `return_memory()` garde les étincelles relevées à côté de ce qui a permis le retour.

## FACT, INTERPRETATION, CURRENT_MODEL

`claim_layers(claim_id)` sépare ce qui s'est passé (preuves et événements cités, jamais modifiés), ce que le système en avait conclu (le claim d'origine et son statut) et ce qu'il comprend maintenant (le claim actif qui le remplace). Une correction peut dire « mon interprétation était trop forte » sans déclarer le fait faux. Chaque claim porte une provenance typée : `user_stated`, `user_inferred` ou `system_hypothesis`.

## Deux mémoires

- `drift_memory()` répond à « qu'est-ce qui nous a fait dériver ? » (type, cause nommée, influence résiduelle, récidives) ;
- `return_memory()` répond à « qu'est-ce qui nous a permis de revenir ? » (ce qui a permis le retour, preuve, leçon, et si le retour a tenu) ;
- `redemption_index()` donne la part des cycles vérifiés durablement : indicateur expérimental, pas une mesure de vertu.

## Limite

La vérification contrôle des conditions structurelles (preuve postérieure, observable, non émise par S, vérificateur distinct de l'acteur). Le logiciel n'authentifie ni l'identité ni l'indépendance du vérificateur : le statut porte `external_authentication: not_performed`, comme pour `verify_repair()`.

## Provenance

- **source attestée** : les deux textes de Mik du 2 octobre 2026 (fil « Teshuvah dans Mémoire C » du projet Waymaker Core Private), le second primant là où ils divergent ; puis son message « בְּשִׁבִירַת הַכֵּלִים » du même jour et son accord pour donner une place à la brisure ;
- **dérivation consolidée** : « Comment implémenter la mémoire pondérée », « Comment intégrer la mémoire des erreurs passées » et « Comment intégrer la mémoire dans l'algorithme » (Google Drive, 19 septembre 2026) : ne jamais effacer, réduire l'influence ; mémoire de dérive et mémoire de retour ; cicatrice ; indice de rédemption ;
- **reconstruction analytique** : les noms de méthodes, les valeurs d'influence par phase (`DRIFT_INFLUENCE`, reprises des facteurs 1,0 / 0,5 / 0,1 / 0,01 de la mémoire pondérée, avec 0,25 ajouté pour `repair_verified`) les contrôles précis de la vérification, la traduction de la brisure en étincelles comptées et le critère des vases isolés.
