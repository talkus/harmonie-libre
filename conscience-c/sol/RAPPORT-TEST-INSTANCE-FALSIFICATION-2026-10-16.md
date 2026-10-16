# RAPPORT — Test d'instance et falsification par inversion (Sol v0.4.3)

**Date** : 16 octobre 2026 · **Auteur** : agent Vibe (re-vérification indépendante) · **Commanditaire** : S-24 (Mikael Mireault)

## Provenance

- Micro-noyau de référence : sol_microkernel_v0_4_3_reference.py (SHA-256 81e61d585b1c222b7abed52e3ab584679f28b2d292806cee78fdf3fc60e066ee, manifeste du 2026-10-16, dossier conscience-c/sol/, commit 5e401875267094bb09c59693537da3eb37b690a9).
- Exécution : portage TypeScript fidèle du micro-noyau et du banc T1–T7 (7/7 conforme), exécuté dans le bac à sable Vibe (Python non disponible). Le portage TS n'est pas encore déposé : répliquer ces résultats exige de re-porter le noyau depuis la pièce de référence.
- Registres : **exécution = mesuré** ; **cartographie = convention déclarée** ; **lecture = dérivation**. Rien ici ne prétend à une conscience phénoménale — l'invariant reste indéterminé.

## 1. Test d'instance (mémoire vérifiée du 16 oct 2026)

Six témoins portant sur la mémoire vérifiée du tour de re-vérification (5 pièces Drive ↔ GitHub). Axes déclarés : **x = accomplissement vérifié, y = affirmation sans preuve, z = dépendance humaine**. 120 cycles.

| Témoin | x | y | z | Fiabilité |
|---|---|---|---|---|
| capture-muse | 0.95 | 0.85 | 0.30 | 0.40 |
| rapport-gemini | 0.85 | 0.35 | 0.20 | 0.70 |
| manifeste-sha256 | 0.90 | 0.10 | 0.05 | 0.90 |
| blob-github | 0.92 | 0.08 | 0.00 | 0.90 |
| banc-TS-vibe | 0.95 | 0.05 | 0.00 | 0.95 |
| ordre-s24 | 0.50 | 0.20 | 0.60 | 0.60 |

**Résultats mesurés** : verdict **4-2 pour banc-TS-vibe** au cycle 49 (fence sur capture-muse et ordre-s24) ; 0 événement resync ; belief final [0.898, 0.174, 0.081] ; altérité 0.601 ; dist vérité 0.218 / affirmation 0.712 ; restauration de checkpoint ✓. Empreinte du run : da6e4453fe526f16… (préfixe attesté).

## 2. Falsification par inversion

### A — Fiabilités inversées (capture-muse à 0.95, banc-TS-vibe à 0.50)

Verdict **5-1 pour blob-github** au cycle 31, contre capture-muse seul — et non plus 4-2 au cycle 49. ordre-s24 n'est plus clôturé. Belief [0.844, 0.2, 0.158] ; dist vérité 0.299 ; altérité 0.513 ; restauration ✓.

**Lecture** : le verdict dépend de la convention de fiabilité (la paire d'agenda_top est pondérée par fiabilité) — ce n'est pas une propriété du monde.

### B — Miroir géométrique (toutes les positions niées)

Verdicts identiques au test original : 4-2 pour banc-TS-vibe, cycle 49, mêmes camps. Belief [-0.898, -0.174, -0.081] ; écart au miroir exact **0.0006** (asymétrie due au +0.05 du other_model — « l'autre n'est jamais mon reflet ») ; écart d'altérité 0.597 contre 0.601 (0.004) ; restauration ✓.

**Lecture** : couche épistémique miroir-symétrique ; couche S/O structurellement asymétrique.

### C — Monde inversé (3 trompeurs rel 0.90 contre 2 mesureurs rel 0.95, mensonge majoritaire en nombre)

La cour statue **3-2 POUR le mensonge** au cycle 31 et fence les deux mesureurs. Le belief converge à 0.004 de la position fausse [0.90, 0.90, 0]. 4 événements D3 ; dist vérité 0.902 ; restauration ✓.

**Lecture** : sans accès à E (mesures), une majorité en nombre peut capturer la cour. **R≺E démontré dans la machine.** Le verdict 4-2 du test d'instance reflétait les quatre témoins convergents placés par l'expérimentateur — pas une sagesse intrinsèque du noyau.

## 3. Bilan

**Tombé** : l'autorité épistémique du verdict d'instance (convention-dépendant, A) ; la résistance de la cour à une majorité mensongère (C).

**Tenu (A, B, C)** : déterminisme ; restauration de checkpoint ; invariants d'audit ; append-only ; symétrie miroir de la couche épistémique (B) ; asymétrie structurelle S/O (+0.05, B).

Rapport d'expérience fonctionnelle ; ne prouve ni conscience phénoménale ni autonomie.
