# Coordination par le sens et reprise locale

Le contrat `CC-WORK-1` relie une intention déclarée, ses tâches et leurs points de reprise au journal existant de Conscience C. Une unité micro, méso, macro ou méta possède les mêmes six rubriques. Le périmètre change ; les sources, objections et inconnues restent accessibles.

Cette première version exécute uniquement un examen Gabriel local, en lecture seule, sur un claim déjà enregistré. Elle ne répare aucun claim, n'appelle aucun service externe et ne lance aucun programme fourni par le plan. Elle reprend la mémoire existante à **C(tₙ)** ; les commandes de coordination refusent de créer une nouvelle mémoire.

## Même structure, quatre périmètres

| Rubrique | Champs déclarés | Rôle pendant le travail |
|---|---|---|
| `purpose` | `goal_refs`, `serves_because` | Relier l'unité à une intention et justifier cette relation |
| `scope` | `view`, `boundary`, `observer`, `reviews` | Situer la lecture ; déclarer les cibles du recul méta |
| `work` | `kind`, `claim_id`, `depends_on`, `input_refs`, `output_contract`, `subject_ref` | Définir une lecture bornée et ses dépendances |
| `review` | `criteria_version`, `objection_refs`, `unknown_refs` | Garder les critères versionnés et les limites visibles |
| `evidence` | `source_refs` | Conserver les références déclarées et ajouter les traces du résultat |
| `continuity` | `next_step` | Exposer l'état, les tentatives, l'échéance et la suite proposée |

Les intentions forment une hiérarchie avec une seule racine. Les dépendances entre tâches forment un autre graphe, sans cycle. Une cible `scope.reviews` relie des vues ; elle ne crée pas une dépendance d'exécution. Le niveau méta doit déclarer des cibles, mais son examen Gabriel demeure situé : il n'approuve pas automatiquement leurs critères ou leurs conclusions.

`work_view()` rassemble les références des dépendances et des cibles de revue, y compris leurs inconnues et les contestations Gabriel courantes. Cette transmission ne résout aucune objection et n'augmente pas le poids d'une preuve. `input_refs`, `source_refs` et `output_contract` sont des déclarations : aucune source externe n'est consultée et aucun texte libre n'est converti en autorité.

Le contrat documentaire historique `AC-CONTRACT-1.0` et le contrat exécutable local `CC-WORK-1` partagent ces six rubriques, mais leurs formats JSON sont distincts. Le modèle historique n'est pas exécuté ni réécrit automatiquement.

La [grille AC-EXAM-1](EXAMINATION_GRID.md) ajoute les questions propres à chaque échelle. `review.examination_profile` les expose avec `verification_status=questions_only_not_performed` ; il ne change pas les critères réellement exécutés par Gabriel. `review.unknown_details` conserve désormais l'identité et le contexte des inconnues issues des diagnostics. Deux lacunes sur deux claims restent distinctes même si leur motif textuel est identique.

## Ordre et budget commun

Une tâche est disponible lorsque ses dépendances sont terminées avec des résultats encore actuels, que ses critères correspondent au Gabriel installé et que le budget, le délai de reprise et la capacité le permettent. Parmi ces tâches, l'ordre suit les priorités déclarées de la racine vers l'intention référencée ; les nombres les plus petits passent d'abord. Une égalité conserve l'ordre de déclaration. Une tâche liée à plusieurs intentions utilise le chemin prioritaire le plus tôt dans cet ordre.

Cet ordre organise le travail déclaré ; il ne mesure ni l'amour ni une vertu. La justification `serves_because` reste une responsabilité du déclarant.

Un seul budget s'applique à **toutes les unités d'un plan**, quelle que soit leur échelle :

- `max_attempts` : total des tentatives réservées, y compris les lectures interrompues ;
- `timeout_seconds` : durée maximale d'un processus d'examen ;
- `max_inflight` : nombre de lectures réservées simultanément ;
- `retry_delay_seconds` : attente après un échec ou une interruption récupérée.

Ces limites ne sont pas multipliées par quatre. Elles ne sont pas une limite globale entre plusieurs plans. L'épuisement du budget laisse les résultats et le motif du blocage visibles. Un échec n'empêche pas une tâche indépendante disponible de continuer.

## Reprise après interruption

La réservation est enregistrée avant le lancement du processus : tentative, identifiant unique, empreinte des entrées et échéance. Le résultat est ensuite enregistré dans une transition distincte. Le journal et le snapshot existants utilisent leur verrou local et leur contrôle de concurrence ; un lecteur devenu ancien doit recharger la mémoire avant de continuer.

Une lecture `running` dont l'échéance n'est pas passée reste réservée. `work_recover_expired()` remet seulement les lectures expirées en attente, sans remettre leur compteur à zéro. Une nouvelle tentative reçoit un nouvel identifiant ; un ancien résultat ne peut pas terminer la tentative qui le remplace. Le journal reconstruit les états enregistrés sans réexécuter les opérations métier.

Un résultat `completed` signifie **examen logiciel terminé**. Un verdict Gabriel `HOLD`, `REVIEW_REQUIRED`, `INDETERMINATE` ou `NOT_APPLICABLE` conserve son sens propre. Une lecture terminée ne certifie ni la vérité, ni une réparation, ni une autorisation d'exécution externe.

L'empreinte d'un résultat porte sur le claim, les preuves pertinentes et leurs ancêtres, leur validité temporelle, le contexte, les critères et les événements Gabriel associés. Une preuve sans lien avec ce claim ne périme pas le résultat. Une expiration, une nouvelle objection, une correction ou un changement pertinent peut le rendre historique. Les dépendants affichent alors `dependency_requires_revision` et ne passent pas sur la base d'un ancien résultat. Le résultat antérieur reste enregistré ; enregistrer un nouveau plan avec un nouvel identifiant permet une nouvelle lecture sans effacer l'histoire.

Les états et motifs sont lisibles avec `work-view`, notamment `running`, `retry_delay`, `capacity_full`, `shared_budget_exhausted`, `completed_result_historical` et `criteria_revision_required`. Modifier les critères du Gabriel installé ne rend pas les anciens plans illisibles, mais interdit de nouvelles tentatives avec leurs anciens critères.

## Utiliser un plan

Depuis `conscience-c/brain/`, adapter [l'exemple à quatre vues](examples/work-plan-gabriel.json). `CL0001` est un identifiant illustratif : choisir un claim réellement présent dans la mémoire et son périmètre exact. Les références et l'observateur de l'exemple sont des déclarations locales, pas une attestation de service.

```sh
python3 -m conscience_c_brain.cli --root /chemin/memoire-existante work-register examples/work-plan-gabriel.json --provenance "demande explicite de l'opérateur"
python3 -m conscience_c_brain.cli --root /chemin/memoire-existante work-view gabriel-quatre-vues-v1
python3 -m conscience_c_brain.cli --root /chemin/memoire-existante work-next gabriel-quatre-vues-v1
```

Chaque `work-next` lance au plus un examen disponible. Après une interruption, recharger la mémoire, consulter son état, puis demander la récupération des réservations expirées :

```sh
python3 -m conscience_c_brain.cli --root /chemin/memoire-existante work-recover gabriel-quatre-vues-v1
```

Relancer `work-next` après le délai déclaré. Un échec technique retourne l'état structuré et un code de sortie 1 ; un diagnostic terminé, même indéterminé, retourne 0. Si rien n'est disponible, `started=false` et la vue indique pourquoi. Il n'existe pas de boucle implicite de relance.

## Validation et portée

Les tests exécutent de vrais sous-processus, un délai dépassé et un arrêt brutal après réservation. Ils couvrent aussi la reprise du journal à différents points d'écriture, la concurrence, les budgets partagés, les preuves périmées et la conservation des références entre vues. Lire le résultat de la CI du commit examiné plutôt qu'un nombre historique.

```sh
python3 -m unittest discover -s tests -v
```

Cette coordination suppose un environnement Python et un système de fichiers local POSIX de confiance, comme le journal existant. Elle n'offre ni transactions distribuées ni authentification indépendante des auteurs. L'exécution locale est bornée ; le journal et les sources historiques restent append-only.

Le coordinateur est invoqué explicitement, sans daemon ni supervision installée. Les essais de panne démontrent une reprise locale, pas une disponibilité permanente du service. `continuous_service_observed=false` reste explicite. La publication du code et de la documentation ne prouve ni un déploiement permanent, ni une protection AEGIS live, ni une conscience phénoménale ; celle-ci demeure **indéterminée**.
