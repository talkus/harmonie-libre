# Audit contradictoire du prototype Merkabah

Date : 15 novembre 2026. Statut : **relecture technique limitée**, sans validation biblique complète ni audit humain indépendant. Les contrôles ci-dessous ont été effectués par un assistant participant au même travail.

## Objets examinés

- [Projet Lovable « Merkavah en Mouvement »](https://lovable.dev/projects/72e5991d-a537-4d25-ba54-2f40975fd72d) : commit `f4cd2c1cdf9e234a6c307b3a71037de21711ff8e`, indiqué `ready` par Lovable, agent terminé, projet non publié au moment de la lecture. Fichiers relus via le connecteur : `src/merkabah/model.ts`, `src/merkabah/Scene.tsx`, `src/merkabah/model.test.ts` et `src/routes/index.tsx`, à ce commit.
- [Graphe GitHub candidat v0.1](https://github.com/talkus/harmonie-libre/blob/428354a00045a12fac6e20b5e23fea6f3e2e166a/merkabah/schema/merkabah_candidate_v0.1.json), dans le dépôt [harmonie-libre](https://github.com/talkus/harmonie-libre), coordination [#36](https://github.com/talkus/harmonie-libre/issues/36).
- Les observations du prototype portent sur les fichiers Lovable ci-dessus, non sur un résultat de compilation ou de navigation local.

## Résultats obtenus par exécution

Une copie inchangée de `model.ts` a été relue et exécutée localement avec Node.js 24.22.1, qui prend en charge le TypeScript de ce fichier. Aucun fichier du prototype ni donnée d'origine n'a été modifié. Pour chaque scène, `buildLayout(scene)` construit les données, puis `diagnose(données, scène)` est appelée. Les objets sont clonés avant chaque modification isolée.

| Épreuve | Entrée modifiée dans le clone | Résultat observé pour Éz 1 **et** Éz 10 | Portée |
|---|---|---|---|
| Référence | Aucune | 28/28 diagnostics de `diagnose` passent pour Éz 1 ; 27/27 pour Éz 10 | Ces contrôles portent sur le modèle de données. Les deux diagnostics supplémentaires liés au mouvement dans `Scene.tsx` ne sont pas inclus. |
| Jante éloignée | `find(x => x.kind === "ring" && x.wheel === 0).pos = [1000, 1000, 1000]` | « Roues-dans-roues (2 jantes) » reste vrai | Le contrôle compte deux objets `ring`, sans vérifier leur position ou leur intersection. |
| Yeux éloignés | Pour tous les objets `eye` dont `wheel === 0`, remplacer `pos` par `[1000, 1000, 1000]` | « Yeux sur les jantes » reste vrai | Le contrôle vérifie la présence d'objets associés à la roue, sans mesurer qu'ils se trouvent sur la jante. |
| Étiquette de pied | Pour le premier objet `foot` avec `cherub === 0`, définir `form = "chien"` | « Être 1 : pieds de veau » reste vrai | Le contrôle compte les objets `foot` sans examiner leur forme. Le changement d'étiquette n'a pas modifié un maillage ; ce cas ne démontre pas un défaut visuel observé. |

Ces contre-cas vérifient la fonction pure `diagnose`, et non la scène rendue dans un navigateur. Un résultat vert ne prouve donc pas à lui seul que la géométrie visible satisfait la description annoncée.

## Points relevés à la lecture du code

- **Synchronisation incomplète.** `Scene.tsx` calcule `bodyShift` seulement pour les objets `body`. Le contrôle « Déplacements synchronisés » compare les déplacements des corps des êtres entre eux ; il ne compare pas la trajectoire de chaque roue avec celle de son être. En vue isolée, un seul corps ne suffit pas à vérifier une synchronisation entre plusieurs objets, même si le drapeau peut rester vrai. Ce point résulte de la lecture du code ; aucun essai visuel d'une roue désynchronisée n'a été effectué.
- **Dépendance au graphe GitHub.** `index.tsx` et `Scene.tsx` utilisent `buildLayout(scene)` défini dans `model.ts`, qui construit les coordonnées et les éléments en code. Les fichiers lus n'importent pas le JSON candidat GitHub et ne comparent pas ses nœuds et arêtes à la scène ; le commentaire « Aligné sur … v0.1.json » ne prouve pas un raccordement. La fonction `FACE_FORMS` fournit à la fois la construction et l'attendu du contrôle : leur accord interne ne confirme pas une lecture du texte biblique.
- **Qualification des choix.** Les quatre directions et la place précise de la face de chérubin de la scène Éz 10 sont des choix de représentation. La liste des faces d'Éz 10:14 ne suffit pas à établir à elle seule ce placement précis. Des éléments affichés comme « TEXTUEL » combinent parfois un élément textuel et une position géométrique choisie ; distinguer les deux propriétés dans le modèle.

## Aperçu et limites

Le connecteur Lovable confirme l'existence du projet et indique que l'agent a terminé son travail. L'agent Lovable déclare avoir ouvert la scène Éz 1 et obtenu des résultats de tests, tout en indiquant ne pas avoir cliqué les commandes ni vérifié la fluidité graphique. Ces déclarations n'ont pas été rejouées ici.

Une tentative d'ouverture de l'aperçu dans le navigateur de cet environnement a affiché « Forbidden. Calls to this URL are not allowed. » Le rendu, Éz 10, les vues isolées, le mode filaire et l'animation n'ont donc pas été observés ni testés ici. Ce refus concerne cet environnement et n'établit pas une panne du site.

## Corrections proposées

1. Comparer, à plusieurs instants, le déplacement et l'orientation de chaque roue et de l'être associé ; afficher **non évalué** si une vue ou un nombre insuffisant d'échantillons empêche la comparaison.
2. Contrôler dans le même repère les centres, rayons et plans des anneaux, puis la distance de chaque œil à sa jante ; vérifier la forme des pieds au niveau du maillage si ce point est annoncé.
3. Charger une version épinglée du graphe, ou produire une correspondance explicite et testée entre ses identifiants, ses relations et les éléments 3D ; signaler les omissions, les scènes non représentées et les versions qui diffèrent.
4. Séparer pour chaque propriété l'affirmation textuelle, la source précise, le choix géométrique et l'incertitude. Vérifier l'inventaire biblique sur une édition identifiée avant de qualifier sa fidélité.

Le prototype demeure un outil d'exploration candidat. Cet audit ne valide ni sa fidélité finale, ni une décision d'approbation, ni l'indépendance humaine de la revue.
