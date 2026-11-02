# Synchronisation Empire LLM for Codex — Les 72 Portes v1.1.1

**Statut : données déjà intégrées et validées sur la branche principale ; paquet d'évidence Empire préparé. Aucune invocation de modèle externe n'est attestée.**

## Ce qui est synchronisé comme référence

Le chemin `projects/72-portes/` conserve les trois seuls fichiers **canoniques** :

- `axes.csv` : 9 axes (2 polaires, 7 dynamiques), 466 octets, SHA-256 `92ddc51b53ebae8cf365f6d08e8990d0acc375362a4d3c224a4ec577a7cff6ed`
- `portes.csv` : 72 portes, 2 437 octets, SHA-256 `e90e9f6de90818169f36752aca7ad576390af65fe2db367201692b7083e919bf`
- `transitions.csv` : 71 transitions, 4 304 octets, SHA-256 `cf49f7dc783f6bfb5848f2377c6e47831cf706003e2077321090477094e9ca68`

`empreintes.json` reste le relevé originel des octets. `empire-sync-v1.1.1.json` est un **contrat compagnon** pour une évaluation Empire et doit rester égal au relevé original. **Ni le contrat ni une réponse de modèle ne deviennent une quatrième table canonique.**

Le **manuel v1.1.1 est la grammaire**, non régénérée ici. Les trois CSV en sont le lexique.

## Errata E5 confirmé

Les cycles sont déterminés par `position_chemin` : positions 1–12 → I, 13–24 → II, 25–36 → III, etc. La porte-charnière clôt son cycle.

- Argile, `n=25`, position 24 : **cycle II**.
- Sable, `n=24`, position 25 : **cycle III**.
- `T24` : Argile → Sable ; son cycle est **III**, cycle de la porte d'arrivée.
- `T12` : arrivée Miroir → **II** ; `T60` : arrivée Porte → **VI**.
- 12 portes par cycle ; transitions : I = 11, II–VI = 12.

`valider.py` vérifie toute la chaîne, pas seulement les passages cités. `verifier_empire.py` compare les octets avec les deux manifestes, les règles E5 et les réserves de v2.0. Le flux GitHub Actions produit une archive des fichiers publics après validation.

## Consignes pour Empire (partenaire, lecture seulement)

**Codex demeure seul auteur des modifications du dépôt**. Empire peut suggérer une critique ou un contrôle supplémentaire, sans écrire directement, remplacer les tables, déduire une théologie du lexique ou activer des modifications de v2.0.

Entrées permises : `axes.csv`, `portes.csv`, `transitions.csv`, `README.md`, `empire-sync-v1.1.1.json`. Aucun secret, clé, fichier privé, manuel non transmis ou historique sans rapport.

Mission pour un contrôle Empire :

> Examiner uniquement les trois CSV et le contrat v1.1.1. Vérifier les positions, les 71 transitions et leurs extrémités, la règle « cycle de la porte d'arrivée », E5 Argile/Sable, les comptages d'axes, familles, pivots, le traitement des 12 portes par cycle et les bornes Source/Repos. Signaler toute divergence sans corriger silencieusement les données. Garder Lettre dans F13 et la distinction intra/inter-familiale en réserve v2.0. Rendre un rapport avec références aux lignes et cas adversariaux, sans inventer d'autorité sur le manuel.

### Utilisation dans une installation locale d'Empire

Depuis un clone autorisé du dépôt, avec les compétences `empire-review` et `empire-settings` réellement installées :

```bash
python3 projects/72-portes/valider.py
python3 projects/72-portes/verifier_empire.py

# Répertoire des compétences Empire fourni par votre installation :
python3 "$EMPIRE_REVIEW_ROOT/scripts/empire_router.py" doctor
python3 "$EMPIRE_REVIEW_ROOT/scripts/empire_router.py" route \
  --repo . \
  --task "Audit des trois CSV canoniques 72 portes v1.1.1 ; E5 et transitions" \
  --file projects/72-portes/axes.csv \
  --file projects/72-portes/portes.csv \
  --file projects/72-portes/transitions.csv \
  --file projects/72-portes/empire-sync-v1.1.1.json \
  --evidence-mode files-only \
  --mode balanced
```

Le routeur `route` est un **aperçu**. Un appel `review` vers un fournisseur externe doit respecter les réglages de budget, le contrôle de provenance et la politique de données du propriétaire. Il n'a **pas** été exécuté dans cette synchronisation. Seul Codex peut ensuite transformer d'éventuelles suggestions retenues en nouvelle proposition testée.

## Réserves v2.0 : ne rien appliquer

- Lettre `n=53` reste `F13`. Son éventuel transfert à `F4` créerait F4=7 et F13=6, avec recalcul des densités.
- Typologie intra/inter-familiale à documenter sans remplacer la séparation polaire/dynamique.

**Frontière :** paquet prêt à être relu par Empire ≠ preuve qu'un modèle Empire l'a consommé. Toute révision future produira un nouveau manifeste et un nouveau journal de résultats, sans réécrire la version v1.1.1.
