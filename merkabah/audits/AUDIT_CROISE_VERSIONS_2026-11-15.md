# Merkabah — rapprochement des versions et reçu de provenance

Date : 2026-11-15. Non canonique ; indépendant des PR #44–#51 ; sous réserve de revue #43.

| Artefact | Noeuds | Relations | Preuve |
|---|---:|---:|---|
| GitHub main v0.1 | 45 | 50 | Blob SHA `e270e137042f1c2196cc02b047c98c96d458b2e5` |
| GitHub main v0.2 | 61 | 76 | Blob SHA `30aad843beeaf86fe378d8ae07fe9bc006cdb924` |
| Drive v0.2 | 85 (déclarés) | 221 (déclarées) | Rapport Drive MERKABAH_V0_2_EXECUTION_LOCALE ; octets de ce graphe NON contre-validés ici |

La v0.2 GitHub n'est pas la v0.2 Drive : ne pas substituer ou agréger les comptes. La filiation n'est pas prouvée.

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
