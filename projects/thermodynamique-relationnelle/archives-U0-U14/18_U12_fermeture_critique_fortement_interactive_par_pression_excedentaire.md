> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : DÉRIVATION + THÉORÈME CONDITIONNEL.** U12 retire l’hypothèse quasi-libre de U11. Il suffit désormais de contrôler la pression excédentaire thermodynamique à basse température. Aucun modèle de quasiparticules n’est requis.

# 1. Objet thermodynamique
En unités $k_B=1$, soit $\ell(\beta)=\lim_{V\to\infty}V^{-1}\log Z_V(\beta)$ la pression adimensionnée d’une phase d’équilibre, $e_0$ sa densité d’énergie fondamentale et $s_0$ sa densité d’entropie résiduelle. Définir
$$
q(\beta)=\ell(\beta)+\beta e_0-s_0.
$$
Alors
$$
\ell(\beta)=-\beta e_0+s_0+q(\beta),
$$
$$
u(\beta)-e_0=-q'(\beta),
$$
$$
s(\beta)-s_0=q(\beta)-\beta q'(\beta),
$$
aux points de différentiabilité.
# 2. Hypothèse U12 minimale
Supposons, pour $\beta\ge\beta_0$ :
- $q(\beta)\ge0$ ;
- $q$ est convexe et non croissante ;
- il existe $A<\infty$ et $p>0$ tels que
$$
0\le q(\beta)\le A\beta^{-p}.
$$
Ces propriétés sont directement thermodynamiques : la convexité vient de la convexité de $\log Z$, tandis que la décroissance correspond à une énergie au-dessus du fondamental.
# 3. Borne d’énergie sans quasiparticules
Pour une fonction convexe,
$$
q'(\beta)\ge\frac{q(\beta)-q(\beta/2)}{\beta/2}.
$$
Donc
$$
0\le -q'(\beta)
\le\frac{2q(\beta/2)}{\beta}
\le2^{p+1}A\beta^{-(p+1)}.
$$
Ainsi
$$
\boxed{0\le u(T)-e_0\le2^{p+1}A\,T^{p+1}.}
$$
# 4. Borne d’entropie et Nernst
Comme
$$
s-s_0=q+\beta(-q'),
$$
on obtient
$$
0\le s(T)-s_0
\le\bigl(1+2^{p+1}\bigr)A\,T^p.
$$
Par conséquent
$$
\boxed{s(T)\to s_0\quad(T\to0).}
$$
Si $s_0$ est commun à une famille paramétrée par $x$, alors
$$
\boxed{s(T,x_1)-s(T,x_2)\to0,}
$$
ce qui donne la branche Nernst dans la classe U12.
# 5. Forme libre-énergie
Comme $f(T)=-T\ell(1/T)$,
$$
f(T)=e_0-Ts_0-Tq(1/T).
$$
La borne U12 implique
$$
\boxed{f(T)=e_0-Ts_0+O(T^{p+1}).}
$$
Le résidu critique de la libre énergie suffit donc à contrôler la troisième loi d’équilibre sans spécifier les degrés de liberté microscopiques.
# 6. Corollaire de variation régulière
Supposons plus fortement
$$
q(\beta)\sim a\beta^{-p}L(\beta),
$$
où $L$ est lentement variable et $p>0$. Comme $-q'$ est monotone par convexité, le théorème de densité monotone pour les fonctions régulièrement variables donne
$$
-q'(\beta)\sim p\frac{q(\beta)}{\beta}.
$$
Ainsi
$$
\boxed{u-e_0\sim pa\,T^{p+1}L(1/T),}
$$
$$
\boxed{s-s_0\sim(p+1)a\,T^pL(1/T).}
$$
Si, en plus, la régularité nécessaire au second ordre est satisfaite (par exemple $q''$ est finalement monotone), alors
$$
q''(\beta)\sim p(p+1)\frac{q(\beta)}{\beta^2},
$$
et donc
$$
\boxed{c_V(T)\sim p(p+1)a\,T^pL(1/T).}
$$
Cette dernière asymptotique nécessite explicitement une hypothèse de régularité supplémentaire ; elle ne découle pas d’une simple borne sur $q$.
# 7. Corollaire critique fortement interactif
Si une théorie critique, éventuellement sans quasiparticules, possède une libre énergie singulière
$$
f(T)-e_0+Ts_0\sim-aT^{p+1}L(1/T),
$$
avec $p>0$, alors U12 impose automatiquement
$$
s-s_0\sim(p+1)aT^pL(1/T).
$$
Dans un régime d’hyperscaling effectif,
$$
p=\frac{d-\theta}{z}>0.
$$
La preuve U12 n’exige toutefois pas que cette identification microscopique de $p$ soit vraie : seule la loi de pression est nécessaire.
# 8. Résultat négatif important
Une borne $q(\beta)=O(1)$ avec exposant effectif $p=0$ ne suffit pas à imposer Nernst. De même, une simple connaissance de la libre énergie moyenne sans contrôle de sa décroissance au bord ne force pas $s-s_0\to0$.
Ainsi le critère structurel est :
$$
\boxed{q(\beta)\to0\text{ avec une décroissance quantitativement contrôlée}.}
$$
# 9. Relation avec U9–U11
- U9 : formulation par entropie spécifique et dualité microcanonique/canonique ;
- U10 : dérivation microscopique de la régularité par défauts locaux gappés ;
- U11 : dérivation par densité d’états collective gapless ;
- U12 : fermeture au niveau de la pression, valable même lorsque ni défauts indépendants ni quasiparticules ne sont disponibles.
# 10. Frontière restante
U12 reste une classe suffisante. Il ne dérive pas automatiquement la loi de pression d’un Hamiltonien fortement interactif arbitraire. Les cas où $q$ n’est pas régulièrement décroissante, où l’extensivité échoue, ou où la limite thermodynamique est pathologique restent hors du théorème.
