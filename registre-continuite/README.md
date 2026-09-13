# Registre de continuite gouverne

Systeme DuckDB de gouvernance de la connaissance avec 11 workflows, 11 invariants,
3 niveaux de sortie, et une couche d'attestation cryptographique.

Valide contre l'Architecture de cloture (11 frontieres).

## Structure

```
registre-continuite/
+-- sql/
|   +-- 001_documents.sql          - Ingestion (Frontiere 1-2)
|   +-- 002_entities.sql           - Extraction (Frontiere 6)
|   +-- 003_relations.sql          - Cycle de vie des relations (Frontiere 7)
|   +-- 004_contradictions.sql     - Suspension (Frontiere 8)
|   +-- 005_status_history.sql     - Trace append-only
|   +-- 006_signing_keys.sql       - Cles + attestations + roles + permissions
|   +-- 007_key_lifecycle.sql      - Cycle de vie NIST + compromised_since
|   +-- 008_chain_integrity.sql    - Chaine de hachage + ancrage externe
+-- attest/
|   +-- __init__.py
|   +-- envelope.py                - Enveloppe JCS (RFC 8785) + signature Ed25519
|   +-- keys.py                    - Enregistrement de cles (ceremonie)
|   +-- keys_lifecycle.py          - 8 phases NIST SP 800-57
|   +-- verify.py                  - Verification en 4 etapes
|   +-- key_crypto.py              - Generation + PKCS#8 chiffre
|   +-- chain.py                   - Append + ancrage du tip
|   +-- audit_chain.py             - Audit de la chaine + CLI
+-- authority/
|   +-- __init__.py
|   +-- apply_transition.py        - Service d'autorite (seul juge)
+-- attest_cli.py                  - CLI producteur de preuves JSON
+-- init_db.py                     - Migration + seed
+-- tests/
|   +-- test_verify_regressions.py     - 6 tests
|   +-- test_lifecycle_regressions.py  - 6 tests
|   +-- test_immutable_history.py      - 1 test
|   +-- test_chain_integrity.py       - 8 tests
+-- requirements.txt
+-- Makefile
+-- .gitignore
```

## Principe

> La cle publique vient du registre, jamais du payload ou des notes.
> Le CLI produit des preuves JSON. Le service d'autorite les applique.
> Seul apply_status_transition ecrit valid dans authorization_verification_result.

## Regle unifiante

> Celui qui detecte ne decide pas. Celui qui decide n'a pas detecte.
> Aucun statut n'est acquis par defaut.

## Installation

```bash
pip install -r requirements.txt
```

## Initialisation

```bash
python3 init_db.py --db registre.duckdb
```

## Produire une attestation

```bash
python3 attest_cli.py attest \
  --private-key ed25519_key.pem \
  --key-id key_mikael_01 \
  --actor-id mikael \
  --actor-role lead_auditor \
  --decision-id dec_001 \
  --decision-type status_transition \
  --subject-type relation \
  --subject-id rel_001 \
  --payload transition.json \
  --policy-versions policies.json \
  --out attestation_001.json
```

## Auditer la chaine

```bash
python3 attest/audit_chain.py --db registre.duckdb --json
# Codes : 0 = PASSED, 1 = VIOLATIONS, 2 = ERROR
```

## Tests

```bash
make test
# ou
pytest tests/ -v
```

## 11 invariants

1. Les originaux ne sont pas reecrits
2. Les inférences ne deviennent pas des faits par repetition
3. Les corrections ne sont pas des effacements
4. Les contradictions deviennent des objets de travail
5. Les decisions ont un auteur, une raison et une date
6. Les exports sont des instantanes verificables, non des verites autonomes
7. Celui qui detecte ne decide pas (Invariant 11)
8. Aucun statut n'est acquis par defaut
9. Rien n'est supprime silencieusement (Workflow 11)
10. La cle publique vient du registre, jamais du payload
11. Une signature emise avant compromised_since reste historiquement valide

## Dependances

- DuckDB >= 0.10
- cryptography >= 42.0
- rfc8785 (canonicalisation JSON)
- pytest >= 8.0

## Licence

Projet prive - Forteresse.
