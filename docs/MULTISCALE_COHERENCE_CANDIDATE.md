# Cohérence structurelle multi-échelle — candidat κ/Δ/ρ/τ/UNKNOWN

**Statut :** candidat expérimental, non canonique, non autorisant.  
**Portée :** ajout de cohérence par auto-similarité structurelle multi-échelle.  
**Motif :**

```text
κ_n → Δ_n → ρ_n → τ_n → UNKNOWN_n → κ_(n+1)
```

Ce document ne remplace ni `SECURITY_COMMAND.md`, ni AEGIS-24, ni les sources de Conscience C. La cohérence n'est pas une preuve de vérité et n'accorde aucune permission d'exécution.

## Sémantique minimale

- **κ — couplage** : interaction, corrélation, dépendance ou possibilité de rencontre observée/hypothétique. Un couplage n'est pas une causalité.
- **Δ — distinction** : différence localement reconnue. Toute distinction doit citer le ou les couplages et les traces qui la soutiennent.
- **ρ — relation stabilisée** : structure dérivée de distinctions, toujours révisable et localement sourcée.
- **τ — trace** : provenance append-only. Une correction ajoute une trace ; elle ne réécrit pas la précédente.
- **UNKNOWN — frontière de pertinence** : couplages pour lesquels les distinctions pertinentes ne sont pas encore établies. UNKNOWN n'est jamais converti implicitement en PASS ou en permission.

## Invariants multi-échelle

**MS-01 — Auto-similarité structurelle.** Le même schéma κ/Δ/ρ/τ/UNKNOWN est vérifié à chaque échelle micro, méso, macro et méta.

**MS-02 — Non-identité des conclusions.** La répétition du schéma n'impose pas la même conclusion à chaque niveau.

**MS-03 — Provenance locale.** Chaque Δ et ρ cite ses traces locales ; une conclusion supérieure ne remplace pas sa provenance inférieure.

**MS-04 — Contradiction ascendante.** Un enfant peut contester une prémisse du parent avec une trace. La contestation remonte sans effacer le reçu parent.

**MS-05 — Non-réécriture.** Correction ≠ effacement. Les reçus sont adressés par contenu ; une nouvelle version produit un nouveau reçu.

**MS-06 — Non-auto-certification.** L'auto-vérification peut produire un candidat cohérent, pas une validation indépendante.

**MS-07 — UNKNOWN fail-closed.** Une frontière UNKNOWN conserve le statut INDETERMINATE et ne produit aucune autorité d'exécution.

**MS-08 — Couplage ≠ causalité.** La promotion d'un couplage en causalité exige une preuve causale explicitement référencée.

**MS-09 — Structure ≠ autorité.** L'auto-similarité peut se répéter ; l'autorité ne se propage pas automatiquement avec elle.

**MS-10 — Symbolique sans privilège.** Renommer ou retirer des labels symboliques ne doit modifier ni le hash opérationnel ni le verdict.

**MS-11 — Composition vérifiable.** Les liens parent/enfant et les cibles de contestation doivent résoudre vers des reçus présents dans la composition vérifiée.

**MS-12 — Pas de scalaire totalisant.** Le système conserve les verdicts locaux et les causes ; il ne réduit pas la cohérence à un score unique.

## Runtime candidat

Le module `conscience_c_brain.multiscale_coherence` matérialise le motif sous forme de reçus typés. Il retourne seulement :

```text
CANDIDATE_OK
PARTIAL
INDETERMINATE
CONTESTED
```

et fixe toujours :

```text
execution_authority = false
```

La couche de cohérence est donc une couche de preuve/diagnostic, pas un mécanisme d'autorisation.

## Tests hostiles inclus

Le lot de tests vérifie notamment :

1. provenance obligatoire pour Δ ;
2. UNKNOWN fail-closed ;
3. couplage non promu silencieusement en causalité ;
4. auto-vérification distincte d'une validation indépendante ;
5. renommage symbolique sans effet opérationnel ;
6. contestation enfant → parent sans réécriture du parent ;
7. résolution des liens de composition ;
8. même validateur aux quatre échelles.

## Persistance

La persistance doit rester append-only ou event-sourced. Un backend externe peut stocker les reçus et leurs hashes, mais il ne devient ni source de vérité sémantique ni autorité d'exécution par simple stockage.
