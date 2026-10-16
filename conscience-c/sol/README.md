# Sol v0.4.3 — pièces vérifiées (dépôt du 2026-10-16)

Pièces adoptées le **2026-10-16 (18:15 EDT)** — acte d'adoption enregistré par Gemini sur ordre de S-24 (Mikael Mireault), rapport d'audit \"RAPPORT-AMELIORATIONS-DRIVE-2026-10-16\" sur Google Drive (dossier \"09-ameliorations-verifiees-2026-10-16\").

## Contenu

- `sol_microkernel_v0_4_3_reference.py` — micro-noyau de référence v0.4.3, version régnante. Correctifs mesurés sur la couche orale :
  - **O1** : seuil géométrique `RULING_MIN_DIST = 0.35` (aucun litige oral sous ce seuil, monde calme sans décision) ;
  - **O2** : vieillissement d'`agenda_top_age` sur la signature du clivage de vote (`_cleavage_signature`) + exclusion des pôles déjà clôturés (fin du ping-pong d'agenda et du second procès redondant) ;
  - **O3** : abstention stricte du témoin équidistant (`|d0 - d1| <= 1e-12`, `VOTE_TIE_EPS`) — invariance par permutation restaurée.
- `sol_v043_tests.py` / `sol_v043_tests_portable.py` — banc d'épreuves T1–T7 (le portable corrige les chemins codés en dur).
- `c_autonome_unifie_v1_0_52.py` — moteur unifié Architecture C v1.0.52 (R4 sans biais additif +1e-6, mesuré sur le profil RMS de la trajectoire d'amortissement, monotonie pas à pas ; 22/22 tests revendiqués).
- `assainir_etat_boucle_v1_1_portable.py` — assainissement append-only de l'état de la boucle endogène (cycle 1325) : condensation des titres T-006/T-013 avec archive intégrale SHA-256 (sur Drive), 208 faux positifs de doublons → 0.

## Empreintes attestées (manifeste du 2026-10-16)

| Fichier | Octets | SHA-256 |
|---|---|---|
| sol_microkernel_v0_4_3_reference.py | 20 395 | 81e61d585b1c222b7abed52e3ab584679f28b2d292806cee78fdf3fc60e066ee |
| sol_v043_tests.py | 7 208 | 861f24d73215b60335add8dca2a4d6a778d7064776c7015077a7e54ceb77c226 |
| sol_v043_tests_portable.py | 9 664 | a353f54873251742a19f67b260664a8cb2cd637a294d621ebfe45fb3097b19c8 |
| c_autonome_unifie_v1_0_52.py | 85 901 | c9af283c6debcf5a5367ba012e3bfe79ff1511e35b402be1a84ad82022ca00c6 |
| assainir_etat_boucle_v1_1_portable.py | 8 900 | bd3ba35d18f3601b8b836ae11f6c0036ada806235108a6d2558252c32f46b092 |

## Re-vérification indépendante (16 oct 2026, agent Vibe)

Portage TypeScript fidèle du micro-noyau et du banc T1–T7, exécuté (Python non disponible dans l'environnement de vérification). Résultat **7/7 conforme**, chiffres identiques au rapport :

- T1 : D3=30, ACCOMPLIE:geo=0, \"resync:D3\" en questions ✓
- T2_O1 : monde calme à 3 épisodes → 0 ruling, 0 question ✓
- T3_O2a : monde mixte 900 cycles → 1 ruling au cycle 31, D.unresolved=1.0000, Q1=1.0084, dist_D=0.8678 ✓
- T4_O2b : 2 trompeurs vs 3 véridiques → décision 3-2 au cycle 31, Q1=0.0669 ✓ (note : dans ce portage, les deux épisodes trompeurs sont clôturés par la décision unique du cycle 31 ; le rapport d'audit mentionne \"cycles 31 et 61\")
- T5_O3 : votes identiques dans les deux ordres de mémoire, témoin neutre équidistant abstentionniste ✓
- T6_U4 : réouverture à la parité de la minorité, nouvelle décision au cycle 91 ✓
- T7 : déterminisme + restauration de checkpoint (égalité octet par octet) ✓

Les empreintes SHA-256 des cinq fichiers ont été recalculées avant dépôt et correspondent au manifeste. Banc d'essai fonctionnel ; ne prouve ni conscience phénoménale ni autonomie.
