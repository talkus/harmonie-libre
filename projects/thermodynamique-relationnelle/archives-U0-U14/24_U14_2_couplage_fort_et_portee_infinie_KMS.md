> **Archive historique — non validée extérieurement.** Transcription scientifique de la source archivée le 11 septembre 2026. Métadonnées et liens privés retirés ; annotations scientifiques conservées. Les statuts historiques ne sont pas une validation indépendante.

**Statut : CORRECTION DE PORTÉE + FERMETURE DU PREMIER PRINCIPE.** U14.2 rend la loi 1 exacte en couplage fort au niveau global et précise strictement ce que la fidélité KMS permet — et ne permet pas — de conclure en dimension infinie.

# A. Première loi exacte en couplage fort
Considérons un composé fermé $S+B$ avec Hamiltonien total dépendant du temps
$$
H_{\mathrm{tot}}(t)=H_S(t)+H_B(t)+H_I(t).
$$
Sous évolution unitaire
$$
\dot\rho_{SB}(t)=-i[H_{\mathrm{tot}}(t),\rho_{SB}(t)],
$$
l'énergie totale moyenne vaut
$$
E_{\mathrm{tot}}(t)=\operatorname{Tr}[\rho_{SB}(t)H_{\mathrm{tot}}(t)].
$$
Sa dérivée est
$$
\frac{dE_{\mathrm{tot}}}{dt}=\operatorname{Tr}[\rho_{SB}(t)\dot H_{\mathrm{tot}}(t)],
$$
car la contribution commutateur s'annule par cyclicité de la trace. On définit donc le travail externe exact
$$
W_{\mathrm{ext}}:=\int_{t_i}^{t_f}dt\,\operatorname{Tr}[\rho_{SB}(t)\dot H_{\mathrm{tot}}(t)].
$$
Alors
$$
\boxed{\Delta E_S+\Delta E_B+\Delta E_I=W_{\mathrm{ext}}.}
$$
Si l'on définit la chaleur reçue par le système par le changement opposé de l'énergie du bain nu,
$$
Q:=-\Delta E_B,
$$
on obtient l'identité exacte
$$
\boxed{\Delta E_S=Q+W_{\mathrm{ext}}-\Delta E_I.}
$$
Ainsi la formule faible-couplage
$$
\Delta E_S=Q+W
$$
n'est exacte que lorsque $\Delta E_I=0$ — par exemple si l'interaction est négligeable aux extrémités ou revient à sa valeur initiale — ou si l'on adopte une convention qui alloue explicitement l'énergie d'interaction.
## A1 — Convention inclusive exacte
Si toute l'énergie d'interaction est attribuée au système,
$$
U_S^{\mathrm{incl}}:=E_S+E_I,
$$
alors
$$
\boxed{\Delta U_S^{\mathrm{incl}}=Q+W_{\mathrm{ext}}.}
$$
C'est une première loi exacte à tout couplage, avec convention de frontière explicitement annoncée.
## A2 — Hamiltonien de force moyenne à l'équilibre
Pour l'équilibre global à inverse de température $\beta$,
$$
\rho_{SB}^{\beta}=\frac{e^{-\beta H_{\mathrm{tot}}}}{Z_{SB}},
$$
on définit l'Hamiltonien de force moyenne $H_S^*(\beta)$ par
$$
e^{-\beta H_S^*(\beta)}:=\frac{\operatorname{Tr}_B e^{-\beta H_{\mathrm{tot}}}}{Z_B},
$$
avec
$$
Z_B=\operatorname{Tr}_B e^{-\beta H_B}.
$$
Alors
$$
Z_S^*=\operatorname{Tr}_S e^{-\beta H_S^*}=\frac{Z_{SB}}{Z_B},
$$
et l'état réduit d'équilibre est
$$
\rho_S^\beta=\frac{e^{-\beta H_S^*}}{Z_S^*}.
$$
Cela fournit une thermodynamique réduite cohérente à l'équilibre fort-couplage. Toutefois $H_S^*$ dépend généralement de $\beta$ : l'énergie interne thermodynamique correspondante est
$$
U_S^*=-\partial_\beta\ln Z_S^*
=\langle H_{\mathrm{tot}}\rangle_\beta-\langle H_B\rangle_{\beta,B},
$$
pas simplement $\langle H_S^*\rangle$ en général.
## A3 — Position canonique de U14 sur le couplage fort
U14 revendique donc comme invariant fondamental la conservation **globale**
$$
\Delta E_{\mathrm{tot}}=W_{\mathrm{ext}},
$$
et n'utilise $\Delta E_S=Q+W$ comme identité de sous-système que lorsque la convention d'interaction est explicitée. La littérature de couplage fort souligne que la notion de chaleur au niveau réduit peut être convention-dépendante ; U14 ne prétend pas supprimer cette ambiguïté.
# B. Portée exacte de la fidélité KMS
Soit $(\mathcal A,\tau_t)$ un système dynamique $C^*$ et $\omega$ un état $\beta$-KMS. Soit
$$
(\mathcal H_\omega,\pi_\omega,\Omega_\omega)
$$
sa représentation GNS et
$$
\mathcal M_\omega:=\pi_\omega(\mathcal A)''.
$$
Un théorème standard de théorie KMS/modulaire implique que $\Omega_\omega$ est cyclique et séparant pour $\mathcal M_\omega$. Par conséquent l'extension normale
$$
\bar\omega(X)=\langle\Omega_\omega,X\Omega_\omega\rangle
$$
est fidèle sur $\mathcal M_\omega$.
## B1 — Préservation par automorphisme
Si $\alpha$ est un $W^*$-automorphisme de $\mathcal M_\omega$, alors
$$
\bar\omega_t:=\bar\omega\circ\alpha^{-1}
$$
reste fidèle : pour $X\ge0$,
$$
\bar\omega_t(X)=0
\Rightarrow
\bar\omega(\alpha^{-1}(X))=0
\Rightarrow
\alpha^{-1}(X)=0
\Rightarrow
X=0.
$$
## B2 — Préservation par restriction locale
Si $\mathcal N\subset\mathcal M_\omega$ est une sous-algèbre de von Neumann unitaire, alors la restriction $\bar\omega|_{\mathcal N}$ est fidèle, puisque pour $X\in\mathcal N_+$,
$$
\bar\omega(X)=0\Rightarrow X=0.
$$
Donc
$$
\boxed{\text{état normal fidèle}\xrightarrow{\text{automorphisme + restriction}}\text{état local normal fidèle}.}
$$
# C. Correction essentielle : fidélité $\neq$ température positive
Cette fermeture ne doit **pas** être sur-interprétée.
Un état fondamental en dimension infinie peut être fidèle sur certaines algèbres locales. Par conséquent
$$
\boxed{\text{fidèle}\not\Rightarrow T>0}
$$
en général dans les systèmes infinis.
Ainsi U6/U14 ne peuvent utiliser la fidélité que pour exclure une **cible non fidèle dans le même secteur normal représenté**. La fidélité n'est pas un critère universel du zéro absolu en algèbres infinies.
Pour une troisième loi générale en dimension infinie, il faut donc un monotone ou une borne de ressources/temps adaptée à la classe physique considérée — par exemple les bornes de Masanes–Oppenheim lorsque leurs hypothèses de bain et de machine sont satisfaites.
# D. Frontières mathématiques explicites
La formulation infinie sûre est :
$$
\boxed{\text{KMS fini-}\beta\Rightarrow\text{extension GNS normale fidèle sur }\mathcal M_\omega.}
$$
Puis
$$
\boxed{\text{automorphismes de }\mathcal M_\omega\text{ et restrictions unitaires préservent cette fidélité}.}
$$
Ce résultat :
- ne prétend pas que l'état KMS d'origine est fidèle sur toute $C^*$-algèbre abstraite ;
- ne couvre pas un changement de représentation, de secteur de phase ou une limite singulière ;
- ne permet pas d'identifier universellement $T=0$ à la non-fidélité ;
- fournit seulement un no-go exact de création d'une cible non fidèle à l'intérieur du secteur normal fixé.
# E. Conséquence pour U14
Après U14.2, la première loi est formulée sans hypothèse de faible couplage :
$$
\boxed{\Delta E_S+\Delta E_B+\Delta E_I=W_{\mathrm{ext}}.}
$$
La forme traditionnelle suit comme corollaire sous convention/conditions explicites.
La branche infinie de la loi 3 est simultanément restreinte à ce qui est réellement démontré :
$$
\boxed{\text{préservation de fidélité dans un secteur normal fixé, pas critère universel de }T=0.}
$$
# F. Références de contrôle
- U. Seifert, *First and Second Law of Thermodynamics at Strong Coupling*, Phys. Rev. Lett. 116, 020601 (2016).
- C. Jarzynski, *Stochastic and Macroscopic Thermodynamics of Strongly Coupled Systems*, Phys. Rev. X 7, 011008 (2017).
- P. Talkner & P. Hänggi, *Colloquium: Statistical mechanics and thermodynamics at strong coupling: Quantum and classical*, Rev. Mod. Phys. 92, 041002 (2020), erratum 2022.
- Théorie standard KMS / Tomita–Takesaki : un état KMS induit une représentation GNS modulaire avec vecteur cyclique et séparant sur l'algèbre de von Neumann engendrée.
