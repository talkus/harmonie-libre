> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : THÉORÈME DE FERMETURE FINIE + TEST (22 août 2026).** U5 ferme le trou laissé par la catalyse approximative/corrélée pour l'inatteignabilité exacte de $T=0$ dans toute classe finie construite à partir de ressources initiales de coût de support fini. La preuve est de l'algèbre linéaire sur les opérateurs strictement positifs ; la thermodynamique intervient ensuite pour interpréter la frontière de rang comme $T=0$.

# Définition — coût de support généralisé
Pour tout état fini-dimensionnel plein rang $\eta$ de dimension $d_\eta$, définir
$$
C_{\rm supp}(\eta):=-\ln\!\left(d_\eta\lambda_{\min}(\eta)\right)\ge0.
$$
Pour un état de rang déficient, définir
$$
C_{\rm supp}(\eta)=+\infty.
$$
Cette définition généralise le coût spectral U1.1 : pour un bain Gibbs fini $\gamma_B$, elle redonne exactement
$$
c_B=-\ln\left(d_B\lambda_{\min}(\gamma_B)\right).
$$
# Propriété additive
Pour deux états pleins rangs,
$$
\lambda_{\min}(\eta_A\otimes\eta_B)=\lambda_{\min}(\eta_A)\lambda_{\min}(\eta_B),
$$
$$
d_{AB}=d_Ad_B,
$$
donc
$$
\boxed{C_{\rm supp}(\eta_A\otimes\eta_B)=C_{\rm supp}(\eta_A)+C_{\rm supp}(\eta_B).}
$$
# Théorème U5 — borne universelle de fermeture finie
Soit un système $S$ de dimension finie dans un état initial strictement positif $\rho_S>0$. Fournissons un nombre fini d'auxiliaires $\eta_1,\ldots,\eta_n$ initialement non corrélés avec $S$, chacun de dimension finie. Autorisons ensuite **n'importe quelle unité globale**, puis la conservation ou la trace de n'importe quels sous-systèmes. L'unité peut en particulier créer des corrélations arbitraires et le protocole peut représenter catalyse exacte, catalyse approximative, batterie, ancillas et contrôle cohérent.
Posons
$$
\eta_A=\bigotimes_{j=1}^n\eta_j,
\qquad
D_A=\prod_j d_j.
$$
L'état global initial vérifie
$$
\lambda_{\min}(\rho_S\otimes\eta_A)
=\lambda_{\min}(\rho_S)\prod_j\lambda_{\min}(\eta_j).
$$
L'unitaire préserve le spectre. Si $X\ge\lambda_{\min}(X)I_{SA}$, alors
$$
\operatorname{Tr}_A X\ge D_A\lambda_{\min}(X)I_S.
$$
Par conséquent l'état final $\rho'_S$ satisfait
$$
\lambda_{\min}(\rho'_S)
\ge D_A\lambda_{\min}(\rho_S)\prod_j\lambda_{\min}(\eta_j).
$$
En remplaçant $d_j\lambda_{\min}(\eta_j)=e^{-C_{\rm supp}(\eta_j)}$,
$$
\boxed{
\lambda_{\min}(\rho'_S)
\ge
\lambda_{\min}(\rho_S)
\exp\!\left[-\sum_jC_{\rm supp}(\eta_j)\right].
}
$$
# Corollaire — loi 3 exacte sous tout budget de support fini
Si
$$
\sum_jC_{\rm supp}(\eta_j)<\infty,
$$
alors
$$
\lambda_{\min}(\rho'_S)>0.
$$
Un état Gibbs exact à $T=0$ pour un Hamiltonien non trivial est supporté sur le sous-espace fondamental et est donc de rang déficient. Ainsi
$$
\boxed{
T=0\ \text{exact}
\Longrightarrow
\sum_j C_{\rm supp}(\eta_j)=\infty
\ \text{ou une limite infinie hors de la fermeture finie.}
}
$$
Cette conclusion est indépendante du fait que les auxiliaires soient appelés bain, catalyseur, batterie ou mémoire.
# Catalyse approximative et corrélée
La preuve U5 ne suppose **rien** sur l'état final du catalyseur. Un catalyseur peut être rendu exactement, approximativement, corrélé avec le système ou même consommé : si son état initial a un coût de support fini, il ne peut pas permettre de produire exactement un état cible de rang déficient à partir d'un état système plein rang.
Cela ferme donc, pour la cible exacte $T=0$, le trou laissé par les catalyseurs approximatifs/corrélés en dimension finie.
Les phénomènes d'embezzlement ne contredisent pas U5 : ils utilisent des familles de catalyseurs dont la taille, la qualité de restitution ou la ressource interne doit croître lorsque l'erreur tend vers zéro. Rubboli–Tomamichel montrent précisément que petite corrélation résiduelle ou petite erreur peut exiger un catalyseur hautement resourceful, avec divergence dans les limites idéales.
# Cible approchée
Si une cible a
$$
\lambda_{\min}(\rho'_S)=\varepsilon>0,
$$
alors U5 impose la borne nécessaire
$$
\boxed{
\sum_jC_{\rm supp}(\eta_j)
\ge
\ln\frac{\lambda_{\min}(\rho_S)}{\varepsilon}.
}
$$
Donc l'approche de la frontière $\varepsilon\to0$ force encore
$$
\sum_jC_{\rm supp}\to\infty.
$$
Pour une cible Gibbs qubit de gap $\Delta$, $\varepsilon=p_e(\beta')$ et on retrouve une borne finie sur $\beta'$ pour tout budget fini.
# Ressources initiales déjà de rang déficient
Si une batterie pure, un ancilla $T=0$ ou un registre de contrôle exactement pur est fourni dès le départ, alors son $C_{\rm supp}=\infty$. U5 ne l'interdit pas : il l'identifie explicitement comme **ressource frontière déjà présente**.
Cela résout le paradoxe apparent des théories catalytiques où une transformation vers un état pur peut avoir un coût de travail moyen fini : le modèle de batterie idéale contient une ressource de support/pureté qui n'est pas capturée par le seul travail moyen. U4 avait déjà montré que $W_{\rm avg}$ peut rester fini alors que $w_{\max}$ diverge.
# Réservoirs infinis
U5 est un théorème fini-dimensionnel. Pour un réservoir réellement infini, $\lambda_{\min}$ global peut ne pas fournir une jauge utile. Le raccord physique est donc : **temps fini + localité/énergie finies **$\Rightarrow$** région effectivement accessible bornée**, puis appliquer U5 sur cette fermeture effective. Masanes–Oppenheim donnent une version rigoureuse de ce principe en reliant refroidissement, volume de bain accessible, fluctuations maximales de travail et temps.
Une théorie qui autorise dès un temps fini un accès effectif à un volume, une énergie ou un contrôle infinis sort explicitement de la classe physique U5.
# Conséquence pour les quatre lois
U5 renforce uniquement la loi 3 ; les lois 0–2 restent celles de U2 : passivité complète/Gibbs, invariant énergétique et monotones de libre énergie/entropie relative.
La structure commune devient donc :
$$
\boxed{
\text{équilibre non trivial}
+\text{conservation microscopique}
+\text{dilation réversible}
+\text{fermeture de ressources à coût de support fini}
\Rightarrow
\text{lois 0--3 (inatteignabilité).}
}
$$
# Contrôles négatifs
- un ancilla pur initial : $C_{\rm supp}=\infty$, donc hors budget fini ;
- un nombre infini d'auxiliaires dont la somme des coûts diverge : hors fermeture finie ;
- un réservoir infini accessible sans borne en temps fini : hors hypothèse de régularité ;
- une opération fondamentale non dilatable à partir de ressources comptabilisées : hors classe U5 et à traiter comme nouvelle ressource/dynamique.
# Vérification numérique indépendante
Un stress-test aléatoire sur des systèmes qubits avec auxiliaires de dimensions 2 et 3 a appliqué des unités globales aléatoires puis tracé les auxiliaires. Sur 200 réalisations, la borne U5 a été respectée dans tous les cas ; le plus petit ratio observé $\lambda_{\min}^{obs}/\lambda_{\min}^{borne}$ était supérieur à 8.
Ce test ne remplace pas la preuve analytique ; il sert seulement de contrôle d'implémentation.
# Statut scientifique
**DÉMONTRÉ pour toute fermeture finie de ressources initiales de coût de support fini.** Cela couvre l'inatteignabilité exacte sous catalyse finie exacte, approximative ou corrélée en sortie, batteries/ancillas pleins rangs et protocoles unitaires arbitraires avec discard.
**RESTE OUVERT :** formulation universelle en algèbres infinies, transitions de phase, thermodynamic limit sans hypothèse de région accessible effective, et équivalence complète avec la formulation macroscopique de Nernst/Lieb–Yngvason.
