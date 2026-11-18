> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : DÉRIVATION CONDITIONNELLE + PONT MACROSCOPIQUE.** U9 traite la limite thermodynamique en remplaçant les objets globaux de support par les densités d'énergie et d'entropie. Le résultat est rigoureux sous des hypothèses explicites d'existence de la limite thermodynamique et d'équivalence des ensembles ; ces hypothèses ne sont pas cachées.

# 1. Séquence thermodynamique
Considérons une famille de systèmes de volume $V$ et paramètre externe $x$, avec Hamiltonien $H_{V,x}$, énergie fondamentale $E_{0,V,x}$ et densité fondamentale
$$
e_0(x)=\lim_{V\to\infty}\frac{E_{0,V,x}}{V}.
$$
On suppose l'existence d'une entropie microcanonique spécifique
$$
s_x(e)=\lim_{V\to\infty}\frac1V\log \Omega_{V,x}(e),
$$
au sens approprié de fenêtre d'énergie, et d'une entropie résiduelle spécifique
$$
s_0= s_x(e_0(x)),
$$
**indépendante de **$x$ dans la classe considérée.
# 2. Hypothèses U9
- $s_x(e)$ est supérieurement semi-continue près de $e_0(x)$ ;
- $s_x(e)$ est continue à droite au bord fondamental :
$$
\lim_{e\downarrow e_0(x)}s_x(e)=s_0;
$$
- la pression canonique spécifique existe et est reliée à $s_x$ par Legendre–Fenchel :
$$
\phi_x(\beta)=\sup_{e\ge e_0(x)}\{s_x(e)-\beta e\};
$$
- cette représentation décrit effectivement les états d'équilibre canoniques de la classe (équivalence thermodynamique des ensembles / principe de comparaison au niveau macroscopique).
# 3. Pression d'excitation
Posons $\varepsilon=e-e_0(x)\ge0$ et
$$
\psi_x(\beta)=\sup_{\varepsilon\ge0}
\{s_x(e_0+\varepsilon)-s_0-\beta\varepsilon\}.
$$
Le point $\varepsilon=0$ donne toujours $\psi_x(\beta)\ge0$.
Supposons qu'il existe $\beta_0$ tel que $\psi_x(\beta_0)<\infty$. Pour tout $\delta>0$,
$$
\sup_{\varepsilon\ge\delta}
\{s_x(e_0+\varepsilon)-s_0-\beta\varepsilon\}
\le
\psi_x(\beta_0)-(\beta-\beta_0)\delta.
$$
Le membre de droite devient négatif pour $\beta$ assez grand, tandis que $\varepsilon=0$ donne zéro. Ainsi tout maximiseur canonique $\varepsilon_{\beta,x}$ satisfait
$$
\boxed{\varepsilon_{\beta,x}\to0\qquad(\beta\to\infty).}
$$
# 4. Théorème de Nernst en limite thermodynamique
Par continuité à droite de $s_x$,
$$
s_x(e_0+\varepsilon_{\beta,x})\to s_0.
$$
Sous équivalence d'ensembles, cette quantité est l'entropie spécifique canonique d'équilibre. Donc
$$
\boxed{s(T,x)\to s_0\qquad(T\to0).}
$$
Comme $s_0$ est indépendant de $x$,
$$
\boxed{s(T,x_1)-s(T,x_2)\to0.}
$$
C'est la forme spécifique/macroscopique du théorème de chaleur de Nernst dans la classe U9.
Si $s_0=0$, on obtient la forme de Planck.
# 5. Asymptotique de libre énergie
La libre énergie spécifique est
$$
f_x(T)=\inf_e\{e-Ts_x(e)\}.
$$
Avec $\beta=1/T$,
$$
f_x(T)=e_0(x)-Ts_0-T\psi_x(1/T).
$$
Comme $\psi_x(\beta)\to0$,
$$
\boxed{f_x(T)=e_0(x)-Ts_0+o(T).}
$$
Cette formule raccorde directement le bord $T=0$ à la dualité entropie–libre énergie.
# 6. Version quantitative sans gap
Supposons en plus, uniformément près du fondamental,
$$
0\le s_x(e_0+\varepsilon)-s_0\le A\varepsilon^\alpha,
\qquad 0<\alpha<1.
$$
Un maximiseur canonique doit satisfaire
$$
\beta\varepsilon_{\beta,x}
\le A\varepsilon_{\beta,x}^\alpha,
$$
d'où
$$
\boxed{
\varepsilon_{\beta,x}
\le
\left(\frac{A}{\beta}\right)^{1/(1-\alpha)}.
}
$$
Puis
$$
\boxed{
s(T,x)-s_0
\le
A^{1/(1-\alpha)}
T^{\alpha/(1-\alpha)}.
}
$$
Ainsi U9 couvre aussi des branches gapless lorsque la densité d'états près du fondamental reste suffisamment régulière.
La pression d'excitation est bornée par
$$
\psi_x(\beta)
\le
A(1-\alpha)
\left(\frac{A\alpha}{\beta}\right)^{\alpha/(1-\alpha)}.
$$
# 7. Commutation des deux limites
Si
$$
\lim_{V\to\infty}\frac1V\log g_{V,x}=s_0
$$
et les hypothèses U9 sont satisfaites, alors
$$
\boxed{
\lim_{T\to0}\lim_{V\to\infty}\frac{S_{V,x}(T)}V
=
\lim_{V\to\infty}\lim_{T\to0}\frac{S_{V,x}(T)}V
=s_0.
}
$$
La non-commutation des limites devient donc un **critère d'échec** explicite de U9.
# 8. Pont vers Lieb–Yngvason
Lieb–Yngvason construisent une entropie additive/extensive $S_{LY}$ à partir de l'accessibilité adiabatique, avec
$$
X\preceq Y\Longleftrightarrow S_{LY}(X)\le S_{LY}(Y)
$$
dans le domaine du principe de comparaison.
U9 fournit le pont statistique suivant : lorsque la limite microcanonique $s_x(e)$ existe, est concave/appropriée à l'équivalence des ensembles, et est calibrée sur les mêmes états d'équilibre macroscopiques, l'entropie spécifique statistique réalise le même ordre thermodynamique à transformation affine près.
**Frontière :** U9 ne prétend pas dériver automatiquement le principe de comparaison depuis tout Hamiltonien microscopique ; cette condition reste un pont structurel à vérifier pour chaque classe de matière.
# 9. Résultats négatifs / failure modes
U9 peut échouer ou nécessiter révision si :
- $s_0$ dépend du paramètre externe $x$ ;
- l'entropie spécifique est discontinue au bord fondamental ;
- une densité exponentielle d'états s'accumule arbitrairement près de $e_0$ ;
- la limite thermodynamique n'existe pas ;
- les ensembles sont non équivalents (notamment certaines interactions de longue portée) ;
- un point critique quantique fait fermer la structure requise ;
- les limites $V\to\infty$ et $T\to0$ ne commutent pas.
# 10. Statut dans l'unification des quatre lois
U2–U7 ferment l'inatteignabilité dynamique/resource-aware de $T=0$ ; U8 traite Nernst pour une classe spectrale finie ; U9 porte Nernst au **niveau thermodynamique spécifique** sous continuité du bord fondamental et dualité de Legendre–Fenchel.
La cible suivante est U10 : établir des conditions microscopiques concrètes (localité/stabilité/temperedness ou classes quantiques de réseau) qui garantissent les hypothèses U9, au lieu de les prendre comme propriétés de la limite thermodynamique.
# Références structurales
- Lieb & Yngvason, *The Physics and Mathematics of the Second Law of Thermodynamics*, Physics Reports 310 (1999).
- Lieb & Yngvason, *The Mathematical Structure of the Second Law of Thermodynamics* (2002).
- Georgii, résultats d'équivalence d'ensembles et principe variationnel en mécanique statistique classique.
- Littérature de grandes déviations / Legendre–Fenchel sur l'équivalence thermodynamique des ensembles.
