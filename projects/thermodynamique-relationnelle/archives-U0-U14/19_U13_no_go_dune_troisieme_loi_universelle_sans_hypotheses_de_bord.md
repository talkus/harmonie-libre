> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : MATH / NO-GO.** U13 démontre qu’une version Nernst de la troisième loi ne peut pas être dérivée pour toutes les familles de Hamiltoniens à partir de la mécanique quantique et de la seule existence d’un état fondamental. Des hypothèses de bord basse énergie sont mathématiquement nécessaires.

# 1. No-go par dégénérescence fondamentale
Considérons deux Hamiltoniens finis de même dimension et même gap $\Delta>0$ :
$$
H_1=\mathrm{diag}(0,\Delta,\Delta,\ldots),
$$
avec dégénérescence fondamentale $g_1=1$, et
$$
H_2=\mathrm{diag}(0,0,\Delta,\ldots),
$$
avec $g_2=2$.
Pour tout système fini,
$$
\lim_{T\to0}S(\gamma_T)=\ln g.
$$
Donc
$$
\lim_{T\to0}\left[S_{H_2}(T)-S_{H_1}(T)\right]=\ln2\neq0.
$$
Ainsi la proposition universelle
$$
S(T,x_1)-S(T,x_2)\to0
$$
pour toute famille arbitraire de Hamiltoniens est fausse.
# 2. No-go thermodynamique par accumulation exponentielle
Pour chaque volume $V$, prenons :
- un état fondamental unique à énergie $0$ ;
- $N_V=\lceil e^{cV}\rceil$ états excités à énergie totale fixe $\Delta>0$.
Alors leur énergie **par volume** est
$$
\frac{\Delta}{V}\to0,
$$
mais leur entropie par volume vaut asymptotiquement
$$
\frac1V\ln N_V\to c>0.
$$
Donc la densité d’entropie microcanonique possède une discontinuité au bord fondamental :
$$
s(e_0)=0,
$$
mais
$$
\liminf_{e\downarrow e_0}s(e)\ge c.
$$
La continuité utilisée dans U9 ne peut donc pas être omise universellement.
# 3. Forme canonique du même contre-exemple
Le partition function est
$$
Z_V(\beta)=1+N_Ve^{-\beta\Delta}.
$$
À $\beta<\infty$ fixé puis $V\to\infty$,
$$
\frac1V\log Z_V(\beta)\to c.
$$
Ainsi l’excès de pression thermodynamique est
$$
q(\beta)=c,
$$
indépendant de $\beta$ : c’est exactement le cas critique $p=0$ rejeté par U12.
L’entropie par volume reste
$$
s(T)-s_0=c
$$
pour tout $T>0$ après la limite thermodynamique.
# 4. Non-commutation des limites
Pour chaque $V$ fixé,
$$
\lim_{T\to0}\frac{S_V(T)}V=0.
$$
Mais
$$
\lim_{T\to0}\lim_{V\to\infty}\frac{S_V(T)}V=c,
$$
tandis que
$$
\lim_{V\to\infty}\lim_{T\to0}\frac{S_V(T)}V=0.
$$
Donc les deux limites ne commutent pas.
# 5. Théorème de maximalité méthodologique
Les exemples précédents satisfont la mécanique quantique ordinaire et possèdent des Hamiltoniens bornés inférieurement. Ils suffisent donc à démontrer :
$$
\boxed{\text{QM générique}+\text{état fondamental}\not\Rightarrow\text{Nernst universel}.}
$$
Pour obtenir la branche Nernst, il faut au moins exclure les mécanismes qui maintiennent une entropie extensive arbitrairement près du bord fondamental.
# 6. Ce que les hypothèses U8–U12 accomplissent
- U8 exclut la variation arbitraire de la dégénérescence fondamentale dans une famille finie et impose un gap uniforme ;
- U9 impose directement la continuité de l’entropie spécifique au bord et l’équivalence thermodynamique pertinente ;
- U10 dérive cette continuité depuis un comptage contrôlé de défauts locaux ;
- U11 la dérive pour des modes collectifs gapless dont le comptage intégré s’annule comme $\Omega^p$, $p>0$ ;
- U12 la remplace par la condition encore plus abstraite et large $q(\beta)=O(\beta^{-p})$, $p>0$.
Ces restrictions ne sont donc pas de simples choix techniques : U13 montre qu’un contrôle basse énergie de ce type est nécessaire à toute revendication Nernst générale.
# 7. Séparation définitive des deux branches de la troisième loi
U13 renforce la séparation déjà conservée :
- **inatteignabilité dynamique** : U2–U7 ;
- **Nernst / entropie basse température** : U8–U12.
L’une ne doit pas être présentée comme équivalente à l’autre sans hypothèses supplémentaires.
# 8. Statut de la théorie thermodynamique après U13
La formulation mathématiquement défendable n’est pas « les quatre lois sont des théorèmes de toute mécanique quantique imaginable ». Elle est :
> Les quatre lois découlent d’un même cadre d’accessibilité pour une classe physique explicitement admissible ; la branche Nernst exige nécessairement des conditions de régularité basse énergie, et U13 démontre qu’aucun théorème universel ne peut les supprimer toutes.
