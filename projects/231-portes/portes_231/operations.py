"""Les cinq opérations de Sefer Yetzirah 2:2 :
« Il les a gravées, taillées, pesées, permutées et combinées »
(חקקן חצבן שקלן והמירן וצרפן).

Le verset est une source attestée. Le contenu donné ici à chaque verbe est une
reconstruction analytique, sauf le décompte des permutations, que le Sefer
Yetzirah donne lui-même à la fin du chapitre 4 (« deux pierres bâtissent deux
maisons, trois en bâtissent six… sept en bâtissent 5040 »).
"""

from __future__ import annotations

from enum import Enum
from itertools import permutations
from math import factorial
from typing import Iterable, Iterator

from .lettres import ALPHABET, Categorie, Lettre, lettre
from .portes import PORTES, Porte


def haqaq() -> tuple[Lettre, ...]:
    """Graver (חקק) : fixer la forme et l'ordre des 22 lettres."""
    return ALPHABET


def hatsav(lettres: Iterable[str | Lettre] = ALPHABET) -> dict[Categorie, tuple[Lettre, ...]]:
    """Tailler (חצב) : séparer les lettres en mères, doubles et simples."""
    taille: dict[Categorie, list[Lettre]] = {c: [] for c in Categorie}
    for l in map(lettre, lettres):
        taille[l.categorie].append(l)
    return {c: tuple(ls) for c, ls in taille.items()}


class Balance(str, Enum):
    """Les deux échelles de pesée proposées.

    CATEGORIE : mère 3, double 2, simple 1 (proposée par mik, 2026-10-04).
    GUEMATRIA : valeurs numériques traditionnelles (1 à 400). Elles sont
    attestées dans la tradition juive, mais le Sefer Yetzirah ne les donne pas.
    """

    CATEGORIE = "catégorie"
    GUEMATRIA = "guématria"


_POIDS_CATEGORIE = {Categorie.MERE: 3, Categorie.DOUBLE: 2, Categorie.SIMPLE: 1}
_GUEMATRIA = dict(zip("אבגדהוזחטיכלמנסעפצקרשת",
                      [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 20, 30, 40, 50, 60, 70, 80, 90, 100, 200, 300, 400]))


def shaqal(l: str | Lettre, balance: Balance = Balance.CATEGORIE) -> int:
    """Peser (שקל) : donner une valeur à une lettre."""
    l = lettre(l)
    if balance is Balance.CATEGORIE:
        return _POIDS_CATEGORIE[l.categorie]
    return _GUEMATRIA[l.glyphe]


def hamir(lettres: Iterable[str | Lettre]) -> Iterator[tuple[Lettre, ...]]:
    """Permuter (המיר) : toutes les « maisons » bâties avec ces « pierres »."""
    pierres = tuple(map(lettre, lettres))
    if len(set(pierres)) != len(pierres):
        raise ValueError("les pierres d'une maison sont des lettres distinctes")
    return permutations(pierres)


def maisons(pierres: int) -> int:
    """Nombre de maisons bâties avec n pierres : n! (Sefer Yetzirah, fin du ch. 4)."""
    if pierres < 0:
        raise ValueError("un nombre de pierres est positif")
    return factorial(pierres)


def tsaraf(x: str | Lettre | None = None, y: str | Lettre | None = None) -> Porte | tuple[Porte, ...]:
    """Combiner (צרף) : deux lettres forment une porte ; sans argument, les 231."""
    if x is None and y is None:
        return PORTES
    if x is None or y is None:
        raise TypeError("tsaraf prend deux lettres, ou aucune")
    return Porte.de(x, y)
