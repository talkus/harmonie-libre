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

## Test d'instance et falsification (16 oct 2026, agent Vibe)

- `RAPPORT-TEST-INSTANCE-FALSIFICATION-2026-10-16.md` — instance du noyau sur mémoire vérifiée (verdict 4-2 pour banc-TS-vibe au cycle 49, empreinte da6e4453fe526f16…), puis falsification par inversion : **A** fiabilités inversées (5-1 pour blob-github au cycle 31 — verdict convention-dépendant) ; **B** miroir géométrique (écart au miroir 0.0006, asymétrie S/O +0.05) ; **C** monde inversé (3-2 pour le mensonge → R≺E démontré dans la machine). SHA-256 : 9153d9824d1b47ae5a7c0c8277e1c11d79554f7c94e53bd61393959a16e4c70b
## État régnant — mise à jour du 17 oct 2026 (agent Vibe, ordre S-24)

Le présent dossier conserve la référence historique v0.4.3 ci-dessus, pièces vérifiées et préservées. L'état régnant du projet a évolué le même soir, chaque adoption au mot de l'architecte (S-24, Mikael Mireault) :

- v0.4.3 adoptée le 16 oct 2026 à 18:15 EDT (ci-dessus) ;
- v0.4.5 « stratification » adoptée à 21:05 EDT ;
- **strat3-multiscale adoptée à 22:15 EDT — version régnante** : `sol_strat3_multiechelle_reference.py`, SHA-256 `a2929cf0eef4c8b81a18f890f97a12a5357ad8c45eede259cee056353d63c190`, POLICY_ID `sol.policy.strat3-multiscale-2026-10-16`, 301 tests (actes d'adoption sur Google Drive, section 09). Adoption confirmée par l'architecte à 22:41 EDT (« Oui je confirme ») après divergence de registre constatée puis résolue par pièces append-only.
- Fusion v0.4.8 : candidate éprouvée, adoption à 22:59 EDT **révoquée** à 23:00 EDT — non régnante.

La référence strat3 n'est pas déposée dans ce dépôt GitHub ; les pièces régna sont sur Drive (section 09) — divergence de couches nommée ici, non résolue par la présente. Limites ouvertes de la régnante (portées par son acte d'adoption) : identité de checkpoint dépendante de l'ordre de présentation ; seuil 0,35 non invariant d'échelle ; provenances non authentifiées ; empreintes non signées ; décisions groupées assumées comme politique (écart connu au banc de la lignée, T4_O2b).

Cette section est une addition : aucun contenu antérieur n'est modifié ni effacé ; l'historique git conserve le tout. Aucune adoption ni révocation n'est prononcée ici — le registre et le mot de l'architecte demeurent les seules autorités.
