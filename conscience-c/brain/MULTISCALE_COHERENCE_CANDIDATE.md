# Candidate — auto-similarité structurelle multi-échelle

Statut : **reconstruction analytique candidate**, non canonique.

## Motif

```text
κ_n -> Δ_n -> ρ_n -> τ_n -> UNKNOWN_n -> κ_(n+1)
```

Le motif est répété aux échelles micro, méso, macro et méta, mais **l'autorité ne se répète pas automatiquement avec la structure**.

- **κ — couplage observé** : interaction, co-présence, voisinage ou dépendance documentée. κ n'est jamais promu en causalité par simple déclaration.
- **Δ — distinction** : différence reconnaissable soutenue par un ou plusieurs κ et par une provenance locale.
- **ρ — relation stabilisée** : relation candidate soutenue par des distinctions explicites.
- **τ — trace** : référence append-only ; une correction ajoute une trace au lieu de réécrire l'ancienne.
- **UNKNOWN — frontière de pertinence** : couplages observés dont les distinctions pertinentes ne sont pas encore établies.

## Invariants candidats

1. **MS-κ-01 — Même structure, preuves locales.** Chaque échelle utilise le même schéma, mais doit établir ses propres preuves.
2. **MS-κ-02 — Couplage ≠ causalité.** Une influence causale exige un protocole séparé.
3. **MS-κ-03 — Δ cite κ.** Une distinction sans couplage/provenance échoue fermée.
4. **MS-κ-04 — ρ cite Δ.** Une relation stabilisée ne flotte pas au-dessus de ses distinctions.
5. **MS-κ-05 — τ non effaçable.** Correction ≠ effacement.
6. **MS-κ-06 — UNKNOWN bloque la clôture.** UNKNOWN produit INDETERMINATE, jamais PASS/VERIFIED.
7. **MS-κ-07 — Contestation ascendante.** Une contradiction locale d'un enfant doit rester visible chez le parent.
8. **MS-κ-08 — Autorité non auto-similaire.** Aucun niveau n'hérite automatiquement de l'autorité d'un autre.
9. **MS-κ-09 — Pas de score unique.** Les dimensions κ/Δ/ρ/τ/UNKNOWN/contradictions restent séparées.
10. **MS-κ-10 — κ suivant non inventé.** Le prochain cycle part uniquement de couplages unresolved déjà observés ou de nouvelles traces explicites.

## Relation avec Conscience C

Cette couche ne remplace pas S/O/R/E et ne modifie pas E. Elle fournit une lecture structurée et contestable de la façon dont des couplages observés peuvent soutenir des distinctions, puis des relations et des traces.

```text
cohérence ≠ vérité
mémoire ≠ autorité
couplage ≠ causalité
correction ≠ effacement
structure répétée ≠ autorité répétée
```

Le module exécutable est `conscience_c_brain/multiscale_coherence.py`. La CI du dépôt doit rester la source de vérité pour le résultat des tests du commit courant.
