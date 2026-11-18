> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : DÉRIVATION + RÉSULTAT NÉGATIF STRUCTURANT.** U4 montre qu'un coût scalaire fondé seulement sur la libre énergie moyenne ne peut pas porter la troisième loi. La structure d'accessibilité doit conserver plusieurs ressources indépendantes.

# 1. No-go : travail moyen fini alors que $T\to0$
Considérons un qubit de gap $\Delta$ en contact avec un bain à inverse de température $\beta$. Un protocole standard élève quasi-statiquement le niveau excité de $\Delta$ à $\Delta+w_{\max}$, puis isole le système et ramène le gap à $\Delta$ en conservant les populations.
Après l'étape isotherme,
$$
p_e=\frac1{1+e^{\beta(\Delta+w_{\max})}}.
$$
Après retour du gap à $\Delta$, définir $\beta_f$ par
$$
\frac{p_e}{1-p_e}=e^{-\beta_f\Delta}.
$$
On obtient exactement
$$
\boxed{\beta_f=\beta\left(1+\frac{w_{\max}}{\Delta}\right)}
$$
et donc
$$
\boxed{T_f=\frac{T}{1+w_{\max}/\Delta}}.
$$
Ainsi
$$
T_f\to0\Longleftrightarrow w_{\max}\to\infty.
$$
# 2. Pourtant le travail moyen reste borné
Pour un qubit thermique de gap $E$,
$$
F_\beta(E)=-k_BT\ln(1+e^{-\beta E}).
$$
Le travail réversible moyen pour relever le niveau est
$$
W_{\rm avg}(w)=F_\beta(\Delta+w)-F_\beta(\Delta)
$$
soit
$$
W_{\rm avg}(w)=k_BT\ln\frac{1+e^{-\beta\Delta}}{1+e^{-\beta(\Delta+w)}}.
$$
Quand $w\to\infty$,
$$
\boxed{W_{\rm avg}\to k_BT\ln(1+e^{-\beta\Delta})<\infty.}
$$
Donc une suite de protocoles peut avoir
$$
T_f\to0
$$
tout en gardant un travail moyen/libre-énergie moyen borné.
# 3. Théorème d'insuffisance
Toute jauge de coût qui ne dépend que de $\Delta F$ ou du travail moyen ne peut pas satisfaire universellement
$$
C<\infty\Longrightarrow T_f>0.
$$
La troisième loi exige au moins une ressource sensible aux queues, au support ou à la complexité opérationnelle : ici $w_{\max}$.
Ce résultat concorde directement avec Masanes–Oppenheim : le travail moyen peut rester fini alors que la fluctuation maximale nécessaire diverge.
# 4. Correction de l'axiome de coût : budget vectoriel
Remplacer provisoirement le coût scalaire par un vecteur de ressources
$$
\mathbf C=(C_{\rm spec},\,V_{\rm acc},\,w_{\max},\,C_{\rm purete},\,L_{\rm cat},\,I_{\rm corr},\,C_{\rm ctrl},\ldots).
$$
Définir
$$
X\preceq_{\mathbf C}Y
$$
si une transformation admissible existe sans dépasser chaque composante du budget. La composition additionne ou sous-additionne les composantes selon leur loi physique.
La forme forte de la loi 3 devient :
$$
\boxed{T=0\notin\Omega_{\mathbf C}(X)\quad\text{pour tout vecteur }\mathbf C\text{ entièrement fini}.}
$$
Cette formulation évite de convertir arbitrairement des ressources incompatibles — volume, énergie pire cas, dimension, pureté et corrélation — en un unique nombre avant d'avoir une théorie physique de leur taux d'échange.
# 5. Composantes déjà contrôlées
- $C_{\rm spec}$ : U1.1, divergence logarithmique quand $\lambda_{\min}\to0$.
- $w_{\max}$ et $V_{\rm acc}$ : pont Masanes–Oppenheim pour réservoirs généraux/infinis et temps fini.
- catalyse exacte : U3 donne $L_{\rm cat}=I_{\rm corr}=0$ et le no-go $D_0$.
- pureté exacte consommée : ressource frontière dont le coût de préparation depuis la fermeture $T>0$ diverge.
# 6. Frontière catalytique
Pour une catalyse approximative ou corrélée, une distance de trace seule est insuffisante lorsque la dimension du catalyseur peut croître. U4 doit utiliser une notion thermodynamique de fuite catalytique, par exemple une distance en travail ou une borne qui combine erreur, dimension, énergie et corrélation.
La littérature montre que les catalyseurs corrélés peuvent réduire fortement les contraintes de convertibilité ; cela confirme qu'ils doivent apparaître comme une ressource explicite et non comme une opération gratuite.
# 7. Nouvelle cible U5
Trouver un théorème de fermeture de type : si toutes les composantes physiquement pertinentes de $\mathbf C$ sont finies, alors
$$
T_f\ge f(\mathbf C,H_S)>0,
$$
avec
$$
f\to0
$$
seulement lorsqu'au moins une composante nécessaire diverge.
Ensuite seulement, chercher une scalarisation dérivée de $\mathbf C$ si la dynamique fournit des taux d'échange universels entre ressources.
# Références
- Masanes & Oppenheim (2017), protocole où le travail moyen reste fini alors que $w_{\max}$ diverge : [https://www.nature.com/articles/ncomms14538](https://www.nature.com/articles/ncomms14538)
- Brandão et al. (2015), secondes lois et catalyse : [https://arxiv.org/abs/1305.5278](https://arxiv.org/abs/1305.5278)
- Shiraishi (2025), catalyse corrélée et libre énergie : [https://doi.org/10.1103/PhysRevLett.134.160402](https://doi.org/10.1103/PhysRevLett.134.160402)
- Shiraishi & Takagi (2025, prépublication) : [https://arxiv.org/abs/2510.05642](https://arxiv.org/abs/2510.05642)
