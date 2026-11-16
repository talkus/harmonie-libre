# Merkabah — exécution externe Blender et NetworkX, candidat v0.4

PR #55. Statut PROPOSED_NOT_VALIDATED. Ni canon ni fusion modifiés.

## Blender (exécuté, pas seulement planifié)
- GitHub Actions SUCCESS : https://github.com/talkus/harmonie-libre/actions/runs/43807613719
- Blender 5.0.1 a généré et testé un fichier .blend.
- Audit headless : beings=4, faces=16, wings=16, wheel_assemblies=4, symbolic_eyes_on_wheels=48, objects=130, status=PASS, errors=[] (log du run 43807583849, même code modèle).
- Frames contrôlées : 1, 31, 61, 91, 121 ; 4 ensembles être/roue déplacés ensemble ; orientations des corps stables et décalages roue/être constants.
- SHA-256 de l'artefact Blender récupéré du run strict 43807613719 : 36c3a49c17dae30bc8ad9b910e3ea278657893a0cfdf0cb189be67b07a4b0d4c ; taille 202056 octets.
- Scène Ezekiel_1 uniquement. Animation par translation; roulement interne des roues non implémenté. Yeux sur corps et ailes selon Ez 10:12 non implémentés. Géométrie interprétative.

## Gephi (exécuté)
- GitHub Actions SUCCESS : https://github.com/talkus/harmonie-libre/actions/runs/43807583802
- GEXF 1.2draft via NetworkX, pas 1.3. 61 nœuds, 76 relations, face_discrepancy_ez10_14=UNCERTAIN.
- Fichier GEXF rouvert dans NetworkX avec cardinalité et statut conservés.
- SHA-256 du GEXF récupéré : 14cf5623a4c3fa6cb98326e5d23c093460c550f1a54ad7d14b55eef6de4d0a1a.

## Délégation et limites
- Délégation réellement exécutée : runner GitHub Actions pour NetworkX et Blender headless.
- Lovable : prototype existant mais synchronisation v0.4 refusée faute de crédits. Aucun nouveau code Lovable produit.
- Godot natif non exécuté; audit indépendant philologique/artistique non attribué.
- Revue nécessaire : anatomie des deux scènes, visage chérubin/bœuf, caméra multi-angles, mouvements des roues, preuve par verset.
