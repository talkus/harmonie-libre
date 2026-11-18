> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

# Définition dérivée
La borne U1
$$
\lambda_{\min}(\Phi(\rho))\ge d_B\lambda_{\min}(\rho)\lambda_{\min}(\gamma_B)
$$
suggère de définir, pour chaque bain,
$$
a_B=d_B\lambda_{\min}(\gamma_B)\in(0,1],
$$
$$
c_B=-\ln a_B\ge0.
$$
Ce coût ne dépend pas de la température cible ; il est calculé à partir du bain réellement disponible.
Après une suite de bains,
$$
\lambda_{\min}(\rho_n)\ge\lambda_{\min}(\rho_0)e^{-C},
$$
avec
$$
C=\sum_k c_{B_k}.
$$
# Borne nécessaire
Pour atteindre un état de plus petite valeur propre $\varepsilon$,
$$
\boxed{C\ge\ln\frac{\lambda_{\min}(\rho_0)}{\varepsilon}.}
$$
Ainsi $\varepsilon\to0$ impose $C\to\infty$.
Pour un qubit thermique de gap $\Delta$,
$$
p_e(\beta')=\frac1{1+e^{\beta'\Delta}},
$$
donc
$$
C_{\rm req}\ge\ln\lambda_{\min}(\rho_0)+\ln(1+e^{\beta'\Delta})
=\beta'\Delta+O(1)
$$
à grand $\beta'$.
# Forme Hamiltonienne du coût
Pour un bain fini,
$$
\lambda_{\min}(\gamma_B)=\frac{e^{-\beta E_{\max}}}{Z_B},
$$
d'où
$$
\boxed{c_B=\beta E_{\max}+\ln Z_B-\ln d_B.}
$$
Le coût spectral est donc une fonction des ressources physiques du bain : température, spectre et dimension.
# Résultat du témoin
- $C=19.5067252981$ pour la séquence test ;
- borne produit : $1.3546258442\times10^{-9}$ ;
- forme exponentielle : $1.3546258442\times10^{-9}$ ;
- coûts requis pour $\beta=1,2,5,10,20,40$ : $0.40025,1.21391,4.09370,9.08703,19.08698,39.08698$ ;
- pente asymptotique mesurée : $0.99999999999999$ pour $\Delta=1$ ;
- avec coût fixé $C=12$, la borne $\varepsilon\ge2.46575\times10^{-6}$ impose encore $\beta\le12.9130$.
# Statut
**DÉRIVATION + TEST.** U1.1 fournit une borne nécessaire et additive, pas encore le coût opérationnel optimal. Le prochain objectif est de montrer que des modèles plus généraux de machine ont un coût opérationnel qui domine cette borne spectrale ou d'identifier précisément les cas qui l'échappent.
