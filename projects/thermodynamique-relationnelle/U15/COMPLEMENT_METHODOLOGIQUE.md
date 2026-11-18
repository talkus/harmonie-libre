# U15 — Complément méthodologique : budgets, anticipation et protocoles T1–T6

**Date :** 18 novembre 2026. **Statut :** dérivation analytique et propositions de protocoles, en réponse aux observations du porteur sur U15 (hypothèse H, §8.3, T1–T6). Addendum à [HISTORIQUE.md](HISTORIQUE.md), sans modification silencieuse des versions historiques. La numérotation T1–T6 ci-dessous est celle de la version de travail revue, distincte des identifiants du registre consolidé [TESTS.md](TESTS.md).

## 1. Hypothèse H : stabilité de la composition

Soit (M,+,≼_M,0) un monoïde préordonné, éventuellement non commutatif. L'hypothèse H est la compatibilité bilatérale du préordre avec l'opération :

\[
a\preceq_M b,\quad c\preceq_M d
\quad\Longrightarrow\quad a+c\preceq_M b+d.
\]

L'écriture additive ne présuppose pas la commutativité. Dans une suite de coûts, les termes sont ordonnés chronologiquement. L'associativité garantit que le regroupement en sous-trajectoires ne change pas le coût total. Si une première sous-trajectoire coûte u≼C_1 et une seconde v≼C_2, H donne u+v≼C_1+C_2. En concaténant uniquement des trajectoires dont les états intermédiaires et le contexte sont compatibles, on obtient

\[
\Phi_{C_2}^{r,*}\circ\Phi_{C_1}^{r,*}
\subseteq\Phi_{C_1+C_2}^{r,*}.
\]

Pour n=0, l'inclusion du chemin vide suppose 0≼C et l'identité admissible. Pour n≥1, la preuve d'effondrement sous A2 et A3 ne requiert pas H séparément, car A3 postule déjà la composition à coût composé ; H justifie la stabilité de cette discipline lorsqu'on passe des coûts exacts aux majorants. Sans H cette stabilité n'est pas garantie en général : sur (N,+,0), prendre l'ordre réflexif augmenté de la seule comparaison stricte 1≼2 ; 1+1=2 n'est alors pas ≼2+1=3. Il n'est plus licite de composer les deux majorants comme si l'ordre était compatible.

Un exemple non commutatif admissible est le monoïde des mots sur un alphabet de ressources/commandes, avec concaténation et ordre de sous-séquence. Si u est une sous-séquence de U et v de V, uv est une sous-séquence de UV ; AB et BA restent distincts. Ce modèle illustre H sans prétendre décrire la thermodynamique.

**Pont avec U1–U14.** Cette hypothèse formalise la conservation de la discipline budgétaire lors du passage des transformations élémentaires aux trajectoires composées, sans supposer qu'une grandeur scalaire caractérise toutes les contraintes. Elle n'est pas une conséquence automatique de chaque note U1–U14 : elle doit être vérifiée pour chaque choix de ressources et de composition. Les coûts consommés séquentiellement peuvent s'additionner ; une largeur matérielle maximale ou une intensité maximale se compose plutôt par max pour des étapes successives. Le parallélisme requiert sa propre règle d'agrégation. Le symbole + peut représenter la loi de composition effectivement déclarée (par exemple somme sur les consommables, max sur les pics), à condition qu'elle soit associative et monotone. La durée de réutilisation, les corrélations, le stock d'auxiliaires et les changements de capacité ne doivent pas être effacés. Sur l'état augmenté, une comptabilité de stock s'écrit b'+c≼b lorsque cette composition est appropriée ; aucun inverse additif n'est présupposé.

## 2. Note du 17 novembre : anticipation récursive et traçabilité

Le lien documenté dans [HISTORIQUE.md](HISTORIQUE.md#architecture-c) est développé ici. Les identifiants INV-11 / CTRL-35 et la notation D→P→R→T→P′ sont repris de la présente demande ; leur libellé canonique intégral n'a pas été retrouvé dans le corpus public consulté. Cette section est une interprétation méthodologique, pas une reproduction de la note source ni une modification d'invariants canoniques.

**Non-négation** : une erreur constatée reste un événement du passé, même lorsque sa conséquence est réparée. **Conservation des erreurs** : l'archive conserve l'énoncé initial, son contexte, la preuve ou objection, le verdict et la correction, en reliant les versions ; elle ne maintient pas l'assertion réfutée comme vraie. Ces deux principes sont les points d'ancrage INV-11 / CTRL-35 indiqués par le porteur. Ils concordent avec la règle de non-réécriture de l'historique dans [AGENTS.md](../../../AGENTS.md) et [SECURITY_COMMAND.md](../../../SECURITY_COMMAND.md), sans prétendre à leur équivalence formelle.

Lecture fonctionnelle proposée, sans imposer de développement inédit aux lettres de la note : D→P→R→T→P′ décrit une première anticipation P, confrontée à une réalité et à une transformation, puis une anticipation révisée P′. Un registre E_t conserve observations, erreurs, ressources engagées et corrections. Schématiquement :

\[
E_{t+1}=E_t\mathbin{\Vert}(\text{observation},\text{erreur constatée},\text{correction},\text{provenance}),\qquad
P_{t+1}=\mathsf{Update}(P_t,E_{t+1};b_t,k_t).
\]

Le symbole ∥ désigne l'ajout traçable, pas une conservation thermodynamique. Les opérations de mémorisation, de vérification et de mise à jour ne sont pas gratuites par hypothèse ; elles utilisent les ressources disponibles et peuvent échouer. Une correction peut modifier les capacités de navigation futures, ou réduire un ensemble trop optimiste de possibilités anticipées. Le réel demeure le critère de correction. Il n'y a ni convergence automatique, ni amélioration strictement monotone, ni point fixe postulé.

**Statut causal.** L'anticipation récursive est une conséquence collatérale possible : si une confrontation révèle une erreur et que cette erreur est conservée de manière exploitable, une mise à jour peut modifier non seulement la prédiction suivante mais aussi la méthode qui la produit. Elle n'est pas la finalité de l'Architecture C. La finalité demeure indépendante de cette conséquence ; aucune loi physique ni identité entre Architecture C et U15 n'en est déduite. La récursivité n'est pas la simple étoile budgétaire (qui s'effondre sous les hypothèses établies) mais une dynamique effective du contexte, des capacités ou de la règle de mise à jour, observable au niveau de l'état augmenté.

**Test opérationnel proposé.** Comparer deux politiques qui reçoivent la même succession de tâches, les mêmes observations, le même budget total et le même état initial, l'une conserve erreurs et provenance et met à jour sa règle, l'autre maintient sa règle fixe (ou dispose d'un journal non exploité). Séparer coût de l'apprentissage, erreur de prédiction hors échantillon, décisions et profils d'accessibilité futurs. Préenregistrer une tâche nouvelle, un seuil d'amélioration et des cas adverses où l'historique devient trompeur. Un gain à budget, précision et tâche comparables soutient un effet opérationnel dans ce modèle ; l'absence de gain réfute la prédiction spécifique, pas le principe de non-négation. Ne pas confondre une correction documentée avec un effet causal mesuré.

## 3. Protocoles T1–T6 de la note revue

Les expériences ci-dessous sont des modèles jouets ou des protocoles proposés, pas des résultats de laboratoire. Pour chaque essai, publier l'alphabet des opérations, les états initial/final (y compris auxiliaires), les coûts et unités, la tolérance, la règle de comparaison, le résultat et les limites. Les tests historiques conservent leur numérotation ; les références ci-dessous sont préfixées « revue ».

| ID (revue) | Dispositif ou modèle | Critère de décision |
|---|---|---|
| T1 — composition | Deux segments x→y→z payés C_1,C_2 ; tester aussi les mots AB/BA et une comptabilité non additive des pics | Vérifier H et l'inclusion à C_1+C_2 ; si un segment intermédiaire est incompatible, ne pas le concaténer. Un contre-exemple invalide l'hypothèse annoncée, pas toutes les théories de ressources. |
| T2 — référentiel/densité | Fixer un ensemble fini de devenirs Ω, une mesure μ, un état et deux conventions (R_0,λ) de la note originale ; calculer R,P et ρ_R pour les mêmes données | Publier une loi de transformation explicite si R,P et leurs unités sont définis. La densité d'accessibilité μ(A_C∩Ω)/μ(Ω) peut servir de contrôle mais ne se confond pas avec ρ_R. Sans définitions et loi, C2 reste ouverte. |
| T3 — fécondité et corrélation finale | Témoin U15.3 à deux cibles, relais et contrôleur, décrit ci-dessous | Même inventaire, même budget, même tâche : on exige une différence d'accessibilité et I(K:S)=0 à la fin. Distinguer résultat exact en alphabet restreint, résultat approché et portée physique U14. |
| T4 — coût d'indépendance/Pareto | Chaîne à coûts (1,3),(1,1),(1,0), raccourci acquis pour (2,1) puis (1,1) ; énumérer les chemins et les coûts | Comparer les profils supérieurs complets et les minima atteints. Le raccourci total (3,2) domine (3,4) si celles-ci sont les seules routes vers 3. Ne pas remplacer l'ensemble supérieur par ses minima dans un cas continu non fermé. Tester une borne U14 seulement après en avoir précisé la classe et la forme. |
| T5 — idempotence | Chaîne a→b→c à coût 1 par arête ; comparer Φ_1(a) à Φ_1²(a) ; contrôle avec monoïde (N,max,0) et coût 1 absorbant | Dans la version additive, c est absent de Φ_1(a) mais présent de sa double application ; le second renouvelle le budget. Dans le modèle max où la composition est admissible au même coût, l'idempotence suit de l'absorption et de l'identité. Cela ne prouve pas qu'elle exige toujours l'absorption. |
| T6 — scalarisation | Coûts incomparables (2,4) et (3,3) dans l'ordre produit ; comparer les décisions sur les deux budgets | Un scalaire d'ordre exact C≤D ssi J(C)≤J(D) est impossible pour ces deux coûts car R est totalement ordonné. Une simple injection ou une famille de monotones n'est pas la même revendication. Si J doit porter sur les états plutôt que les budgets, définir séparément comment il reconstruit chaque relation, sa continuité et son additivité. Une absence de candidat n'est pas une preuve. |

### T3 : dispositif qualitatif et témoin exact

Reprendre l'alphabet de [U15.3](U15_3.md#1-hypothèses-et-preuve-exacte) : deux cibles S_1,S_2, un relais Q, un contrôleur K ; tous thermiques et indépendants au départ, Hamiltoniens dégénérés H=0, trois auxiliaires purs |0> indépendants, chacun compté. Les portes A (chargement de Q), B_i (échange Q–S_i), D_i (Fredkin contrôlé par K=0) et, uniquement dans le contexte relationnel activable r, la préparation K par SWAP (une porte et un auxiliaire pur) constituent l'alphabet déclaré. Aucun SWAP direct non contrôlé vers les cibles, aucune post-sélection, aucun auxiliaire usé recyclé.

Budget commun : trois auxiliaires purs et trois portes. Tâche : deux cibles exactement pures, non corrélées entre elles et avec K, sans imposer à la référence un état final K pur. **Avec activation** : préparer K, puis D_1,D_2. Les deux cibles sont pures et K reste pur ; toutes les sorties sont produit car les échanges sont des permutations déterministes sur des facteurs indépendants. I(K:S_1S_2)=0 exactement ; le coût de préparation est payé. **Sans activation** : la branche initiale K=1 de probabilité 1/2 désactive chaque D_i. Le relais ne peut livrer deux puretés indépendantes en moins de deux chargements et deux échanges ; quatre portes sont nécessaires. La tâche n'est donc pas accessible sous trois portes, même avec trois auxiliaires. Il s'agit d'une fécondité relative à un budget et à un alphabet : elle est économique globalement (la tâche reste accessible à budget supérieur), pas extensive au sens d'inaccessibilité à tout budget. Elle est extensive à budget fixé si ce terme est défini par différence d'accessibilité locale. La préparation modifie une capacité effective puis celle-ci est utilisée deux fois ; cela ne démontre pas la non-simulabilité absolue ni une fermeture étoilée non triviale.

Ce témoin exact est déjà dérivable du résultat U15.3 pour m=2. Il confirme une existence de fécondité à budget fixé sans corrélation finale **dans le modèle restreint**. Il ne tranche pas une conjecture universelle limitée à des instances A4′/U14 de support fini ou d'alphabet thermique complet. À H=0, les ressources pures restent payées ; leur coût de support diverge. La variante fidèle à H≠0 de U15.3 offre une erreur et une corrélation bornées, pas I=0 exact pour le Fredkin lorsque p≠q et 0<η<1. Un SWAP direct entre deux qubits de même gap indépendants, thermique et froid, donne un contrôle expérimental exact I=0 avant/après et à support fini, mais consomme l'auxiliaire et ne constitue pas en soi un témoin de recrutement récursif.

Pour un essai matériel, préparer les entrées, exécuter les deux circuits sous budget identique, caractériser les populations et l'état joint par tomographie adaptée, publier la distance à la cible et un intervalle d'incertitude pour I. Un résultat compatible avec zéro à précision finie n'établit pas l'égalité mathématique à zéro. La preuve exacte ci-dessus demeure distincte du test expérimental. Inclure un troisième bras autorisant les SWAP directs : ce bras atteint (2,2) et élimine l'avantage de préparation, vérifiant la limite opérationnelle du résultat.

## 4. Trace de révision

- H : clarification de la somme ordonnée et de la portée de l'hypothèse.
- Note du 17 novembre : mise en relation explicitement conditionnelle, interprétation référencée par le porteur (INV-11 / CTRL-35), source intégrale à rattacher si disponible.
- T1–T6 : protocole qualitatif, critères et contrôles ; T3 muni d'une preuve exacte restreinte.
- Aucun changement des conclusions de [U15.4.3](U15_4_3.md) ni de leurs statuts épistémiques ; les résultats négatifs restent visibles. Aucune validation externe revendiquée.
