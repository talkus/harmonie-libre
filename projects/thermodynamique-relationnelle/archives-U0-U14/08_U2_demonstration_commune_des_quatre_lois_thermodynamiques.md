> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**U2 — théorème commun, domaine fini.** Les lois 0, 1, 2 et la forme d’inatteignabilité de la loi 3 découlent d’un même cadre opérationnel sous hypothèses explicites. Ce résultat est une démonstration dans cette classe, pas une preuve de toutes les formulations possibles de la thermodynamique.

# Cadre commun
Un système thermométrique fini est un couple $(\mathcal H,H)$ avec au moins deux énergies distinctes. Les opérations élémentaires utilisent :
- des ressources d’équilibre disponibles en copies arbitraires sans rendre la théorie triviale ;
- une évolution microscopiquement réversible $U$ ;
- la conservation exacte $[U,H_{\rm tot}]=0$ ;
- des auxiliaires thermiques finis et, pour toute opération de coût fini, à température finie ;
- la possibilité de jeter un sous-système après l’évolution ;
- une batterie explicite lorsqu’un transfert de travail doit être comptabilisé.
Le coût spectral d’un bain fini $B$ est
$$
c_B=-\ln\!\left[d_B\lambda_{\min}(\gamma_B)\right]\ge0,
$$
et le coût d’une suite finie est $C=\sum_k c_{B_k}$.
# Théorème U2
Sous ce cadre :
1. les classes d’équilibre sont exactement les classes Gibbs/KMS de même $\beta$ — **loi 0** ;
2. toute opération élémentaire conserve exactement l’énergie totale — **loi 1** ;
3. à $\beta$ fixé, l’entropie relative à Gibbs et donc la libre énergie hors équilibre ne peuvent augmenter sous une opération thermique libre — **loi 2** ;
4. depuis un état de rang plein, aucune suite de coût spectral fini utilisant uniquement des auxiliaires thermiques finis à $\beta<\infty$ ne peut produire exactement un état $T=0$ de rang déficient — **loi 3, inatteignabilité**.
# Preuve de la loi 0 — l’équilibre et la température émergent
## Étape 0.1 — non-trivialité ⇒ passivité complète
Une ressource déclarée libre peut être ajoutée en un nombre arbitraire de copies. Si plusieurs copies permettaient d’extraire du travail cycliquement, une quantité arbitrairement grande de ressource libre fournirait du travail et trivialiserait l’ordre des transformations.
La ressource d’équilibre libre doit donc être **complètement passive**.
## Étape 0.2 — passivité complète ⇒ Gibbs/KMS
Le théorème de Pusz–Woronowicz donne que les états complètement passifs sont les états KMS ou les états fondamentaux. En dimension finie et à température strictement positive,
$$
\gamma_\beta(H)=\frac{e^{-\beta H}}{Z_H(\beta)}.
$$
Ainsi la forme Gibbs n’est pas postulée comme définition de la température : elle est sélectionnée par la non-trivialité opérationnelle.
## Étape 0.3 — relation d’équilibre
Définissons
$$
A\sim_T B
$$
si le produit de leurs ressources d’équilibre demeure complètement passif pour $H_A+H_B$.
Si $\beta_A=\beta_B=\beta$,
$$
\gamma_{\beta}(H_A)\otimes\gamma_{\beta}(H_B)
=\gamma_{\beta}(H_A+H_B),
$$
donc le produit est complètement passif.
Inversement, si $\beta_A\ne\beta_B$ et les deux Hamiltoniens sont thermométriquement non triviaux, le produit
$$
\gamma_{\beta_A}(H_A)\otimes\gamma_{\beta_B}(H_B)
$$
ne peut pas s’écrire comme un Gibbs unique $e^{-\beta(H_A+H_B)}/Z$. Il n’est donc pas complètement passif ; suffisamment de copies permettent une extraction de travail.
Par conséquent
$$
\boxed{A\sim_TB\iff\beta_A=\beta_B.}
$$
L’égalité de $\beta$ est réflexive, symétrique et transitive. En particulier,
$$
A\sim_TB\land B\sim_TC\Rightarrow A\sim_TC.
$$
C’est la loi 0 et le paramètre de température apparaît comme étiquette des classes d’équivalence.
# Preuve de la loi 1 — invariant énergétique
Pour système $S$, bain $B$ et batterie $W$,
$$
[U,H_S+H_B+H_W]=0.
$$
Donc
$$
U^\dagger H_{\rm tot}U=H_{\rm tot},
$$
et pour tout état initial
$$
\Delta E_S+\Delta E_B+\Delta E_W=0.
$$
En posant l’énergie reçue par le système
$$
Q=-\Delta E_B,\qquad W=-\Delta E_W,
$$
on obtient exactement
$$
\boxed{\Delta E_S=Q+W.}
$$
La loi 1 est donc l’invariant du même ensemble de transformations qui définira l’accessibilité thermodynamique.
# Preuve de la loi 2 — monotonie de l’ordre thermodynamique
Considérons une opération thermique libre à même $\beta$ :
$$
\Phi_\beta(\rho_S)=\operatorname{Tr}_B\left[U(\rho_S\otimes\gamma_B(\beta))U^\dagger\right],
$$
avec $[U,H_S+H_B]=0$.
Le produit Gibbs satisfait
$$
\gamma_S(\beta)\otimes\gamma_B(\beta)
=\frac{e^{-\beta(H_S+H_B)}}{Z_SZ_B},
$$
donc il commute avec $U$ et
$$
\Phi_\beta(\gamma_S)=\gamma_S.
$$
Par contraction de l’entropie relative sous tout canal CPTP,
$$
D(\Phi_\beta(\rho)\Vert\gamma_S)
=D(\Phi_\beta(\rho)\Vert\Phi_\beta(\gamma_S))
\le D(\rho\Vert\gamma_S).
$$
Or
$$
k_BT\,D(\rho\Vert\gamma_S)
=F_\beta(\rho)-F_\beta(\gamma_S).
$$
Ainsi
$$
\boxed{F_\beta(\Phi_\beta(\rho))\le F_\beta(\rho).}
$$
Sans batterie, $Q=\Delta E_S$ et $\Delta F=\Delta E-T\Delta S\le0$ donne
$$
\boxed{\Delta S_S-\frac{Q}{T}\ge0,}
$$
forme de Clausius.
Avec une batterie idéale dont l’entropie ne change pas, le même bilan donne le travail reçu par le système
$$
\boxed{W\ge\Delta F_S,}
$$
ou, en extraction, $W_{\rm out}\le F_{\rm initial}-F_{\rm final}$.
À l’échelle quantique générale, des monotones supplémentaires peuvent être nécessaires pour caractériser toutes les transitions ; cela renforce plutôt qu’il n’annule le principe de monotonie.
# Preuve de la loi 3 — frontière de rang à coût infini
Soit $\rho>0$ un état de rang plein et $\gamma_B>0$ un bain fini à $\beta<\infty$. Alors
$$
\rho\otimes\gamma_B
\ge\lambda_{\min}(\rho)\lambda_{\min}(\gamma_B)I_{SB}.
$$
Une conjugaison unitaire préserve cette inégalité. En prenant la trace partielle,
$$
\Phi_\beta(\rho)
\ge d_B\lambda_{\min}(\rho)\lambda_{\min}(\gamma_B)I_S.
$$
Donc
$$
\boxed{\lambda_{\min}(\Phi_\beta(\rho))
\ge a_B\lambda_{\min}(\rho),\qquad
a_B=d_B\lambda_{\min}(\gamma_B)>0.}
$$
Après $n$ opérations,
$$
\lambda_{\min}(\rho_n)
\ge\lambda_{\min}(\rho_0)\prod_{k=1}^n a_{B_k}
=\lambda_{\min}(\rho_0)e^{-C_n},
$$
avec
$$
C_n=\sum_{k=1}^n[-\ln a_{B_k}].
$$
Tout $C_n<\infty$ implique
$$
\lambda_{\min}(\rho_n)>0.
$$
Un état Gibbs exact à $T=0$ est supporté uniquement sur le sous-espace fondamental et est de rang déficient dès que le système possède au moins un état excité. Il a donc $\lambda_{\min}=0$. Contradiction.
Ainsi
$$
\boxed{T=0\ \text{exact}\Rightarrow C=\infty.}
$$
Plus quantitativement, atteindre une cible de valeur propre minimale $\varepsilon$ nécessite
$$
\boxed{C\ge\ln\frac{\lambda_{\min}(\rho_0)}{\varepsilon}.}
$$
Pour un qubit de gap $\Delta$, si
$$
L=\lambda_{\min}(\rho_0)e^{-C}>0,
$$
alors toute cible Gibbs atteignable satisfait
$$
p_e(\beta')\ge L,
$$
soit
$$
\boxed{\beta'\le\frac1\Delta\ln\frac{1-L}{L}.}
$$
Pour tout coût fini, $\beta'$ reste fini et donc $T'>0$.
# Corollaire temps fini
Le résultat précédent est d’abord un théorème de **ressources finies**. Pour le convertir en temps, il faut une hypothèse physique reliant durée finie et ressources accessibles finies : région de bain finie causalement accessible, transfert d’énergie maximal fini et vitesse d’interaction finie.
Sous ce type d’hypothèses, Masanes–Oppenheim obtiennent des bornes quantitatives de température en fonction des ressources et du temps ; dans leur exemple de rayonnement en dimension spatiale $D$, la borne se comporte comme $T'\gtrsim t^{-(2D+1)}$, soit $t^{-7}$ pour $D=3$.
Le projet doit donc distinguer :
- **U2 interne** : $C<\infty\Rightarrow T'>0$, démontré ci-dessus ;
- **corollaire temporel** : $t<\infty\Rightarrow C(t)<\infty\Rightarrow T'>0$, sous hypothèses de machine physiquement régulière.
# Contrôles négatifs
1. **Ressource déjà à **$T=0$ : un ancilla pur fondamental peut refroidir exactement par SWAP. Il n’est donc pas une ressource libre à coût fini de la classe U2.
2. **Hamiltonien thermométriquement trivial** : si un système n’a aucune séparation d’énergie, $\beta$ n’est pas identifiable ; il ne peut pas servir de thermomètre pour la loi 0.
3. **Ressources non physiques illimitées** : un bain de densité d’états pathologique ou un transfert d’énergie non borné peut contourner l’inatteignabilité temporelle ; ces cas montrent pourquoi la finitude physique est une hypothèse réelle et falsifiable.
# Ce qui est démontré et ce qui ne l’est pas
**DÉMONTRÉ dans U2 :** les quatre propriétés 0/1/2/3-inatteignabilité dérivent d’une architecture opérationnelle commune en dimension finie avec ressources thermiques libres à température finie.
**NON DÉMONTRÉ universellement :** la formulation de Nernst/Heat Theorem pour toute famille de Hamiltoniens, les réservoirs arbitraires infinis, les catalyseurs de pureté/rang déficient, les transitions de phase et une équivalence complète avec toute l’axiomatique macroscopique de Lieb–Yngvason.
# Références de contrôle
- Pusz & Woronowicz, *Passive states and KMS states for general quantum systems*, Commun. Math. Phys. 58 (1978) 273–290.
- Brandão, Horodecki, Ng, Oppenheim & Wehner, *The second laws of quantum thermodynamics*, arXiv:1305.5278 / PNAS 112 (2015).
- Lieb & Yngvason, *The Physics and Mathematics of the Second Law of Thermodynamics*, Phys. Rep. 310 (1999), arXiv:cond-mat/9708200.
- Masanes & Oppenheim, *A general derivation and quantification of the third law of thermodynamics*, Nature Communications 8, 14538 (2017), arXiv:1412.3828.
# Verdict scientifique U2
$$
\boxed{
\text{équilibre non trivial}
+\text{conservation énergétique}
+\text{réversibilité microscopique}
+\text{ressources finies}
\Longrightarrow
\text{lois }0,1,2,3\text{ (inatteignabilité) dans la classe U2}.}
$$
La prochaine étape n’est plus de redémontrer séparément les quatre lois dans ce domaine, mais d’élargir le domaine de validité sans perdre le théorème : catalyseurs généraux, réservoirs infinis physiquement réguliers, limite macroscopique et coût-temps optimal.
