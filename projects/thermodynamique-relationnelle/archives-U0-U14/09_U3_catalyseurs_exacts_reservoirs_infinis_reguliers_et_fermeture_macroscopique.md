> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : DÉRIVATION + EXTENSION CONDITIONNELLE.** U3 étend U2 sans rendre gratuites des ressources cachées. Le résultat ferme les catalyseurs exacts non corrélés et raccorde U2 aux réservoirs infinis réguliers et à la limite macroscopique. Les catalyseurs corrélés/approximatifs restent une frontière séparée.

# 1. Classe U3
On conserve les opérations thermiques de U2 et on autorise en plus un catalyseur $\eta_C$ avec Hamiltonien $H_C$, sous la condition exacte
$$
\Lambda(\rho_S\otimes\eta_C)=\rho'_S\otimes\eta_C,
$$
avec restitution **exacte et non corrélée** du catalyseur.
Les ressources consommées doivent appartenir à la fermeture de préparation à température finie et coût fini. Une ressource de rang déficient consommée n'est donc pas gratuite : U1.1 lui attribue une limite de préparation divergente depuis l'intérieur de rang plein.
# 2. Lemme de support $D_0$
Pour un état $\rho$ et une référence de Gibbs strictement positive $\gamma$, définir la divergence de Rényi-Petz d'ordre zéro
$$
D_0(\rho\Vert\gamma)=-\ln\operatorname{Tr}(\Pi_\rho\gamma),
$$
où $\Pi_\rho$ projette sur le support de $\rho$.
Elle satisfait la data processing inequality pour les canaux CPTP et elle est additive sur les produits tensoriels.
Une opération thermique globale sur $S+C$ préserve $\gamma_S\otimes\gamma_C$. Donc
$$
D_0(\rho'_S\otimes\eta_C\Vert\gamma_S\otimes\gamma_C)
\le
D_0(\rho_S\otimes\eta_C\Vert\gamma_S\otimes\gamma_C).
$$
Par additivité et restitution exacte du catalyseur,
$$
D_0(\rho'_S\Vert\gamma_S)
\le
D_0(\rho_S\Vert\gamma_S).
$$
Si $\rho_S$ est de rang plein, alors $D_0(\rho_S\Vert\gamma_S)=0$. Comme $D_0\ge0$,
$$
D_0(\rho'_S\Vert\gamma_S)=0.
$$
Puisque $\gamma_S>0$, cela force $\Pi_{\rho'_S}=I$. Donc
$$
\boxed{\rho_S>0\Longrightarrow\rho'_S>0}
$$
même avec un catalyseur exact arbitraire rendu intact et non corrélé.
# 3. Conséquence pour la troisième loi
Un état thermique exact à $T=0$ est de rang déficient sur le sous-espace fondamental. Il est donc inaccessible depuis un état de rang plein par toute opération catalytique exacte U3 :
$$
\boxed{T>0\ \not\xrightarrow[\text{catalyse exacte U3}]{}\ T=0.}
$$
La loi 3 n'est donc pas cassée par les catalyseurs exacts.
# 4. Ressource frontière : pureté / support déficient
Si un ancilla, une batterie ou une autre ressource de rang déficient est **consommée**, le terme catalytique ne s'annule plus. Une telle ressource peut transporter la pureté nécessaire pour produire un état final de support plus petit.
Cela ne réfute pas U1.1 : préparer exactement une ressource de rang déficient depuis les ressources thermiques libres de rang plein exige
$$
C\ge\ln\frac{\lambda_{\min}(\rho_0)}{\varepsilon}\to\infty
$$
lorsque $\varepsilon\to0$.
La pureté parfaite est donc une **ressource frontière à coût de préparation divergent** dans la fermeture U3.
# 5. Frontière : catalyse corrélée ou approximative
Si le catalyseur est seulement rendu marginalement, ou avec une erreur $\varepsilon>0$, la simplification additive précédente échoue. Des phénomènes de catalyse corrélée et d'« embezzlement » peuvent élargir fortement les transformations possibles.
La version universelle devra donc inclure explicitement dans le coût :
- erreur de restitution ;
- dimension du catalyseur ;
- corrélation créée système-catalyseur ou entre catalyseurs ;
- variation de pureté/cohérence ;
- travail et fluctuations de travail.
Aucune catalyse approximative/corrélée ne sera dite « gratuite » par définition.
# 6. Réservoirs infinis et temps fini
Le no-go de rang de U1 concerne directement une suite finie de ressources de dimension finie. Masanes–Oppenheim étendent l'inatteignabilité à des protocoles arbitraires, y compris avec réservoir de dimension infinie, en bornant les ressources physiques de la machine : volume accessible du bain et fluctuations maximales de travail, puis en reliant ces ressources au temps.
U3 adopte donc le pont régulier :
$$
\text{temps fini}\Longrightarrow\text{volume accessible fini et fluctuations de travail finies}.
$$
Sous les conditions de régularité thermodynamique du bain, cela implique
$$
\boxed{t<\infty\Longrightarrow T_{\mathrm{final}}>0.}
$$
Ce raccord est externe à la borne spectrale U1.1 mais compatible avec elle.
# 7. Fermeture macroscopique
Dans le secteur d'équilibre macroscopique, si la relation d'accessibilité satisfait les axiomes de composition, scaling, stabilité et principe de comparaison de Lieb–Yngvason, il existe une entropie additive/extensive $S$ telle que
$$
X\preceq Y\Longleftrightarrow S(X)\le S(Y).
$$
Ainsi le même langage d'accessibilité de U0–U3 possède une limite macroscopique où la famille de contraintes microscopiques se résume à l'ordre entropique usuel.
Le principe de comparaison n'est pas encore dérivé du modèle microscopique U3 : il reste une hypothèse de fermeture macroscopique à démontrer ou à remplacer.
# 8. Statut des quatre lois sous U3
- **Loi 0** : complète passivité $\Rightarrow$ Gibbs/KMS et classes de température commune.
- **Loi 1** : conservation microscopique exacte de l'énergie.
- **Loi 2** : monotonicité des divergences/free energies ; catalyse exacte compatible ; limite macroscopique entropique conditionnelle à Lieb–Yngvason.
- **Loi 3** : no-go de support même avec catalyse exacte ; coût spectral divergent pour préparer la frontière ; réservoirs infinis couverts sous régularité finie-temps/ressources.
# 9. Résultat négatif utile
U3 **ne** permet pas d'affirmer que tous les catalyseurs sont innocents. Les catalyseurs corrélés peuvent réduire fortement la famille des contraintes et, dans des résultats récents, la convertibilité sous certaines classes catalytiques est gouvernée essentiellement par la libre énergie. Cela renforce la nécessité de compter la corrélation et la qualité de restitution comme ressources physiques.
# 10. Prochain verrou U4
Construire une fonction de coût totale
$$
\mathcal C_{\rm tot}=C_{\rm bain}+C_{\rm travail}+C_{\rm purete}+C_{\rm catalyse}+C_{\rm correlation}+C_{\rm controle}
$$
qui satisfasse :
$$
\mathcal C_{\rm tot}<\infty\Longrightarrow T_{\rm final}>0
$$
pour les protocoles catalytiques approximatifs/corrélés physiquement réguliers, puis dériver le principe de comparaison macroscopique depuis la limite microscopique au lieu de l'ajouter.
# Références
- Pusz & Woronowicz (1978), passivité complète/KMS.
- Brandão et al. (2015), opérations thermiques catalytiques et secondes lois quantiques : [https://arxiv.org/abs/1305.5278](https://arxiv.org/abs/1305.5278)
- Masanes & Oppenheim (2017), troisième loi quantitative avec ressources et réservoirs infinis : [https://www.nature.com/articles/ncomms14538](https://www.nature.com/articles/ncomms14538)
- Lieb & Yngvason (1999), accessibilité adiabatique et entropie : [https://arxiv.org/abs/cond-mat/9708200](https://arxiv.org/abs/cond-mat/9708200)
- Shiraishi (2025), catalyse corrélée et libre énergie : [https://doi.org/10.1103/PhysRevLett.134.160402](https://doi.org/10.1103/PhysRevLett.134.160402)
- Shiraishi & Takagi (2025, prépublication), thermal operations + catalyse corrélée : [https://arxiv.org/abs/2510.05642](https://arxiv.org/abs/2510.05642)
