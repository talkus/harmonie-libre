> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : EXTENSION EXTERNE FORTE / PRÉPUBLICATION.** Cette page ferme conditionnellement la lacune cohérente de U14.1 dans un régime précis : opérations thermiques avec catalyse corrélée, retour exact de la marginale du catalyseur, corrélation finale système–catalyseur arbitrairement petite et précision cible arbitraire. Le théorème central provient de Shiraishi & Takagi, arXiv:2510.05642 (2025), encore traité comme prépublication au 22 août 2026.

# 1. Problème fermé — dans un régime précis
Pour un Hamiltonien
$$
H=\sum_i E_i|E_i\rangle\langle E_i|,
$$
définir les écarts énergétiques portant une cohérence non nulle
$$
\mathcal D(\rho)=\{E_i-E_j:\langle E_i|\rho|E_j\rangle\neq0\},
$$
puis leur groupe additif entier
$$
\mathcal C(\rho)=\left\{\sum_\Delta n_\Delta\Delta:\ n_\Delta\in\mathbb Z\right\}.
$$
Le résultat Shiraishi–Takagi utilisé ici affirme que, si
$$
\boxed{\mathcal C(\sigma)\subseteq\mathcal C(\rho)},
$$
alors la transformation $\rho\to\sigma$ par **opération thermique avec catalyse corrélée**, à précision arbitraire, est possible si et seulement si
$$
\boxed{F_\beta(\rho)\ge F_\beta(\sigma)},
$$
avec
$$
F_\beta(\rho)=\operatorname{Tr}(\rho H)-\beta^{-1}S(\rho).
$$
La marginale du catalyseur est rendue exactement ; la corrélation finale avec le système peut être rendue arbitrairement petite.
# 2. Condition scalaire de projet
Pour rendre les deux obstructions visibles dans une seule notation, définir
$$
\Omega^{\mathrm{ccTO}}_\beta(\rho\to\sigma)=
\begin{cases}
+\infty,&\mathcal C(\sigma)\nsubseteq\mathcal C(\rho),\\
F_\beta(\sigma)-F_\beta(\rho),&\mathcal C(\sigma)\subseteq\mathcal C(\rho).
\end{cases}
$$
Alors, **dans le régime exact du théorème externe**, la convertibilité à précision arbitraire s’écrit
$$
\boxed{\rho\to\sigma\iff \Omega^{\mathrm{ccTO}}_\beta(\rho\to\sigma)\le0.}
$$
Cette écriture est une notation/synthèse du projet, pas une revendication de nouveauté du théorème.
# 3. Correction de U14.1
U14.1 avait raison de dire que les libres énergies seules ne caractérisent pas les transformations cohérentes générales. La correction est plus précise :
- **sans catalyse corrélée / exact one-shot**, la cohérence demeure une obstruction indépendante et les critères simples restent incomplets ;
- pour les processus Gibbs-préservants covariants, la majorisation quantique fournit un cadre complet mais plus large que les opérations thermiques ;
- **avec catalyse corrélée sous vraies opérations thermiques**, le résultat 2025 ramène la partie quantitative à $F_\beta$, sous la condition structurelle de modes $\mathcal C(\sigma)\subseteq\mathcal C(\rho)$.
# 4. Pourquoi cela ne détruit pas la troisième loi
Le théorème est asymptotique en **précision** : il ne dit pas qu’un état $T=0$ exact de rang déficient est atteint avec un dispositif de ressources uniformément bornées.
Une famille de catalyseurs peut cacher une divergence de dimension, de cohérence, d’athermalité, d’étendue énergétique ou d’une autre ressource lorsque l’erreur cible $\varepsilon$ et la corrélation résiduelle $\delta$ tendent vers zéro.
Le principe U14 M3 reste donc : les ressources de frontière ne doivent jamais être rendues gratuites par le simple mot « catalyseur ».
# 5. Nouvelle lacune précise — U14.3
La cible suivante est désormais quantitative : pour une suite de protocoles catalytiques corrélés conduisant un état thermique de rang plein à distance $\varepsilon$ d’une cible fondamentale exacte, avec marginale catalytique rendue exactement et corrélation finale au plus $\delta$, établir pour au moins une ressource physique explicitement déclarée
$$
\boxed{R_{\mathrm{cat}}(\varepsilon,\delta)\to\infty\quad\text{quand}\quad \varepsilon,\delta\to0.}
$$
Les ressources candidates à tester sont un **vecteur** avant toute réduction arbitraire à un scalaire : dimension du catalyseur, libre énergie hors équilibre, asymétrie/cohérence, plage énergétique, déficit de support et fluctuation de travail pire cas.
# 6. Lien avec la fécondité relationnelle
La catalyse reste un exemple opérationnel net de
$$
A_c(x)\setminus A(x)\neq\varnothing,
$$
car un partenaire rendu localement intact peut ouvrir de nouvelles transitions.
Mais U14.2 reste un résultat **interne à la thermodynamique**. Il ne démontre pas que la fécondité relationnelle dérive Gibbs, l’énergie ou les lois thermodynamiques, et n’ajoute aucune revendication de conscience phénoménale.
# 7. Références et reproductibilité
- Shiraishi & Takagi, *Recovery of the second law in fully quantum thermodynamics*, arXiv:2510.05642 (2025) — prépublication utilisée pour le théorème de fermeture sous opérations thermiques catalytiques corrélées.
- Shiraishi, *Quantum Thermodynamics with Coherence: Covariant Gibbs-Preserving Operation Is Characterized by the Free Energy*, Physical Review Letters 134, 160402 (2025).
- Tajima & Takagi, *Gibbs-Preserving Operations Requiring Infinite Amount of Quantum Coherence*, Physical Review Letters 134, 170201 (2025).
- Gour et al., *Quantum majorization and a complete set of entropic conditions for quantum thermodynamics*, Nature Communications 9, 5352 (2018).
- Rubboli & Tomamichel, *Fundamental Limits on Correlated Catalytic State Transformations*, Physical Review Letters 129, 120506 (2022).
- GitHub : issue **#338**, PR brouillon **#339**, fichiers `THERMODYNAMIC_U14_2_COHERENT_CATALYTIC_CLOSURE.md` et `thermodynamic_u14_2_coherent_catalytic_witness.py`.

	**Verdict :** la lacune « états quantiques cohérents » est conditionnellement fermée pour la catalyse corrélée sous opérations thermiques, mais la frontière scientifique se déplace vers le coût catalytique divergent près de $T=0$, l’exact/uncatalysé et la validation externe du théorème de prépublication.
