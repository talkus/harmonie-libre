# Merkabah — audit contradictoire initial v0.2 (2026-11-15)

**Statut : constat documentaire, non-validation.** Source : `merkabah/schema/merkabah_candidate_v0.2.json`, `merkabah/schema/merkabah.schema.json`, `merkabah/tests/test_graph.py`, consultés dans GitHub. Travail lié à #36, #39, #40 et #43.

## Constats observables
1. Le graphe v0.2 possède les 4 êtres, 4 roues, 16 faces, 16 ailes, ainsi que des nœuds distincts pour mains, jambes et pieds. Ézéchiel 10 est représenté par des nœuds collectifs, une séquence de gloire et une divergence de faces non résolue. **Cela vérifie la présence dans le JSON, pas leur conformité historique ou philologique.**
2. Le test existant `test_graph.py` lit **v0.1**, et ne contrôle donc pas les ajouts v0.2.
3. Le schéma JSON `merkabah.schema.json` est incompatible avec v0.2 : `PROPOSITION_NON_VALIDEE` vs `PROPOSED_NOT_VALIDATED` ; `kind` vs `type` ; `relation` vs `type` ; `epistemic_status` vs `status` ; `sources` vs `source`. Il faut harmoniser le contrat, pas masquer l'échec.
4. Dans v0.2, les valeurs de référence `ez1:7`, `ez1:8`, `ez10:14`, `ez10:18`, etc. n'existent pas dans la table `sources` (qui ne liste que `ez1`, `ez10`). Lien vers les versets non résolu dans le registre interne.
5. La liste des faces d'Ézéchiel 10:14 dans la note du modèle doit faire l'objet d'une **vérification textuelle** : sa formulation actuelle ne doit pas être présumée exacte. Ne pas substituer une interprétation à une citation.
6. La délégation Lovable est attestée dans `merkabah/DELEGATION_AGENT_3D.md`. Son projet a été constaté `ready` et `agentFinished=true` par le connecteur, **sans audit de fidélité**. Une demande de révision additionnelle a été refusée par Lovable pour absence de crédits ; elle n'a donc pas été exécutée.

## Épreuve jointe
`merkabah/tests/test_candidate_v02_audit.py` ajoute des contrôles de cardinalité, d'intégrité des références, de scènes et de statut. Le test de provenance est conçu pour échouer jusqu'à la réparation documentée. **Aucun PASS n'est revendiqué dans ce rapport.**

## Délégation restante
- #37 : spécialiste de l'hébreu / exégèse, contrôler précisément Éz 1:10 et 10:14 sur une édition identifiée et distinguer variantes et interprétations.
- #39 et #40 : ingénieur de données, réconcilier le schéma et le modèle, compléter les identifiants de versets, puis exécuter les tests en CI et joindre les journaux.
- #41/#42 : artiste Blender et développeur Godot, produire les modèles sources et des vues auditables ; le prototype Lovable ne remplace pas ces livrables.
- #43 : auditeur indépendant, contrôler les images, le comportement des mouvements et les sources avant toute validation humaine.

Règles : ni fusion automatique, ni modification du canon ; `RETROUVÉ ≠ RECONSTRUIT` et `correspondance dans un JSON ≠ fidélité biblique`.
