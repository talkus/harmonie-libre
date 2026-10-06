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
- **property_ref / property_version / scope_ref / observer_ref** : toute conclusion est explicitement liée à une propriété, une version, une portée et un observateur.
- **revision_triggers** : conditions explicites de réouverture ; un maintien n'est donc jamais confondu avec une irrévisabilité.
- **provenance_bundle_refs** : provenance de provenance, notamment pour les témoins externes et les agrégations inter-échelles.

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

**MS-20 — Contrat explicite.** Chaque reçu nomme la propriété examinée, sa version, sa portée et l'observateur. Une conclusion sans ces quatre coordonnées est PARTIAL.

**MS-21 — Réouverture explicite.** Chaque reçu publie au moins un `revision_trigger`. La stabilité peut être justifiée, mais elle ne se transforme pas silencieusement en fermeture.

**MS-22 — Provenance de provenance.** Un témoin externe déclaré doit être relié à un bundle de provenance ; les bundles d'un enfant doivent survivre dans son parent. Un miroir d'une même origine n'est toujours pas un nouveau témoin.

**MS-23 — Stutter-invariance locale.** Deux reçus du même niveau qui ne diffèrent que par leur identité d'événement ou leur pointeur parent ont le même `state_digest` et le même verdict local. Un no-op ne fabrique donc pas artificiellement du progrès.

**MS-24 — No-depth privilege.** Un niveau supérieur ne peut pas convertir un enfant PARTIAL, INDETERMINATE ou CONTESTED en preuve plus forte. Les verdicts locaux restent visibles dans le rapport composé.

**MS-25 — Charge de la transformation.** Une future couche de décision devra justifier tout CHANGE par rapport à la baseline HOLD ; le simple fait de changer n'est pas une amélioration.

**MS-26 — Stabilité–plasticité.** Le système doit résister au bruit sans devenir fermé à une preuve matérielle nouvelle.

**MS-27 — Transformation bornée.** Une correction doit avoir une portée déclarée et une condition d'arrêt ; elle ne déclenche pas par défaut une réécriture de toutes les échelles.

**MS-28 — HOLD révocable.** Le maintien est un résultat de premier ordre, distinct du silence et du manque de données, et reste réouvrable par ses déclencheurs.

**MS-29 — Quiescence.** Plusieurs niveaux peuvent demeurer cohérents sans mutation continue, sans que ce repos soit promu en vérité finale.

**MS-30 — Externalités inter-échelles.** Un HOLD local n'est pas cohérent s'il masque une objection, un coût ou une contradiction significative à une autre échelle.

Les invariants MS-25 à MS-30 sont des exigences de la future couche de décision ; le module actuel n'en revendique pas encore l'implémentation complète.

**MS-31 — Passage de première classe.** Le passage entre deux niveaux n'est pas implicite : un `ScaleBridge` peut nommer le transformateur, le reçu enfant, le reçu parent et les dimensions conservées.

**MS-32 — Conservation du doute.** Un passage ne peut pas faire disparaître silencieusement `UNKNOWN`, une contestation ou l'état des preuves. Le pont transporte ces dimensions séparément.

**MS-33 — Pertes explicites et justifiées.** Une abstraction peut perdre du détail, mais toute perte déclarée exige une justification traçable. La compression n'est donc jamais assimilée à une preuve.

**MS-34 — Autorité non transmissible.** Un pont inter-échelles ne peut pas transporter ni créer une autorité d'exécution. `authority_transfer=true` est une erreur structurelle.

**MS-35 — Anti-laundering d'abstraction.** Une information incertaine, contestée ou invalide au niveau enfant ne devient pas plus certaine par le seul fait d'être résumée à un niveau supérieur.

**MS-36 — Audit bidirectionnel.** La lecture descendante retrouve les reçus et origines qui fondent une synthèse ; la correction ascendante peut remonter une objection sans réécrire l'historique du parent.

## Contrat par niveau

| Échelle | Unité typique | Passage valide |
|---|---|---|
| micro | trace, observation, distinction | provenance locale + origin_ref + parent méso explicite |
| méso | branche, épisode, exécution, pratique | union des origines enfants + parent macro |
| macro | relations entre branches / programme | interfaces + divergences + parent méta |
| méta | règles de comparaison et de révision | racine contestable, sans parent supérieur |

La structure se répète ; **la conclusion ne se répète pas nécessairement**.

Le passage lui-même devient aussi vérifiable :

~~~text
ScaleBridge(child, parent)
  = transform_ref
  + preserved_origin_refs
  + preserved_provenance_bundle_refs
  + carried_unknown_ids
  + carried_contestation_ids
  + carried_evidence_status
  + declared_loss_refs
  + loss_justification_refs
  + authority_transfer = false
~~~

Cela ajoute une seconde auto-similarité : non seulement chaque niveau applique le même contrat, mais chaque **passage** entre niveaux applique le même contrat de conservation, transformation et contestabilité.

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
14. présence des quatre échelles pour un verdict multiscale complet ;
15. propriété/version/portée/observateur obligatoires ;
16. déclencheurs de révision obligatoires ;
17. témoin externe sans provenance de provenance refusé comme complet ;
18. conservation des bundles de provenance vers le parent ;
19. stutter-equivalence sous changement d'identité/pointeur parent ;
20. impossibilité pour un niveau supérieur de masquer un enfant PARTIAL ;
21. mode strict exigeant un pont explicite pour chaque arête enfant→parent ;
22. conservation inter-échelles de UNKNOWN, contestations et état des preuves ;
23. refus d'un transfert d'autorité par un pont ;
24. pertes d'information explicitement justifiées et détection des origines/provenances inventées.

## Ancrages méthodologiques

- **W3C PROV-O** : sépare entités, activités, agents et dérivations ; l'architecture conserve de la même façon source, transformation et responsabilité.
- **RFC 9162** : les preuves de cohérence d'un arbre de Merkle illustrent la différence entre append-only vérifiable et vérité du contenu enregistré.
- **TLA+ / stuttering** : une spécification peut tolérer des pas qui ne changent pas l'état pertinent. Le candidat matérialise maintenant une version locale et limitée de cette idée via `state_digest` / `stutter_equivalent`; ce n'est pas une preuve TLA+.
- **W3C PROV bundles** : la provenance de provenance motive `provenance_bundle_refs`, sans transformer la provenance en vérité.
- **RAPTOR / GraphRAG** : leurs hiérarchies montrent l'utilité de représentations à plusieurs niveaux d'abstraction ; elles motivent l'organisation multi-échelle mais ne valident ni les verdicts ni l'autorité de ce candidat.

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


## Extension Ω ↔ Δ — horizon local co-engendré

La nouvelle inversion retire le dernier absolu implicite : **Ω n'est pas une région stable située derrière les formes**.

On écrit désormais, pour un contrat d'observation local :

~~~text
Ω_(observer, scope, scale, property, version) ↔ Δ_local
~~~

Une distinction locale contribue à configurer ce qui apparaît comme son horizon pertinent ; un changement d'observateur, de portée, de propriété, de version, de distinction ou d'UNKNOWN peut donc produire un nouvel horizon local.

Cette réciprocité reste épistémique. Elle ne prétend pas que l'action « crée toute possibilité réelle », seulement que **le modèle de ce qui est possible ou pertinent dépend lui-même de ses formes d'observation et de distinction**.

**MS-37 — Horizon local seulement.** Tout Ω opérationnel cite exactement un reçu, une échelle, un observateur, une portée et un contrat de propriété. `epistemic_scope` reste `local`.

**MS-38 — Forme → horizon.** Un horizon opérationnel est dérivé d'un reçu local ; un Ω flottant sans provenance de forme est PARTIAL.

**MS-39 — Ω ↔ Δ.** Une modification des distinctions locales peut reconfigurer Ω ; réciproquement, changer le contrat d'observation peut modifier quelles distinctions sont disponibles. Aucune direction n'est déclarée causalité métaphysique.

**MS-40 — Non-totalisation de Ω.** Aucun horizon local ne peut être promu en « frontière du réel » ou « ensemble exhaustif de toutes les possibilités ».

**MS-41 — UNKNOWN local ≠ impossibilité absolue.** Un `UNKNOWN` décrit une limite du contrat courant. Il ne permet jamais d'inférer que ce qui est inconnu est impossible pour tout autre observateur, toute autre échelle ou tout contrat futur.

**MS-42 — Reconfiguration traçable.** Tout passage Ω_n → Ω_(n+1) publie les distinctions ajoutées ou retirées, les UNKNOWN ouverts ou résolus et les traces invoquées comme causes.

**MS-43 — Croissance non monotone.** La révision peut ouvrir ou fermer des distinctions ou des UNKNOWN. « Plus de distinctions » n'est pas assimilé automatiquement à « plus de vérité » ou « plus de progrès ».

**MS-44 — Actualisation ≠ preuve d'un réservoir préalable.** Le fait qu'une nouvelle distinction devienne formulable n'établit pas qu'elle existait auparavant comme possibilité déjà représentée dans un espace exhaustif.

**MS-45 — Neutralité symbolique de l'horizon.** Les labels symboliques restent hors du hash opérationnel ; renommer Keter, Ω, Nehar di-Nur ou toute autre analogie ne change pas le verdict.

Le module candidat `horizon_reciprocity.py` implémente seulement cette couche locale :

~~~text
ScaleReceipt
    ↓ deterministic derivation
LocalHorizon
    ↓ explicit traced reconfiguration
HorizonTransition
~~~

et conserve toujours :

~~~text
execution_authority = false
~~~

### Tests supplémentaires

Les tests de cette extension vérifient :

1. Ω dérivé d'une forme ou d'un reçu exact ;
2. changement d'observateur → horizon local distinct ;
3. changement de portée → horizon local distinct ;
4. nouvelle distinction → reconfiguration explicitement déclarée ;
5. UNKNOWN conservé comme frontière locale ;
6. revendication d'horizon absolu ou total rejetée ;
7. horizon flottant sans reçu exact rejeté ;
8. diff de reconfiguration vérifié contre l'état réel ;
9. impossibilité de certifier un espace futur exhaustif ;
10. causes de reconfiguration obligatoirement reliées à des traces connues ;
11. coexistence de plusieurs horizons au même niveau ;
12. renommage symbolique sans effet opérationnel.

La formulation conceptuelle devient donc :

~~~text
ce qui ouvre ↔ ce qui distingue
~~~

mais la formulation exécutable reste plus prudente :

~~~text
forme locale / contrat d'observation
    ↔
horizon épistémique local et révisable
~~~

Aucune de ces deux directions ne reçoit un privilège ontologique ou une autorité d'exécution.


### Réciprocité opérationnelle sans cercle auto-validant

L'implémentation précédente matérialisait surtout :

~~~text
Δ_n → Ω_n
~~~

La direction inverse est désormais rendue explicite, mais asymétrique :

~~~text
Δ_n --derive--> Ω_n

(Ω_n + κ_available + τ_evidence)
  --constrain/admit as candidate--> Δ_candidate_(n+1)

Δ_candidate_(n+1)
  --review / evidence / contestation--> Δ_(n+1)

Δ_(n+1) --derive--> Ω_(n+1)
~~~

Ici `Δ_candidate` est une distinction candidate, pas une vérité acquise.

**MS-46 — Ω n'est pas une preuve.** L'horizon peut contraindre la pertinence d'une distinction candidate, mais ne peut jamais servir lui-même de preuve de cette distinction.

**MS-47 — Preuve externe au cercle.** Toute distinction candidate doit citer des couplages et des traces disponibles indépendamment du hash de l'horizon qui la conditionne.

**MS-48 — Admission ≠ vérité.** `admissible_for_review=true` signifie uniquement que la proposition satisfait le contrat structurel pour être examinée ; cela ne la promeut ni en vérité, ni en relation stabilisée, ni en action permise.

**MS-49 — Anti-auto-validation.** Une distinction candidate ne peut pas s'auto-promouvoir via `claims_truth` ni transporter `execution_authority`.

**MS-50 — UNKNOWN ciblé.** Une proposition qui prétend répondre à un UNKNOWN doit citer un `unknown_id` réellement présent dans l'horizon local ; elle ne peut pas déclarer résolue une inconnue étrangère au contrat courant.

La formule exécutable de la réciprocité devient donc :

~~~text
Ω contraint la recherche de Δ
mais τ/κ soutiennent Δ ;
Δ reconfigure ensuite Ω.
~~~

Ce choix empêche le cercle auto-certifiant `Ω prouve Δ ; Δ prouve Ω`.
## Extension pluralité d'horizons — auto-similarité micro / méso / macro / méta

La réciprocité Ω ↔ Δ est maintenant répétée sous la même discipline aux quatre échelles, sans transformer l'accord en preuve.

~~~text
micro : horizons locaux → évaluations locales → désaccord conservé
méso  : horizons locaux → évaluations locales → désaccord conservé
macro : horizons locaux → évaluations locales → désaccord conservé
méta  : horizons locaux → évaluations locales → désaccord conservé
~~~

Le même validateur structurel s'applique partout ; **les conclusions n'ont pas à être identiques**.

**MS-51 — Pluralité d'horizons par échelle.** Une propriété peut être examinée depuis plusieurs Ω locaux au même niveau sans qu'un horizon de référence soit déclaré souverain.

**MS-52 — Accord ≠ indépendance.** Deux appuis ne comptent comme structurellement distincts que s'ils diffèrent d'horizon et d'observateur et n'ont pas d'origine ni de bundle de provenance commun.

**MS-53 — Miroir ≠ corroboration.** Deux copies ou dérivations d'une même origine ne produisent jamais deux preuves indépendantes.

**MS-54 — Corroboration structurelle ≠ validation indépendante.** Même lorsque deux chemins d'appui sont structurellement distincts, le runtime conserve `independent_validation=false`.

**MS-55 — Pas de vote majoritaire épistémique.** Une contestation explicite reste `CONTESTED`, même face à plusieurs appuis. Elle n'est pas effacée par comptage.

**MS-56 — Indétermination conservée.** Un horizon `INDETERMINATE` ne devient pas support par agrégation.

**MS-57 — Auto-similarité du contrat, pas du verdict.** Micro, méso, macro et méta utilisent le même schéma de provenance, pluralité, contestation et non-autorité ; leurs verdicts peuvent diverger.

**MS-58 — Non-masquage ascendant.** Un niveau supérieur ne peut pas convertir une contestation ou indétermination d'un niveau inférieur en `CANDIDATE_OK` global.

**MS-59 — Complétude multi-échelle explicite.** Un rapport dit multi-échelle doit contenir micro, méso, macro et méta ; une échelle manquante garde le résultat `PARTIAL`.

**MS-60 — Autorité toujours nulle.** La pluralité des horizons et la répétition du motif n'accordent aucune permission : `execution_authority=false` à chaque niveau et au rapport composé.

La forme candidate complète devient :

~~~text
Ω_i ↔ Δ_i
  ↓
évaluation locale sourcée
  ↓
{support | challenge | indeterminate}
  ↓
comparaison inter-horizons sans fusion
  ↓
répétition du même contrat à micro / méso / macro / méta
~~~

La cohérence recherchée n'est donc pas « tout le monde conclut pareil », mais :

~~~text
chaque conclusion reste liée à son horizon,
chaque accord conserve sa provenance,
chaque désaccord reste visible,
et aucune échelle ne blanchit l'incertitude d'une autre.
~~~

## Extension cycle de vie de Φ — Λ_t, maturation et régénération

Le nouvel axe corrige la régression `Φ → Θ → Ψ → ...` : Θ et Ψ restent des **labels conceptuels**, pas des méta-autorités exécutables.

Le runtime encode uniquement un contrat local :

~~~text
Ω ↔ Δ
  ↓
Φ_n
  ↓ traces
Λ_t = contexte historique local
  ↓
{MATURE | REGENERATE | DEFER | RETIRE}
  ↓
Ω' ↔ Δ'
~~~

`Λ_t` n'est pas un score scalaire de maturité. Il comprend une phase historique déclarée, un horizon local, des traces, une portée, un observateur et des déclencheurs de révision.

**MS-61 — Gain borné.** Le contexte exige `0 < G_Φ < ∞`. Ce gain n'est ni une vérité, ni un rythme optimal, ni un sélecteur automatique de décision.

**MS-62 — Λ local et sourcé.** Toute maturité historique cite des traces disponibles et un horizon local connu.

**MS-63 — Maturation ≠ régénération.** `MATURE` conserve l'identité de Φ et change sa version ; `REGENERATE` exige un successeur Φ distinct.

**MS-64 — Différer est un premier ordre.** `DEFER` ne choisit aucun successeur en secret et exige une condition explicite de réexamen.

**MS-65 — Retrait sans remplacement implicite.** `RETIRE` peut mettre fin à un Φ sans fabriquer silencieusement Φ_(n+1).

**MS-66 — Pas de rythme absolu.** Toute revendication d'un `right rhythm` final ou optimal est rejetée par le contrat (`claims_optimal_rhythm=false`).

**MS-67 — Ψ n'est pas une autorité.** Le discernement entre maturation et régénération est un résultat local justifié, pas un méta-opérateur souverain.

**MS-68 — Même G_Φ, décisions différentes.** Des contextes Λ distincts peuvent légitimement choisir des chemins différents avec la même valeur de gain.

**MS-69 — Auto-similarité du cycle de vie.** Le même contrat s'applique à micro, méso, macro et méta ; les chemins choisis peuvent diverger.

**MS-70 — Non-masquage inter-échelles.** Une contestation ou une phase historique indéterminée à une échelle reste visible dans le rapport composé.

**MS-71 — Aucun choix n'autorise l'exécution.** `execution_authority=false` pour toutes les décisions et pour leur agrégation.

La conséquence architecturale est :

~~~text
innovation n'est pas présumée supérieure à maturation ;
stabilité n'est pas présumée supérieure à transformation ;
retrait n'est pas présumé être un échec ;
le contexte historique local doit rester révisable.
~~~

Le système ne cherche donc plus un correcteur du correcteur. Il applique le même contrat de provenance, contestabilité, révision et non-autorité à chaque décision de cycle de vie.
