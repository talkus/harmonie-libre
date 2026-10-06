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

## Extension ensemble de dynamiques — 𝔛 et UNKNOWN_Ξ

L'inversion suivante retire le privilège d'une dynamique génératrice unique. `Ξ` n'est jamais observé directement dans ce candidat : il est reconstruit à partir de projections et de traces.

~~~text
{Ω, Δ, Φ, τ}_observés
    ↓ reconstruction
𝔛_n = {Ξ_1, Ξ_2, ..., Ξ_k}
    ↓ nouvelles traces
𝔛_(n+1) = A(𝔛_n, τ_n)
~~~

Le runtime ne classe pas ces hypothèses avec un score totalisant et ne sélectionne pas automatiquement un « vrai moteur caché ».

**MS-72 — Ξ reconstruit, non observé.** Une hypothèse génératrice doit publier ses projections, ses hypothèses, ses origines et sa provenance.

**MS-73 — Non-unicité conservée.** Plusieurs Ξ compatibles peuvent demeurer simultanément admissibles.

**MS-74 — Équivalence observationnelle.** Deux hypothèses donnant les mêmes projections sur les dimensions actuellement observées restent distinctes mais sont regroupées comme observationnellement équivalentes pour ce contrat.

**MS-75 — UNKNOWN_Ξ.** `unknown_xi=true` lorsqu'une dynamique unique ne peut pas être déterminée : plusieurs hypothèses admissibles subsistent ou au moins une hypothèse reste sous-déterminée.

**MS-76 — Hors-modèle de premier ordre.** Si aucune hypothèse n'est compatible, le système retourne `out_of_model=true`; il ne choisit pas la moins mauvaise par défaut.

**MS-77 — Compatibilité ≠ vérité.** Un seul Ξ compatible peut produire `CANDIDATE_OK` structurel, mais `independent_validation=false` et aucune promotion en vérité n'en découle.

**MS-78 — Révision sans effacement.** Chaque révision conserve les identifiants de l'espace précédent, les hypothèses retenues, sous-déterminées, rejetées et nouvellement proposées.

**MS-79 — Nouvelle hypothèse ≠ privilège.** Une hypothèse ajoutée après observation est évaluée avec le même contrat que les anciennes et doit exposer ses hypothèses et sa provenance.

**MS-80 — Projection locale.** La comparaison d'un Ξ à des traces reste liée à une échelle, un observateur et une portée explicites.

**MS-81 — Auto-similarité de 𝔛.** Le même opérateur de révision de l'espace d'hypothèses s'applique à micro, méso, macro et méta ; les ensembles de dynamiques peuvent être différents à chaque niveau.

**MS-82 — Non-masquage.** `UNKNOWN_Ξ` ou `out_of_model` à une échelle ne peut pas être blanchi par une synthèse supérieure.

**MS-83 — Pas de gagnant scalaire.** Aucun score global ne réduit l'écologie des reconstructions à un classement unique.

**MS-84 — Structure ≠ autorité.** Ni la compatibilité, ni l'unicité locale, ni la répétition multi-échelle ne confèrent une autorité d'exécution.

La forme candidate devient :

~~~text
𝔛_n
  ↕ projections / observations
Ω_n ↔ Δ_n
  → τ_n
  → Φ_n
  → révision de 𝔛
𝔛_(n+1)
~~~

avec deux sorties explicitement distinctes :

~~~text
UNKNOWN_Ξ  = plusieurs reconstructions restent admissibles
OUT_OF_MODEL = aucune reconstruction actuelle ne couvre les traces
~~~

Le second cas est essentiel : l'ouverture du modèle exige de pouvoir reconnaître que **l'espace actuel de dynamiques est lui-même insuffisant**.

## Axiome racine candidat — non-clôture opérationnelle

La formulation philosophique la plus dépouillée proposée est :

~~~text
non-clôture
~~~

ou :

~~~text
aucune présentation n'épuise ce qui se présente
~~~

Le runtime adopte une version volontairement plus faible et vérifiable. Il **ne code pas** `∀P, ∃P' ≠ P` comme fait ontologique, car l'existence effective d'une autre présentation ne peut pas être déduite du seul refus de clôture.

Il code :

~~~text
par défaut, aucune présentation locale ne peut se déclarer exhaustive ;
une clôture n'est admissible que relativement à un domaine borné,
un critère explicite et des preuves de clôture ;
même alors, cette clôture reste locale et réouvrable.
~~~

**MS-85 — Non-clôture par défaut.** Une présentation qui ne revendique aucune exhaustivité reste `OPEN`; l'ouverture n'est ni une erreur ni une preuve d'incomplétude métaphysique.

**MS-86 — Clôture globale interdite.** Aucun reçu local ne peut revendiquer l'exhaustivité du réel, de toutes les perspectives ou de toutes les possibilités.

**MS-87 — Clôture locale bornée.** `LOCALLY_CLOSED` exige un domaine borné, un critère de clôture, des références de preuve et aucune inconnue silencieusement conservée.

**MS-88 — Preuve de clôture ≠ vérité totale.** Une clôture locale structurellement admissible reste `independent_validation=false`, `globally_exhaustive=false` et `execution_authority=false`.

**MS-89 — Réouverture obligatoire.** Même une clôture locale publie des déclencheurs de révision. Changer de portée, de propriété ou recevoir une preuve nouvelle peut rouvrir le contrat.

**MS-90 — UNKNOWN incompatible avec clôture silencieuse.** Un élément non résolu interdit de déclarer exhaustive la présentation locale concernée.

**MS-91 — Quatre clôtures locales ≠ clôture globale.** La complétude micro + méso + macro + méta n'est jamais promue par composition en totalité absolue.

**MS-92 — Non-clôture multi-échelle.** Le même garde-fou s'applique à chaque niveau et au composé ; une indétermination locale reste visible.

**MS-93 — Non-clôture ≠ génération forcée de nouveauté.** Le système ne doit pas inventer une nouvelle présentation uniquement pour satisfaire l'axiome. `DEFER`, `HOLD`, `RETIRE` et absence de nouvelle hypothèse restent permis.

**MS-94 — Non-clôture ≠ relativisme.** Une présentation peut être réfutée, localement close ou mieux soutenue qu'une autre ; le garde-fou interdit seulement le saut injustifié de local à total.

La forme racine exécutable devient donc :

~~~text
présentation locale
  → {OPEN | INDETERMINATE | LOCALLY_CLOSED}
  → toujours scope-bounded
  → jamais globally_exhaustive
  → toujours reopenable
~~~

Cette couche donne un sens opérationnel à la formule :

~~~text
Il y a toujours plus que ce qui est actuellement distingué.
~~~

sans la convertir en affirmation métaphysique automatique. Ce qui est garanti par le runtime est plus précis : **ce qui est actuellement distingué n'a jamais, par défaut, le droit de se déclarer totalité.**

## Extension cohérence ↔ tension — sans dialectique obligatoire

La nouvelle inversion retire le privilège de la cohérence comme valeur ou substrat ultime. Le runtime maintient deux axes distincts :

~~~text
verdict de cohérence locale
et
état des tensions locales
~~~

Il ne code donc pas `C* ↔ T` comme loi métaphysique universelle. Il code seulement que cohérence et tension peuvent se révéler, se contraindre ou se reconfigurer mutuellement sous un contrat local.

**MS-95 — Cohérence et tension sont orthogonales.** `COHERENT` n'implique pas absence de tension ; une tension n'implique pas `INCOHERENT`.

**MS-96 — Tension sourcée.** Toute tension cite un contrat local, au moins deux relations, des traces et une justification.

**MS-97 — Tension ≠ erreur.** Une tension peut être `CONSTITUTIVE`, `RESOLVABLE`, `INDETERMINATE` ou `OUT_OF_SCOPE`; aucun de ces états n'est assimilé automatiquement à un défaut.

**MS-98 — Tension ≠ fécondité.** La générativité reste `UNESTABLISHED` par défaut. La déclarer `SUPPORTED` exige des preuves spécifiques.

**MS-99 — Fécondité contestable.** Une tension peut avoir une générativité `CONTESTED`; ce désaccord reste visible.

**MS-100 — Pas d'exhaustivité des tensions.** L'absence de tension enregistrée ne permet jamais de conclure qu'aucune autre tension pertinente n'existe.

**MS-101 — Incohérence admissible comme constat.** `INCOHERENT` est un verdict local possible, pas un échec du validateur ni une faute à réparer automatiquement.

**MS-102 — Dissonance non instrumentalisée.** Une rupture, contradiction ou souffrance observée n'est jamais requalifiée en « utile » ou « nécessaire » sans preuve explicite de l'effet invoqué.

**MS-103 — Auto-similarité du contrat.** Le même schéma cohérence/tension s'applique à micro, méso, macro et méta, sans exiger les mêmes verdicts.

**MS-104 — Non-masquage.** Une tension contestée ou indéterminée à une échelle reste visible dans l'agrégation multi-échelle.

**MS-105 — Pas de totalité harmonique.** Plusieurs verdicts `COHERENT` locaux ne produisent pas par composition une cohérence globale absolue.

**MS-106 — Pas de totalité conflictuelle.** Plusieurs tensions locales ne prouvent pas davantage que « le conflit » est la nature fondamentale du système.

**MS-107 — Relation plutôt que substance.** `C*` et `T` sont traités comme des verdicts/relations sous contrat, jamais comme des entités cachées.

**MS-108 — Structure ≠ autorité.** Cohérence, tension ou générativité ne produisent aucune permission : `independent_validation=false`, `execution_authority=false`.

La forme exécutable devient :

~~~text
(traces, relations, échelle, observateur, propriété)
        ↓
coherence_verdict ∈ {COHERENT, INCOHERENT, CONTESTED, INDETERMINATE}
        ||
tensions ∈ {CONSTITUTIVE, RESOLVABLE, INDETERMINATE, OUT_OF_SCOPE}
        ↓
révision / contestation / maintien
~~~

Le point central est que le double axe `cohérence / tension` n'est pas forcé en opposition dialectique. Il reste possible de constater : cohérence avec tension, incohérence sans tension identifiée, tension non générative, ou absence actuelle de relation justifiée.

## Extension fécondité durable — détecter l'épuisement sans régression infinie

L'architecture remplace la recherche d'un critère parfait par une question locale : **la forme demeure-t-elle féconde sous son contrat courant ?**

Le candidat refuse toutefois `max(fécondité)` comme score unique. La fécondité reste multi-dimensionnelle :

~~~text
reprise
génération
réouverture
impact sur les voies viables
risque de fossilisation
risque de dissolution
~~~

**MS-109 — Fécondité ≠ scalaire.** Aucun `fecundity_score` totalisant n'est calculé ; `scalar_score=None` est conservé dans les rapports.

**MS-110 — Nouveauté ≠ fécondité.** Générer de nouvelles possibilités ne suffit pas si la reprise ou la réouverture sont perdues.

**MS-111 — Reprise positive.** Une forme féconde doit conserver une capacité de reprise soutenue par des preuves locales ; absence de preuve ≠ preuve d'absence.

**MS-112 — Réouverture positive.** Une forme peut rester stable tout en restant féconde si elle demeure explicitement réouvrable.

**MS-113 — Pas de destruction silencieuse des voies viables.** Toute fermeture de voie doit être tracée et justifiée ; sinon la fécondité est dégradée.

**MS-114 — Fermeture justifiée ≠ infertilité automatique.** Une voie peut être fermée pour une raison traçable sans que toute la forme soit déclarée non féconde.

**MS-115 — Fossilisation et dissolution séparées.** Ces risques restent deux dimensions distinctes et ne sont jamais compressés en un score d'équilibre.

**MS-116 — Données insuffisantes ≠ absence de risque.** `INSUFFICIENT_DATA` maintient le verdict `INDETERMINATE`.

**MS-117 — Pas de nouveauté obligatoire.** `generation_status=NOT_TRIGGERED` n'est pas à lui seul une dégradation si reprise, réouverture et stewardship des voies restent soutenus.

**MS-118 — Détection plutôt qu'optimisation.** Le module détecte `SUSTAINED`, `DEGRADED`, `INDETERMINATE` ou `CONTESTED`; il ne choisit ni n'autorise la transformation suivante.

**MS-119 — Auto-similarité multi-échelle.** Le même contrat de fécondité s'applique à micro, méso, macro et méta.

**MS-120 — Non-masquage.** Une dégradation, contestation ou indétermination locale reste visible dans l'agrégation multi-échelle.

**MS-121 — Fécondité ≠ optimalité.** Même `SUSTAINED` ne signifie jamais « forme optimale », « meilleure forme » ou « critère final ».

**MS-122 — Fécondité ≠ autorité.** `optimality_claim=false` et `execution_authority=false` à chaque niveau et au rapport composé.

La formulation exécutable devient :

~~~text
forme locale
  ↓ preuves séparées
{reprise, génération, réouverture, impacts de voies, risques}
  ↓
{SUSTAINED | DEGRADED | INDETERMINATE | CONTESTED}
  ↓
aucune transformation automatique
~~~

La compression conceptuelle est alors :

~~~text
Conserver ce qui demeure fécond.
Réexaminer ce qui cesse de l'être.
Transformer seulement sous un contrat séparé de décision et de preuve.
~~~

Ce correctif évite deux erreurs symétriques : fossiliser une forme parce qu'elle a été utile, ou la remplacer uniquement parce qu'une nouveauté est possible.
