# Merkabah — contrôle structurel indépendant (2026-11-15)

Statut : CONTROLE PARTIEL, NON VALIDÉ. Aucun changement du canon.

## Sources observées
- Graphe candidat : merkabah/schema/merkabah_candidate_v0.1.json (GitHub, lecture directe)
- Tests Python existants : merkabah/tests/test_graph.py (lecture directe ; NON exécutés ici)
- Délégation : merkabah/DELEGATION_AGENT_3D.md
- Prototype externe : https://lovable.dev/projects/72e5991d-a537-4d25-ba54-2f40975fd72d (état API ready, agentFinished=true, non publié)

## Vérification effectuée
Le JSON a été chargé et 10 prédicats ont été évalués directement en JavaScript sur les données lues : identifiants uniques, extrémités existantes, quatre êtres, quatre roues, quatre faces de formes distinctes par être, quatre ailes par être, association et mouvement roue/être, yeux sur jantes, sources référencées existantes, statut PROPOSED_NOT_VALIDATED. Résultat : 10/10 vrais. Graphe : 45 nœuds et 50 arêtes.

## Interprétation
Cohérence structurelle minimale du candidat. Ce contrôle ne prouve ni l'exactitude exégétique, ni la géométrie, ni la fidélité de l'animation. Le prototype Lovable est construit et prêt à consulter, pas audité.

## Lacunes et contre-épreuves
- Les tests Python/NetworkX et le rendu Blender/Godot n'ont pas été exécutés lors de ce contrôle.
- Les nœuds du graphe ne matérialisent pas encore explicitement mains, jambes, pieds, yeux individuels, jantes, structure interne des roues, ni variantes Ez 10.
- Les sources sont au niveau du chapitre, pas du verset pour chaque assertion ; cela ne suffit pas à une validation philologique.
- L'identification des faces dans Ez 1:10 et Ez 10:14 doit rester distinguée ; aucune résolution implicite.
- Vérifier en 3D les quatre orientations, l'absence de retournement, la synchronicité et la non-disparition des parties.

## Décision
Maintenir PROPOSED_NOT_VALIDATED. Demander audit contradictoire sur #43. Ne pas fusionner un rendu visuel au canon. Aucun agent humain externe confirmé comme responsable des issues #37–#43.
