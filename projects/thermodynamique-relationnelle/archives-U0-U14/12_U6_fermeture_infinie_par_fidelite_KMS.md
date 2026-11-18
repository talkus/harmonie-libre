> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**U6 — extension infinie exacte.** En dimension infinie, la quantité $\lambda_{\min}$ n'est plus adaptée : un état thermique normal à température finie peut avoir des valeurs propres qui s'accumulent vers zéro. La bonne propriété qualitative est la **fidélité** : absence de noyau / support total.

# 1. Cas type-I normal : réservoir infini avec matrice densité Gibbs
Soit un système $S$ et un auxiliaire/réservoir séparable $A$. Supposons
$$
\rho_S>0,
$$
et que l'état auxiliaire normal $\eta_A$ soit **fidèle**, c'est-à-dire
$$
\ker\eta_A=\{0\}.
$$
Cela inclut un état Gibbs normal
$$
\gamma_A(\beta)=\frac{e^{-\beta H_A}}{Z_A},\qquad 0<\beta<\infty,
$$
lorsque $Z_A<\infty$ : l'exponentielle est strictement positive et la matrice densité a un noyau nul, même si $\inf\sigma(\gamma_A)=0$.
Considérons une unité globale arbitraire $U$ et
$$
X=U(\rho_S\otimes\eta_A)U^\dagger.
$$
Le produit d'états fidèles est fidèle et l'unité conserve le noyau nul.
Pour tout vecteur non nul $|\psi\rangle\in\mathcal H_S$,
$$
\langle\psi|\rho'_S|\psi\rangle
=\operatorname{Tr}\left[X\left(|\psi\rangle\langle\psi|\otimes I_A\right)\right],
$$
où
$$
\rho'_S=\operatorname{Tr}_A X.
$$
Puisque $X$ est fidèle et $|\psi\rangle\langle\psi|\otimes I_A$ est un projecteur non nul, cette trace est strictement positive. Donc
$$
\boxed{\rho'_S\ \text{est fidèle}.}
$$
Ainsi une unité globale avec un réservoir normal fidèle à température finie, suivie d'une trace partielle, ne peut pas préparer exactement un état de support strictement plus petit.
# 2. Corollaire zéro absolu
Pour un Hamiltonien non trivial, l'état thermique exact à $T=0$ est supporté sur le sous-espace fondamental et n'est pas fidèle sur l'espace total dès qu'il existe des niveaux excités.
Donc
$$
\boxed{\text{état fidèle à }T>0\ +\ \text{ressources thermiques fidèles}\ \not\to\ T=0\text{ exact}.}
$$
Ce résultat reste vrai même si le réservoir possède une dimension de Hilbert infinie ; contrairement à U5, il ne donne pas une borne quantitative sur la distance à $T=0$.
# 3. Forme algébrique $C^*$ / thermodynamic limit
Soit une algèbre d'observables $\mathcal A$ et un état fidèle $\omega$.
Pour toute automorphisme $\alpha\in\operatorname{Aut}(\mathcal A)$,
$$
\omega'(A)=\omega(\alpha^{-1}(A))
$$
est encore fidèle : si $A\ge0$ et $\omega'(A)=0$, alors $\omega(\alpha^{-1}(A))=0$ et la fidélité implique $A=0$.
La restriction d'un état fidèle à une sous-algèbre unitaire est également fidèle.
Ainsi, si l'état global initial d'une phase KMS à $0<\beta<\infty$ est fidèle dans la représentation physique considérée, une dynamique fermée par automorphisme suivie de l'observation/restriction d'un sous-système ne peut produire un état local non fidèle.
Les KMS normales sur un facteur sont fidèles ; plus généralement la normal extension d'un état KMS dans sa représentation GNS est fidèle. Le projet doit garder cette condition de fidélité explicite lorsque plusieurs phases ou algèbres non simples sont présentes.
# 4. Phase transitions
La présence de plusieurs phases KMS au même $\beta$ ne détruit pas la loi 0 : la classe d'équilibre peut être un **simplexe de phases KMS au même inverse de température**, plutôt qu'un état unique.
La loi 0 porte donc sur la température commune, pas sur l'unicité microscopique de l'état d'équilibre.
# 5. Quantitatif versus exact
U6 ferme l'**atteignabilité exacte** dans les réservoirs infinis normaux/fidèles et dans les phases KMS fidèles. Il ne fournit pas à lui seul une borne $T_f\ge f(t)>0$.
Pour une borne de vitesse/coût, conserver U4 + le pont de Masanes–Oppenheim : en temps fini, les ressources physiquement accessibles (volume de bain, énergie maximale, fluctuations de travail) doivent être bornées. Leur théorème couvre notamment des réservoirs de dimension infinie sous ces contraintes.
# 6. Frontière essentielle : Nernst ≠ inatteignabilité universelle
La littérature montre que le théorème de chaleur de Nernst et le principe d'inatteignabilité ne sont pas logiquement équivalents sans hypothèses supplémentaires. L'état actuel du projet démontre la **forme d'inatteignabilité** ; il ne doit pas être renommé silencieusement « preuve universelle du théorème de Nernst ».
Dans la formulation moderne, le heat theorem dépend notamment de la dégénérescence du sous-espace fondamental et de sa variation avec les paramètres du Hamiltonien.
# 7. Critère U6
**DÉMONTRÉ sous hypothèses explicites :**
- ressources initiales normales et fidèles en type I, ou état global KMS fidèle dans le cadre algébrique ;
- dynamique fermée décrite par une unité/automorphisme ;
- sortie obtenue sans post-sélection par restriction/trace partielle.
Alors la fidélité de l'état local est préservée et un état exact $T=0$ non fidèle est inaccessible.
# 8. Loophole suivant
Une opération **conditionnelle/post-sélectionnée** n'est pas une simple restriction d'un état fidèle : un projecteur suivi de normalisation peut produire un état de support réduit avec une probabilité non nulle. U7 doit donc traiter explicitement mesure, post-sélection, probabilité de succès, coût de mémoire/record et remise à zéro du dispositif de mesure.
