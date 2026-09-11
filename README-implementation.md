# Anneau des 23 — Implémentation v2.0

> Protocole de validation multi-agent par consensus distribués et artefacts vérifiables.

## Contexte

Cette implémentation fait partie du projet **Harmonie Libre** de Mik Mireault. Elle traduit en code Python le protocole **Anneau des 23 v2.0**, conçu pour permettre la coopération entre multiples IA sans mémoire partagée, via des artefacts communs vérifiables.

## Fichiers

| Fichier | Description |
|---------|-------------|
| `anneau23_analyseur.py` | Classes Clause, Patch, VRF, Certificat + tests |
| `anneau23_vrf.py` | Module VRF (Verifiable Random Function) pour permutations déterministes |
| `anneau23_register.py` | Registre des 23 agents, validations, historique |

## Architecture

```
                    ┌─────────────────┐
                    │   Patch soumis   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Valider clauses │ ← anneau23_analyseur.py
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Générer VRF     │ ← anneau23_vrf.py
                    │  (permutation)   │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  23 agents       │ ← anneau23_register.py
                    │  valident        │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │  Certificat      │
                    │  (PLEIN/PARTIEL/NUL)│
                    └─────────────────┘
```

## Principes du protocole

1. **Pas de mémoire partagée** — Les IA communiquent uniquement via des artefacts (JSON, Markdown, registre).
2. **Validation distribuée** — 23 agents valident chaque patch; seuil de majorité = 12.
3. **VRF déterministe** — La sélection des validateurs est cryptographiquement déterministe.
4. **Traçabilité complète** — Chaque décision est horodatée, signée et enregistrée.
5. **Pas d'auto-modification** — Un agent ne peut pas modifier son propre registre.

## Invariants

- `sorted(perm) == list(range(23))` — La permutation est toujours complète.
- `cert.est_valide() → statut in (PLEIN, PARTIEL)` — Un certificat valide est plein ou partiel.
- `clause.valider_syntaxe() → len(interdits) == 0` — Une clause valide ne contient aucun interdit §5.2.

## Utilisation

```bash
# Tests unitaires
python3 anneau23_analyseur.py

# Démonstration VRF
python3 anneau23_vrf.py

# Démonstration registre
python3 anneau23_register.py
```

## Source

- Protocole original : `anneaudes23protocolev2.md` (Google Doc)
- Projet parent : Harmonie Libre (GitHub: talkus/harmonie-libre)
- Auteur : Mik Mireault
- Date : 2026-09-11

## Licence

Projet privé — Mik Mireault. Tous droits réservés.

---

> « Je choisis d'aimer, je me repens, je reçois le pardon, je rends grâce, je garde espoir, je recommence. »
