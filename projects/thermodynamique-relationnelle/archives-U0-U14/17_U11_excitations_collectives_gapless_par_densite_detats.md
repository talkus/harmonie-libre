> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : MATH + DÉRIVATION + TEST à construire.** U11 étend la fermeture basse température aux excitations collectives gapless de type bosonique/quasi-libre sous une borne de densité d’états intégrée. Le but est d’obtenir directement $S/V\to s_0$ et $C_V/V\to0$ sans gap spectral.

# Hypothèses U11
Pour chaque volume $V$, soit $G_V(\Omega)$ le nombre cumulé de modes collectifs strictement positifs d’énergie $\omega\le\Omega$. Les modes exactement nuls sont absorbés dans le secteur fondamental/résiduel $s_0$.
Supposons qu’il existe $A<\infty$ et $p>0$ tels que, uniformément dans $V$ et dans la famille de paramètres considérée,
$$
\frac{G_V(\Omega)}{V}\le A\Omega^p,\qquad \Omega>0.
$$
Le secteur UV doit être thermiquement régulier ; la forme la plus simple est que la borne ci-dessus soit globale, ou qu’au-delà d’un cutoff fixe la contribution au partitionnement soit finie à une température positive et donc exponentiellement négligeable lorsque $\beta\to\infty$.
# Partition bosonique
Pour des modes bosoniques indépendants/quasi-libres,
$$
q_V(\beta):=\frac1V\log Z_{\rm exc}
=\int_0^\infty -\log(1-e^{-\beta\omega})\,d\left(\frac{G_V(\omega)}V\right).
$$
Une intégration de Stieltjes par parties donne
$$
q_V(\beta)
\le A\int_0^\infty \omega^p\frac{\beta\,d\omega}{e^{\beta\omega}-1}
=A\Gamma(p+1)\zeta(p+1)\,\beta^{-p}.
$$
Donc
$$
\boxed{q_V(\beta)=O(T^p)}
$$
uniformément dans le volume.
# Énergie
Avec $h_\beta(\omega)=\omega/(e^{\beta\omega}-1)$, qui est positive et décroissante,
$$
u_V(\beta):=\frac{U_{\rm exc}}V
=\int h_\beta(\omega)\,d\left(\frac{G_V(\omega)}V\right).
$$
La même intégration par parties donne
$$
u_V(\beta)
\le A p\Gamma(p+1)\zeta(p+1)\,\beta^{-(p+1)}.
$$
Ainsi
$$
\boxed{u_V(T)=O(T^{p+1})}.
$$
# Entropie
Avec $k_B=1$,
$$
s_{\rm exc}=q_V+\beta u_V.
$$
Donc
$$
\boxed{
0\le s_V(T)-s_0
\le A(p+1)\Gamma(p+1)\zeta(p+1)T^p.
}
$$
En particulier,
$$
\boxed{s_V(T)\to s_0}
$$
uniformément en $V$. Si $s_0$ est commun dans la famille,
$$
s(T,x_1)-s(T,x_2)\to0,
$$
ce qui donne la branche Nernst.
# Capacité calorifique
La capacité par mode vaut
$$
c(x)=\frac{x^2e^x}{(e^x-1)^2}=\left(\frac{x}{2\sinh(x/2)}\right)^2,
$$
fonction décroissante de $x>0$. Une nouvelle intégration par parties donne
$$
\frac{C_V}{V}
\le A p\Gamma(p+2)\zeta(p+1)\,T^p.
$$
Donc
$$
\boxed{C_V/V\to0.}
$$
# Corollaire dispersion
Pour un nombre fini de branches avec dispersion basse énergie
$$
\omega_j(k)\sim c_j|k|^z
$$
en dimension spatiale $d$, le nombre de modes sous $\Omega$ satisfait typiquement
$$
G(\Omega)/V\propto \Omega^{d/z}.
$$
Ainsi
$$
\boxed{p=\frac dz},
$$
et
$$
s-s_0,\ C_V/V=O(T^{d/z}).
$$
Exemples : phonons acoustiques en $d=3,z=1$ donnent la loi de Debye $C_V\propto T^3$ ; un mode quadratique $z=2$ donne $C_V/V=O(T^{d/2})$.
# Corollaire critique avec hyperscaling effectif
Lorsqu’un point critique possède une forme d’échelle thermique équivalente à une densité d’états effective avec
$$
p=\frac{d-\theta}{z}>0,
$$
U11 prédit
$$
s-s_0,\ C_V/V=O\left(T^{(d-\theta)/z}\right).
$$
Cette ligne est un **corollaire de scaling**, pas une preuve microscopique pour tout point critique ; les variables dangereusement irrélevantes et les violations d’hyperscaling doivent être testées séparément.
# Contrôles négatifs
U11 ne s’applique pas si :
- $p\le0$ ;
- un nombre extensif de modes exactement nuls n’est pas inclus correctement dans $s_0$ ;
- $G_V(\Omega)/V$ tend vers une constante non nulle quand $\Omega\downarrow0$ ;
- la factorisation/quasi-liberté ou une borne de partition équivalente échoue ;
- le résidu d’entropie $s_0$ dépend du paramètre externe ;
- une phase critique possède une accumulation IR plus forte que toute puissance positive.
# Relation avec U9 et U10
- U9 formule la fermeture en termes d’entropie spécifique au bord fondamental.
- U10 dérive cette régularité par comptage de défauts locaux gappés.
- **U11 fournit une deuxième dérivation microscopique, gapless, à partir du comptage des modes collectifs.**
# Références structurales
- Théorie de Debye : densité phononique $D(\omega)\propto\omega^{d-1}$ pour les modes acoustiques linéaires, donnant $C\propto T^d$ ; en trois dimensions, $T^3$.
- Scaling quantique : lorsque l’hyperscaling avec exposant de violation $\theta$ est valide, la chaleur spécifique peut suivre $T^{(d-\theta)/z}$.
# Prochain test
Construire un témoin standard-library vérifiant numériquement les intégrales Bose pour plusieurs $p$, les cas $d=3,z=1$ et $d=2,z=2$, et un contrôle négatif avec un plateau de densité d’états à zéro.
