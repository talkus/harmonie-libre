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
python -m portes_231 --table    # la table des 231 portes
```

Fichiers du dossier :

- `lettres.py`, `portes.py`, `exemples.py` : les lettres, les portes et les opérateurs nommés (texte du 2 octobre).
- `roue.py` : la Roue, avec rotation et réflexion (texte du 4 octobre).
- `operations.py` : les cinq opérations de 2:2, de Haqaq à Tsaraf.
- `axes.py` : les mères comme axes, les doubles comme opérateurs bistables.
- `cube.py` : le cube des chapitres 4 et 5 (doubles = six côtés et palais, simples = douze bordures).
- `empreintes.py` : les empreintes SHA-256 de la table, dans les deux ordres.
- [`TABLE_231.md`](TABLE_231.md) : la table des 231 portes, générée par le code.
- [`TABLE_231_ETENDUE.csv`](TABLE_231_ETENDUE.csv) : la table étendue (catégories, poids combinés, distances, cube).
- [`EMPREINTES.md`](EMPREINTES.md) : les empreintes, générées par le code.
- [`COMPARAISON.md`](COMPARAISON.md) : la comparaison avec le Yi Jing, l'arbre des sefirot, Lulle et le code génétique.

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
| Les cinq opérations : graver, tailler, peser, permuter, combiner ; n pierres bâtissent n! maisons | Sefer Yetzirah 2:2 ; fin du ch. 4 | `source_attestee` |
| Contenu de chaque opération, poids 3/2/1, mères comme axes, doubles comme opérateurs sur Z₂³, réflexion de la roue | relecture de mik, 2026-10-04, et conventions de ce module | `reconstruction_analytique` |
| 7 doubles = six côtés (haut, bas, est, ouest, nord, sud) et le palais saint au milieu ; 12 simples = douze bordures diagonales, chacune nommée par deux directions | Sefer Yetzirah ch. 4 et 5 | `source_attestee` |
| Ces douze bordures sont les douze arêtes du cube dont les six côtés sont les faces | conséquence géométrique de la ligne précédente | `derivation_consolidee` |
| Cube {−1, 0, 1}³, axe de chaque mère, ordre d'attribution des côtés et des bordures, règle de pas de la roue, poids combinés | relecture du 2026-10-04 et conventions de ce module | `reconstruction_analytique` |
| Valeurs de guématria | tradition juive, hors Sefer Yetzirah | `derivation_consolidee` |
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

## Les cinq opérations, les axes et la table (relecture du 4 octobre)

**Les cinq opérations** (Sefer Yetzirah 2:2) sont des fonctions distinctes
dans `operations.py` :

- `haqaq()` grave l'alphabet ordonné.
- `hatsav()` taille un ensemble de lettres en mères, doubles et simples.
- `shaqal()` pèse une lettre. Il y a deux balances : par catégorie (mère 3,
  double 2, simple 1, comme mik le propose), ou en guématria. La guématria est
  traditionnelle, mais le Sefer Yetzirah ne la donne pas.
- `hamir()` donne toutes les permutations d'un groupe de lettres.
  `maisons(n) = n!` reprend le décompte que le texte donne lui-même à la fin du
  chapitre 4 (« deux pierres bâtissent deux maisons… sept en bâtissent 5040 »).
- `tsaraf()` combine deux lettres en une porte. Sans argument, il rend les 231
  portes.

**Les mères comme axes, les doubles comme opérateurs bistables** (`axes.py`).
Trois axes binaires ont exactement 2³ − 1 = 7 parties non vides. Chaque double
reçoit une partie distincte : ב agit sur א, ג sur מ, ד sur א et מ, et ainsi de
suite jusqu'à ת qui agit sur les trois. En dagesh, la double bascule ses axes.
En raphe, elle les laisse. Sur Z₂, l'appliquer deux fois revient au départ :
c'est ce qui la rend bistable. Les 7 doubles et l'identité forment le groupe
Z₂³. L'espace Z₃³ que mik propose est disponible (`Etat(modulo=3)`). Il y faut
trois applications pour revenir au départ, donc la double n'y est plus
bistable. Le Sefer Yetzirah ne dit pas quelle double agit sur quelle mère :
l'attribution suit l'ordre des doubles et le comptage binaire, et c'est une
convention.

**La réflexion** (`refleter()`) complète la rotation. Les deux ensemble
engendrent le groupe diédral D₂₂ que mik propose.

**Deux points de la relecture ne sont pas repris tels quels.** Les fonctions
`rotate()` et `reflect()` de la relecture ramènent encore chaque paire à (min, max). Elles
rendent donc toujours les mêmes 231 portes et effacent l'avant et l'arrière.
`tourner()` et `refleter()` gardent l'ordre des lettres de chaque opérateur.
Quant à la polarité face/dos propre à chaque lettre, attribuée à
Abulafia, elle n'est pas codée sans source à citer : les portes ont déjà une
face et un dos.

**La table des 231 portes** est dans [`TABLE_231.md`](TABLE_231.md). Elle donne
pour chaque porte les noms des deux lettres, leurs catégories, et les lectures
face et dos. Un test vérifie que le fichier correspond toujours au code.

## Le cube, les empreintes et la règle de la roue (seconde relecture du 4 octobre)

**Le cube vient du texte, à une déduction près.** La relecture lit les 12
simples comme les 12 arêtes d'un cube. Le Sefer Yetzirah ne prononce pas le
mot « cube ». Il donne aux 7 doubles les six côtés et le palais saint au
milieu (ch. 4), et aux 12 simples les douze bordures diagonales, chacune
nommée par deux directions voisines (est-haut, est-nord…) (ch. 5). Douze paires
de côtés voisins, ce sont les douze arêtes du cube dont les six côtés sont les
faces : c'est une déduction directe (`derivation_consolidee`), pas une
correspondance numérique. En revanche, 7 = 2³ − 1 dans `axes.py` reste une
reconstruction analytique, que le texte ne demande pas. Dans {−1, 0, 1}³, ce cube
se lit sans reste (`cube.py`). Le centre et les 6 faces donnent les 7 doubles,
les 12 milieux d'arêtes les 12 simples, les 3 axes les 3 mères. Il reste les 8
coins : ce sont les 8 états de Z₂³ de `axes.py`, et les 8 trigrammes du Yi
Jing. 1 + 6 + 12 + 8 = 27 = 3³.

Ce cube ne recouvre pas exactement la lecture algébrique de `axes.py`. Le
texte place une double à une case : un côté, ou le centre. La lecture
algébrique fait de chaque double un mouvement qui bascule des axes. Les deux
sont gardées. La première suit le texte, la seconde explique la bistabilité.
Les conventions du cube (quelle mère porte quel axe, dans quel ordre les
doubles et les simples prennent leurs places) restent des conventions. L'ordre
des douze bordures suit la recension du Gra et reste à vérifier sur le texte
hébreu.

**Empreintes** (`empreintes.py`, [`EMPREINTES.md`](EMPREINTES.md)). La table
a une empreinte SHA-256 dans l'ordre alphabétique et une dans l'ordre 3-7-12.
Les deux diffèrent, puisque leurs numéros diffèrent. Relues par leurs seules
lettres, elles donnent toutes deux l'empreinte des 231 portes sans numéro.
C'est ce qui scelle qu'elles décrivent les mêmes portes. Une troisième
empreinte scelle la bijection entre les deux numérotations. Les valeurs sont
fixées dans un test : changer la table oblige à changer le fichier.
L'empreinte garantit qu'un contenu n'a pas changé d'une version à l'autre,
mais elle ne dit rien de plus sur ce contenu. Dans ce module, l'ordre n'est
pas cosmétique : il fixe la face, la rotation et les orbites. Un outil qui
lit les portes dans un ordre donné doit donc citer l'empreinte de cet ordre.

**Règle de transition** (`etat_suivant`, `trajectoire`, `periode` dans
`roue.py`). S(t+1) = ρ₁(S(t)) : chaque porte active avance d'un cran. C'est
une extension, puisque le texte dit que la roue tourne sans donner de pas.
Si les 231 portes sont actives, rien ne bouge : l'ensemble est un point fixe.
La dynamique n'apparaît que sur un sous-ensemble. Une porte revient en 22 pas,
sauf entre deux lettres diamétralement opposées, où elle revient en 11. Un
opérateur orienté, lui, revient toujours en 22 pas : l'orientation compte
encore ici.

**Table étendue** ([`TABLE_231_ETENDUE.csv`](TABLE_231_ETENDUE.csv)). On y
trouve, pour chaque porte :
- les lettres, leurs noms et leurs catégories ;
- les poids 3/2/1, leur somme et leur produit ;
- la somme de guématria ;
- les distances sur les deux roues ;
- la case de chaque lettre sur le cube.

Le statut de chaque colonne est dans `table_etendue.py` (`STATUTS`). Le
produit des poids sépare exactement les six familles de portes : 9, 6, 3, 4, 2
et 1 donnent 3, 21, 36, 21, 84 et 66 portes. La somme, elle, confond
double-double et mère-simple, qui valent toutes deux 4.

## Trois niveaux d'ordre

Le mot « ordre » recouvre trois choses distinctes dans ce module :

1. **L'ordre des lettres** (alphabétique ou 3-7-12). Il est conventionnel pour
   K₂₂ : toute permutation des sommets donne le même graphe. Il ne l'est plus
   dès qu'on numérote. Les deux ordres numérotent les 231 portes différemment,
   et la correspondance entre les deux numérotations est une permutation des
   231 portes, pas l'identité. `bijection()` la scelle.
2. **L'ordre des deux lettres dans une porte.** Il est sans effet pour les 231
   portes non orientées, et il compte pour les 462 opérateurs : c'est la face
   et le dos. La face est fixée par l'ordre alphabétique.
3. **L'ordre de lecture des 231 portes.** Il est sans effet pour l'ensemble,
   et il compte pour un outil qui les parcourt en séquence. L'empreinte de
   sérialisation de chaque ordre le fige.

La période d'une porte sous la rotation ne dépend que de l'écart entre ses
deux lettres sur la roue. Les 11 portes antipodales (écart 11) reviennent en
11 pas, les 220 autres en 22. Un test vérifie la période minimale de chaque
porte dans les deux ordres.
