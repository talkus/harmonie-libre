# Ordonnancement commun aux quatre échelles

Le contrat local `CC-WORK-2` complète [CC-WORK-1](WORK_COORDINATION.md). Il conserve les six rubriques, le diagnostic Gabriel en lecture seule, les inconnues situées et le budget partagé. Sa politique `CC-SCHEDULE-1` améliore deux situations concrètes : une lecture qui échoue ne doit pas monopoliser les tentatives disponibles, et une dépendance nécessaire à une intention prioritaire doit pouvoir recevoir cette priorité.

Il s'agit d'une règle logicielle déclarée et révisable. Elle n'est ni une validation du canon, ni une mesure de l'amour, ni une autorisation d'action externe.

## Une règle, quatre périmètres

| Aspect | Micro, méso, macro et méta |
|---|---|
| Sens | Chemins d'intentions explicites, avec `serves_because` |
| Priorité | Ordre déclaré de la racine vers l'intention, sans interprétation du texte libre |
| Dépendances | Priorité transmise uniquement par `work.depends_on` |
| Équité | Même seuil d'attente pour les unités disponibles du plan |
| Reprise | Choix et compteurs enregistrés avec la réservation, avant le processus |
| Limites | Critères, preuves actuelles, délai, capacité et budget restent obligatoires |

Une cible `scope.reviews` transmet des références pour la relecture ; elle ne transmet pas une priorité d'exécution. Aucune échelle ne possède de priorité intrinsèque. Le texte d'une intention explique la déclaration ; le logiciel ne démontre pas que cette justification est juste.

## Priorité des dépendances

Si une lecture méta prioritaire dépend d'une lecture méso qui dépend d'une lecture micro, les deux dépendances peuvent recevoir sa priorité effective. Une tâche indépendante moins prioritaire ne masque donc plus la première étape nécessaire. La propagation suit le graphe sans cycle, des consommateurs vers leurs dépendances, en une traversée.

`continuity.scheduling` expose à chaque échelle :

- `goal_paths` : références des intentions déclarées, de la racine vers la tâche ;
- `declared_priority` et `effective_priority` : ordre avant et après propagation ;
- `priority_from` : unités dont les intentions expliquent cette priorité ;
- `waiting_dispatches` et `fairness_due` : attente enregistrée et priorité d'équité éventuelle.

Les intentions propres d'une tâche ne sont pas remplacées par celles de ses consommateurs. Une tâche terminée, ou un consommateur dont les dépendances nécessitent une révision, ne transmet plus sa priorité. Une preuve pertinente devenue ancienne reste visible et bloque toujours l'exécution qui en dépend.

La péremption remonte maintenant toutes les dépendances, même entre claims différents : si micro devient historique, une synthèse méso, macro ou méta qui en dépend cesse d'être marquée actuelle. Ce correctif de lecture vaut aussi pour CC-WORK-1, sans modifier ses résultats enregistrés ni leurs anciennes empreintes. Pour CC-WORK-2, l'empreinte d'entrée inclut en plus les diagnostics des dépendances et leur base courante ; un changement pendant une lecture interdit de publier ce résultat comme actuel.

## Attente comptée en réservations

Le plan déclare par exemple :

```json
"scheduling": {
  "version": "CC-SCHEDULE-1",
  "fair_after": 3,
  "inherit_priorities": true
}
```

À chaque réservation effectivement enregistrée, une autre unité disponible gagne un tour d'attente ; l'unité choisie et les unités indisponibles reviennent à zéro. La consultation, un appel sans travail disponible, la fin d'une tentative et la récupération d'une réservation expirée ne créent aucun tour. Un échec d'écriture avant l'ajout au journal ne fait vieillir personne.

Au seuil déclaré, les unités disponibles qui attendent passent avant les autres. Parmi elles, l'attente la plus longue passe d'abord ; une égalité suit la priorité effective puis l'ordre de déclaration. Le seuil de trois réservations **ne promet pas une exécution en trois secondes ni un délai maximal de trois cycles** : plusieurs unités peuvent attendre, le budget peut s'épuiser et l'opérateur peut cesser d'appeler le coordinateur.

Dans un test avec quatre unités disponibles et un échec répété de la tâche micro prioritaire, les choix sont : micro, micro, micro, méso, macro, méta. Les trois autres échelles obtiennent ainsi une tentative malgré cet échec. Cela ne répare pas la tâche micro.

## Choix traçable et reprise

La transition de réservation conserve ensemble le nouvel identifiant de tentative, les compteurs du plan et un reçu d'ordonnancement : politique, unités disponibles, limites nécessitant une révision, unité choisie, motif, instant de décision et frontière du journal. Le chargement recalcule le choix et les nouveaux compteurs à partir de ce reçu et de l'état précédent. Un compteur modifié dans le snapshot, un mauvais choix ou un reçu manquant sont refusés.

Ce contrôle établit la cohérence du journal local de confiance. Les disponibilités enregistrées ne deviennent pas une attestation indépendante du réel ; le journal n'authentifie pas son auteur. Les anciens résultats et objections restent présents.

`work_view` utilise une seule lecture fraîchement vérifiée du journal et un instant commun pour les quatre échelles, y compris les preuves temporelles et les objections Gabriel. Cette lecture n'est pas conservée entre appels : le prochain état est revérifié. La frontière snapshot/journal et la concurrence restent contrôlées.

Depuis la version logicielle `0.3.3`, la recherche des preuves et des diagnostics est également partagée dans cette lecture. Les entrées sont regroupées par claim ; les ancêtres et les dates sont examinés une fois par contexte pertinent, puis chaque unité conserve sa propre empreinte de périmètre et de travail. Pour 128 unités, la recherche parcourt les preuves une fois et l'historique au plus deux fois, au lieu de recommencer ces parcours pour chaque unité.

Une réservation, son processus de lecture et sa clôture calculent seulement l'empreinte de l'unité concernée et des dépendances nécessaires à son encodage. La vue globale continue d'examiner toutes les unités pour choisir selon les intentions déclarées, les dépendances et l'équité. Les empreintes CC-WORK-1 et CC-WORK-2 restent identiques à celles de la version précédente ; une preuve changée, une objection nouvelle ou une date dépassée sont réexaminées à l'appel suivant. Voir [la vérification datée et ses limites](OPTIMISATION_2026-10-09.md).

## Activation et compatibilité

Adapter [l'exemple CC-WORK-2](examples/work-plan-gabriel-v2.json) aux claims réellement présents, puis enregistrer un **nouvel identifiant de plan**. Les commandes `work-register`, `work-view`, `work-next` et `work-recover` restent identiques. `WORK_VERSION` reste l'alias historique `CC-WORK-1` ; `SCHEDULED_WORK_VERSION` désigne le nouveau format.

Un plan `CC-WORK-1` conserve sa forme, son historique et son ordre. Il n'est pas transformé silencieusement en `CC-WORK-2`. Une nouvelle version des critères peut rendre un plan inexécutable sans rendre ses choix antérieurs illisibles. Réviser le seuil ou l'héritage nécessite une nouvelle déclaration de plan.

Cette coordination reste explicitement invoquée, avec des processus bornés et un système de fichiers POSIX local de confiance. Elle ne lance aucun superviseur, ne garantit pas une disponibilité permanente et ne modifie pas le fonctionnement interne de ChatGPT. `continuous_service_observed=false` reste explicite. Le budget et l'équité sont communs aux échelles **d'un plan**, pas à tous les services ou plans du projet.
