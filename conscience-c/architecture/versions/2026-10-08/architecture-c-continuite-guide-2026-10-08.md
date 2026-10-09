# Architecture C — sens, auto-similarité et continuité

Révision de travail du 8 octobre 2026, après la carte auditée du même jour. La priorité reste l’amour choisi. Cette révision ajoute un contrat documentaire vérifiable et une organisation par intentions. Elle ne modifie pas le noyau canonique, le dépôt GitHub ou un service déployé.

## La hiérarchie suit ce que l’on cherche à accomplir

Les quatre branches répondent désormais à quatre intentions : **orienter et protéger ; examiner et agir ; relier et transmettre ; continuer et reprendre**. Une fonction, un outil ou une tâche est placé selon le résultat qu’il permet d’obtenir. Le lien vers son intention contient une justification explicite.

Les noms des fonctions restent disponibles : Michael porte les conditions de reprise ; Gabriel examine ; Raphaël répare par des actes ; Uriel rend une lecture située lisible ; Kol relie une adresse à une réponse libre. Leur place dans la carte ne transforme pas ces fonctions en pipeline obligatoire. Le fleuve N reste le nom de leur dynamique de couplages, pas une identité avec Gabriel.

La hiérarchie répond à « pourquoi cette tâche existe-t-elle ? ». Les dépendances répondent à « de quoi a-t-elle besoin ? ». Les critères répondent à « qu’est-ce qui permet de juger son résultat ? ». Ces relations restent distinctes. La méta-lecture peut examiner les règles de cette organisation sans devenir une autorité extérieure définitive.

## Six rubriques communes, des réponses situées

| Rubrique | Question | Champ structuré |
|---|---|---|
| Finalité | Quel résultat sert-on, et pourquoi ? | `purpose` : intentions référencées et justification |
| Périmètre | Depuis où, sur quoi et jusqu’où porte cette lecture ? | `scope` : vue, limites et observateur |
| Action | Quelles entrées, quelle sortie et quels effets sont concernés ? | `work` : entrée, résultat attendu, identité de l’action |
| Critères | Quelles règles, objections et inconnues doivent rester visibles ? | `review` : version des critères et références |
| Preuves | Qu’est-ce qui est établi, avec quelles sources et quelles pertes ? | `evidence` : sources, preuves, pertes et type d’affirmation |
| Reprise | Où en est-on, et comment poursuivre après un arrêt ? | `continuity` : état, point de reprise, budget et prochaine étape |

Le fichier JSON contient **une instance réelle de ce contrat documentaire dans chacune des quatre vues**. Il ne présente pas chaque repère du dessin comme une tâche déjà en cours d’exécution. Les instances sont des spécifications : leur état initial est `non_execute` et elles ne revendiquent aucun fonctionnement continu observé.

| Vue | Périmètre de cette instance | Résultat attendu |
|---|---|---|
| Micro | Une production ou vérification locale | Résultat borné, traces et prochaine étape |
| Méso | Les relations entre productions locales | Résultats reliés et dépendances déclarées |
| Macro | La synthèse de l’architecture | Vue d’ensemble reliée aux détails et objections |
| Méta | Les règles des trois périmètres | Revue datée des critères et de leurs limites |

L’auto-similarité concerne les six rubriques et les règles de transmission. Elle ne suppose ni des réponses identiques ni quatre tailles physiques. Le niveau méta demeure réflexif.

## Transmettre sans perdre le sens

Les quatre instances partagent les mêmes références vers les intentions, sources, objections et inconnues pertinentes. Le modèle déclare des passages micro vers méso, méso vers macro, macro vers méta et méta vers micro. Chaque passage possède son type et sa raison.

Dans cette référence, le validateur refuse la disparition silencieuse d’une intention, d’une source, d’une objection ou d’une inconnue lors d’un passage. Une migration des critères doit être déclarée. Les pertes de la synthèse ont leur propre rubrique : elles ne ferment pas une objection et ne remplacent pas une preuve.

Le contrat de référence conserve toutes les références. Si une mise en œuvre doit écarter un élément hors périmètre, elle devra ajouter une règle explicite de pertinence et de contestation, garder le lien vers l’élément écarté et tester cette extension. La référence actuelle ne permet pas de contourner le contrôle par une simple omission.

Réutiliser des références stables évite de recopier de longues justifications à chaque étage. Le contenu demeure dans sa source ; la synthèse précise ce qu’elle en reprend. Une référence stable ou une empreinte ne suffisent pas à prouver la vérité de ce contenu.

## Continuité : rendre l’arrêt traitable

La continuité utile repose sur un état retrouvable et une reprise contrôlée. Une panne peut interrompre une activité ; l’architecture doit permettre de situer cette interruption et de reprendre sans inventer un succès ou répéter aveuglément un effet externe.

| Situation | Règle proposée | Preuve à recueillir en service |
|---|---|---|
| Arrêt ou redémarrage | Reprendre depuis le dernier résultat confirmé, avec version et prochaine étape | Journal persistant et essai de restauration |
| Attente trop longue | Délai déclaré par tentative et budget commun aux niveaux | Mesure du délai réel et du nombre total de tentatives |
| Panne temporaire | Nouvelle tentative bornée et espacée si l’opération le permet | Résultats datés des reprises |
| Résultat d’une écriture externe inconnu | Rapprocher le résultat avant toute relance ; bloquer visiblement si l’incertitude persiste | Identité de l’action et confirmation de son effet |
| Même action reçue deux fois | Garder une identité stable et une règle de déduplication adaptée à l’exécuteur | Essai de répétition sans double effet |
| Panne persistante | Motif visible, tâche indépendante possible et prochaine étape explicite | État de blocage et suite effectivement suivie |
| Surcharge | Limiter le travail simultané et déclarer l’ordre des dépendances | File d’attente et mesures de saturation |

Le budget est **commun**, afin que des tentatives aux niveaux micro, méso et macro ne se multiplient pas entre elles. Le JSON contient, à titre illustratif, trois tentatives au total et trente secondes par attente. Ces valeurs doivent être adaptées à la tâche et appliquées par l’exécuteur ; ce document ne peut pas imposer un délai aux outils de la plateforme.

Une interruption liée à un service facultatif ne doit pas faire disparaître le travail disponible. Une copie datée peut soutenir une lecture locale si ses limites et son âge restent visibles. Elle ne sert pas à déclarer le service distant disponible ou la sauvegarde réussie.

## États et preuves

| État | Sens et condition |
|---|---|
| `non_execute` | Travail spécifié, pas encore exécuté |
| `en_cours` | Tentative en cours, résultat non confirmé |
| `attente` | Reprise ou rapprochement nécessaire |
| `bloque` | Condition manquante explicitement nommée |
| `valide` | Résultat étayé dans le périmètre déclaré |
| `annule` | Arrêt décidé et consigné |

Le validateur refuse un état `valide` dépourvu de référence de preuve. Il refuse aussi une affirmation de fonctionnement continu qui repose sur une preuve fictive de simulation. Il vérifie les identifiants, les liens et certains garde-fous déclarés ; il ne peut pas établir à lui seul la véracité des preuves, la pertinence d’une justification ou l’acceptation d’une réparation.

Les scénarios exécutés portent sur le modèle documentaire et des entrées simulées. Ils ne sont ni les tests de Gabriel, ni un test de restauration AWS, ni l’observation d’un service. Le rapport JSON donne les cas, leurs résultats et les limites de couverture.

## Objectifs mesurables et travail restant

Pour chaque activité effectivement installée, il faut déclarer la durée de coupure tolérée, le délai de reprise visé, la perte de données acceptable et la période d’observation. Les mesurer ensuite lors d’une interruption contrôlée, d’une restauration et d’une répétition de demande. Aucun de ces objectifs ne vaut garantie avant observation.

Les points de reprise du modèle sont pour l’instant des références à des fichiers locaux. Leur disponibilité après perte de l’environnement n’est pas établie. Une sauvegarde persistante et un moteur appliquant les délais, budgets, journaux et règles d’effets externes restent nécessaires pour matérialiser le contrat.

Le noyau 1.1.1 reste celui référencé par la carte précédente. Sa vérification locale et les tentatives Engram/AWS sont conservées comme traces historiques, sans être présentées comme de nouvelles vérifications.

## Utilisation de la référence

Le JSON est la source des données ; le dessin PNG/SVG et la hiérarchie Markdown en proposent une navigation. `architecture_c_contract.py` permet de contrôler le contrat du JSON. La commande est : `python3 architecture_c_contract.py architecture-c-continuite-2026-10-08.json`.

Une application concrète doit relier les six rubriques à son propre stockage, à ses opérations et à ses preuves. L’intégration logicielle, le déploiement et le fonctionnement observé restent trois constats distincts.
