> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**U8 — fermeture conditionnelle de la branche Nernst.** L'inatteignabilité U2–U7 et le théorème de chaleur de Nernst ne sont pas universellement équivalents. U8 fournit des conditions spectrales suffisantes sous lesquelles Nernst et $C\to0$ sont démontrés quantitativement.

# 1. Hypothèses spectrales
Considérons une famille de Hamiltoniens finis $H(x)$ de dimension $d$, avec énergie fondamentale décalée à zéro. Supposons sur le domaine de paramètres étudié :
1. dégénérescence fondamentale constante $g\ge1$ ;
2. gap uniforme
$$
\Delta(x)\ge\Delta_*>0;
$$
1. pour la borne de capacité calorifique, énergie maximale uniforme $E_{max}(x)\le E_*<\infty$.
Soit $P_0(x)$ le projecteur fondamental et
$$
\tau_0(x)=\frac{P_0(x)}g.
$$
# 2. Poids excité
Pour
$$
\gamma_{\beta,x}=\frac{e^{-\beta H(x)}}{Z_{\beta,x}},
$$
le poids total hors du sous-espace fondamental est
$$
p_x(\beta)=\operatorname{Tr}[(I-P_0)\gamma_{\beta,x}].
$$
Le partitionnement donne
$$
Z_{exc}\le(d-g)e^{-\beta\Delta_*},
$$
donc
$$
\boxed{p_x(\beta)\le\frac{d-g}{g}e^{-\beta\Delta_*}.}
$$
La borne est uniforme en $x$.
# 3. Distance exacte au sous-espace fondamental
$\gamma_{\beta,x}$ et $\tau_0(x)$ commutent et leurs supports excité/fondamental sont orthogonaux. On obtient exactement
$$
\boxed{\frac12\|\gamma_{\beta,x}-\tau_0(x)\|_1=p_x(\beta).}
$$
# 4. Entropie et Nernst
Par Fannes–Audenaert, pour $d\ge2$,
$$
\left|S(\gamma_{\beta,x})-\ln g\right|
\le p_x\ln(d-1)+h_2(p_x),
$$
où $h_2$ est l'entropie binaire.
Comme $p_x(\beta)$ décroît exponentiellement, uniformément,
$$
\boxed{S(\gamma_{\beta,x})\to\ln g\quad(\beta\to\infty)}.
$$
Ainsi, pour deux paramètres $x_1,x_2$ de la même famille,
$$
\boxed{S(T,x_1)-S(T,x_2)\to0\quad(T\to0).}
$$
C'est la forme Nernst du théorème de chaleur dans cette classe.
Si $g=1$, on obtient en plus la forme de Planck
$$
S(T,x)\to0.
$$
Si $g>1$, l'entropie résiduelle commune $\ln g$ subsiste mais Nernst reste satisfait puisque les différences tendent vers zéro.
# 5. Capacité calorifique
Dans l'ensemble canonique,
$$
C_x(\beta)=k_B\beta^2\operatorname{Var}_{\gamma_{\beta,x}}(H(x)).
$$
Puisque le fondamental est à énergie zéro et $H^2\le E_*^2$ sur le sous-espace excité,
$$
\operatorname{Var}(H)\le\langle H^2\rangle\le E_*^2p_x(\beta).
$$
Donc
$$
\boxed{C_x(\beta)\le k_B\beta^2E_*^2\frac{d-g}{g}e^{-\beta\Delta_*}\to0.}
$$
La capacité calorifique tend donc uniformément vers zéro dans cette classe.
# 6. Pourquoi U8 n'est pas universel
Les hypothèses indiquent exactement les mécanismes d'échec possibles :
- si $g(x)$ change, alors $S(T,x)\to\ln g(x)$ et la différence de Nernst peut rester non nulle ;
- si le gap se ferme, la convergence uniforme peut disparaître ;
- dans la limite thermodynamique, $d$ et la densité d'états croissent et peuvent concurrencer l'exponentielle $e^{-\beta\Delta}$ ;
- à une transition de phase quantique, gap et dégénérescence peuvent changer simultanément.
Ces exceptions sont cohérentes avec la littérature montrant la non-équivalence générale entre Nernst et inatteignabilité.
# 7. Relation avec U2–U7
U2–U7 : **dynamique/accessibilité** — $T=0$ exact exige une ressource frontière dans les classes considérées.
U8 : **spectre/équilibre** — sous gap uniforme et dégénérescence constante, l'entropie possède une limite universelle $\ln g$ et $C\to0$.
Les deux branches deviennent complémentaires plutôt qu'identifiées.
# 8. Verrou macroscopique restant
La prochaine étape est de remplacer les bornes finies $d,E_*$ par des hypothèses sur la **densité d'états**, le volume et la limite thermodynamique. Une fermeture macroscopique doit contrôler la compétition entre croissance du nombre d'états et suppression de Boltzmann, puis raccorder cette limite à l'ordre d'accessibilité de Lieb–Yngvason.
# Statut
**DÉRIVATION mathématique dans la classe finie uniformément gappée à dégénérescence fondamentale constante.**
