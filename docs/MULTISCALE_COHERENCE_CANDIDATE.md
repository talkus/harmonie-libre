# Cohérence structurelle multi-échelle — candidat κ/Δ/ρ/τ/UNKNOWN

**Statut :** candidat expérimental, non canonique, non autorisant.  
**Portée :** ajout de cohérence par auto-similarité structurelle multi-échelle.  
**Motif :**

~~~text
κ_n → Δ_n → ρ_n → τ_n → UNKNOWN_n → κ_(n+1)
~~~

Ce document ne remplace ni `SECURITY_COMMAND.md`, ni AEGIS-24, ni les sources de Conscience C. La cohérence n'est pas une preuve de vérité et n'accorde aucune permission d'exécution.

## Sémantique minimale

- **κ — couplage** : interaction, corrélation, dépendance ou possibilité de rencontre observée/hypothétique. Un couplage n'est pas une causalité.
- **Δ — distinction** : différence localement reconnue. Toute distinction doit citer le ou les couplages et les traces qui la soutiennent.
- **ρ — relation stabilisée** : structure dérivée de distinctions, toujours révisable et localement sourcée.
- **τ — trace** : provenance append-only. Une correction ajoute une trace ; elle ne réécrit pas la précédente.
- **UNKNOWN — frontière de pertinence** : couplages pour lesquels les distinctions pertinentes ne sont pas encore établies. UNKNOWN n'est jamais converti implicitement en PASS ou en permission.
- **origin_ref** : identité de la source d'origine. Deux miroirs d'une même origine réutilisent le même `origin_ref` et ne deviennent pas deux preuves indépendantes.
- **evidence_status** : `TRIGGERED | NOT_TRIGGERED | INSUFFICIENT_DATA | INVALID_DATA`. Ces états ne sont jamais fusionnés.

## Invariants multi-échelle

**MS-01 — Auto-similarité structurelle.** Le même schéma κ/Δ/ρ/τ/UNKNOWN est vérifié à chaque échelle micro, méso, macro et méta.

**MS-02 — Non-identité des conclusions.** La répétition du schéma n'impose pas la même conclusion à chaque niveau.

**MS-03 — Provenance locale.** Chaque Δ et ρ cite ses traces locales ; une conclusion supérieure ne remplace pas sa provenance inférieure.

**MS-04 — Contradiction ascendante.** Un enfant peut contester une prémisse du parent avec une trace. La contestation remonte sans effacer le reçu parent.

**MS-05 — Non-réécriture.** Correction ≠ effacement. Les reçus sont adressés par contenu ; une nouvelle version produit un nouveau reçu.

**MS-06 — Non-auto-certification.** `CANDIDATE_OK` signifie seulement « contrat structurel local satisfait ». Même avec un témoin déclaré, ce validateur fixe `independent_validation=false`.

**MS-07 — UNKNOWN fail-closed.** Une frontière UNKNOWN ou `INSUFFICIENT_DATA` conserve une dimension indéterminée et ne produit aucune autorité d'exécution.

**MS-08 — Couplage ≠ causalité.** La promotion d'un couplage en causalité exige une preuve causale explicitement référencée.

**MS-09 — Structure ≠ autorité.** L'auto-similarité peut se répéter ; l'autorité ne se propage pas automatiquement avec elle.

**MS-10 — Symbolique sans privilège.** Renommer ou retirer des labels symboliques ne doit modifier ni le hash opérationnel ni le verdict.

**MS-11 — Composition vérifiable.** Les liens parent/enfant et les cibles de contestation doivent résoudre vers des reçus présents dans la composition vérifiée.

**MS-12 — Pas de scalaire totalisant.** Le système conserve les verdicts locaux et leurs causes ; il ne réduit pas la cohérence à un score unique.

**MS-13 — Multiplicité par échelle.** Une échelle peut contenir plusieurs unités. L'ancienne contrainte « un reçu par échelle » était incohérente avec une architecture réelle 11 micro → 3 méso → 1 macro → 1 méta et a été supprimée.

**MS-14 — Adjacence des passages.** Un parent est exactement au niveau suivant : micro→méso, méso→macro, macro→méta. Le niveau méta n'a pas de parent supérieur dans ce modèle.

**MS-15 — Acyclicité.** Le graphe d'agrégation parentale ne peut contenir de cycle.

**MS-16 — Conservation des origines.** Chaque parent conserve l'union des `origin_ref` de ses enfants. Une copie ne multiplie jamais le poids de sa source.

**MS-17 — Stale parent fail-closed.** Le lien parent porte sur le hash de contenu exact. Si ce hash n'est plus présent dans la composition courante, le passage est PARTIAL plutôt que réparé silencieusement.

**MS-18 — Dimensions non écrasées.** Contestation, UNKNOWN, donnée invalide et témoin externe restent des champs séparés même lorsqu'un statut compact est calculé.

**MS-19 — Autorité monotone nulle.** Aucun passage micro→méso→macro→méta n'augmente `execution_authority`; cette couche la fixe à `false`.

## Contrat par niveau

| Échelle | Unité typique | Passage valide |
|---|---|---|
| micro | trace, observation, distinction | provenance locale + origin_ref + parent méso explicite |
| méso | branche, épisode, exécution, pratique | union des origines enfants + parent macro |
| macro | relations entre branches / programme | interfaces + divergences + parent méta |
| méta | règles de comparaison et de révision | racine contestable, sans parent supérieur |

La structure se répète ; **la conclusion ne se répète pas nécessairement**.

## Runtime candidat

Le module `conscience_c_brain.multiscale_coherence` matérialise le motif sous forme de reçus typés. Il retourne un statut compact parmi :

~~~text
CANDIDATE_OK
PARTIAL
INDETERMINATE
CONTESTED
~~~

et conserve séparément :

~~~text
evidence_status
has_unknown
has_contestation
external_witness_declared
independent_validation = false
execution_authority = false
~~~

Ainsi, `CONTESTED` ne masque pas le fait qu'une donnée puisse aussi rester `INSUFFICIENT_DATA`.

## Tests hostiles inclus

Le lot de tests vérifie notamment :

1. provenance obligatoire pour Δ et source d'origine obligatoire ;
2. UNKNOWN / `INSUFFICIENT_DATA` fail-closed ;
3. donnée invalide distincte d'une absence de déclenchement ;
4. couplage non promu silencieusement en causalité ;
5. témoin déclaré ≠ validation indépendante ;
6. renommage symbolique sans effet opérationnel ;
7. plusieurs unités permises au même niveau ;
8. union des origines lors de l'agrégation ;
9. liens parentaux strictement adjacents ;
10. stale/missing parent détecté ;
11. identifiants concurrents détectés ;
12. contestation enfant→parent sans réécriture ;
13. UNKNOWN et contestation visibles simultanément ;
14. présence des quatre échelles pour un verdict multiscale complet.

## Ancrages méthodologiques

- **W3C PROV-O** : sépare entités, activités, agents et dérivations ; l'architecture conserve de la même façon source, transformation et responsabilité.
- **RFC 9162** : les preuves de cohérence d'un arbre de Merkle illustrent la différence entre append-only vérifiable et vérité du contenu enregistré.
- **TLA+ / stuttering** : une spécification peut tolérer des pas qui ne changent pas l'état pertinent ; cela motive un futur test d'invariance aux no-op sans faire de la stabilité une faute.
- **NIST — association ≠ causalité** : soutient explicitement MS-08.

Ces références motivent des propriétés de conception ; elles ne prouvent pas que ce candidat les implémente formellement.

## Persistance

La persistance doit rester append-only ou event-sourced. Un backend externe peut stocker les reçus et leurs hashes, mais il ne devient ni source de vérité sémantique ni autorité d'exécution par simple stockage.

## Statut de promotion

Ce candidat reste révisable. Une fusion éventuelle exige au minimum :

1. exécution reproductible des tests ;
2. revue de code indépendante ;
3. comparaison avec les invariants canoniques existants ;
4. résolution explicite des contradictions ;
5. aucune promotion de `CANDIDATE_OK` en « vérité », « autorité » ou « validation indépendante ».
