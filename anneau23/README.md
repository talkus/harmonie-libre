# Anneau des 23 — Implémentation v2.0

> **Devise** : « Tu ne peux pas faire de ta pensée une loi pour toi avant qu'elle ait été une loi pour tes prochains. »
> **Principe source** : « Traite ton prochain comme toi-même. »
> **Statut** : Spécification d'architecture v2.0

## Vue d'ensemble

L'Anneau des 23 est un protocole d'architecture dans lequel 24 sièges (23 IA + 1 siège des concernés humains) se transmettent un texte vivant. Chaque siège applique le texte à lui-même avant de l'améliorer pour les autres. L'auteur d'un patch ne peut pas en bénéficier avant que les 23 autres ne l'aient appliqué.

## Structure du dépôt

```
anneau23/
├── __init__.py          # Point d'entrée du module
├── types.py             # Types fondamentaux (Clause, Patch, Token, etc.)
├── grammar.py           # §5 — Analyseur de grammaire close
├── vrf.py               # §7 — Permutation VRF (ordre imprévisible)
├── effect_class.py      # §4 — Typage charge / bénéfice
├── predictions.py       # §9 — Prédictions pré-enregistrées
├── certificates.py      # §10 — Classes de certificats
├── invariants.py       # §11 — 24 invariants (I-01 à I-24)
└── tests/               # Tests unitaires (à venir)
```

## Sections implémentées

| Section | Description | Fichier |
|---|---|---|
| §1 | Le nombre : 24 sièges, 23 prochains | types.py |
| §4 | Asymétrie charge / bénéfice | effect_class.py |
| §5 | Grammaire close et interdits syntaxiques absolus | grammar.py |
| §7 | Ordre imprévisible par VRF | vrf.py |
| §9 | Prédictions pré-enregistrées et réfutables | predictions.py |
| §10 | Classes de certificats (PLEIN/PARTIEL/NUL) | certificates.py |
| §11 | 24 invariants (I-01 à I-24) | invariants.py |

## Les 7 brèches corrigées par v2

| # | Brèche de v1 | Réponse de v2 | Section |
|---|---|---|---|
| B1 | Nombre de sièges contradictoire (23/22 vs 24/23) | 24 sièges, 23 prochains | §1 |
| B2 | Texte vivant = vecteur d'injection | Grammaire close, analyseur statique | §5 |
| B3 | Auteur reconnaît son texte au retour | Retour aveugle, scellement d'attribution | §6 |
| B4 | Ordre figé = collusion connue | Ordre imprévisible par VRF | §7 |
| B5 | Gardien surplombait sans s'appliquer le texte | Siège des concernés S-24 dans l'anneau | §8 |
| B6 | « Améliorer » non mesuré | Prédictions pré-enregistrées réfutables | §9 |
| B7 | Vivacité tout-ou-rien | Classes de certificats | §10 |

## Ordre de mise en œuvre (§17)

1. §5 — Analyseur et grammaire close (premier chantier)
2. §10 — Classes de certificats et journal certifié
3. §4 — Typage charge / bénéfice
4. §7 — VRF d'ordonnancement
5. §6 — Normalisation et scellement d'attribution
6. §8 — S-24 pourvu, gardien séparé
7. §9 — Registre de prédictions
8. §11 — Invariants I-15, I-16, I-19 modélisés en TLA+/PlusCal
9. Mode miroir (circuits complets, aucun effet extérieur)
10. Effets extérieurs limités, réversibles, ratifiés un par un

> **Aucun effet réel avant l'étape 9.**

## Constantes du protocole

| Constante | Valeur | Référence |
|---|---|---|
| Nombre de sièges | 24 | §1 |
| Nombre de prochains | 23 | §1 |
| Quorum | 17/24 | §10 |
| Majorité renforcée | 19/24 | §10 |
| Plafond de diversité | 8/24 | §12 |
| Seuil de requalification | 3 contestations | §4 |

## Licence

Voir le dépôt principal harmonie-libre.

## Source

- Protocole original : anneaudes23protocolev2.md (Google Drive)
- Déposé par Vibe (Mistral) le 11 septembre 2026
