# Reliability Gate — refuser les faux succès

Prototype **shadow-only**, déterministe et sans dépendance externe, soumis au
[SECURITY_COMMAND](../SECURITY_COMMAND.md) et à la règle
**Amour choisi sous contrainte de vérité/réalité**. La bienveillance n'autorise
ni faux certificat ni promotion arbitraire. Le programme évalue des assertions
techniques, **jamais la valeur morale d'une personne**.

## Où il corrige les défaillances observées

- **Hallucination de preuve** : ratification, absence de bypass, WORM, fiabilité
  globale et auto-application retournent `SUSPEND` faute de vérification hors
  de ce composant, même si l'entrée prétend apporter un certificat.
- **Action à fort impact** : `HUMAN_SEAL_REQUIRED`. La fonction ne signe rien.
- **Absence, contradiction temporelle ou forme invalide** : `SUSPEND` ou
  `BLOCK`; jamais un `ALLOW` déduit d'une entrée utilisateur.
- **Oubli d'un incident** : journal local JSONL hash-chaîné et tests de
  falsification. L'historique d'un ancien constat n'est pas modifié.
- **Biais de l'autotest** : 30 cas de *frontière de preuve* en CI, pas 30
  validations factuelles ou humaines. Les prompts mémorisés dans Archivist
  ne sont pas un benchmark indépendant et ne prouvent aucune exactitude RAG.

## Essayer localement

```bash
python -m unittest discover -s reliability_gate/tests -v
python -m reliability_gate.cli evaluate reliability_gate/fixtures/example.json --ledger /tmp/fleuve-receipts.jsonl
python -m reliability_gate.cli verify /tmp/fleuve-receipts.jsonl
```

`ADVISE` signifie **document consultable uniquement**, pas autorisation
d'exécuter. Les autres verdicts ont un code de sortie 2.
Les entrées sont de petits objets JSON sans secret et avec une référence de
source (pas un objet métier brut). Les métadonnées de preuve **ne sont pas
authentifiées** : une URL, un timestamp ou un hash fourni par le demandeur
n'est jamais une attestation.

| Verdict | Effet réel |
| --- | --- |
| `BLOCK` | Refus d'une entrée structurellement invalide |
| `SUSPEND` | Preuve absente, hors date ou non indépendante |
| `HUMAN_SEAL_REQUIRED` | Impact élevé ou irréversibilité |
| `ADVISE` | Observation limitée, sans exécution ni reconnaissance de vérité |

**Frontière exacte** : l'outil ne route pas les RPC Supabase, les Edge
Functions, GitHub merge ni les réponses ChatGPT. Le workflow GitHub ne devient
une condition de merge obligatoire que si un administrateur configure les
règles de protection de branche. Le journal local SHA-256 n'est pas WORM :
suppression de la fin, remplacement intégral et contrôle de l'hôte ne sont
pas détectables sans scellement externe.

Conserver les revues humaines, l'authentification des preuves, la
synchronisation Archivist/Supabase et le scellement externe comme
**travaux non réalisés**. Aucun résultat local n'autorise à modifier le Nom.
