> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**U7 — fermeture du loophole de mesure projective idéale dans la classe de ressources finies.** Une post-sélection mathématique peut réduire le support, mais sa réalisation physique comme mesure répétable avec record classique parfait exige une ressource frontière : pointeur non fidèle, dimension d'appareil infinie, ou approximation non nulle.

# 1. Loophole abstrait
Pour un projecteur $P$, l'opération conditionnelle
$$
\rho\mapsto\rho_P=\frac{P\rho P}{\operatorname{Tr}(P\rho)}
$$
peut transformer un état fidèle en état de support réduit.
Une mesure d'énergie idéale suivie d'une post-sélection sur le niveau fondamental donnerait donc formellement un état $T=0$ avec probabilité $p_g=\operatorname{Tr}(P_g\rho)>0$ pour un état thermique à température finie.
Ce calcul est correct comme règle conditionnelle ; la question U7 est le coût de sa **réalisation physique exacte**.
# 2. Théorème de pointeur fini fidèle
Considérons une observable non dégénérée avec au moins deux valeurs propres $|i\rangle$. Soit un appareil fini $M$ initialisé dans un état fidèle
$$
\sigma_M>0.
$$
Supposons une mesure idéale répétable réalisée par une unité $U$ telle que, lorsque le système arrive dans $|i\rangle$, le résultat $i$ est enregistré et le système reste dans $|i\rangle$.
Pour l'entrée
$$
|i\rangle\langle i|\otimes\sigma_M,
$$
la marginale finale du système est pure $|i\rangle\langle i|$. Toute extension bipartite d'une marginale pure factorise, donc
$$
U\left(|i\rangle\langle i|\otimes\sigma_M\right)U^\dagger
=|i\rangle\langle i|\otimes\sigma_i.
$$
L'unitarité conserve le spectre non nul de l'état global. En dimension finie, $\sigma_i$ possède donc le même spectre que $\sigma_M$ et reste fidèle :
$$
\operatorname{supp}\sigma_i=\mathcal H_M.
$$
Un record classique parfait exige que les états de pointeur associés à deux résultats distincts soient parfaitement distinguables, donc à supports orthogonaux :
$$
\operatorname{supp}\sigma_i\perp\operatorname{supp}\sigma_j,
\qquad i\neq j.
$$
C'est impossible si chaque support vaut tout $\mathcal H_M$.
Ainsi
$$
\boxed{\text{appareil fini + pointeur fidèle}\ \not\Rightarrow\ \text{mesure projective répétable exacte à records parfaits}.}
$$
# 3. Ressource nécessaire
Pour obtenir une mesure projective exacte, au moins une hypothèse doit sortir de la fermeture finie U5/U6 :
- **pointeur initial non fidèle** (par exemple état ready pur) : U5 lui attribue $C_{supp}=\infty$ ;
- **appareil de dimension infinie** : la coordonnée taille/dimension du budget U4 diverge ;
- **mesure seulement approximative** : les records ne sont pas parfaitement orthogonaux et la projection n'est pas exacte ;
- abandon de répétabilité/idéalité, qui change le protocole et doit être analysé séparément.
Le modèle de mesure de von Neumann utilise précisément un état ready pur et des états de pointeur orthogonaux.
# 4. Corollaire thermodynamique
Une post-sélection idéale sur l'état fondamental ne constitue donc pas un protocole de refroidissement à coût fini **dans la fermeture U** si sa mesure exacte réclame une ressource de pointeur non fidèle ou une dimension infinie.
Le succès probabiliste n'abolit pas le coût frontière : la probabilité $p_g$ peut être non nulle, mais l'instrument exact qui rend le branchement parfaitement projectif n'est pas gratuit.
# 5. Important : ce qui n'est pas démontré
U7 ne prouve pas que toute mesure quantique approximative coûte une quantité universelle donnée. Il établit un **no-go exact** pour le modèle idéal répétable à appareil fini fidèle.
Des POVM, mesures non répétables et protocoles faibles peuvent être implémentés avec ressources finies ; ils doivent alors être évalués selon leur erreur, leur probabilité de succès, la pureté générée et le coût de remise à zéro.
# 6. Budget de mesure candidat
Ajouter au budget vectoriel U4 :
$$
\mathbf C_{meas}=(d_M,C_{supp}(\sigma_M),\epsilon_{meas},p_{succ}^{-1},I_{record},C_{reset},\ldots).
$$
Pour une préparation exacte par post-sélection, U7 montre qu'au moins une coordonnée frontière doit être atteinte dans le modèle idéal : $C_{supp}=\infty$, $d_M=\infty$ ou $\epsilon_{meas}\to0$ via une limite de ressources à quantifier.
# 7. Statut
**DÉRIVATION exacte dans le modèle de mesure idéal répétable avec appareil fini.**
Cette étape ferme le contre-exemple « mesure projective gratuite » à l'inatteignabilité en rendant explicite la ressource cachée du pointeur/record.
