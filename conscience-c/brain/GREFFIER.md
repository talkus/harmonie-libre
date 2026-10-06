# Le greffier : Nemotron par Amazon Bedrock

Le greffier tient le greffe du ledger de C. Il présente les faits, il ne juge pas
et ne certifie pas. Code : `conscience_c_brain/greffier.py`. Tests :
`tests/test_greffier.py`.

## Partage des rôles

| Étape | Qui | Pourquoi |
|---|---|---|
| Vérifier la chaîne d'`events.jsonl` (seq, prev_hash, SHA-256) | le code | une vérification ne se délègue pas au modèle ; sur une histoire rompue, aucun appel n'est fait |
| Assembler le dossier (événements bruts, seq, hash) | le code | le greffier a accès à l'histoire brute, pas à un résumé |
| Rédiger l'acte de greffe | Nemotron 3 Super, `nvidia.nemotron-super-3-120b`, API Converse | présenter la trajectoire, citer chaque seq, dire ce qui manque |
| Relire les citations | le code | toute seq citée absente du dossier est nommée dans `citations_inconnues` ; le texte n'est pas retouché |
| Enregistrer l'acte | `greffe.jsonl`, registre chaîné à part | le greffier n'écrit jamais dans `events.jsonl` |

Chaque acte porte `statut: reconstruction_analytique`, `certifie: false` et
`decision: appartient_a_l_humain`. La réparation ne peut pas être auto-certifiée :
le greffier constate, l'humain décide.

## Région

Nemotron 3 Super n'est **pas** offert en `ca-central-1` (fiche Bedrock du modèle,
vérifiée le 2026-10-03). Le greffier appelle `us-east-1` par défaut ; `--region`
change ce choix parmi les régions de la fiche (us-east-1, us-east-2, us-west-2,
eu-west-1, …).

## Lancer dans AWS CloudShell

CloudShell a déjà Python 3 et boto3, et les identifiants du compte.

```bash
git clone -b claude/nemotron-greffier-bedrock-qn7och https://github.com/talkus/harmonie-libre.git
cd harmonie-libre/conscience-c/brain
python3 -m conscience_c_brain.cli --root ./brain_state status   # crée un ledger s'il n'y en a pas
python3 -m conscience_c_brain.greffier --root ./brain_state --dry-run   # dossier, sans appel
python3 -m conscience_c_brain.greffier --root ./brain_state             # acte de Nemotron
```

`--depuis N` limite le dossier aux événements à partir de la seq N. Un appel coûte
quelques milliers de jetons ; il n'y a aucun serveur à louer.
