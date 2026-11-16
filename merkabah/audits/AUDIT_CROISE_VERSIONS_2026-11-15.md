# Merkabah — rapprochement des versions et reçu de provenance

Date : 2026-11-15. Non canonique ; indépendant des PR #44–#51 ; sous réserve de revue #43.

| Artefact | Noeuds | Relations | Preuve |
|---|---:|---:|---|
| GitHub main v0.1 | 45 | 50 | Blob SHA `e270e137042f1c2196cc02b047c98c96d458b2e5` |
| GitHub main v0.2 | 61 | 76 | Blob SHA `30aad843beeaf86fe378d8ae07fe9bc006cdb924` |
| Drive v0.2 | 85 (vérifiés) | 221 (vérifiées) | Fichier Drive `merkabah_39_graphe_multidimensionnel_v0_2.json` lu en octets exacts ; SHA-256 `74425d2db5ca07eb1f91b1401175493fe72b8893cb8abff21a2086a4e1fe3954` |

La v0.2 GitHub n'est pas la v0.2 Drive : ne pas substituer ou agréger les comptes. La filiation entre les deux artefacts n'est pas prouvée malgré leur présence vérifiée.

## Constats sur GitHub v0.2 exact

- MAJEUR : **16** nœuds référencent un `source` qui n'existe pas dans la liste `sources` (`ez1`, `ez10` seulement).
- MAJEUR : **26** relations ont une source non déclarée, par exemple `ez1:7` ou `ez10:20`.
- MAJEUR : **68** assertions n'ont pas de `status` explicite ; ne pas supposer TEXTUEL par défaut.
- Structure : zéro relation orpheline détectée sur v0.2 ; quatre êtres avec faces et ailes et quatre roues associés. Aucune preuve de géométrie, cinématique ni philologie ne découle de ce contrôle.
- `merkabah/tests/test_graph.py` sur main cible encore explicitement `merkabah_candidate_v0.1.json`, donc pas de PASS v0.2 démontré.

## Reproduction

```bash
node --test merkabah/tests/test_audit_integrite.mjs
node merkabah/tools/run_audit.mjs merkabah/schema/merkabah_candidate_v0.2.json
node merkabah/tools/run_audit.mjs merkabah/schema/merkabah_candidate_v0.2.json --strict
```

`--strict` échoue intentionnellement avec ce v0.2 tant que les sources et statuts ne sont pas déclarés. Le mode normal émet seulement le reçu et permet une revue.

## Délégations et barrières

- #39 et #40 : mettre en correspondance les identifiants de versets avec des sources déclarées, spécifier les statuts, puis relancer sur les octets de la version candidate finale.
- #37 : contre-lecture indépendante des faces Ézéchiel 1:10 (bœuf) et 10:14 (chérubin), sans interprétation imposée.
- #41/#42 : contrôle des quatre êtres et de leur mouvement dans Blender/Godot ou un moteur 3D interactif ; prototype ≠ preuve biblique.
- #43 : auditeur indépendant et autorité humaine seuls habilités à conclure. Interdiction de fusion automatique ou de promotion CANON_VERIFIED.

RETROUVÉ ≠ RECONSTRUIT ; ÉCRIT ≠ RELU_VÉRIFIÉ.

## Contrôle natif du graphe Drive (rejeu ultérieur à l'audit initial)

- Le fichier Drive `merkabah_39_graphe_multidimensionnel_v0_2.json` a été récupéré avec **281 499 octets** et une empreinte SHA-256 complète `74425d2db5ca07eb1f91b1401175493fe72b8893cb8abff21a2086a4e1fe3954`.
- **85/85 identifiants uniques**, **221/221 IDs de relations uniques**, **0 arête vers un nœud absent**.
- La suite originale Drive `merkabah_40_tests_networkx.py`, SHA-256 `47c9d47fd4e99714d71812b8d7f10119e7cbf8158233157485d14b2925b5d6a8`, exécutée en Python avec **NetworkX natif 3.6.1** : **3 tests exécutés, 3 réussis**, incluant deux mutations adversariales (gyroscope central, fidélité auto-certifiée).
- Important : sur les 221 relations, **129** sont des arêtes `cited_by` de provenance ; elles ne constituent pas 129 relations anatomiques ou physiques supplémentaires.
- La compilation syntaxique Python de `merkabah_41_blender_kit.py` a réussi ; **Blender n'est pas disponible** dans l'environnement et aucun rendu `bpy` n'a été exécuté.
- Le script Godot archivé `merkabah_42_godot_simulation.gd` contient une fonction `step_merkabah` qui calcule `group_position` et renvoie `cherub_yaw_rotation_delta: 0.0`. Il ne montre pas d'application de ces données aux transformations visuelles des objets Node3D ni de boucle `_process` ; **animation native Godot non démontrée**. À vérifier dans le projet complet, pas seulement dans ce fragment de script.
- Malgré les tests nominaux du Drive, **aucune fidélité philologique, géométrie 3D ou animation n'est certifiée** sans les essais spécialistes #41–#43.
