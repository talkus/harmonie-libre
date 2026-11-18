> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**But** — Tester scientifiquement si les lois 0, 1, 2 et 3 de la thermodynamique peuvent être obtenues comme conséquences d'une seule structure d'accessibilité physique : états, transformations admissibles, invariants, monotones et coût fini.

# Principe directeur
Une théorie unifiée thermodynamique candidate est organisée autour de la relation
$$
X\preceq_C Y
$$
qui signifie : il existe une transformation physique admissible $\Phi$ envoyant $X$ vers $Y$ sous un budget de ressources/coût $\mathcal C[\Phi]\le C$.
Le projet doit distinguer strictement : **MATH**, **DÉRIVATION**, **HYPOTHÈSE**, **TEST**, **OBSTRUCTION**.
# Cible d'unification
- Loi 0 : caractériser les états et classes d'équilibre thermique.
- Loi 1 : faire apparaître la conservation de l'énergie comme invariant des transformations admissibles fermées.
- Loi 2 : faire apparaître l'ordre irréversible via des monotones d'accessibilité, notamment entropie / libre énergie / entropie relative selon le régime.
- Loi 3 : faire de $T=0$ une frontière inaccessible à toute transformation de coût fini.
# Discipline méthodologique
Une analogie avec « différence → relation → transformation » n'est pas une preuve. Le projet ne sera considéré comme scientifiquement unificateur que si les quatre lois découlent d'un ensemble commun d'axiomes plus compact, avec limites classiques/quantique reproduites et critères de falsification explicites.
# Références de départ
- Lieb & Yngvason : accessibilité adiabatique et construction axiomatique de l'entropie.
- Pusz & Woronowicz : passivité complète et états KMS/états fondamentaux.
- Brandão et al. : lois secondes quantiques / contraintes de transformations.
- Masanes & Oppenheim : inatteignabilité du zéro absolu avec ressources finies.
# Statut initial
**ARCHITECTURE CANDIDATE.** Les lois 0–2 ont des raccords mathématiques établis dans des formalismes existants. La véritable nouveauté à tester est de savoir si une même notion d'accessibilité avec coût peut inclure la loi 3 sans la réintroduire comme axiome indépendant.
00 — Axiomes d’accessibilité et coût
01 — Lois 0 et 1 : équilibre et invariant énergétique
02 — Loi 2 : ordre, entropie relative et libre énergie
03 — Loi 3 : zéro absolu comme frontière de coût infini
04 — Théorème unificateur candidat U0
05 — Falsification, benchmarks et journal
06 — U1 : unification finie des lois 0–3
07 — U1.1 : coût spectral dérivé et divergence vers T=0
# 22 août 2026 — Jalon U1 confirmé dans la classe finie

	**DÉRIVATION + TEST reproductible.** Le projet possède maintenant une unification interne explicite des lois 0–3 pour une classe finie d'opérations thermiques à température finie. Cette réussite est réelle mais bornée : elle n'est pas encore une preuve universelle de toute la thermodynamique.

Pour
$$
\Phi_\beta(\rho_S)=\operatorname{Tr}_B\left[U(\rho_S\otimes\gamma_B(\beta))U^\dagger\right],
$$
avec bain fini, $\beta<\infty$ et $[U,H_S+H_B]=0$, la même classe d'opérations donne :
- loi 0 : $\gamma_S(\beta)$ est point fixe/libre ;
- loi 1 : conservation exacte de l'énergie totale dans la dilatation ;
- loi 2 : contraction $D(\Phi(\rho)\Vert\gamma_\beta)\le D(\rho\Vert\gamma_\beta)$ ;
- loi 3 : les états strictement positifs restent strictement positifs après toute composition finie, donc l'état exact $T=0$ de rang déficient n'est pas accessible depuis un état thermique de rang plein avec seulement des ressources thermiques finies à température finie.
Borne :
$$
\lambda_{\min}(\Phi_\beta(\rho))\ge d_B\lambda_{\min}(\rho)\lambda_{\min}(\gamma_B)>0.
$$
Contrôle négatif conservé : une ressource pure déjà à $T=0$ permet un SWAP exact vers l'état fondamental ; l'hypothèse de ressources libres à température finie est donc essentielle et falsifiable.
Référence exécutable : PR brouillon GitHub #292 et $research/thermodynamic-accessibility/thermodynamic_u1_witness.py$.
**Étapes suivantes obligatoires :** catalyseurs, pureté comme ressource, dimensions infinies, limite thermodynamique, coût/temps continu et raccord axiomatique complet à l'accessibilité macroscopique.
## Extension U1.1 — coût spectral et divergence vers le zéro absolu
À partir de la borne U1, définir pour chaque bain fini à température finie
$$
a_B=d_B\lambda_{\min}(\gamma_B),\qquad c_B=-\ln a_B\ge0.
$$
Après une séquence de bains,
$$
\lambda_{\min}(\rho_n)\ge\lambda_{\min}(\rho_0)e^{-C},\qquad C=\sum_k c_{B_k}.
$$
Par conséquent, atteindre une plus petite valeur propre $\varepsilon$ exige nécessairement
$$
\boxed{C\ge\ln\frac{\lambda_{\min}(\rho_0)}{\varepsilon}}.
$$
Donc $\varepsilon\to0$ impose $C\to\infty$. Pour une cible thermique qubit de gap $\Delta$, le coût requis croît asymptotiquement comme $\beta'\Delta+O(1)$.
**Statut : DÉRIVATION + TEST, borne nécessaire.** U1.1 ne prétend pas encore être le coût opérationnel optimal ; il fournit une jauge de ressources dérivée du bain lui-même et un pont quantitatif entre l'inaccessibilité de rang de U1 et une divergence de coût vers $T=0$.
08 — U2 : démonstration commune des quatre lois thermodynamiques
# 22 août 2026 — U2 : démonstration commune consolidée

	**DÉMONTRÉ dans la classe U2.** Les quatre lois ne sont plus traitées comme quatre raccords séparés : elles sont dérivées d’un même cadre opérationnel fini. Référence de recherche : PR brouillon GitHub **#293** et page **08 — U2**.

Le noyau commun est :
$$
\boxed{\text{équilibre libre non trivial}+\text{conservation énergétique}+\text{réversibilité microscopique}+\text{ressources finies}.}
$$
Il donne :
- **loi 0** — la non-trivialité des ressources libres impose la passivité complète ; en dimension finie, celle-ci sélectionne Gibbs/KMS. Deux systèmes sont en équilibre thermique exactement lorsqu’ils appartiennent à la même classe $\beta$, d’où la transitivité ;
- **loi 1** — $[U,H_{tot}]=0$ implique exactement $\Delta E_S=Q+W$ ;
- **loi 2** — la préservation de Gibbs et le data processing donnent $D(\Phi(\rho)\Vert\gamma)\le D(\rho\Vert\gamma)$, donc libre énergie non croissante pour une opération libre et forme de Clausius ;
- **loi 3 (inatteignabilité)** — la stricte positivité est conservée quantitativement et $\lambda_{\min}(\rho_n)\ge\lambda_{\min}(\rho_0)e^{-C}$ ; ainsi $T=0$ exact exige $C=\infty$.
Le témoin indépendant vérifie numériquement un modèle qubit : Gibbs fixe exactement, conservation énergétique à la précision machine, contraction de l’entropie relative et borne spectrale respectée.
**Frontière scientifique :** U2 démontre la forme d’inatteignabilité de la loi 3 dans cette classe. La formulation de Nernst/Heat Theorem, les catalyseurs généraux de pureté, les réservoirs infinis arbitraires, transitions de phase et la limite macroscopique complète restent des extensions à établir, pas des résultats acquis.
09 — U3 : catalyseurs exacts, réservoirs infinis réguliers et fermeture macroscopique
10 — U4 : no-go de la libre énergie seule et budget vectoriel de ressources
11 — U5 : fermeture finie par coût de support généralisé
12 — U6 : fermeture infinie par fidélité KMS
13 — U7 : fermeture de la post-sélection et coût de mesure idéale
14 — U8 : Nernst spectral et capacité calorifique à basse température
15 — U9 : limite thermodynamique par entropie spécifique et dualité de Legendre
16 — U10 : fermeture microscopique par comptage de défauts locaux
17 — U11 : excitations collectives gapless par densité d’états
18 — U12 : fermeture critique fortement interactive par pression excédentaire
19 — U13 : no-go d’une troisième loi universelle sans hypothèses de bord
20 — U14 : théorème maître d’accessibilité thermodynamique
# 22 août 2026 — U14 devient la synthèse canonique

	**SYNTHÈSE CANONIQUE.** U14 condense U1–U13 en quatre hypothèses structurelles et un théorème maître. Les pages antérieures restent la provenance détaillée, les preuves intermédiaires, les témoins et les contre-exemples ; elles ne sont pas effacées.

Les quatre hypothèses maîtresses sont :
1. équilibre libre non trivial $\Rightarrow$ passivité complète/KMS-Gibbs ;
2. dynamique fermée réversible avec conservation de l’énergie ;
3. ressources de frontière/support explicitement comptabilisées ;
4. pour la branche Nernst, pression excédentaire $q_x(\beta)$ convexe, décroissante et $\sup_xq_x(\beta)\to0$ avec entropie résiduelle commune $s_0$.
Le nouveau lemme minimal est
$$
0\le s_x(\beta)-s_0\le q_x(\beta)+2q_x(\beta/2)\to0,
$$
qui montre qu’aucune loi de puissance n’est nécessaire pour Nernst : la simple disparition convexe de l’excès de pression suffit.
La formulation condensée est
$$
\boxed{\text{M1--M3}\Rightarrow\text{lois 0,1,2 et 3A (inatteignabilité)}}
$$
et
$$
\boxed{\text{M1--M4}\Rightarrow\text{lois 0,1,2 et 3A+3B (Nernst)}}.
$$
U13 reste le no-go qui prouve qu’on ne peut pas supprimer universellement M4. Référence reproductible : **PR brouillon GitHub #307**, fichiers $THERMODYNAMIC_U14_MASTER_THEOREM.md$ et $thermodynamic_u14_master_theorem_witness.py$.
**Frontière de publication :** la cohérence mathématique interne est établie dans la classe définie ; la priorité/nouveauté scientifique et la formulation finale publiable exigent encore revue bibliographique dédiée et expertise externe.
21 — Audit bibliographique de nouveauté et revue adverse de U14
22 — Revue externe : reviewers, paquet et messages de sollicitation
23 — U14.1 : secondes lois quantiques et pont ressources→temps
24 — U14.2 : couplage fort et portée infinie/KMS
# 22 août 2026 — Pont relationnel v0.7 : frontière canonique

	**Statut révisé.** U14 demeure une synthèse thermodynamique interne solide dans ses hypothèses, mais **ne doit plus être présentée comme la preuve de la théorie unificatrice relationnelle**. Le programme R1–R6/R7 cherche précisément le pont manquant et conserve les no-go lorsqu’une structure physique n’est pas identifiable depuis le noyau relationnel seul.

## Ce qui est maintenant relié sans importer Gibbs au départ
### Altérité-support → frontière inaccessible
Pour une interaction finie avec état système et ancilla de plein support,
$$
\lambda_{\min}(\Phi(\rho_A))\ge d_B\lambda_{\min}(\rho_A)\lambda_{\min}(\sigma_B)>0.
$$
Une suite finie de telles interactions reste dans l’intérieur de l’espace d’états. Le raccord à la troisième loi intervient seulement ensuite, lorsqu’un état $T=0$ est identifié à une cible de support déficient. Une ressource pure/frontière gratuite constitue un contrôle négatif explicite.
### No-go Gibbs sans générateur distingué
Si l’état d’équilibre unique doit être covariant sous toutes les conjugaisons unitaires et qu’aucune dynamique/charge distinguée n’est fournie, alors il commute avec tout $U$ et vaut nécessairement $I/d$. Le noyau relationnel totalement symétrique ne sélectionne donc pas un Gibbs fini non trivial.
### Temps → générateur additif
Une représentation temporelle réversible continue donne $U_t=e^{-itH}$. Pour deux systèmes non interactifs,
$$
U_{AB}(t)=U_A(t)\otimes U_B(t)
\Rightarrow
H_{AB}=H_A\otimes I+I\otimes H_B.
$$
L’énergie peut ainsi entrer comme interprétation physique du générateur temporel, mais l’identification « générateur = énergie physique » et la conservation sous interactions restent des données de représentation à justifier.
## Gibbs généralisé comme théorème de composition conditionnel
Soit $q\in\mathbb R^m$ un ensemble complet de distinctions additives pertinentes. Si les systèmes réellement indépendants factorisent, si leurs descripteurs s’additionnent, et si une même règle positive régulière $h$ décrit les poids de composition, alors
$$
h(q+r)=h(q)h(r).
$$
Sous continuité/mesurabilité,
$$
\boxed{h(q)=e^{-\lambda\cdot q}},
$$
d’où
$$
\boxed{\rho_{eq}\propto e^{-\sum_a\lambda_aQ_a}}.
$$
Le Gibbs canonique $e^{-\beta H}$ n’est que le cas où l’énergie est la seule charge pertinente. Les charges supplémentaires conduisent à un Gibbs généralisé ; les charges non commutatives et le couplage fort restent hors de cette dérivation élémentaire.
## Relation nulle et localité
- État : $I(A:B)=0\iff\rho_{AB}=\rho_A\otimes\rho_B$.
- Processus : Choi factorisé $\iff\Phi_{AB}=\Phi_A\otimes\Phi_B$.
- Le non-signalling seul n’est pas une relation nulle : une cause commune peut créer des corrélations sans signal.
- Médiation : $I(A:C\mid B)=0$ est le candidat standard de chaîne de Markov quantique exacte.
## Budget exact de relation dans le secteur additif
Pour $H_{AB}=H_A+H_B$,
$$
\boxed{F_\beta(\rho_{AB})-F_\beta(\rho_A)-F_\beta(\rho_B)=\beta^{-1}I(A:B)}.
$$
Et pour trois systèmes,
$$
\boxed{F_\beta(ABC)+F_\beta(B)-F_\beta(AB)-F_\beta(BC)=\beta^{-1}I(A:C\mid B)}.
$$
Ces identités donnent un raccord quantitatif exact entre corrélation et libre énergie dans ce secteur, sans constituer de nouvelles lois.
## Nouvelle cible R7+
La cible n’est plus « refaire U14 ». Elle est :
1. définir les relations nulles/actives indépendamment de la thermodynamique ;
2. dériver ou réfuter les conditions de factorisation et de composition qui produisent la famille exponentielle ;
3. mesurer la **fécondité** comme surplus de convertibilité $\mathfrak F_c(x)=\mathcal A_c(x)\setminus\mathcal A(x)$ ;
4. chercher une borne reliant ce surplus aux budgets de monotones, corrélations et travail sur toute la trajectoire, y compris en présence de catalyse.
# 22 août 2026 — F4 : budget relationnel et catalyse
F4 complète le pont v0.7 en séparant **nouvelle convertibilité** et **corrélation finale**.
Pour une catalyse exacte non corrélée, le partenaire peut ouvrir une transformation tout en revenant exactement à son état et avec $I(S:C)_{final}=0$ ; la corrélation finale n’est donc pas un budget universel de fécondité.
En revanche, si un catalyseur conserve sa marginale mais reste corrélé à la cible dans un secteur à Hamiltonien additif et libre énergie non croissante,
$$
\boxed{\beta^{-1}I(S:C)_{final}\le F_\beta(\rho_S)-F_\beta(\sigma_S).}
$$
Cette borne compte la corrélation résiduelle à la sortie. Elle ne mesure pas l’ensemble des nouveaux devenirs catalytiques et ne remplace pas les familles de secondes lois/monotones nécessaires dans les régimes exacts appropriés.
Conséquence méthodologique : les futures extensions catalytiques de U14 doivent déclarer séparément **type de restitution du catalyseur**, corrélations finales permises, erreur, dimension/ressource du catalyseur et classe d’opérations. Les régimes exact, corrélé et approximatif ne doivent plus être mélangés.
24 — U14.2 : fermeture cohérente par catalyse corrélée
# 22 août 2026 — U14.2 ferme conditionnellement le secteur cohérent catalytique

	**NOUVEAU JALON — portée bornée.** La lacune des états cohérents est maintenant conditionnellement fermée dans le régime des opérations thermiques avec catalyse corrélée à précision arbitraire, sur la base du théorème Shiraishi–Takagi arXiv:2510.05642 (prépublication au 22 août 2026). Cela ne constitue ni une fermeture du problème exact non catalysé, ni une dérivation depuis la théorie relationnelle.

La condition structurelle est
$$
\mathcal C(\sigma)\subseteq\mathcal C(\rho),
$$
et, sous cette condition, la condition quantitative devient
$$
\boxed{F_\beta(\rho)\ge F_\beta(\sigma)}.
$$
Notation compacte du projet :
$$
\Omega^{\mathrm{ccTO}}_\beta(\rho\to\sigma)=
\begin{cases}
+\infty,&\mathcal C(\sigma)\nsubseteq\mathcal C(\rho),\\
F_\beta(\sigma)-F_\beta(\rho),&\text{sinon}.
\end{cases}
$$
Dans le régime du théorème externe, la convertibilité à précision arbitraire équivaut à $\Omega^{\mathrm{ccTO}}_\beta\le0$.
24 — U14.2 : fermeture cohérente par catalyse corrélée
**Nouvelle priorité U14.3 :** établir une borne de divergence de ressource catalytique $R_{cat}(\varepsilon,\delta)\to\infty$ lorsque l’on approche une cible exacte $T=0$ avec erreur $\varepsilon\to0$ et corrélation résiduelle $\delta\to0$. Cette étape est nécessaire pour empêcher qu’une ressource infinie soit dissimulée dans le catalyseur.
25 — U14.3 : coût de support catalytique au bord de rang
# 22 août 2026 — U14.3 : divergence catalytique de support démontrée dans le secteur fini

	**DÉRIVATION FERMÉE.** La nouvelle lacune ouverte par U14.2 possède déjà une fermeture partielle forte : pour toute dilatation unitaire finie avec auxiliaires finis explicitement comptés, la distance à une cible de rang déficient est minorée par le budget total de support. Les corrélations finales avec un catalyseur n’annulent pas la borne.

Pour $\operatorname{rank}(\sigma)=r<d_S$,
$$
\boxed{T(\rho'_S,\sigma)\ge(d_S-r)\lambda_{\min}(\rho_S)e^{-C_{\rm supp}}}
$$
et donc
$$
\boxed{C_{\rm supp}\ge\max\!\left\{0,\ln\frac{(d_S-r)\lambda_{\min}(\rho_S)}{\varepsilon}\right\}}
$$
pour une erreur au plus $\varepsilon$.
Par conséquent $\varepsilon\to0$ impose $C_{\rm supp}\to\infty$. Un catalyseur de rang déficient est compté directement avec coût $+\infty$.
25 — U14.3 : coût de support catalytique au bord de rang
Référence de travail : issue GitHub **#340**, PR brouillon **#341**, témoin `U14_3_CATALYTIC_SUPPORT_WITNESS_PASS`.
**Frontière suivante :** généraliser cette divergence aux catalyseurs/réservoirs véritablement infinis avec contraintes physiques finies d’énergie, moments, localité et temps.
