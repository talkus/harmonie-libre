# Les 231 Portes — opérateurs binaires

Ce module donne une place dans le code à deux textes de mik : celui du 2 octobre 2026,
« Les 231 Portes comme Opérateurs Binaires Fondamentaux ». Il en suit les
étapes : les 22 lettres comme primitives (étape 1), la règle de composition
par catégories (étapes 2 et 3), les opérateurs nommés (étape 4), la matrice
22×22 (étape 5) et l'API `porte(x, y)` (étape 6). Celui du 4 octobre, qui
formalise la Roue (Galgal) comme graphe complet K₂₂, vit dans `roue.py`.

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

from portes_231 import tourner, orbites, Ordre
tourner(porte("א", "ב"), 1)              # ב→ג : la roue avance d'un cran
{d: len(ps) for d, ps in orbites().items()}   # 10 orbites de 22 portes, une de 11
```

## Ce qui vient d'où

| Élément | Source | Statut |
|---|---|---|
| 22 lettres ; 3 mères אמש, 7 doubles בגדכפרת, 12 simples הוזחטילנסעצק | Sefer Yetzirah 1:2, ch. 3 à 5 | `source_attestee` |
| 231 portes, face et dos (ענג en haut, נגע en bas) | Sefer Yetzirah 2:4 (recension du Gra) | `source_attestee` |
| Primitives (Unit, Stream, Container…), bits des doubles, règle 3×3, noms d'opérateurs | texte de mik, 2026-10-02 | `reconstruction_analytique` |
| Roue tournant en avant et en arrière (גלגל חוזר פנים ואחור) | Sefer Yetzirah 2:4 | `source_attestee` |
| Graphe K₂₂, matrice d'adjacence, rotation modulaire, numérotation par catégories, rôles système (mères = contrôle global, simples = routage) | texte de mik, 2026-10-04 | `reconstruction_analytique` |
| Rotation de la roue comme « VRF ou rotation de clés de chiffrement » | texte de mik, 2026-10-04 | `indetermine` ; non codé |
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

## La Roue (texte du 4 octobre)

Le second texte s'accorde avec le premier sur l'essentiel : 22 lettres, 231
portes non orientées, deux transitions dirigées par porte. Il ajoute le
graphe K₂₂, sa matrice d'adjacence et la rotation de la roue. `roue.py` les
reprend : `adjacence()`, `est_porte()`, `cercle()`, `tourner()`, `distance()`
et `orbites()`.

**Deux numérotations, une seule face.** Le second texte numérote les lettres
par catégorie (`LetterOpCode` : א=0, מ=1, ש=2, ב=3 … ת=9, ה=10 … ק=21). Cette
numérotation est disponible sur chaque lettre (`Lettre.opcode`) et comme
ordre de roue (`Ordre.CATEGORIES`). Elle ne change pas l'ensemble des 231
portes (c'est testé). En revanche, elle inverserait la face de 69 portes si
on la prenait pour définir « i < j ». La face reste donc alphabétique, comme
dans le premier texte, pour ne rien casser : la face de ב–מ reste ב→מ.

**L'ordre sur la roue compte.** Le Sefer Yetzirah ne dit pas dans quel ordre
les lettres sont fixées sur la roue. La rotation, elle, en dépend : א et מ
sont à distance 10 sur la roue alphabétique, et voisines sur la roue par
catégories. `tourner()` et `orbites()` prennent donc l'ordre en paramètre.
Par défaut, c'est l'ordre alphabétique.

Écrire le code a fait apparaître quatre choses.

1. **La matrice d'adjacence est pleine.** Elle vaut 1 partout sauf sur la
   diagonale (A = J − I) : `validate_gate(u, v)` revient à tester u ≠ v. Elle
   ne porte aucune information au-delà du nombre 22. Ce sont les opérateurs
   du premier texte qui distinguent une porte d'une autre.
2. **La rotation du texte perd le sens de la roue.** `rotate_wheel` ramène
   chaque paire à (min, max). Elle rend donc toujours le même ensemble de 231
   portes (une rotation est un automorphisme de K₂₂), et l'avant ne se
   distingue plus de l'arrière. Ici, `tourner()` garde l'orientation : X ⊗ Y
   devient X' ⊗ Y', et `tourner(op, k)` puis `tourner(op, -k)` rend `op`.
   Une conséquence se lit dans les tests : au passage de ת à א, une face
   devient un dos.
3. **Ce que la rotation garde, ce sont des orbites.** La distance entre les
   deux lettres d'une porte (de 1 à 11) ne change pas quand la roue tourne.
   Les 231 portes se rangent ainsi en 10 orbites de 22 portes, plus une orbite
   de 11 pour les lettres diamétralement opposées : 10 × 22 + 11 = 231.
4. **La rotation n'est pas une VRF.** Elle est publique et prévisible. Une
   fonction aléatoire vérifiable (VRF) demande une clé secrète et produit une
   sortie imprévisible sans cette clé. La rotation peut ordonner l'activation
   des paires de nœuds sans ordonnanceur central, mais elle n'apporte aucune
   garantie cryptographique. Ce rapprochement reste `indetermine` et n'est
   pas codé.

Les deux textes donnent aux lettres des rôles différents. Le premier dit
mères = types (Unit, Stream, Transform). Le second dit mères = contrôle
global, simples = routage. Ce sont deux reconstructions. Le code garde les
primitives du premier texte, et ce tableau garde la trace du second.
