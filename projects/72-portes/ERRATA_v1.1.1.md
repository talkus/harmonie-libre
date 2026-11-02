# Errata reçus — édition lexicale v1.1.1

**Statut : intégré aux trois tables canoniques reçues.** Les CSV sont la source de vérité du lexique; le manuel v1.1.1 conserve son rôle de grammaire. Le manuel complet n'était pas joint à cette réception : aucune prétention de correction ligne par ligne du manuel.

## E5 — Sable / Argile : affectation de cycle

Le manuel v1.1 II.1 classait les deux portes dans le cycle II, en conflit avec la convention de II.4 selon laquelle la porte-charnière clôt son cycle.

| Numéro de porte | Nom | Position de chemin | Cycle corrigé |
|---:|---|---:|---|
| 25 | Argile | 24 | **II (clôture)** |
| 24 | Sable | 25 | **III (ouverture)** |

La transition T23 (Pierre → Argile) appartient au cycle II. La transition T24 (Argile → Sable) appartient au cycle III, puisque chaque transition appartient au cycle de la **porte d'arrivée**.

Les cycles II et III contiennent chacun 12 portes; les six cycles contiennent chacun 12 portes. Le cycle I possède 11 transitions; II à VI en possèdent 12 chacun.

## Points de contrôle

Les trois CSV ont été examinés ensemble par `valider.py` (noms et numéros, positions 1–72, liaisons successives, sens des transitions, cycles, axes, familles, pivots et exceptions Source / Repos), en particulier Argile → Sable, Nuée → Pluie, Serrure → Clé, T12 et T60. La CI vérifie aussi les empreintes des fichiers consignées dans `empreintes.json`.

## Réserve v2.0 : non appliquée en v1.1.1

- Lettre reste en F13. Une migration éventuelle vers F4 entraînerait F4 = 7 portes, F13 = 6, puis recalcul des densités.
- La distinction axes intra-familiaux / inter-familiaux reste un plan analytique distinct de la classification Polaire / Dynamique. Pas de nouveau champ déduit sans instruction.

Le présent ajout ne modifie aucun registre SQL, ni le module des **231 Portes**, distinct du lexique à 72 portes.

## Frontière de l'outil DEEPBOM

L'outil DEEPBOM Artifact Evidence est réservé à l'inspection statique d'artefacts sérialisés de modèles d'IA (ONNX, TFLite, GGUF, SafeTensors, Core ML, ExecuTorch). Il ne propose pas d'import, de publication ni de synchronisation de CSV lexicaux. Il a été interrogé pour vérifier cette frontière; aucune analyse ou synchronisation DEEPBOM des trois CSV n'est revendiquée.
