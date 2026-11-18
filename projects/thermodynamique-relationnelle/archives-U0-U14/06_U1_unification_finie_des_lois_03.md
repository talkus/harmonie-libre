> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**U1 — résultat initial.** Dans une classe finie d'opérations thermiques à température finie, les quatre lois apparaissent comme quatre propriétés du même objet d'accessibilité. Référence exécutable : [draft PR #292]([lien interne retiré]).

# Classe commune
$$
\Phi_\beta(\rho_S)=\operatorname{Tr}_B\left[U(\rho_S\otimes\gamma_B(\beta))U^\dagger\right],
$$
avec
$$
[U,H_S+H_B]=0,
$$
bain fini et $\beta<\infty$.
# Quatre propriétés
**Loi 0** : $\Phi_\beta(\gamma_S(\beta))=\gamma_S(\beta)$ ; l'état thermique est le point fixe/libre.
**Loi 1** : l'énergie totale de la dilatation est conservée ; avec bain+batterie, $\Delta E_S=Q+W$.
**Loi 2** :
$$
D(\Phi_\beta(\rho)\Vert\gamma_\beta)\le D(\rho\Vert\gamma_\beta),
$$
donc la différence de libre énergie $k_BT D(\rho\Vert\gamma_\beta)$ ne croît pas dans ce cadre.
**Loi 3 — inatteignabilité dans U1** : si $\rho>0$ et $\gamma_B>0$, alors $\rho\otimes\gamma_B>0$, l'unitaire conserve la stricte positivité et la trace partielle d'un opérateur strictement positif reste strictement positive. Ainsi toute composition finie préserve le rang plein. L'état $T=0$, supporté uniquement sur le sous-espace fondamental, est donc inaccessible exactement depuis un état de température finie.
# Borne quantitative
Pour un bain de dimension $d_B$,
$$
\boxed{\lambda_{\min}(\Phi_\beta(\rho))\ge d_B\lambda_{\min}(\rho)\lambda_{\min}(\gamma_B)>0.}
$$
Pour une cible Gibbs qubit de gap $\Delta$, si $p_e\ge L>0$,
$$
\beta'\le\frac1\Delta\ln\frac{1-L}{L}.
$$
La température inverse atteignable reste donc finie lorsque la borne de ressource reste strictement positive.
# Contrôle négatif essentiel
Une ressource déjà pure à $T=0$ permet un SWAP exact vers l'état fondamental. Le théorème dépend donc réellement du fait que les ressources thermiques libres soient elles-mêmes à température finie/rang plein ; il ne cache pas la loi 3 dans une définition arbitraire de coût.
# Résultat numérique du témoin
- erreur point fixe loi 0 : $2.78\times10^{-17}$ ;
- erreur conservation énergie : $0$ ;
- entropie relative : $0.2560125\to0.0205569$ ;
- $\lambda_{\min}$ observée après collision : $0.1897303$, borne analytique $0.0956752$ ;
- 5 bains à températures finies : $p_e=4.5397869\times10^{-5}>0$, $\beta_{\rm eff}=10$ ;
- borne de rang composée : $1.3546\times10^{-9}>0$ ;
- contrôle avec ressource $T=0$ : $p_e=0$ par SWAP exact.
# Statut scientifique
**DÉRIVATION + TEST dans un domaine restreint.** U1 est une vraie unification interne de la classe finie considérée, mais pas encore une preuve universelle. Les extensions critiques sont : catalyseurs, ressources de pureté, dimensions infinies, temps/coût continu, thermodynamic limit et récupération axiomatique complète de Lieb–Yngvason.
