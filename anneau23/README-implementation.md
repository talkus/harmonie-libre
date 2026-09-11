# Anneau des 23 — Implémentation v2.0

## Vue d'ensemble

L'Anneau des 23 est un protocole de gouvernance vérifiable pour systèmes multi-agents.
Il définit 23 clauses et 24 invariants structurels, avec 7 brèches connues.

Ce dépôt contient l'implémentation Python de trois sections clés:

| Fichier | Section | Description |
|---------|---------|-------------|
| `anneau23_analyseur.py` | §5 | Analyseur statique des invariants de l'Anneau |
| `anneau23_vrf.py` | §7 | Ordonnancement déterministe par VRF (permutation vérifiable) |
| `anneau23_predictions.py` | §9 | Prédictions réfutables issues des invariants |

## Installation

```bash
# Python 3.10+ requis, aucune dépendance externe
python anneau23_analyseur.py
python anneau23_vrf.py
python anneau23_predictions.py
```

## Architecture

### §5 — Analyseur statique

L'analyseur vérifie que chaque clause respecte ses invariants structurels.
Il détecte les brèches et propose des correctifs (patches).

```python
from anneau23_analyseur import Anneau23, Clause

anneau = Anneau23()
clause = Clause(numero=1, texte="L'Anneau refuse le dogme...")
anneau.ajouter_clause(clause)
rapport = anneau.analyser()
```

### §7 — Ordonnancement VRF

Le VRF (Verifiable Random Function) produit une permutation déterministe
et auditable des clauses. La permutation est reproductible et vérifiable.

```python
from anneau23_vrf import ordonnancer_clauses, verifier_permutation

ordre = ordonnancer_clauses("2026-09-11:mission-001")
# Vérification indépendante possible
```

### §9 — Prédictions réfutables

Chaque invariant produit des prédictions testables. Si une prédiction est
réfutée, l'invariant associé doit être révisé.

```python
from anneau23_predictions import PREDICTIONS_REGISTRE, générer_rapport_prédictions

rapport = générer_rapport_prédictions()
```

## Invariants (24)

1. I01 Refus du dogme
2. I02 Révisabilité
3. I03 Vérifiabilité
4. I04 Non-substitution
5. I05 Proportionnalité
6. I06 Minimalité
7. I07 Trace persistante
8. I08 Citation source
9. I09 Séparation des pouvoirs
10. I10 Consentement explicite
11. I11 Droit de retrait
12. I12 Audibilité
13. I13 Réversibilité
14. I14 Gradation
15. I15 Non-automatisation
16. I16 Contexte de conservation
17. I17 Décompte explicite
18. I18 Partage vérifiable
19. I19 Carence attestée
20. I20 Priorité au consentement
21. I21 Archive lisible
22. I22 Non-extrapolation
23. I23 Décompte des brèches
24. I24 Horodatage vérifiable

## Brèches connues (7)

1. B01 Archive incomplète
2. B02 Citation manquante
3. B03 Consentement implicite
4. B04 Substitution silencieuse
5. B05 Extrapolation non marquée
6. B06 Pouvoir non séparé
7. B07 Trace effaçable

## Licence

Projet personnel — Mikael Mireault — 2026
