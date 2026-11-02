# Les 72 Portes — lexique canonique v1.1.1

**Statut : tables canoniques reçues et validées, errata intégrés.**

Les trois fichiers CSV UTF-8 (séparateur `;`) constituent **la source de vérité lexicale** de cette version. Le **manuel v1.1.1 demeure la grammaire** du système, et n'est pas remplacé ni reconstruit ici à partir des données reçues. Le manuel complet n'a pas été fourni dans ce lot.

- [`axes.csv`](axes.csv) : 9 axes, dont 2 polaires et 7 dynamiques.
- [`portes.csv`](portes.csv) : 72 portes, 16 familles, 12 pivots et 6 cycles de 12 portes.
- [`transitions.csv`](transitions.csv) : les 71 transitions ordonnées du chemin.
- [`valider.py`](valider.py) : validation croisée déterministe et sans dépendance externe.
- [`empreintes.json`](empreintes.json) : empreintes SHA-256 des trois fichiers canoniques, pour détecter les changements d'octets.

Exécuter depuis ce dossier : `python3 valider.py`.

## Convention de lecture

Les numéros `n` identifient les portes : ils ne sont **pas** leur ordre dans le chemin. C'est `position_chemin` qui donne l'ordre de traversée, de 1 à 72 sans répétition.

Une porte à une position `p` de 1 à 12 appartient au cycle I, 13 à 24 au II, 25 à 36 au III, 37 à 48 au IV, 49 à 60 au V et 61 à 72 au VI. La porte de position 12, 24, 36, 48, 60 ou 72 **clôt son cycle**.

Une transition `Tn` relie la porte de position `n` à celle de position `n+1` ; elle **appartient au cycle de sa porte d'arrivée**, pas à celui de son départ. `T12` appartient donc au cycle II (arrivée Miroir) et `T60` au cycle VI (arrivée Porte). Le cycle I compte 11 transitions ; chacun des cycles II à VI en compte 12.

La Source n'a pas de transition entrante, le Repos pas de transition sortante. Les 70 portes intermédiaires en possèdent une de chaque.

## Errata v1.1.1 intégrés

**E5 — Sable et Argile.** L'attribution antérieure des deux au cycle II contredisait `position_chemin`. Les données canoniques corrigent :

| Porte | Identifiant `n` | `position_chemin` | Cycle canonique |
|---|---:|---:|---|
| Argile | 25 | 24 | **II** — porte finale |
| Sable | 24 | 25 | **III** — porte initiale |

Ainsi `T23` aboutit à Argile (II), `T24` aboutit à Sable (III). Les autres croisements sensibles sont Nuée → Pluie et Serrure → Clé ; leur ordre est déterminé par `position_chemin`, indépendamment de `n`.

## Modifications réservées pour v2.0 — **non appliquées**

1. Réaffecter Lettre de F13 (Signes) à F4 (Voix) créerait F4=7 et F13=6 ; recalculer les densités de ces familles. Le lexique v1.1.1 conserve **Lettre en F13**.
2. Documenter la distinction entre axes intra-familiaux et inter-familiaux en complément de la typologie polaire/dynamique, sans les confondre. Cette classification supplémentaire n'est **pas** ajoutée aux CSV.

## Portée et provenance

Ce nouveau module est **distinct** de [`../231-portes/`](../231-portes/), qui décrit un autre système. Les contrôles effectués établissent la cohérence **structurelle** du lexique remis : ils ne démontrent pas les interprétations narratives ou métaphysiques du manuel.

**DEEPBOM Artifact Evidence :** le connecteur ChatGPT v2.5.0 n'analyse que des artefacts de déploiement de modèles IA (TFLite, ONNX, GGUF, SafeTensors, Core ML, ExecuTorch). Aucun de ces formats n'a été fourni avec les trois CSV ; **aucune synchronisation ni analyse DEEPBOM n'est donc revendiquée**. Les tables restent disponibles dans ce dépôt, avec leurs empreintes, pour une éventuelle intégration future par un mécanisme compatible. Les empreintes ne sont pas un certificat DEEPBOM.
