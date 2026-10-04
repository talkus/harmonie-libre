"""Le cube des chapitres 4 et 5 : les 27 cases de {−1, 0, 1}³.

Ce que le Sefer Yetzirah pose lui-même :

* les 3 mères sont trois (air, eau, feu) ;
* les 7 doubles sont les six côtés, haut, bas, est, ouest, nord, sud, et le
  palais saint au milieu (ch. 4) ;
* les 12 simples sont les douze bordures diagonales (ch. 5), c'est-à-dire les
  arêtes d'un cube dont les six côtés sont les faces.

Placé dans {−1, 0, 1}³, ce cube se lit sans reste : le centre (1 case) et les
centres des faces (6) donnent les 7 doubles, les milieux des arêtes (12) les
12 simples, les axes les 3 mères. Il reste les 8 coins, qui sont exactement les
8 états de Z₂³ de ``axes.py`` (et les 8 trigrammes du Yi Jing).
1 + 6 + 12 + 8 = 27 = 3³.

Conventions (reconstruction analytique) :

* axe des mères : א = haut/bas, מ = est/ouest, ש = nord/sud ;
* doubles dans l'ordre בגדכפרת : haut, bas, est, ouest, nord, sud, palais ;
* simples dans l'ordre הוזחטילנסעצק : les douze bordures dans l'ordre de la
  liste de 5:2 (est-haut, est-nord, est-bas, sud-haut, sud-est, sud-bas,
  ouest-haut, ouest-sud, ouest-bas, nord-haut, nord-ouest, nord-bas).
  L'ordre de cette liste suit la recension du Gra ; il reste à vérifier sur
  le texte hébreu, et d'autres recensions attribuent autrement.
"""

from __future__ import annotations

from itertools import product

from .lettres import DOUBLES, MERES, SIMPLES, Categorie, Lettre, lettre

Point = tuple[int, int, int]

# Les six côtés : une direction par signe de chaque axe (א, מ, ש).
DIRECTIONS: dict[str, Point] = {
    "haut": (1, 0, 0), "bas": (-1, 0, 0),
    "est": (0, 1, 0), "ouest": (0, -1, 0),
    "nord": (0, 0, 1), "sud": (0, 0, -1),
}
PALAIS: Point = (0, 0, 0)

_COTES_DES_DOUBLES = ("haut", "bas", "est", "ouest", "nord", "sud", "palais")
_BORDURES = (
    ("est", "haut"), ("est", "nord"), ("est", "bas"),
    ("sud", "haut"), ("sud", "est"), ("sud", "bas"),
    ("ouest", "haut"), ("ouest", "sud"), ("ouest", "bas"),
    ("nord", "haut"), ("nord", "ouest"), ("nord", "bas"),
)


def _somme(a: Point, b: Point) -> Point:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


PLACES: dict[Lettre, Point] = {}
NOMS_DE_PLACE: dict[Lettre, str] = {}
for _d, _cote in zip(DOUBLES, _COTES_DES_DOUBLES):
    PLACES[_d] = PALAIS if _cote == "palais" else DIRECTIONS[_cote]
    NOMS_DE_PLACE[_d] = _cote
for _s, (_c1, _c2) in zip(SIMPLES, _BORDURES):
    PLACES[_s] = _somme(DIRECTIONS[_c1], DIRECTIONS[_c2])
    NOMS_DE_PLACE[_s] = f"{_c1}-{_c2}"

# Une mère n'est pas une case : c'est un axe (indice 0, 1, 2).
AXE_DES_MERES: dict[Lettre, int] = {m: i for i, m in enumerate(MERES)}
NOMS_D_AXE: dict[Lettre, str] = dict(zip(MERES, ("haut-bas", "est-ouest", "nord-sud")))


def place(l: str | Lettre) -> Point:
    """La case d'une double ou d'une simple dans {−1, 0, 1}³."""
    l = lettre(l)
    if l.categorie is Categorie.MERE:
        raise ValueError(f"{l.nom} est une mère : c'est un axe, pas une case")
    return PLACES[l]


def genre(p: Point) -> str:
    """Centre, face, arête ou coin, selon le nombre de coordonnées non nulles."""
    return ("centre", "face", "arête", "coin")[sum(1 for v in p if v)]


CASES: tuple[Point, ...] = tuple(product((-1, 0, 1), repeat=3))
COINS: tuple[Point, ...] = tuple(p for p in CASES if genre(p) == "coin")
