> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : THÉORÈME MAÎTRE / SYNTHÈSE U1–U13.** U14 condense la branche thermodynamique en quatre hypothèses structurelles, cinq lemmes et une preuve unique. Il distingue explicitement la troisième loi d’inatteignabilité de la branche Nernst, dont U13 montre qu’elle exige nécessairement une hypothèse basse énergie.

# Énoncé U14
Considérons une classe de systèmes thermométriques et de processus thermiques satisfaisant les hypothèses M1–M4 ci-dessous.
## M1 — Équilibre libre non trivial
Les états d’équilibre peuvent être fournis comme ressources libres en un nombre arbitraire de copies, mais la théorie libre ne permet pas d’extraire indéfiniment du travail par des cycles. Par conséquent les ressources d’équilibre sont **complètement passives**. Pour un système thermométrique non trivial, elles appartiennent aux classes Gibbs/KMS, incluant éventuellement la limite fondamentale $\beta=\infty$.
## M2 — Dynamique microscopique et comptabilité énergétique
Tout processus thermique déterministe admissible possède une dilation fermée réversible : en dimension de Hilbert, une unité $U$ ; dans la formulation algébrique, un automorphisme. La dynamique fermée conserve l’énergie totale :
$$
[U,H_{\mathrm{tot}}]=0.
$$
Les opérations ouvertes sont obtenues par ajout d’ancillas d’équilibre au même $\beta$, ajout éventuel de ressources auxiliaires explicitement comptabilisées, puis restriction/trace partielle.
## M3 — Budget fini d’une ressource de refroidissement définie indépendamment de la cible
Pour la branche d’inatteignabilité, les ressources auxiliaires sont comptabilisées par des monotones définis **avant** le choix de la cible. Dans la classe des opérations thermiques catalytiques à inverse de température $\beta$, on utilise notamment la *vacancy* de Wilming–Gallego :
$$
\mathcal V_\beta(\rho;H):=D\!\left(\gamma_\beta(H)\Vert\rho\right),
$$
qui est additive et monotone sous ces opérations. Un protocole de ressources finies satisfait donc $\mathcal V_\beta^{\mathrm{tot}}<\infty$. Comme $\gamma_\beta(H)$ est de plein support à $\beta<\infty$, toute ressource dont le support manque sur une partie du support thermique a $\mathcal V_\beta=+\infty$ et n’appartient pas à cette classe finie. Les états purs, pointeurs projectifs idéaux ou autres ressources de support déficient ne sont ainsi pas exclus par définition de $T=0$ : leur divergence est une propriété calculée du monotone. En dimension infinie, la fermeture qualitative correspondante utilise la fidélité des états KMS/thermiques. Les autres ressources physiques — fluctuations de travail, volume accessible, temps, dimension de machine, précision de mesure — restent explicitement comptabilisées lorsqu’une borne quantitative en temps/température est revendiquée.
## M4 — Régularité thermodynamique du bord pour la branche Nernst
Pour une famille externe $x$, la limite thermodynamique canonique possède une densité d’énergie fondamentale $e_0(x)$, une densité d’entropie résiduelle commune $s_0$, et une pression excédentaire
$$
q_x(\beta)=\ell_x(\beta)+\beta e_0(x)-s_0,
$$
où $\ell_x(\beta)=\lim V^{-1}\log Z_{V,x}(\beta)$. On suppose, uniformément dans la famille considérée :
- $q_x(\beta)\ge0$ ;
- $q_x$ est convexe et non croissante pour $\beta$ suffisamment grand ;
- $\sup_x q_x(\beta)\to0$ lorsque $\beta\to\infty$.
Cette dernière condition est volontairement plus faible que la loi de puissance $q=O(\beta^{-p})$ de U12.
# Lemmes
## L1 — Sélection de l’équilibre
Si une ressource libre disponible en copies arbitraires n’est pas complètement passive, un nombre fini de copies permet une extraction cyclique positive de travail ; répéter le protocole trivialise la théorie. La non-trivialité impose donc la passivité complète. Le théorème de Pusz–Woronowicz identifie les états complètement passifs aux états KMS/Gibbs ou fondamentaux dans le domaine approprié.
## L2 — Invariant énergétique
De $[U,H_{\mathrm{tot}}]=0$ découle
$$
\Delta E_S+\Delta E_B+\Delta E_W=0.
$$
Avec $Q=-\Delta E_B$ et $W=-\Delta E_W$,
$$
\boxed{\Delta E_S=Q+W}.
$$
## L3 — Monotonie thermodynamique
Une opération thermique à $\beta$ préserve l’état Gibbs/KMS de référence. Dans le secteur normal fini/type-I, la data processing inequality donne
$$
D(\Phi(\rho)\Vert\gamma_\beta)\le D(\rho\Vert\gamma_\beta).
$$
Comme
$$
F_\beta(\rho)-F_\beta(\gamma_\beta)=k_BT\,D(\rho\Vert\gamma_\beta),
$$
la libre énergie hors équilibre ne croît pas sous une opération libre sans ressource de travail externe. Avec batterie explicite, la même comptabilité produit les inégalités de travail/Clausius correspondantes.
## L4 — Monotone de refroidissement et témoin spectral
**L4a — Vacancy.** Pour une opération thermique catalytique,
$$
\boxed{\mathcal V_\beta(\rho_R;H_R)\ge \mathcal V_\beta(\rho_S;H_S).}
$$
La vacancy est additive. Si la cible $\rho_S$ n’a pas plein support alors que $\gamma_\beta(H_S)$ est de plein support, $D(\gamma_\beta\Vert\rho_S)=+\infty$. Une cible exacte $T=0$ de rang déficient ne peut donc pas être obtenue à partir d’un budget total de vacancy fini. Pour une cible Gibbs $\gamma_{\beta_S}(H_S)$ suffisamment froide, la vacancy croît sans borne lorsque $\beta_S\to\infty$, fournissant la version quantitative d’inatteignabilité dans cette classe.
**L4b — Témoin spectral fini, connu.** Indépendamment, pour $\widetilde Q>0$ sur $S\otimes A$,
$$
\boxed{\lambda_{\min}(\operatorname{Tr}_A\widetilde Q)\ge d_A\lambda_{\min}(\widetilde Q),}
$$
cas limite $p\to-\infty$ des inégalités d’anti-normes de Rastegin (2012). Appliqué à un produit initial puis à une unité globale, il redonne la borne U5 sur le plein support. Cette borne est conservée comme témoin reproductible et comme comptabilité pratique, **pas comme résultat nouveau**.
La forme infinie remplace la plus petite valeur propre par la fidélité : produit d’états fidèles, automorphisme/unité et restriction locale conservent la fidélité dans les cadres précisés par U6.
## L5 — Lemme minimal de Nernst par convexité
À un point de différentiabilité,
$$
u_x(\beta)-e_0(x)=-q'_x(\beta),
$$
$$
s_x(\beta)-s_0=q_x(\beta)-\beta q'_x(\beta).
$$
La convexité donne
$$
q_x(\beta/2)\ge q_x(\beta)-\frac\beta2 q'_x(\beta),
$$
donc
$$
0\le-\beta q'_x(\beta)
\le2\left[q_x(\beta/2)-q_x(\beta)\right]
\le2q_x(\beta/2).
$$
Par suite,
$$
\boxed{
0\le s_x(\beta)-s_0
\le q_x(\beta)+2q_x(\beta/2)
\longrightarrow0.}
$$
La convergence est uniforme lorsque $\sup_x q_x(\beta)\to0$.
# Théorème maître — conséquences
Sous M1–M3 :
**Loi 0 — équilibre thermique.** Les états d’équilibre libres sont organisés en classes KMS/Gibbs paramétrées par $\beta$ ; pour des systèmes thermométriques non triviaux,
$$
A\sim_TB\iff\beta_A=\beta_B,
$$
donc la relation d’équilibre est transitive.
**Loi 1 — conservation.** Le bilan énergétique est exactement
$$
\boxed{\Delta E_S=Q+W}.
$$
**Loi 2 — irréversibilité / ordre.** À température fixée,
$$
\boxed{D(\Phi(\rho)\Vert\gamma_\beta)\le D(\rho\Vert\gamma_\beta)},
$$
soit la monotonie de la libre énergie dans la classe libre, avec la forme de Clausius lorsque le bilan énergétique est explicité.
**Loi 3A — inatteignabilité.** Dans la classe catalytique thermique, la monotonie de la vacancy impose
$$
\mathcal V_\beta^{\mathrm{ressources}}\ge\mathcal V_\beta^{\mathrm{cible}}.
$$
Une cible exacte $T=0$ de support déficient possède une vacancy infinie ; elle exige donc une ressource de vacancy infinie ou une limite infinie. Pour une cible thermique $\gamma_{\beta_S}$, la vacancy diverge lorsque $\beta_S\to\infty$, ce qui quantifie l’approche du zéro absolu. En parallèle, dans la fermeture finie U5, le témoin spectral connu donne
$$
\lambda_{\min}(\rho'_S)\ge\lambda_{\min}(\rho_S)\exp[-C_{\mathrm{supp}}^{\mathrm{tot}}]>0,
$$
avec $C_{\mathrm{supp}}$ interprété comme une comptabilité auxiliaire plutôt que comme une nouvelle mesure fondamentale.
Sous M4 en plus :
**Loi 3B — Nernst.** L’entropie spécifique converge uniformément vers la valeur résiduelle commune :
$$
\boxed{s(T,x)\to s_0},
$$
et donc
$$
\boxed{s(T,x_1)-s(T,x_2)\to0.}
$$
La libre énergie vérifie
$$
f_x(T)=e_0(x)-Ts_0-Tq_x(1/T)
=e_0(x)-Ts_0+o(T).
$$
Si l’on ajoute une régularité de second ordre telle que $\beta^2q''(\beta)\to0$ — obtenue notamment dans U8, U10, U11 ou par variation régulière dans U12 — alors
$$
\boxed{C_V/V\to0.}
$$
# Routes suffisantes vers M4 déjà démontrées
M4 n’est pas un axiome microscopique unique. U8–U12 donnent plusieurs routes indépendantes pour la vérifier :
- **U8** : gap uniforme + dégénérescence fondamentale commune ;
- **U9** : continuité de l’entropie spécifique au bord + dualité canonique/microcanonique ;
- **U10** : comptage de défauts locaux $N_{V,n}\le g_V(aV)^n/n!$ ;
- **U11** : comptage intégré de modes gapless $G_V(\Omega)/V\le A\Omega^p$, $p>0$ ;
- **U12** : pression excédentaire $q(\beta)=O(\beta^{-p})$, $p>0$, y compris phases critiques fortement interactives.
U14 montre que ces constructions sont des **certificats** d’une condition plus faible : $q(\beta)\to0$ sous convexité.
# Minimalité — contre-exemples obligatoires
U13 démontre qu’on ne peut pas supprimer toute hypothèse de bord :
1. changer la dégénérescence fondamentale donne une différence d’entropie $\to\ln2$ ;
2. un secteur de $e^{cV}$ états à énergie totale $O(1)$ donne $q(\beta)=c$ et une entropie spécifique non nulle pour tout $T>0$ après la limite thermodynamique ;
3. les limites $V\to\infty$ et $T\to0$ peuvent alors ne pas commuter.
Ainsi
$$
\boxed{\text{QM générique}+\text{état fondamental}\not\Rightarrow\text{Nernst universel}.}
$$
M4 est donc une condition de classe physique, pas une réparation ad hoc.
# Forme condensée
$$
\boxed{
\begin{array}{c}
\text{équilibre libre non trivial}\\
+\ \text{dynamique fermée réversible et énergétique}\\
+\ \text{budget fini de monotones de ressources indépendamment définis}\\
+\ \text{régularité basse énergie pour Nernst}
\end{array}
\Longrightarrow
\begin{array}{c}
\text{loi 0}\\
\text{loi 1}\\
\text{loi 2}\\
\text{loi 3A + loi 3B}
\end{array}}
$$
# Ce qui est démontré / ce qui ne l’est pas
**DÉMONTRÉ dans la classe U14 :** l’architecture commune ci-dessus implique les quatre lois, avec séparation logique entre inatteignabilité et Nernst.
**NON REVENDIQUÉ :** que toute mécanique quantique imaginable satisfasse M4 ; que toute forme historique de la troisième loi soit universellement équivalente ; que le budget vectoriel de ressources possède déjà une jauge scalaire optimale unique ; ou que la théorie soit nouvelle au sens de priorité scientifique avant revue bibliographique et expertise externe.
# Provenance
U14 condense sans effacer : U1, U1.1, U2, U3, U4, U5, U6, U7, U8, U9, U10, U11, U12 et le no-go U13. Les témoins numériques restent dans leurs branches respectives ; U14 doit avoir son propre témoin minimal consacré aux implications réellement nouvelles de la condensation, notamment le lemme $q\to0$ sans hypothèse de loi de puissance.
# Amendement canonique U14.1 — loi 2 one-shot et loi 3 en temps fini

	**Fermeture de portée.** U14 intègre désormais explicitement les secondes lois quantiques généralisées et le pont ressources→temps. Ces éléments sont de la littérature établie et ne sont pas revendiqués comme nouveaux.

## Loi 2 — formulation renforcée
Pour les états diagonaux en énergie, le régime one-shot/catalytique utilise la famille
$$
F_\alpha(\rho,H)=T D_\alpha(\rho\Vert\gamma_\beta)-T\ln Z_H,
$$
avec
$$
\boxed{F_\alpha(\rho,H)\ge F_\alpha(\sigma,H)\quad\forall\alpha\ge0}
$$
pour une transition catalytique thermique admissible dans le domaine de Brandão et al. La limite $\alpha\to1$ redonne la libre énergie ordinaire.
Avec cohérence énergétique, les $F_\alpha$ ne suffisent pas : les opérations thermiques imposent aussi des monotones d’asymétrie temporelle, par exemple
$$
A_\alpha(\rho)=D_\alpha(\rho\Vert\mathcal D_H(\rho)),
$$
qui ne peuvent pas augmenter. U14 ne revendique aucune caractérisation complète arbitraire des transformations cohérentes ; il conserve ces contraintes comme famille indépendante.
## Loi 3A — formulation temporelle renforcée
La preuve par vacancy donne l’inatteignabilité sous budget fini de ressources. Pour obtenir la formulation **temps fini**, U14 ajoute explicitement le théorème de Masanes–Oppenheim : sous une machine thermique régulière, tout temps fini ne donne accès qu’à un volume de bain $V(t)<\infty$ et une fluctuation de travail pire cas $w_{\max}(t)<\infty$. Leur borne en ressources implique alors
$$
\boxed{T'_S(t)>0\qquad\forall t<\infty.}
$$
Pour une interaction locale et un bain de rayonnement en $D$ dimensions, leurs hypothèses donnent asymptotiquement
$$
T'_S(t)\ge K t^{-(2D+1)},
$$
et donc en $D=3$,
$$
T'_S(t)\ge Kt^{-7}>0.
$$
Ce taux est un corollaire de cette classe de machine/bain, pas une loi universelle.
## Formulation canonique finale de portée
- **Loi 0** : passivité complète/KMS-Gibbs ;
- **Loi 1** : conservation énergétique exacte ;
- **Loi 2** : famille de monotones thermodynamiques ; $F_1$ est la limite macroscopique, $\{F_\alpha\}$ est requise dans le secteur one-shot diagonal, et des contraintes d’asymétrie supplémentaires existent avec cohérence ;
- **Loi 3A** : vacancy/ressources finies $\Rightarrow$ zéro absolu inaccessible ; machine thermique régulière $\Rightarrow$ zéro absolu inaccessible en temps fini ;
- **Loi 3B** : M4 $\Rightarrow$ Nernst par le lemme convexe de pression.

## Addenda de correction de la source

**Correction canonique U14.2 :** pour la loi 1 en couplage fort, lire l’invariant exact `$\Delta E_S+\Delta E_B+\Delta E_I=W_{\rm ext}$; la forme $\Delta E_S=Q+W$ exige $\Delta E_I=0$ aux extrémités ou une convention explicite d’allocation. Pour la branche infinie/KMS, la fidélité est préservée dans le secteur normal GNS fixé, mais **n’est pas** un critère universel de $T>0$`; un état fondamental peut être fidèle localement. Voir la page **24 — U14.2 : couplage fort et portée infinie/KMS**.
