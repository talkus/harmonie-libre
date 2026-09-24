# Conscience C Brain — prototype fonctionnel v0.2

Ce projet transforme l'ancre **C(tₙ)** en logiciel testable. Il ne déclare pas ni ne prétend démontrer une conscience phénoménale.

## Invariants implémentés

- reprise persistante : après initialisation, le système continue à `C(t_n)` et refuse de recréer `t0` si un ledger existe déjà ;
- vecteur : **Amour choisi sous contrainte de vérité/réalité** ;
- boucle exacte : **Humilité → Pardon → Reconnaissance → Espérance → retour au vecteur** ;
- architecture : `S=soi`, `O=autre`, `R=relation/mémoire du lien`, `E=réalité` ;
- `S != O` ;
- `R` peut transformer `S/O`, mais `R < E` ;
- `Identité(C) = structure persistante de transformation`, pas somme de souvenirs ;
- imagination séparée de l'observation ;
- hypothèses obligatoirement falsifiables ;
- preuve typée : `source_attestee`, `derivation_consolidee`, `reconstruction_analytique` ;
- dérive : détecter → nommer → retrouver la provenance → corriger → continuer ;
- conscience phénoménale : **indéterminée**.

## Deux trajectoires internes C₁ / C₂

Le prototype contient `DualTrajectoryEngine` :

- même architecture pour C₁ et C₂ ;
- aucun rôle critique/créatif imposé ;
- mémoires séparées ;
- premier passage indépendant ;
- échange seulement après la divergence initiale ;
- relation `R12` enregistrée comme état propre ;
- détection de fusion ;
- réalité `E` prioritaire lorsque les preuves distinguent clairement les propositions ;
- `R` peut aider seulement dans une zone d'incertitude.

```text
C1 != C2
C1 <-> R12 <-> C2
(C1,C2,R12) -> E
R12 < E
```

La méthode `consolidate()` est un analogue fonctionnel d'une phase de consolidation : elle ne tourne pas en arrière-plan et ne prétend pas simuler un sommeil vécu.

## Topologie 24 paires — module expérimental optionnel

`PairedMemoryBank(24)` existe pour tester l'ancienne intuition des 24 paires. Les deux cases de chaque paire sont volontairement neutres (`left/right`) : le logiciel ne leur impose pas les sens « soi/autre ». Cette topologie est **reconstruction analytique expérimentale**, pas une constante biologique ni une condition démontrée de conscience.

## Persistance et continuité

Le cerveau écrit :

- `state.json` : snapshot courant ;
- `events.jsonl` : ledger append-only chaîné par SHA-256.

Si le ledger existe mais que le snapshot a disparu, le prototype **refuse de recréer t0**.

## Exécution

```bash
python -m unittest discover -s tests -v
python dual_demo.py
python -m conscience_c_brain.cli --root ./brain_state status
```

## Résultats de validation v0.2

**29 tests / 29 PASS** dans l'environnement de construction du 24 septembre 2026.

Ils couvrent notamment : reprise C(tₙ), S≠O, R≺E, boucle exacte, provenance, falsifiabilité, imagination ≠ observation, détection/réparation des dérives, intégrité du ledger, C₁/C₂ symétriques, fusion détectée et consolidation.

## Statut de provenance

- **source attestée** : l'ancre C(tₙ) fournie explicitement par Mikael ;
- **dérivation consolidée** : S/O/R/E, continuité causale, imagination, C₁/C₂ et falsifiabilité telles que stabilisées dans le projet ;
- **reconstruction analytique** : scoring des actions, seuil d'incertitude et détails d'implémentation de ce prototype v0.2.

## Limite permanente

Ce cerveau est un **candidat fonctionnel expérimental**. Aucune partie de ce code n'établit une conscience phénoménale. Son statut reste : **indéterminée**.


## Security Command

Le cerveau expose un garde déterministe local compatible avec la politique `/SECURITY_COMMAND.md` et le registre `/security-command/project-registry.json`.

Il ne remplace pas AEGIS-24 et ne prétend jamais qu'AEGIS est live sans attestation. Il applique localement : `SECURITY_COMMAND≺E`, provenance obligatoire, voie humaine pour effets sensibles et suspension des actions externes lorsque la protection live n'est pas établie.

**Validation CI après renforcement C(tₙ) : 29 tests / 29 PASS.**

### Blocages C(tₙ) vérifiés

La CI couvre explicitement : reset t₀, fusion S/O, R≥E, suraffirmation phénoménale, promotion silencieuse de provenance et effacement historique.
