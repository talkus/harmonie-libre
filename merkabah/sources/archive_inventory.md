# Merkabah — Inventaire d'archives (M0b)

**Tâche** : #38 · **Prise de tâche** : commentaire `6903972003` (16 nov 2026) · **Statut du présent document** : INVENTAIRE MESURÉ — aucune pièce ci-dessous n'est promue CANON_VERIFIED.

Règle tenue : **aucun statut CANON_VERIFIED sans les octets**. `RETROUVÉ` signifie seulement que les octets ont été relus et mesurés ce tour (16 nov 2026) — cela ne prouve pas la filiation historique d'une pièce. `RÉFÉRENCÉ` signifie métadonnées seulement : octets non relus.

Méthode de mesure : MD5 natif (`md5sum`) sur les octets exportés ; SHA-256 par instrument TypeScript pur bancé (RFC 1321 / NIST CAVP, 7/7 PASS) — `sha256sum` natif étant en panne dans le substrat. Les documents Google-native exportés en texte perdent leur mise en forme : les empreintes portent sur les **octets exportés**, jamais sur une mise en forme non mesurée.

## 1. Pièces relues byte-exact ce tour (RETROUVÉ)

| # | Pièce | URL Drive (fileId) | Taille exportée | MD5 (octets exportés) | Statut |
|---|---|---|---|---|---|
| 1 | `merkabah_core.py` (noyau 28 oct 2026) | [1lT2f8-32PWpU6L6mYZpV_Ie9N3XAHsfW](https://drive.google.com/file/d/1lT2f8-32PWpU6L6mYZpV_Ie9N3XAHsfW/view) | 5 587 o | `0fb33af35b02b5f38747a3bd5809b495` | RETROUVÉ — filiation non prouvée |
| 2 | `merkabah_engine.py` | [1fMSvcqsVxq1VCB4rD4kW3jaVcyW_jPZ2](https://drive.google.com/file/d/1fMSvcqsVxq1VCB4rD4kW3jaVcyW_jPZ2/view) | 7 260 o | `07d034288686af7943ffea667b8b78f7` | RETROUVÉ |
| 3 | `merkabah_boussole.py` | [1U-oJO0A_hrykYFLnZoWibwN6EUWvJydw](https://drive.google.com/file/d/1U-oJO0A_hrykYFLnZoWibwN6EUWvJydw/view) | 7 742 o | `a16c2f2239df601052c8283490c1573e` | RETROUVÉ |
| 4 | `merkabah_v3_indexical_cherubim.py` | [1jRL5svLnzH4w98-15CcHnG8Mk7dMBlgA](https://drive.google.com/file/d/1jRL5svLnzH4w98-15CcHnG8Mk7dMBlgA/view) | 13 825 o | `0b264f40f0afbd14cc6a15758960f364` | RETROUVÉ |
| 5 | `HANDOFF_CORRIGIBILITE_MERKABAH.md` (28 oct 2026) | [1Lr1JVChOiuwDLXJpQnZCtZymaP7JBL7g](https://drive.google.com/file/d/1Lr1JVChOiuwDLXJpQnZCtZymaP7JBL7g/view) | 6 512 o | `b97a908539be6fa90d1158922ccf8d24` | RETROUVÉ — statut déclaré dans la pièce : CANON_NOT_VERIFIED |
| 6 | `merkabah_40_tests_networkx.py` (R33 V21, 15 nov) | [1Me3lI7BhIQFI7hi4wnAwboG4xdfsGXcS](https://drive.google.com/file/d/1Me3lI7BhIQFI7hi4wnAwboG4xdfsGXcS/view) | 11 673 o | `4bd5b10506e570f9446bbf002fba3302` | RETROUVÉ — SHA-256 conforme au préfixe déclaré |
| 7 | `merkabah_43_audit_independant_et_delegation_r33.py` (R33 V21, 15 nov) | [1ZCkxplxWEeDxn-sY7KCsfvruFdU1orWn](https://drive.google.com/file/d/1ZCkxplxWEeDxn-sY7KCsfvruFdU1orWn/view) | 11 036 o | `ebb4a40fe8c4104f293a12bc5df2205b` | RETROUVÉ — SHA-256 conforme au préfixe déclaré |
| 8 | Doc « Merkabah — mémoire indexicale des archives et Tikkun » (28 oct 2026) | [186jcOZB8saswpuFvAzyNMryueYj_2HmMAtx-sjUzjYE](https://docs.google.com/document/d/186jcOZB8saswpuFvAzyNMryueYj_2HmMAtx-sjUzjYE/view) | export 7 615 o | `c2258f57f4681f718eb25c2ba0837d3b` | RETROUVÉ (export) |
| 9 | Doc « MERKABAH — Plan collaboratif multidimensionnel v0.1 — 2026-11-15 » | [1tZV-BGhkEt6qpPxQjN6sSOFMyeYd9FVe_S9hk4dLpRM](https://docs.google.com/document/d/1tZV-BGhkEt6qpPxQjN6sSOFMyeYd9FVe_S9hk4dLpRM/view) | export 3 948 o | `6678d6e8a38a396cdfb1a0334d2fa836` | RETROUVÉ (export) — statut déclaré : PROPOSITION NON VALIDÉE |
| 10 | Doc « MERKABAH_V0_2_EXECUTION_LOCALE_37_42_ET_DELEGATION_43_R33_V21_2026-11-15 » | [1Y_6f-aCvX6cvRtL7ma56jZulpg2QBgnqeJqfIBWzTrw](https://docs.google.com/document/d/1Y_6f-aCvX6cvRtL7ma56jZulpg2QBgnqeJqfIBWzTrw/view) | export 6 673 o | `0df58064a6a85bbe9ca729b827216104` | RETROUVÉ (export) |
| 11 | Doc « GPT — Archives propres 06 — Galgal, empreintes, bijection et dynamique — 2026-10-03 » | [1Es_6ohm3Z1IlkYW3aEIK68rq9ltplwFe-CTmlStjHaQ](https://docs.google.com/document/d/1Es_6ohm3Z1IlkYW3aEIK68rq9ltplwFe-CTmlStjHaQ/view) | export 112 055 o | `4f1c42543cf1af58bb61c2271d67ca05` | RETROUVÉ (export) — lignée Galgal distincte |

## 2. Vérifications SHA-256 contre déclarations R33 V21 (nouveau ce tour)

Le document R33 V21 (pièce 10) déclarait des préfixes SHA-256 pour deux scripts sans que les octets aient été relus. Contre-épreuve exécutée ce tour, instrument bancé 7/7 PASS :

| Pièce | Préfixe déclaré par R33 V21 | SHA-256 recalculé sur les octets | Verdict |
|---|---|---|---|
| `merkabah_40_tests_networkx.py` | `47c9d47fd4e9…` | `47c9d47fd4e99714d71812b8d7f10119e7cbf8158233157485d14b2925b5d6a8` | **CONFORME** |
| `merkabah_43_audit_independant_et_delegation_r33.py` | `7b53351116bc…` | `7b53351116bcdf340609df40d79afe75e356d6455085704206573c5c4751c282` | **CONFORME** |

La délégation R33 V21 passe ainsi de « déclarée » à « RETROUVÉE et corroborée par les octets ». Reste non vérifié : le tête WORM SQLite déclaré `4ecd56a2acbe6d6c…` (fichier non relu ce tour).

## 3. Le noyau original — divergence nommée, sans effacement

- La **mémoire indexicale du 28 oct 2026** (pièce 8) déclarait : noyau `merkabah_core.py` « ATTESTÉ PAR UNE PASSATION », fichier original « non retrouvé en octets autonomes », statut CANON_NOT_VERIFIED.
- Les **octets sont aujourd'hui sur Drive** (pièce 1) et ont été relus deux fois indépendamment :
  - Reçu de reprise #38 (commentaire `6903576075`, 16 nov 00:00Z, session voisine) : 5 587 octets, SHA-256 `daa229e628910a00840f79cb3d7e32eba6b033b3ed0722611acd6a3fb52ce8a8`, démo exécutée (K 0,04 → FRAGMENTATION R=0,45 ; K 0,28 → COUPLAGE_JUSTE R=0,75 ; K 2,50 → CAPTURE R=0,99) — PR technique #46.
  - Présent inventaire : MD5 `0fb33af35b02b5f38747a3bd5809b495` sur les mêmes octets.
- **Statut maintenu : CANON_NOT_VERIFIED.** RETROUVÉ dans Drive ≠ authenticité de la filiation historique du chemin `artifacts/merkabah_core.py`. La preuve de chaîne d'origine, date et empreinte initiale reste à produire avant toute promotion.
- Garde de la mémoire indexicale conservée : ne pas identifier ce noyau (quatre oscillateurs, calibration K) au graphe biblique 3D du projet Merkabah ; ne pas l'assimiler non plus à `Registre_Merkabah/merkabah.py` (prototype antérieur).

## 4. Pièces référencées sans octets relus (RÉFÉRENCÉ)

| Pièce | Localisation | Métadonnées | Statut |
|---|---|---|---|
| Campagne R33 du 15 nov : explorateur HTML (78 843 o), JSON (281 499 o), ZIP délégation (485 530 o), SQLite reçus (20 480 o) | Dossier Drive `SOL_Microkernel_Travail` ([1INEqutN-dhjugnsLJhBPlbNFiT_epxST](https://drive.google.com/drive/folders/1INEqutN-dhjugnsLJhBPlbNFiT_epxST)) | tailles déclarées par la coordination | RÉFÉRENCÉ |
| Scripts Galgal (`galgal.py`, `galgal_proofs.py`, `test_galgal.py`) | référencés par Archives propres 06 (pièce 11) | 49 tests réussis déclarés, aucune approbation humaine | RÉFÉRENCÉ — lignée Galgal distincte du noyau |
| Tête WORM SQLite délégation | déclarée par R33 V21 : `4ecd56a2acbe6d6c…` | — | RÉFÉRENCÉ — non vérifiée contre octets |

## 5. Limites déclarées

1. Les empreintes portent sur les **octets exportés** ; pour les documents Google-native, la mise en forme originale n'est pas mesurable par ce canal.
2. Aucune exécution Python/Blender/Godot n'est possible dans le substrat du scribe : la calibration du noyau citée en §3 est celle du reçu de reprise #38 (session voisine), non re-exécutée ici.
3. Ce document est un inventaire de provenance, pas une validation : les statuts CANON_VERIFIED relèvent de l'audit indépendant (#43) avec preuve de filiation.
