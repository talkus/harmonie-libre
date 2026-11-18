> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : THÉORÈME MICROSCOPIQUE SUFFISANT.** U10 fournit une classe explicite de modèles dont le comptage des excitations implique directement la régularité basse énergie utilisée dans U9. Il ne prétend pas que toute matière admet une décomposition en défauts indépendants.

# 1. Hypothèses de comptage D1–D4
Pour chaque volume $V$ et paramètre $x$, décomposer l'espace des états en secteurs d'excitation $n=0,1,2,\ldots$.
- le secteur $n=0$ est le secteur fondamental, de dimension $g_{V,x}$ ;
- toute énergie dans le secteur $n$ satisfait
$$
E-E_{0,V,x}\ge n\Delta,
$$
avec **gap de défaut uniforme** $\Delta>0$ ;
- le nombre d'états du secteur $n$ est borné par
$$
\boxed{
N_{V,n,x}\le g_{V,x}\frac{(aV)^n}{n!}
}
$$
avec $a<\infty$ uniforme dans la famille ;
- la densité d'entropie fondamentale existe,
$$
\frac1V\log g_{V,x}\to s_0,
$$
avec $s_0$ indépendant de $x$.
Cette forme couvre notamment des gaz dilués de défauts/localized excitations et le modèle de spins indépendants gappés.
# 2. Borne uniforme sur la fonction de partition
Le rapport de partition excité est borné par
$$
\frac{Z_{V,x}(\beta)}{g_{V,x}e^{-\beta E_{0,V,x}}}
\le
\sum_{n\ge0}\frac{(aVe^{-\beta\Delta})^n}{n!}
=
\exp\bigl(aVe^{-\beta\Delta}\bigr).
$$
Donc la pression d'excitation spécifique
$$
q_{V,x}(\beta)=\frac1V\log\frac{Z_{V,x}}{g_{V,x}e^{-\beta E_0}}
$$
satisfait uniformément
$$
\boxed{0\le q_{V,x}(\beta)\le a e^{-\beta\Delta}.}
$$
La limite thermodynamique, lorsqu'elle existe, hérite de la même borne.
# 3. Continuité microcanonique au bord — dérivation de l'hypothèse U9
Considérons les états dont l'énergie satisfait
$$
E-E_0\le V\varepsilon.
$$
La borne $E-E_0\ge n\Delta$ implique
$$
n\le rV,\qquad r=\varepsilon/\Delta.
$$
Ainsi le nombre d'états sous ce seuil est au plus
$$
\sum_{n\le rV}g_V\frac{(aV)^n}{n!}.
$$
Avec $n!\ge(n/e)^n$, pour $y=n/V$,
$$
\frac1V\log\frac{N_{V,n}}{g_V}
\le y\log\frac{ae}{y}.
$$
Pour $0<r<a$, la fonction est croissante sur $0<y\le r$, donc après passage à la limite,
$$
\boxed{
s(e_0+\varepsilon)-s_0
\le
r\log\frac{ae}{r},
\qquad r=\frac{\varepsilon}{\Delta}.
}
$$
Or
$$
r\log\frac{ae}{r}\to0\qquad(r\to0^+).
$$
Donc
$$
\boxed{
\lim_{e\downarrow e_0}s(e)=s_0.
}
$$
U10 dérive ainsi la régularité du bord fondamental utilisée par U9 à partir d'une hypothèse microscopique de comptage.
# 4. Nernst canonique uniforme sans distance globale au fondamental
La fonction $q_V(\beta)$ est décroissante et convexe en $\beta$. Pour une fonction convexe,
$$
-q_V'(\beta)
\le
\frac{2}{\beta}\bigl[q_V(\beta/2)-q_V(\beta)\bigr]
\le
\frac{2a}{\beta}e^{-\beta\Delta/2}.
$$
L'entropie spécifique vaut, aux points de différentiabilité,
$$
\frac{S_V}{V}
=
\frac{\log g_V}{V}
+q_V(\beta)-\beta q_V'(\beta).
$$
Donc
$$
\boxed{
0\le
\frac{S_V}{V}-\frac{\log g_V}{V}
\le
 a e^{-\beta\Delta}
+2a e^{-\beta\Delta/2}.
}
$$
La borne est **uniforme en volume**. En prenant d'abord $V\to\infty$ puis $T\to0$,
$$
\boxed{s(T,x)\to s_0.}
$$
Comme $s_0$ est commun,
$$
s(T,x_1)-s(T,x_2)\to0.
$$
C'est une preuve directe de Nernst dans la classe de défauts U10, sans utiliser une distance de trace globale au sous-espace fondamental.
# 5. Énergie d'excitation spécifique
La même convexité donne
$$
u(\beta)-e_0=-q'(\beta)
\le
\frac{2a}{\beta}e^{-\beta\Delta/2},
$$
donc
$$
\boxed{u(T)\to e_0.}
$$
# 6. Exemple exact : spins indépendants
Pour $V$ spins à deux niveaux de gap $\Delta$,
$$
N_{V,n}=\binom Vn\le\frac{V^n}{n!},
$$
donc U10 s'applique avec $a=1$, $g_V=1$.
La pression d'excitation exacte est
$$
q(\beta)=\log(1+e^{-\beta\Delta})\le e^{-\beta\Delta},
$$
en accord avec le théorème.
# 7. Ce que U10 ferme et ce qu'il ne ferme pas
**Fermé :**
- croissance exponentielle du nombre total d'états avec le volume ;
- multiplicité extensive d'excitations localisées ;
- ordre de limite $V\to\infty$ avant $T\to0$ dans cette classe ;
- continuité microcanonique au bord requise par U9.
**Non démontré pour toute matière :**
- systèmes critiques sans coût minimal de défaut ;
- excitations collectives fortement contraintes ;
- interactions longue portée / non additives ;
- phases topologiques ou fractoniques nécessitant un comptage différent ;
- classes où $N_{V,n}$ croît plus vite que la borne factorielle.
# 8. Pont vers les théorèmes généraux de mécanique statistique
Pour les systèmes classiques à interactions courtes stables/tempered et plusieurs systèmes de réseau quantiques locaux, la littérature rigoureuse fournit séparément l'existence de limites thermodynamiques et la dualité entre entropie et pression sous des hypothèses appropriées.
U10 fournit un **critère basse énergie supplémentaire** qui suffit à garantir le comportement de bord nécessaire à Nernst.
# 9. Statut dans l'unification
U9 donnait une fermeture macroscopique conditionnée par la régularité de $s(e)$. U10 dérive cette régularité et une borne canonique uniforme pour une classe microscopique concrète.
La cible suivante U11 est d'élargir le comptage au-delà des défauts gappés : densités d'états gapless contrôlées, phonons/bosons et points critiques avec exposants thermodynamiques explicites.
