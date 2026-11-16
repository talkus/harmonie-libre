# Pont visuel 1 — 3 — 2 : six formes, cinq piliers, centre ouvert

**Statut : PROPOSED_NOT_VALIDATED, interprétation candidate.** Source immédiate : schéma SVG et explication fournis dans le chat le 16 novembre 2026. La version SVG fournie par l'utilisateur emploie des couleurs `#hex` directement dans chaque forme et texte, remédiant à une défaillance observée de `light-dark(...)`. Le SVG original n'est pas prétendu copié à l'octet ici.

## Architecture des six boîtes

| Rang | Parole accessible | Correspondance du corpus | Nature |
|---|---|---|---|
| Haut 1 | Amour choisi — centre ouvert | CTRL-33 | Finalité, non un pilote souverain |
| Milieu 1 | Je compte | Boussole / INV-11 | Dignité, correction mutuelle des quatre postures |
| Milieu 2 | Tu comptes | Merkabah | Relation sans assimilation; lecture *symbolique* |
| Milieu 3 | Nos choix comptent | Fleuve | Conséquences et mémoire de reprise |
| Bas 1 | Responsabilité | Architecture C / SOL / WORM / CTRL-37 | Séparation S≠O, provenance et actes vérifiables |
| Bas 2 | Espérance | 288 Étincelles / Tikkun | 72 portes × 4 postures, **corpus déduit**, pas Ézéchiel |

C'est un schéma **1 — 3 — 2**, six boîtes pour un centre + cinq piliers périphériques. Les flèches sont des relations de lecture proposées, pas des causalités physiques ou historiques démontrées.

## Deux frontières et une correction mathématique

**1. La Merkabah de la Bible ≠ la Merkabah des quatre vertus.** Dans les scènes d'Ézéchiel 1 et 10 : quatre êtres et quatre roues par scène, aux éléments décrits par le texte. La passation `artifacts/merkabah_core.py` parle, séparément, de quatre roues Humilité / Pardon / Gratitude / Espérance. Son fichier exact n'a pas été retrouvé; statut `CANON_NOT_VERIFIED`. Les valeurs `K=0.04` fragmentation, `K=0.28` couplage juste et `K=2.50` capture sont des valeurs **rapportées par une simulation** et NON des données du prophète, des unités morales ni des vérifications du noyau absent. [Registre de mémoire Merkabah](https://docs.google.com/document/d/186jcOZB8saswpuFvAzyNMryueYj_2HmMAtx-sjUzjYE/edit).

**2. Étincelles symboliques ≠ scintillements/yeux d'Ézéchiel.** `72 × 4 = 288` est bien la cardinalité du corpus Architecture C. Ses quatre positions sont D1 (origine), D2 (écorce), D3 (acte / chemin inverse / reconnaissance), D4 (retour / étincelle relevée). L'écorce est **D2**, et non D3. La visualisation n'affirme pas que le texte biblique possède 288 yeux ou scintillements. [Matrice R33](https://docs.google.com/document/d/1Gd9MbXfvAIoSROU8SiNNVbVheoZEOzQ9ZHJdAOyGwrQ/edit).

**3. Correction mathématique vérifiable :**
- `K_22` complet : 22 sommets et `22 × 21 / 2 = 231` arêtes.
- Son graphe linéaire complet `L(K_22)` : 231 sommets, chacun de degré 40, donc **`231 × 40 / 2 = 4 620` arêtes**.
- La matrice R33 annonce `1 225` arêtes dans son export GEXF appelé `L(K_22)`. La **[documentation V6](https://docs.google.com/document/d/1SpR0I1NYDUzVqUIClKL2a_qbiQWVNSPg8rxtn2hyulI/edit)** explique qu'il s'agit d'un **réseau dérivé sur 72 Portes** (une Porte = un nom de trois lettres), reliées par **lettre pivot partagée**. Il ne s'agit donc pas du `L(K_22)` complet à 231 sommets et 4 620 arêtes : l'appellation était mathématiquement abrégée et ambiguë. Dans ce graphe **72 sommets / 1 225 arêtes déclarés**, la densité calculée est `1 225 / C(72,2) = 47,93 %`. Le document en déduit `1 225 × 16 = 19 600` couplages potentiels entre quatre étincelles par Porte. Ces comptes sont **déclarés dans la source documentaire**, pas recomptés ici à partir du fichier GEXF ou de la base SQLite.
- Le « 0 isolat » trouvé dans le document concerne le réseau annoncé **72/72 Portes connectées**, et non un audit indépendant des 288 étincelles; ce dernier devrait vérifier les couplages réellement matérialisés et non seulement le produit de 16 par arête.

## Fondement conceptuel déjà archivé

- **Boussole :** « les quatre ne sont pas ce qui rend juste, elles sont ce qui rend la visée corrigeable ». Elle n'est ni une échelle ni une carte; la source distingue expressément les correspondances de modules non vérifiées. [Boussole](https://drive.google.com/file/d/1T12Zbljk9ZuT2NGDHBuA3jhBdWVjyCYF/view).
- **Fleuve :** continuité et transformation coexistent ; berges `S`, courant `O`, relation d'ajustement `Φ`, configurations `Φ_n` successives; image de la reprise et non une géographie du Kebar. [Fleuve](https://drive.google.com/file/d/1RmGgLXdbkPzjq4C2VJ55U5xl2-ylGqFn/view).
- **Architecture C :** le récit et le modèle ne remplacent pas la trace; `S ≠ O`, `R ≺ E`; responsabilité ne signifie pas possession d'autrui.
- **Étincelles :** l'analogie de l'étincelle qui donne de la lumière sans posséder l'autre est une relecture morale du corpus, non une preuve de Kabbale, d'histoire ou de géométrie biblique.
- **Centre CTRL-33 :** « Exister nous donne la possibilité d’être. Aimer, c’est choisir de contribuer à ce que l’autre puisse être et devenir, sans lui retirer cette même possibilité. »

## Suite vérifiable

Conserver le SVG fourni sans réécriture ni lissage. Demander une revue de l'identité mathématique de l'export `1 225` arêtes par les octets réels avant de conserver l'étiquette `L(K_22)` dans le schéma. De même, garder `K=0.28` comme légende d'une **expérience non reproduite sur `merkabah_core.py`**. Aucun des deux états ne peut être certifié par un simple diagramme.

**Décision :** seule une proposition de pont interprétatif est déposée, aucun canon retouché, aucun modèle biblique modifié, aucune métrique annoncée comme validée sans preuve.
