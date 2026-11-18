# Historique U15 — registre de corrections
## U15.0 : trois objets distincts
- Densité du réel : \(\rho_{\mathcal R}=R/(R+P)\), relative au référentiel et à l'échelle ; R et P doivent avoir une définition opérationnelle et des unités compatibles. Aucun invariant universel établi.
- Accessibilité : \(x\preceq_C^r y\), transformation admissible sous budget vectoriel ordonné C et contexte r. Relation à budget fixé, en général non transitive ; l'union sur les budgets est un préordre sous identité et composition.
- Fécondité : \(\mathfrak F_C^r(x)=\mathcal A_C^r(x)\setminus\mathcal A_C^\varnothing(x)\). Différence de devenirs accessibles, pas corrélation finale. F4/F5 et U4 sont des résultats internes du corpus à vérifier contre leurs hypothèses sources.
- U4 exclut, selon le corpus, une réduction à la seule libre énergie. Les théories de ressources thermiques connues ont déjà des familles de monotones.

Pour \(\Phi_C^r(A)=\bigcup_{x\in A}\mathcal A_C^r(x)\), définissons l'étoile comme l'union des compositions dont les budgets somment à au plus C. Si la famille est monotone en budget, composable et extensive (pour le terme n=0), alors \(\Phi_C^{r,*}=\Phi_C^r\). Preuve : n=1 fournit une inclusion ; composition et monotonie donnent l'autre, identité traitant n=0. Cette égalité ne donne pas l'idempotence : a→b→c à coût 1 par arête, \(\Phi_1^2(a)=\{a,b,c\}\) mais \(\Phi_1(a)=\{a,b\}\). L'absorption \(C+C\preceq C\) est suffisante, avec extensivité. A1 n'implique pas que seule l'identité coûte zéro. Une relation peut être moins féconde quand le budget croît : a accessible à coût 1 avec et 2 sans relation ; la différence contient a à C=1 puis devient vide à C=2.

## U15.1 : capacité et contexte dynamiques
État augmenté \(z=(x,r,b,k)\), b inventaire restant, k capacité. Les pas admissibles modifient simultanément état, relation, ressources et capacités. Une écriture correcte en monoïde ne présuppose pas la soustraction : \(b'+c\preceq b\). La conservation et la comptabilité doivent inclure tout auxiliaire. Distinguer chemin à k constant, chemin de capacité finale k (peut changer entre-temps), et projection sur x sans condition sur k final. Les trois objets ne sont pas interchangeables. La variation de k n'évite pas le théorème d'effondrement sur l'état augmenté complet.

Exemple v1 : chaîne 0→1→2→3 de coûts (1,3),(1,1),(1,0), raccourci sous k1 de coût (1,1), préparation k1 depuis 0 de coût (2,1). Au budget (4,3), chaîne fixe accessible {0,1}, capacité préparée {0,3} au budget restant (2,2), projection dynamique {0,1,3}. Ce témoin est abstrait ; k0 et k1 sont incomparables. v2 : 0→1 seulement sous k0, 1→2 seulement sous k1, changement k0→k1 seulement depuis 0. 2 est inaccessible depuis 0,k0. Les encodages naïfs qui autorisent la préparation depuis 1 échouent.

**Rétractation explicite :** l'affirmation « v3′ continu échappe à Fritz » n'est pas prouvée. Un état poubelle totalise une action partielle mais ne garantit pas la commutativité. Fritz n'impose ni finitude ni dénombrabilité. Le monoïde commutatif libre des multisets finis sur Z, muni du préordre engendré par les réécritures [z]→[z′], reproduit exactement la portée des chemins sur les singletons (le nombre de termes est conservé). Cela ne prouve pas une action commutative de portes, mais invalide le critère de nouveauté fondé sur la seule cardinalité ou la croissance des dimensions.

## U15.2 : le profil complet, pas uniquement Pareto
\[
\mathcal B(z,z')=\{C:\exists\text{ trajectoire admissible } z\to z'\text{ de coût }\preceq C\}.
\]
Ce profil supérieur est monotone en budget et compatible avec la concaténation légitime. Il conserve les coûts, l'état final de capacité et les compromis. Un ensemble supérieur n'est pas nécessairement filtrant au sens dirigé. Dans v3′, k∈[0,1], coût d'augmentation \(\varepsilon^2\), accès à la cible à coût (1,(1-k)^2). n pas égaux atteignent k=1 pour (1,1/n). Profil exact [1,∞)×(0,∞), minima atteints vides ; fermeture [1,∞)×[0,∞). Le bord n'est pas atteint. Une discipline de coût avec durée explicite \(\sum_i(\Delta k_i)^2/\Delta t_i\ge(\Delta k)^2/\sum_i\Delta t_i\) empêche la disparition par subdivision à durée fixée ; l'interprétation physique exige une métrique et des unités.

Fécondité extensive : cible accessible avec relation et non sans sur un domaine de budgets fixé. Économique : extension stricte du profil des budgets suffisants ; publier gains et pertes séparément s'ils sont incomparables. Opérationnelle : différence des profils de tâches futures conditionnés par les capacités finales, à inventaire comparable. Une densité d'accessibilité \(\mu(\mathcal A_C\cap\Omega)/\mu(\Omega)\) est monotone en C pour une mesure fixe finie non nulle ; elle n'est pas la densité du réel originale.

## U15.3 : témoins et limites
Les profils de coût de purification dans un alphabet restreint sont démontrés dans U15_3.md. Le contrôleur pur préservé est catalytique relativement à la contrainte de portes, pas une nouvelle classe universelle d'opérations. L'extension de plein rang n'est pas une preuve de catalyse exacte non corrélée. Les états purs sont aux limites de certains coûts de support. H=0 est un Hamiltonien dégénéré, pas une absence de thermodynamique : à T>0 la référence Gibbs existe, mais ne distingue pas les températures.

## U15.4 : réinvestissement
Le gain de débit n'implique ni création de pureté ni irréductibilité aux cadres existants. La version corrigée sépare profondeur de circuit et nombre total de portes, inventaire, travail, énergie, capacité, précision, temps et coûts de pilotage. Voir U15_4.md.

## Architecture C
L'anticipation récursive est une conséquence possible de la conservation des erreurs, du refus du déni et de la correction continue ; elle n'est pas le telos. La correspondance avec la dynamique de capacité est une analogie structurelle à tester, non une loi physique ni une identité entre systèmes.
