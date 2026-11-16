# Audit ciblé Merkabah v0.2 — proposition, non validée

Date de contrôle : 2026-11-15. Source : `merkabah/schema/merkabah_candidate_v0.2.json` (lecture seule). Aucun canon modifié.

## Constats reproductibles

1. **Sources orphelines** : les nœuds et arêtes ajoutés citent `ez1:7`, `ez1:8`, `ez10:14`, `ez10:18`, `ez10:19`, `ez10:20` et d'autres références `ez10:...` ; la liste `sources` déclare uniquement `ez1` et `ez10`. Un validateur qui exige que chaque `source` référence un identifiant déclaré doit les refuser. Ne pas supprimer la précision des versets : ajouter une table de sources explicites ou normaliser les champs chapitre/verset.
2. **Tests non alignés** : `merkabah/tests/test_graph.py` pointe explicitement vers `merkabah_candidate_v0.1.json`. Les ajouts v0.2 ne sont pas couverts par ces tests tant que la cible n'est pas changée.
3. **Différence des faces** : Éz 1:10 et Éz 10:14 doivent demeurer distincts et signalés comme incertitude philologique. Le commentaire de v0.2 décrit l'ordre des faces d'Éz 10:14 d'une manière à contre-vérifier sur une édition biblique précise avant tout usage géométrique.
4. **Traçabilité du statut** : `PROPOSED_NOT_VALIDATED` est correct. Aucun résultat d'exécution de tests ni validation de rendu 3D n'a été observé dans ce contrôle.

## Contrôles à confier aux contributeurs

- #37 : vérifier verset par verset les quatre faces, les mouvements et l'ordre des faces selon la traduction et le texte hébreu ; fournir références exactes.
- #39 : réparer les références de provenance sans effacer les variantes ; documenter le schéma.
- #40 : ajouter des tests exécutables sur v0.2 pour provenance, identifiants, 4 êtres, 16 faces, 16 ailes, 4 roues, relations et scènes séparées ; joindre sortie de tests réelle.
- #41 et #42 : vérifier la géométrie et le prototype Lovable sans déclarer le rendu fidèle avant inspection.
- #43 : contre-validation indépendante, avis contradictoire et décision humaine.

## Critère de sortie

Aucun statut `VALIDATED` tant que la provenance, les tests v0.2, la divergence Éz 1/10 et la revue visuelle indépendante ne sont pas documentés. Centre simple, complexité périphérique.
