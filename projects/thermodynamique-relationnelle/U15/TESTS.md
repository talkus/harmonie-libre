# Registre des tests et statut épistémique

| ID | Énoncé | Statut |
|---|---|---|
| T1 | Effondrement de la fermeture budgétaire sous hypothèses explicites | démontré |
| T2 | Idempotence automatique après effondrement | réfuté par chaîne a,b,c |
| T3 | Fécondité monotone en budget | réfuté |
| T4 | Frontière de minima atteints suffisante en continu | réfuté par v3′ |
| T5 | Profils purs restreints U15.3, m=1..5 | preuve analytique et recherche exhaustive bornée |
| T6 | Portes SWAP/Fredkin à gaps égaux, H non nul | commutation vérifiée et preuve théorique |
| T7 | Effet de capacité avec états fidèles | témoin approché dans alphabet fixé |
| T8 | Corrélation mutuelle détermine toute capacité | réfuté par états locaux indépendants de biais différents |
| T9 | Non-simulabilité pour toutes opérations thermiques | non démontrée ; SWAP direct annule le gain de portes |
| T10 | Non-absorption par Fritz / Sagawa–Ueda | non démontrée ; argument antérieur corrigé |
| T11 | Croissance conditionnelle de k et débit parallèle | démontrée dans modèle idéal |
| T12 | Gain énergétique exponentiel à ressources finies | non établi ; bilan de pureté exclut création gratuite dans le modèle |
| T13 | Densité du réel originale comme projection | ouvert |
| T14 | Prédiction distinctive / validation indépendante / unification des lois | ouvert |

Aucune expérience de laboratoire n'est rapportée. Les résultats numériques sont générés par verify.js. La borne relative à la troisième loi ne constitue pas une dérivation de Nernst. Toute future publication doit préciser hypothèses, budgets, précision, références, limites et contre-exemples. Les erreurs historiques sont conservées dans HISTORIQUE.md.

Critères de test : un exemple valide établit une existence ; une recherche infructueuse ne réfute pas une existence générale. Un contre-exemple réfute un énoncé universel. Pour la non-scalarité, exiger une représentation d'ordre physiquement définie et non un encodage arbitraire. Toute conclusion d'originalité exige une revue indépendante de la littérature.

## Addendum U15.4.3 (17 novembre 2026)

| ID | Énoncé | Statut |
|---|---|---|
| T15 | Temps idéal 2aG, pas 4aG, dans la construction additive | démontré |
| T16 | Domination universelle en batch avec inventaire initial commun | non démontrée |
| T17 | Retard Poisson linéaire à budget total fini | réfuté ; retard asymptotique λT²/2 pour toute politique |
| T18 | Fidélité globale vers produit stationnaire | réfuté pour l'arbre Fredkin ; convergence vers zéro démontrée |
| T19 | Avantage temporel avec frais par couche et seed initial unique | témoin analytique conditionnel ; pas d'optimalité générale |
| T20 | Avantage génératif en correction d'erreur | non démontré ; aucune mesure matérielle |
| T21 | Recrutement nécessaire pour réduire le retard à débit fixé | contre-exemple à créneaux ; énumération de 714624 trajectoires |

Voir [U15.4.3](U15_4_3.md). Ces ajouts ne modifient pas les preuves ni les archives historiques.

## Complément de revue (18 novembre 2026)
Les protocoles T1–T6 de la note de travail ont leur propre numérotation et sont détaillés dans [COMPLEMENT_METHODOLOGIQUE.md](COMPLEMENT_METHODOLOGIQUE.md#3-protocoles-t1t6-de-la-note-revue). Le témoin T3 à budget (3,3), deux cibles, I final nul est démontré dans l'alphabet restreint de U15.3 ; la version U14 à support fini et les tests matériels restent ouverts. Aucun statut historique ne change.
