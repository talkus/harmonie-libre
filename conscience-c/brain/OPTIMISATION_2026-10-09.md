# Coordination multi-échelle — vérification du 9 octobre 2026

La version logicielle `0.3.3` réduit les recherches répétées pendant un examen, à partir de `main` au commit `1461cd31022fbbe7b9398379285e4bc68a15a360`. Les quatre échelles gardent le même contrat, des périmètres distincts et la priorité déclarée par les intentions. Une réservation ne calcule désormais que sa base pertinente et, pour CC-WORK-2, celles de ses dépendances transitives.

Le partage est limité à un appel. Il n'ajoute aucun cache persistant, aucun budget par échelle ni aucune nouvelle autorité. La vue globale conserve les inconnues situées, les objections, les dates, les compteurs d'équité et la distinction entre dépendance d'exécution et cible de relecture. Les empreintes historiques des deux formats restent compatibles.

## Validation locale

Le 9 octobre 2026, `python -m unittest discover -s tests -v` a réussi **486 tests** ; `python ../verify_reprise.py` a réussi **11 contrôles de continuité**. Ces nombres décrivent cette exécution locale, pas un résultat permanent.

Les cinq nouveaux tests vérifient les empreintes capturées avant l'optimisation, la borne des parcours pour 128 unités, les dépendances transitives d'une lecture ciblée et la prise en compte ultérieure des changements de preuves, d'objections et de temps. Les tests existants vérifient aussi la récupération après arrêt de processus, le budget, l'équité, les refus d'écriture concurrente et la péremption ascendante.

## Mesure bornée

La mesure compare uniquement le calcul des bases de preuves, avec des données synthétiques : deux claims concernés, 5 005 entrées de preuves, 5 006 événements et sept répétitions par cas. Les quatre périmètres sont répétés dans les plans de 128 unités. Le résultat est la médiane mesurée dans l'environnement local.

| Contrat | Unités | Avant | Après |
|---|---:|---:|---:|
| CC-WORK-1 | 4 | 3,524 ms | 0,686 ms |
| CC-WORK-2 | 4 | 4,639 ms | 0,837 ms |
| CC-WORK-1 | 128 | 162,142 ms | 2,685 ms |
| CC-WORK-2 | 128 | 137,012 ms | 2,379 ms |

Les empreintes avant/après sont identiques dans les quatre cas. Cette mesure exclut la vérification cryptographique du journal, les écritures et le démarrage des processus. Elle ne mesure donc ni la vitesse complète du service ni sa disponibilité. Les détails et empreintes des fichiers examinés sont conservés dans [le reçu local](validation/2026-10-09-work-bases.json).

## Déploiement et prochaine reprise

Cette vérification ne déploie pas `0.3.3` sur AWS. Le connecteur AWS exige une réauthentification ; l'état actuel des services n'a pas pu être consulté. Le [reçu antérieur de `0.3.2`](deployment/VERIFICATION_2026-10-09.md) reste un constat historique distinct.

La prochaine étape opérationnelle est de rétablir l'accès AWS, installer la version validée, puis revérifier le service et la reprise depuis une mémoire réelle compatible. Une activation nécessite cette mémoire et un plan lié à ses claims existants. Aucun état `t0` n'est créé pour combler leur absence. Aucun fonctionnement continu ni absence d'interruption n'est attesté par les tests locaux.
