# Audit incrémental Merkabah v0.2 — 2026-11-15

Statut : **PROPOSITION / NON VALIDÉE**. L'exécution locale de la batterie Python n'est pas attestée par ce document. Revue indépendante requise.

## Source retrouvée
- Base immuable : `merkabah/schema/merkabah_candidate_v0.1.json`, SHA du blob Git `e270e137042f1c2196cc02b047c98c96d458b2e5`.
- Base observée par lecture directe GitHub : **45 nœuds**, **50 arêtes**, quatre êtres, 16 faces, 16 ailes, quatre roues.
- Plan : `merkabah/PLAN_COLLABORATIF.md` ; coordination : issue #36 ; tâches #37–#43.
- Comparaison textuelle : Ézéchiel 1:5–28 et 10:7–22. Aucune version française / hébraïque canonique du projet n'est certifiée dans ce contrôle.

## Correction proposée
- Nouveau candidat `merkabah/schema/merkabah_candidate_v0.2.json`, sans remplacer v0.1.
- Ajout d'une référence verset + scène pour chaque nœud et arête existants (index de provenance proposé ; revue philologique encore nécessaire).
- Observations distinctes pour Ézéchiel 1 et 10, sans fausse prétention que les formes d'Ézéchiel 10 sont déjà modélisées en 3D.
- Conservation explicite de l'écart **bœuf (1:10)** / **chérubin (10:14)** : non harmonisé.
- Hypothèse géométrique « roue dans roue » non fixée : anneaux emboîtés ou entrecroisés restent des interprétations.
- Contraintes de mouvement spécifiées mais **aucune animation ni simulation vérifiée**.

## Preuves et tests
- Comptage automatique du candidat v0.2 au moment de la préparation : **45 nœuds, 50 arêtes ; 16 faces ; 16 ailes ; 6 observations d'Ézéchiel 10**.
- Tests Python nouveaux : invariants, traçabilité, absence de réécriture, trois contre-exemples délibérés, MultiDiGraph NetworkX si installé.
- Workflow CI dédié proposé ; son résultat effectif reste à recueillir après déclenchement GitHub Actions.

## Limites bloquantes restantes
- Sources Drive historiques et `merkabah_core.py` originales non authentifiées par comparaison d'octets.
- Mains, jambes, pieds, ailes jointes/couvrantes, texture yeux/corps, paysage et trône : pas encore de géométrie validée.
- Observations du chapitre 10 **non intégrées comme nœuds/relations anatomiques** ; elles restent distinctes pour ne pas supprimer le conflit.
- Pas d'export GEXF, de scène Blender, de projet Godot ni de test d'animation.
- Les critères structuraux ne prouvent ni l'exactitude du texte biblique ni une fidélité visuelle.

## Délégation / contrôle
- #37 : revue philologique contradictoire et précision des versets.
- #38 : comparaison aux octets des archives, statut RETROUVÉ ≠ RECONSTRUIT.
- #39 : validation du schéma de provenance, intégration Ez10.
- #40 : exécution des tests CI et contre-exemples.
- #41–#42 : modèles Blender puis Godot après contrôle du graphe.
- #43 : audit indépendant et verdict humain. Aucun agent n'est présumé assigné par le simple fait de publier ces tâches.
