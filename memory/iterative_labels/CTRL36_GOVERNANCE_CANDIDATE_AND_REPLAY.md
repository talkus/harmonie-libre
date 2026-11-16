# CTRL-36 — Référence technique candidate / rapprochement WORM / PR #56

Date de contre-épreuve : 2026-11-15 (heure Québec) / 2026-11-16 UTC. 
État: **PROPOSITION DE HIÉRARCHIE — NON RATIFIÉE, NON FUSIONNÉE**.

## Répartition sans fusion ni remplacement des sources

1. **Les sources primaires, les corrections explicites et la décision humaine autorisée prévalent toujours.**
2. **CTRL-36 / R33 V22** est proposé comme **référence gouvernante technique** pour l'étiquetage épistémique par passes, sous réserve de contre-validation complète et de contre-visa humain. Il ne devient ni souverain ni canon par la simple PR.
3. **WORM Interchat / étiqueteur shell** demeure l'instrument local de tenue du journal et de classement opérationnel (DOMAINE / SENS / STATUT). Ses écritures historiques et scellures restent intouchées.
4. **PR #56** reste un adaptateur expérimental pour la consultation des versions et le rapprochement des deux interfaces. Elle ne duplique pas le ledger CTRL-36 et ne prétend pas autoriser une promotion.
5. En cas de divergence, produire `CONFLIT_OUVERT` et suspendre la promotion ; ne pas écraser ni convertir automatiquement.

## Preuves originales consultées directement

Dossier Drive : https://drive.google.com/drive/folders/1INEqutN-dhjugnsLJhBPlbNFiT_epxST

ZIP CTRL-36 :
https://drive.google.com/file/d/1_1Kc1X95NrLxr0i4FlFtUPJA5kG6Uw66/view
- taille 530217 octets ; SHA-256 **d7c25b36f184da4447e257547375fb51e54791d578aafb57015a752100269485**.

Script Python :
https://drive.google.com/file/d/1M5Ht3noZh-PFNnIDecXfIw4jGXTvPZdr/view
- taille 85918 octets ; SHA-256 **ebf4f024841385b750429c93ee62a71b550b2f456c1b015c6c9025e2a2aa4a16**.

SQLite inclus dans le ZIP, contrôlé en lecture seule :
- taille 1921024 octets ; SHA-256 **160c2cad92cfbf2752026a557ff93e3d98c67e09b9c3b396f7d9dfb55ea93ee0**.
- 6 règles `C36_R01..C36_R06`, 18 passes, 4 unités mémoire ; répartition 5+6+4+3.
- Les 4 trajectoires maintiennent T constant ; K est strictement croissant. Les liens entre événements consécutifs et le hash de tête correspondent aux valeurs du rapport.
- Les 18 passes **ne sont pas 18 itérations d'une même unité** ; elles constituent le total de quatre trajectoires.

## Tests effectués dans l'environnement de contre-épreuve

Python **3.13.5**. Archive extraite en répertoire de travail temporaire ; base originale de l'archive non modifiée. Copie du fichier SQLite v22 sous le nom historique attendu par la suite v16, uniquement dans ce répertoire de test.

- Sous-suite CTRL-36 `test_51..test_58` : **8/8 PASS**, exécutés réellement.
- Commande `python memoire_cli.py label-iteratif --sidecar journal_apprentissage_incompris_r33_v22_ctrl36_etiquetage_iteratif_worm.sqlite3` : **exit 0**.
- Son résultat retrouve `ctrl36_passes_count=18`, `ctrl36_rules_count=6`, racine `36b75ef98634521b1487a411fd65d7ebc49f1515f17d2b9c7d81e60b78c698da`, tête `9706a1b62039d1f0180d5d25d7caab8d6fbe2079631692dedcd56c070fed05be`.
- La suite complète : **58 tests lancés, 30 PASS, 1 FAIL, 27 ERROR** sur la copie partielle. Les données historiques demandées par cette suite (notamment `ctrl26_systeme_reussite_data.json` et fichiers L0/L1/graphes externes) ne sont pas livrées dans cette archive. Un test de topologie ne retrouve pas ses données. **Ne pas attribuer ces échecs à CTRL-36 sans reconstituer les dépendances exactes**. Ne pas déclarer `58/58 REJOUE` ici.
- Le résultat Merkle a été *reproduit par l'outil livré*, mais pas recalculé par une seconde implémentation cryptographique indépendante.
- Les sceaux `O_S24_EXTERNE` et l'attribution humaine ne sont pas authentifiés par ces seules vérifications locales.
- WORM Interchat #300, annoncé séparément, n'est pas démontré par le ZIP.

## Garde de promotion

CTRL-36 reste une **référence gouvernante proposée**, non souveraine. Pas de fusion de PR #56 ni d'adoption canonique avant :
- reconstruction complète des dépendances et tests 58/58 dans un environnement explicitement scellé ;
- seconde vérification de la racine Merkle et des signatures/reçus humains ;
- revue contradictoire de la compatibilité DISS-01, RCI L3, anti-étiquette commode et Porte Ouverte ;
- approbation explicite de l'autorité humaine.

R ≺ E. RETROUVÉ ≠ RECONSTRUIT. ÉCRIT ≠ REJOUÉ. Correction ≠ effacement.
