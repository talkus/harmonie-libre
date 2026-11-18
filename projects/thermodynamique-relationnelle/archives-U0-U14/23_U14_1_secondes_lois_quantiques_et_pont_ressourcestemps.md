> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : EXTENSION CANONIQUE DE U14.** Cette page ferme deux points de portée : la loi 2 au régime quantique one-shot/catalytique et la formulation temporelle de la loi 3. Les résultats utilisés ici sont des théorèmes publiés ; ils renforcent U14 mais ne sont pas revendiqués comme nouveaux.

# A. Loi 2 au régime quantique one-shot
## A1 — États diagonaux en énergie
Pour un Hamiltonien $H$ et l’état Gibbs
$$
\gamma_\beta=\frac{e^{-\beta H}}{Z_H},
$$
on définit, en unités $k_B=1$,
$$
F_\alpha(\rho,H)=T\,D_\alpha(\rho\Vert\gamma_\beta)-T\ln Z_H,
$$
où $D_\alpha$ est la divergence de Rényi appropriée et $\alpha\ge0$.
Dans le secteur où $[\rho,H]=[\sigma,H]=0$ et pour les opérations thermiques catalytiques exactes dans le cadre de Brandão–Horodecki–Ng–Oppenheim–Wehner, une transition admissible
$$
\rho\longrightarrow\sigma
$$
obéit à toute la famille
$$
\boxed{F_\alpha(\rho,H)\ge F_\alpha(\sigma,H)\qquad\forall\alpha\ge0.}
$$
Dans le domaine précis étudié par ces auteurs, cette famille fournit la caractérisation des transitions catalytiques sans cohérence énergétique. La limite $\alpha\to1$ redonne
$$
F_1(\rho,H)=\operatorname{Tr}(\rho H)-TS(\rho).
$$
Ainsi la loi 2 de U14 doit être lue comme une **famille de monotones** au régime one-shot, et non comme un scalaire unique.
## A2 — États avec cohérence énergétique
Soit $\mathcal D_H$ la déphasing complète entre sous-espaces d’énergie. Les opérations thermiques sont covariantes sous les translations temporelles et ne peuvent pas augmenter les ressources d’asymétrie temporelle.
Une famille de contraintes supplémentaires est
$$
A_\alpha(\rho)=D_\alpha\!\left(\rho\Vert\mathcal D_H(\rho)\right),
$$
avec
$$
\boxed{A_\alpha(\Phi(\rho))\le A_\alpha(\rho).}
$$
Les travaux de Lostaglio–Jennings–Rudolph montrent que les seules libres énergies $F_\alpha$ sont insuffisantes lorsque la cohérence entre niveaux d’énergie est présente. U14 ne prétend donc **pas** que $\{F_\alpha\}$ caractérise toutes les transformations cohérentes ; les monotones d’asymétrie/cohérence constituent des contraintes indépendantes.
## A3 — Formulation canonique corrigée de la loi 2
La loi 2 dans U14 devient :
- au régime macroscopique/i.i.d., la famille se contracte vers la libre énergie ordinaire $F_1$ ;
- au régime one-shot sans cohérence, utiliser la famille $\{F_\alpha\}_{\alpha\ge0}$ ;
- avec cohérence énergétique, ajouter les contraintes d’asymétrie temporelle $\{A_\alpha\}$ et ne revendiquer qu’une famille de conditions nécessaires sauf théorème de suffisance explicitement cité.
# B. Passage ressources finies → temps fini pour la loi 3
## B1 — Borne en ressources
Masanes–Oppenheim considèrent les protocoles de refroidissement les plus généraux compatibles avec conservation totale de l’énergie et réversibilité microscopique. Ils bornent la température finale par deux ressources physiques :
- le volume effectivement accessible du bain $V$ ;
- la fluctuation de travail pire cas $w_{\max}$.
Sous leurs hypothèses sur la densité d’états / capacité calorifique du bain, tout couple fini $(V,w_{\max})$ donne une borne
$$
\boxed{T'_S\ge \Theta(V,w_{\max};H_S,H_B,T)>0.}
$$
Atteindre $T'_S=0$ exige donc qu’au moins une ressource pertinente diverge.
## B2 — Hypothèse de machine thermique régulière
Pour traduire la borne en temps, on impose une hypothèse physique indépendante : pour toute machine thermique fixée et tout temps fini $t$,
$$
V(t)<\infty,\qquad w_{\max}(t)<\infty.
$$
Plus généralement, on peut écrire
$$
t\ge h_V(V),\qquad t\ge h_W(w_{\max}),
$$
avec $h_V,h_W$ croissantes et non bornées. Alors, pour tout $t<\infty$,
$$
\boxed{T'_S(t)\ge \Theta(V(t),w_{\max}(t),\ldots)>0.}
$$
Par conséquent
$$
\boxed{T'_S=0\Longrightarrow t=\infty}
$$
dans cette classe de machines thermiques régulières.
## B3 — Cas local et borne explicite
Pour une interaction locale dans un bain de dimension spatiale $D$, la propagation finie donne une borne du type
$$
t\ge \frac{1}{v}V^{1/D},
$$
et une puissance finie de pompage de travail peut être modélisée par
$$
t\ge \frac{1}{u}w_{\max}.
$$
Pour un bain de rayonnement / champ bosonique massless dans le régime étudié par Masanes–Oppenheim, on obtient à grand $t$
$$
\boxed{T'_S(t)\ge \frac{K}{t^{2D+1}}}
$$
avec $K>0$ dépendant des paramètres physiques. En trois dimensions,
$$
\boxed{T'_S(t)\ge \frac{K}{t^7}>0\qquad(t<\infty).}
$$
Ce $t^{-7}$ n’est pas présenté comme loi universelle de refroidissement : c’est un corollaire explicite pour cette classe de bain et ces relations ressources–temps.
# C. U14 après fermeture
La formulation maître corrigée est :
$$
\boxed{\text{M1--M3 + famille de monotones de loi 2}\Rightarrow\text{lois 0,1,2 et 3A}}
$$
avec, pour la version temporelle de 3A,
$$
\boxed{\text{borne en ressources + machine thermique régulière}\Rightarrow T(t)>0\ \forall t<\infty.}
$$
Et sous M4,
$$
\boxed{\text{M1--M4}\Rightarrow\text{Nernst (3B)}.}
$$
# D. Frontière conservée
- Les $F_\alpha$ ne suffisent pas à caractériser arbitrairement les états cohérents.
- Le passage ressources→temps dépend de l’hypothèse physique de machine thermique régulière et de la classe de bain ; U14 ne transforme pas ce pont en axiome universel.
- La branche Nernst reste séparée logiquement de l’inatteignabilité.
- Ces renforcements sont de la littérature établie ; la nouveauté éventuelle de U14 reste dans sa synthèse/organisation et doit toujours passer la revue externe.
# 22 août 2026 — extension U14.2

	**Mise à jour de portée.** L’énoncé A2/A3 ci-dessus reste correct pour le problème cohérent général, exact ou non catalysé. Il n’est toutefois plus la frontière la plus forte dans le régime **catalytique corrélé** : une prépublication 2025 de Shiraishi–Takagi fournit un critère nécessaire et suffisant sous vraies opérations thermiques à précision arbitraire, sous une condition de support des modes de cohérence.

Dans ce régime précis,
$$
\mathcal C(\sigma)\subseteq\mathcal C(\rho)
$$
et
$$
F_\beta(\rho)\ge F_\beta(\sigma)
$$
sont la structure de convertibilité à retenir selon le théorème externe. La page canonique correspondante est .
La nouvelle lacune prioritaire est le coût de catalyse près du bord $T=0$ : montrer qu’au moins une ressource physique déclarée diverge lorsque erreur cible et corrélation résiduelle tendent simultanément vers zéro.
