# Merkabah — décision de contrôle de compatibilité (candidat)
- Date de travail: 2026-11-15 (heure Québec).
- Le fichier `merkabah/schema/merkabah.schema.json` de la branche principale décrit un autre modèle (`kind/scene/epistemic_status/sources`) et un statut `PROPOSITION_NON_VALIDEE`. Il n'est donc **pas** un validateur du candidat v0.3 (`type/source/status`, `PROPOSED_NOT_VALIDATED`).
- Un schéma distinct `merkabah/schema/merkabah_v03.schema.json` est ajouté, sans écraser les anciennes conventions. Les vérifications croisées (unicité, références et cardinalités) restent dans le banc Python.
- `test_motion_candidate.py` teste un mouvement géométrique minimal SYNTHÉTIQUE : quatre couples être-roue translatés en synchronie; les orientations des faces et décalages associés restent constants. Cette loi est une hypothèse de simulation, **pas une démonstration de la mécanique décrite dans Ézéchiel**.
- Limites : les géométries Blender ne sont pas encore exécutées ici, aucune validation exégétique, aucune attribution indépendante confirmée.
- Statut : PROPOSITION / À EXÉCUTER ET REVOIR ; PR #55.
