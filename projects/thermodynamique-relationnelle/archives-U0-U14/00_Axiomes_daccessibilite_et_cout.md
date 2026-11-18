> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

# Objets primitifs
Un système est décrit par un espace d'états $\mathcal S$, un Hamiltonien $H$ lorsque la description énergétique est disponible, un ensemble de transformations admissibles $\mathfrak T$ et une fonction de coût $\mathcal C:\mathfrak T\to[0,\infty]$.
Pour un budget $C$ :
$$
X\preceq_C Y\iff\exists\Phi\in\mathfrak T:\ \Phi(X)=Y,\ \mathcal C[\Phi]\le C.
$$
La relation sans budget est $X\preceq Y$ s'il existe au moins une transformation admissible de coût fini.
# Axiomes candidats A1–A6
1. **Identité** : $X\preceq_0 X$.
2. **Composition** : si $X\preceq_{C_1}Y$ et $Y\preceq_{C_2}Z$, alors $X\preceq_{C_1+C_2}Z$.
3. **Composition parallèle** : les systèmes indépendants peuvent être composés et les coûts sont subadditifs/additifs selon le modèle de ressources.
4. **Conservation fermée de l'énergie** : les dilatations fermées fondamentales satisfont $[U,H_{\rm tot}]=0$.
5. **État thermique de référence** : à inverse de température $\beta$, $\gamma_\beta=e^{-\beta H}/Z$ est préservé par les opérations thermiques admissibles.
6. **Coût physique** : temps, dimension de machine, énergie maximale, travail disponible ou norme de contrôle doivent être explicitement bornés pour tout $C<\infty$.
# Critère d'unification
Les quatre lois ne doivent pas être quatre axiomes indépendants. Elles doivent apparaître comme propriétés différentes de $(\mathcal S,H,\mathfrak T,\mathcal C)$ : équivalence d'équilibre, conservation, ordre monotone, frontière inaccessible.
