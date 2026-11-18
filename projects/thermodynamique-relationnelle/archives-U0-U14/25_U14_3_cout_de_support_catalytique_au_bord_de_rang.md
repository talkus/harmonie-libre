> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : MATH / DÉRIVATION.** U14.3 étend la borne spectrale U1/U1.1 à des auxiliaires finis arbitraires, y compris des catalyseurs pouvant rester corrélés au système. Le résultat ferme le contournement par catalyse dans le secteur fini lorsque le déficit de support est explicitement compté.

# 1. Coût de support
Soit $S$ de dimension $d_S$, avec état initial fidèle
$$
\rho_S>0.
$$
On ajoute des auxiliaires finis $\eta_j$ de dimensions $d_j$, puis une unité globale arbitraire et on réduit vers $S$.
Définir
$$
a_{\rm supp}(\eta_j)=d_j\lambda_{\min}(\eta_j),
$$
$$
c_{\rm supp}(\eta_j)=-\ln a_{\rm supp}(\eta_j),
$$
et $c_{\rm supp}=+\infty$ si $\eta_j$ est de rang déficient. Le budget total est
$$
C_{\rm supp}=\sum_j c_{\rm supp}(\eta_j).
$$
# 2. Théorème spectral
L’état global initial vérifie
$$
\rho_S\otimes_j\eta_j\ge \lambda_{\min}(\rho_S)\prod_j\lambda_{\min}(\eta_j)\,I.
$$
La conjugaison unitaire conserve l’ordre de Löwner et la trace partielle donne un facteur $\prod_jd_j$. Par conséquent
$$
\boxed{\lambda_{\min}(\rho'_S)\ge\lambda_{\min}(\rho_S)e^{-C_{\rm supp}}.}
$$
Aucune conservation d’énergie n’est requise pour cette borne ; elle s’applique donc a fortiori aux opérations thermiques.
# 3. Distance à un bord de rang
Soit $\sigma$ une cible supportée sur un projecteur $P$ de rang $r<d_S$. La mesure $\{P,I-P\}$ et la contraction de la distance de trace donnent
$$
T(\rho'_S,\sigma)\ge\operatorname{Tr}[(I-P)\rho'_S].
$$
Donc
$$
\boxed{T(\rho'_S,\sigma)\ge(d_S-r)\lambda_{\min}(\rho_S)e^{-C_{\rm supp}}.}
$$
Si $T(\rho'_S,\sigma)\le\varepsilon$,
$$
\boxed{C_{\rm supp}\ge\max\!\left\{0,\ln\frac{(d_S-r)\lambda_{\min}(\rho_S)}{\varepsilon}\right\}.}
$$
Ainsi
$$
\boxed{\varepsilon\to0\Longrightarrow C_{\rm supp}\to+\infty.}
$$
# 4. Corollaire troisième loi
Pour une limite Gibbs $T\to0$ supportée sur le sous-espace fondamental de rang $g_0<d_S$, prendre $r=g_0$. Toute suite finie-dimensionnelle construite depuis un état de rang plein et des auxiliaires de coût de support uniformément borné reste à distance strictement positive du bord exact.
Un catalyseur pur ou de rang déficient ne fournit pas un contre-exemple : il possède $c_{\rm supp}=+\infty$ dans le budget déclaré.
# 5. Catalyse corrélée
La preuve ne suppose aucune factorisation finale. Le catalyseur peut être rendu dans sa marginale et rester corrélé au système : après trace du catalyseur, la même borne sur $\rho'_S$ demeure.
U14.2 et U14.3 sont donc compatibles : la catalyse corrélée peut permettre une précision arbitraire dans le régime du théorème Shiraishi–Takagi, mais une suite approchant un support $T=0$ exact ne peut garder $C_{\rm supp}$ borné dans le secteur fini.
# 6. Vérification
Le témoin déterministe GitHub **passe** : `U14_3_CATALYTIC_SUPPORT_WITNESS_PASS`.
Exemple : $\lambda_{\min}(\rho)=0.3$, catalyseur candidat $(0.6,0.4)$, donc $e^{-c}=0.8$ et borne $0.24$. Une permutation CNOT crée une corrélation finale positive mais la marginale système conserve $\lambda_{\min}=0.3\ge0.24$. Pour $\varepsilon=10^{-6}$, la borne impose $C_{\rm supp}\ge12.6115377536$.
GitHub : issue **#340**, PR brouillon **#341**.
# 7. Frontière restante
- auxiliaires véritablement infinis sous contraintes d’énergie/moments ;
- limite thermodynamique où dimensions et spectres varient ensemble ;
- coût opérationnel optimal en dimension, libre énergie, cohérence, plage d’énergie et travail pire cas ;
- pont indépendant entre primitives relationnelles et structure thermodynamique.

	**Verdict :** le contournement fini par catalyse corrélée est fermé au niveau du support : approcher un bord de rang déficient exige un budget de support divergent, logarithmiquement en $1/\varepsilon$.
