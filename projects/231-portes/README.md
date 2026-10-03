# Les 231 Portes — opérateurs binaires

Ce module donne une place dans le code au texte de mik du 2 octobre 2026,
« Les 231 Portes comme Opérateurs Binaires Fondamentaux ». Il en suit les
étapes : les 22 lettres comme primitives (étape 1), la règle de composition
par catégories (étapes 2 et 3), les opérateurs nommés (étape 4), la matrice
22×22 (étape 5) et l'API `porte(x, y)` (étape 6).

```bash
cd projects/231-portes
python -m unittest discover -s tests -v
python -m portes_231            # résumé et matrice des faces
python -m portes_231 א מ        # les deux lectures d'une porte
python -m portes_231 --nommes   # les 52 opérateurs nommés
```

```python
from portes_231 import porte, Porte

porte("א", "ב")("esprit", "contenant")   # 'État conditionnel: esprit si contenant'
p = Porte.de("ש", "ת")
p.face.nommage.fonction                  # 'hash()'
p.dos.nommage.fonction                   # 'sign()'
```

## Ce qui vient d'où

| Élément | Source | Statut |
|---|---|---|
| 22 lettres ; 3 mères אמש, 7 doubles בגדכפרת, 12 simples הוזחטילנסעצק | Sefer Yetzirah 1:2, ch. 3 à 5 | `source_attestee` |
| 231 portes, face et dos (ענג en haut, נגע en bas) | Sefer Yetzirah 2:4 (recension du Gra) | `source_attestee` |
| Primitives (Unit, Stream, Container…), bits des doubles, règle 3×3, noms d'opérateurs | texte de mik, 2026-10-02 | `reconstruction_analytique` |
| Les portes comme « code source de la création », le Tikkun Olam par l'exécution correcte du code (étape 7) | lecture de mik | `indetermine` ; non codé |

Le code garde cette séparation : `Lettre.statut_categorie` et
`Operateur.statut_porte` valent `source_attestee`, `Lettre.statut_primitive`
et `Operateur.statut_lecture` valent `reconstruction_analytique`. Aucune
lecture computationnelle n'est promue en source attestée.

## Conventions choisies

Là où le texte laisse un choix ouvert ou se contredit, une seule convention
est tenue partout :

1. **Face = ordre alphabétique.** La face d'une porte est X ⊗ Y où X précède
   Y dans l'alphabet, comme dans la matrice de l'étape 5 ; le dos est Y ⊗ X.
   Trois exemples de l'étape 4 sont écrits dans l'autre ordre : מ–ד, מ–ז et
   ש–ט. Leur sens est gardé tel quel, attaché à la paire ordonnée : `fopen()`
   reste Stream ⊗ Access, mais c'est le dos de la porte ד–מ, pas sa face. Même
   chose pour `split()` (dos de ז–מ) et `map()` (dos de ט–ש, dont la face est
   `reduce()`).
2. **Raphe = 0, dagesh = 1.** Le texte dit « fort (dagesh) et faible (raphe) »
   sans fixer lequel vaut 1. L'état faible vaut 0 : Bet vide = 0, plein = 1.
3. **Un nom n'est pas une clé.** `map()` nomme deux opérateurs (מ ⊗ ש et
   ש ⊗ ט), `split()` aussi (ז ⊗ ח et מ ⊗ ז). Les opérateurs sont indexés par
   leur paire de lettres, jamais par leur nom.

## Ce que le code a fait apparaître

La règle de l'étape 6 ne regarde que les catégories. Entre deux lettres de la
même catégorie, X ⊗ Y et Y ⊗ X suivent donc la même règle :
`porte("ה", "ו")("x", "y")` et `porte("ו", "ה")("x", "y")` donnent tous deux
« Composition d'axes: x puis y ». La non-commutativité de ces portes vit dans
leurs primitives (`Observe ⊗ Concat` ≠ `Concat ⊗ Observe`, les 462 signatures
sont distinctes) et dans les noms de l'étape 4, pas dans la règle. Le module
garde la règle telle que le texte la donne et le dit ici, plutôt que d'inventer
une distinction.

Sur 462 opérateurs, 52 portent un nom venu du texte (26 portes, face et dos).
Les 410 autres n'ont que leur règle et leur signature : c'est la place laissée
pour la suite.
