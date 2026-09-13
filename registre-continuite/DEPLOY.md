# Guide de deploiement — Registre de continuite gouverne

## 1. Pre-requis

- Python 3.10+
- DuckDB >= 0.10
- Git

## 2. Installation

Clonez le depot et installez les dependances.

## 3. Generer une paire de cles

Utilisez scripts/generate_keypair.py avec une phrase de passe de 16+ caracteres.
Notez la cle publique (hex) et l empreinte SHA-256.
Ne JAMAIS committer le fichier PEM.

## 4. Initialiser la base

python3 init_db.py --db registre.duckdb --seed

Ceci execute les 9 fichiers SQL dans l ordre et insere le premier cas reel.

## 5. Enregistrer la cle dans le registre

Utilisez register_actor_key() puis activate_key() depuis attest.keys et attest.keys_lifecycle.
La cle publique vient du registrant, pas du payload.

## 6. Produire une attestation

python3 attest_cli.py attest avec les arguments necessaires.
Voir examples/ pour des fichiers de reference.

## 7. Auditer la chaine

make audit ou python3 attest/audit_chain.py --db registre.duckdb --json
Codes : 0 = PASSED, 1 = VIOLATIONS, 2 = ERROR

## 8. Tests

make test (silencieux) ou make test-verbose (detaille)

## 9. Securite

- Le fichier PEM ne quitte jamais la machine qui signe
- La phrase de passe ne quitte jamais la tete de l operateur
- Permissions 0600 sur le PEM
- Rotation additive toutes les 90 jours (recommande)
- Ancrage du tip apres chaque session d audit
- Audit de chaine avant toute decision basee sur le registre

## 10. Integration n8n

Importer n8n/registre-continuite-workflow.json dans n8n.
Variables : KEY_PATH, KEY_ID, ACTOR_ID.
