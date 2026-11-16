# Étiquetage itératif de la mémoire — prototype v0.1

Module isolé, à intégrer par revue dans Conscience C / Architecture C. Ne remplace pas le ledger SHA-256 existant et n'agit pas directement sur la mémoire interne de ChatGPT.

## Contrat
- Chaque itération reçoit un type épistémique, un pointeur de preuve, un groupe de filiation, un acteur, une raison et le hash de l'itération précédente.
- Une nouvelle étiquette s'ajoute; jamais d'écrasement de l'ancienne. CONFLIT_OUVERT demeure dans l'historique même après une revue.
- Une copie de la même source garde son lineage_id: aucune indépendance artificielle.
- RELU_VERIFIE et REJOUE exigent une déclaration de revue indépendante et une trace antérieure. **Cette déclaration n'est pas une vérification externe garantie** : le futur adaptateur devra contrôler l'identité du réviseur et la preuve réelle avant toute promotion exploitable.
- Le hash vérifie l'intégrité interne, **pas la vérité**; la méthode audit() ne vérifie pas les archives externes.
- Le résultat ne donne aucune autorité d'exécution.
- Une mémoire textuelle sans consentement, source ou légitimité ne doit pas être ingérée automatiquement.

## Tests
`python -m unittest discover -s memory/iterative_labels -p 'test_*.py' -v`

Sept contrôles sont fournis. Une implémentation locale équivalente a réussi 7/7 tests lors de la préparation; les tests GitHub du commit courant ne sont pas encore confirmés.

## Étape suivante
Adapter au ledger `conscience-c/brain` en conservant les anciens événements et leurs empreintes; tests de concurrence, export/import, reprise et vérification de non-régression sur les statuts déjà stockés.
