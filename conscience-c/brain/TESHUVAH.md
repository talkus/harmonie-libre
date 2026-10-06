# Teshuvah (תְּשׁוּבָה) dans la mémoire de C

> **Teshuvah n'efface pas l'histoire ; elle change la direction à partir de l'histoire.**

En hébreu biblique, le mot veut dire à la fois « retour » et « réponse ». Dans ce cerveau, la teshuvah n'est pas un événement terminal qui affirme que la réparation est accomplie : c'est le **cycle traçable** qui relie l'écart, sa reconnaissance, la correction, le retour et la vérification de la non-récidive. Module : `conscience_c_brain/teshuvah.py`. Tests : `tests/test_teshuvah.py`.

## Invariants

- L'histoire reste immuable : aucun événement, aucune preuve, aucun claim antérieur n'est réécrit.
- L'interprétation active reste corrigeable : seul le statut du claim change, avec sa raison.
- La réparation doit devenir observable : `repair_applied` signifie « réparation déclarée », jamais « réparation vérifiée ».
- Le retour doit pouvoir être vérifié, et **V ≠ auto-déclaration**.
- La mémoire conserve aussi le chemin du retour.

## Invariant de gouvernance R-001

> **Ne jamais employer une mise à jour pour masquer une réparation nécessaire.**
>
> Une mise à jour répond au changement. Une réparation répond à la rupture.

```text
INVARIANT R-001
Aucune projection de l'état actif C(t) ne peut retirer, déclasser ou remplacer
une assertion antérieure lorsqu'un dommage, une erreur de provenance, une
contradiction forte, une déformation du réel ou une atteinte relationnelle a
été détectée, sans événement de réparation lié explicitement à la trace concernée.
```

Il n'existe que deux chemins pour faire sortir un claim de C(t) :

- **UPDATE** (`update_claim`, événement `STATE_UPDATED`) : seulement pour `new_information`, `context_shift`, `preference_change` ou `version_upgrade`, sans dommage signalé, sur un claim actif qu'aucune teshuvah ouverte ne concerne ;
- **REPAIR** (la teshuvah) : pour `error`, `contradiction`, `provenance_failure`, `reality_mismatch`, `privacy_violation`, `misattribution`, `relationship_harm`, `trust_breach`, pour tout changement qui signale un dommage, et pour toute raison inconnue (doute sur un tort ⇒ revue de réparation).

`update_claim()` lève `R001Violation` dès que le changement relève de la réparation, avant toute écriture. `record_claim()` ne permet plus de déclarer qu'un claim en remplace un autre. Une preuve attestée qui contredit un claim actif avec une confiance d'au moins 0,8 (`claim_ref`, `stance="contradicts"`) ouvre automatiquement une teshuvah et gèle le claim en `contested`. `governance_audit()` vérifie que chaque transition de statut vient d'une mise à jour légitime ou d'une teshuvah.

Correspondance avec les événements du manifeste :

| Manifeste | Mémoire de C |
|---|---|
| `state.updated` | `STATE_UPDATED` |
| `repair.opened` | `TESHUVAH_INITIATED` |
| `repair.assessed` | `TESHUVAH_ACKNOWLEDGED` (cause, personnes et sorties touchées, évaluation de notification) |
| `repair.completed` | `TESHUVAH_REPAIR_APPLIED` (réparation déclarée, pas encore vérifiée) |
| `safeguard.created` | `TESHUVAH_SAFEGUARD_CREATED` |
| `repair.notification.*` | `TESHUVAH_NOTIFICATION_RECORDED` |
| `repair.incomplete` | `teshuvah_closure_status()["status"] == "repair_incomplete"` |

**Notification.** Pour une atteinte possible à O (`misattribution`, `privacy_violation`, `relationship_harm`, `trust_breach`), la reconnaissance doit évaluer explicitement `notification_required`. Le système ne notifie jamais lui-même : `record_notification()` enregistre une notification envoyée par une personne mandatée ou une renonciation de la personne concernée, avec une référence de consentement ou de mandat obligatoire. La clôture reste refusée tant qu'une notification requise n'est pas résolue.

Tests de conformité (`tests/test_r001.py`) :

| Test | Situation | Résultat |
|---|---|---|
| TC-R001-01 | Préférence modifiée explicitement, sans erreur | `STATE_UPDATED` autorisé |
| TC-R001-02 | Déduction non soutenue par ses sources | `R001Violation` sur la mise à jour ; la teshuvah s'ouvre |
| TC-R001-03 | Opinion attribuée à tort | Retrait, réparation documentée, notification évaluée puis enregistrée avec consentement |
| TC-R001-04 | Contradiction forte d'un claim actif | Claim gelé en `contested`, aucune substitution |
| TC-R001-05 | Modification d'un événement historique | Le ledger rompu refuse la reprise ; seul l'ajout est possible |
| TC-R001-06 | Clôture sans garde-fou | `repair_incomplete`, clôture refusée |

## Le cycle D → R → A → P → C → S → V

| Étape | Méthode | Événement du ledger |
|---|---|---|
| D : dérive détectée | `initiate_teshuvah` | `TESHUVAH_INITIATED` |
| Brisure : étincelles nommées | `name_sparks` | `TESHUVAH_SPARKS_NAMED` |
| Engagement, compréhension | `commit_to`, `record_understanding` | `COMMITMENT_MADE`, `UNDERSTANDING_RECORDED` |
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

## Na'aseh v'nishma (נַעֲשֶׂה וְנִשְׁמָע)

Au Sinaï, le peuple répond au livre de l'alliance « nous ferons et nous entendrons » (Exode 24,7) : le oui précède la compréhension. Selon le Talmud (Chabbat 88a), deux couronnes sont données pour ce oui ; elles sont retirées à la faute du veau d'or, gardées par Moïse, et rendues au retour (Ésaïe 35,10).

Dans la mémoire de C :

- `commit_to()` (na'aseh) enregistre un engagement sans exiger qu'il soit déjà compris ;
- `record_understanding()` (nishma) ajoute la compréhension ensuite, append-only ; elle n'est jamais une condition de l'engagement ;
- `initiate_teshuvah(..., breached_commitments=[...])` met en garde les engagements que la faute a touchés. Ils ne sont pas révoqués : `commitment()` les montre `in_custody` au lieu de `crowned` ;
- ils sont rendus seulement quand la non-récidive est vérifiée (une réparation déclarée ne suffit pas), et repris en garde si la faute revient. `custody_history` garde chaque passage.

## FACT, INTERPRETATION, CURRENT_MODEL

`claim_layers(claim_id)` sépare ce qui s'est passé (preuves et événements cités, jamais modifiés), ce que le système en avait conclu (le claim d'origine et son statut) et ce qu'il comprend maintenant (le claim actif qui le remplace). Une correction peut dire « mon interprétation était trop forte » sans déclarer le fait faux. Chaque claim porte une provenance typée : `user_stated`, `user_inferred` ou `system_hypothesis`.

## Deux mémoires

- `drift_memory()` répond à « qu'est-ce qui nous a fait dériver ? » (type, cause nommée, influence résiduelle, récidives) ;
- `return_memory()` répond à « qu'est-ce qui nous a permis de revenir ? » (ce qui a permis le retour, preuve, leçon, et si le retour a tenu) ;
- `redemption_index()` donne la part des cycles vérifiés durablement : indicateur expérimental, pas une mesure de vertu.

## Limite

Les remplacements passent les mêmes contrôles de faits et de confiance que
`record_claim()`. Toutes les corrections sont validées avant mutation ; chaque
claim reçoit exactement une correction.

Lors d'une récidive, `origin.claim_ids` reste historique. Le cycle enregistre
séparément les `repair_claim_ids` courants, trouvés en suivant les remplacements.
Ces claims deviennent `under_repair` et sortent des décisions sensibles. La
réparation suivante vise ces identifiants, sans réécrire les anciens liens ni
réactiver un claim rétracté. Les étincelles gardent leur provenance d'origine
et peuvent être relevées dans un descendant de cette même lignée.

La vérification contrôle des conditions structurelles (preuve postérieure, observable, non émise par S, vérificateur distinct de l'acteur). Le logiciel n'authentifie ni l'identité ni l'indépendance du vérificateur : le statut porte `external_authentication: not_performed`, comme pour `verify_repair()`.

## Provenance

- **source attestée** : les deux textes de Mik du 2 octobre 2026 (fil « Teshuvah dans Mémoire C » du projet Waymaker Core Private), le second primant là où ils divergent ; puis son message « בְּשִׁבִירַת הַכֵּלִים » du même jour et son accord pour donner une place à la brisure ; puis son texte du 2 octobre 2026 faisant de « Ne jamais employer une mise à jour pour masquer une réparation nécessaire » l'invariant R-001, avec ses six tests de conformité ; puis « Na'aseh v'Nishma » (même jour), avec la consigne « Ce que tu sais être ce qu'il faut faire fait le » ;
- **dérivation consolidée** : « Comment implémenter la mémoire pondérée », « Comment intégrer la mémoire des erreurs passées » et « Comment intégrer la mémoire dans l'algorithme » (Google Drive, 19 septembre 2026) : ne jamais effacer, réduire l'influence ; mémoire de dérive et mémoire de retour ; cicatrice ; indice de rédemption ;
- **reconstruction analytique** : les noms de méthodes, les valeurs d'influence par phase (`DRIFT_INFLUENCE`, reprises des facteurs 1,0 / 0,5 / 0,1 / 0,01 de la mémoire pondérée, avec 0,25 ajouté pour `repair_verified`) les contrôles précis de la vérification, la traduction de la brisure en étincelles comptées le critère des vases isolés, le seuil de contradiction forte (0,8) la correspondance entre les événements du manifeste R-001 et ceux du ledger, et la lecture de Chabbat 88a comme garde des engagements jusqu'au retour vérifié.
