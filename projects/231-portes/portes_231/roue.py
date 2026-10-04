"""La Roue (Galgal) : le graphe complet K₂₂ et sa rotation.

Suit le texte de mik du 2026-10-04 : « Vingt-deux lettres fondamentales,
fixées sur la Roue à 231 Portes, et la Roue tourne en avant et en arrière »
(Sefer Yetzirah 2:4).

* Les 22 lettres sont les sommets, les 231 portes les arêtes de K₂₂.
* La matrice d'adjacence vaut 1 hors de la diagonale, 0 sur la diagonale.
* Tourner la roue de k crans déplace chaque lettre de k places sur le cercle.

Le Sefer Yetzirah ne dit pas dans quel ordre les lettres sont posées sur la
roue. Deux ordres sont offerts : alphabétique (celui de la table des 231
portes dans la recension du Gra, et celui de la face dans ce module) et par
catégories (celui de ``LetterOpCode`` dans le texte du 2026-10-04).
Statut : reconstruction analytique.
"""

from __future__ import annotations

from enum import Enum
from typing import overload

from .lettres import ALPHABET, ORDRE_CATEGORIES, Lettre, lettre
from .portes import PORTES, Operateur, Porte

TAILLE = 22


class Ordre(str, Enum):
    ALPHABETIQUE = "alphabétique"
    CATEGORIES = "catégories"


def cercle(ordre: Ordre = Ordre.ALPHABETIQUE) -> tuple[Lettre, ...]:
    """Les 22 lettres dans l'ordre où elles sont posées sur la roue."""
    return ALPHABET if ordre is Ordre.ALPHABETIQUE else ORDRE_CATEGORIES


def position(l: str | Lettre, ordre: Ordre = Ordre.ALPHABETIQUE) -> int:
    l = lettre(l)
    return l.rang if ordre is Ordre.ALPHABETIQUE else l.opcode


def adjacence(ordre: Ordre = Ordre.ALPHABETIQUE) -> list[list[int]]:
    """Matrice d'adjacence de K₂₂ : A[i][j] = 1 si i ≠ j, sinon 0."""
    return [[int(i != j) for j in range(TAILLE)] for i in range(TAILLE)]


def est_porte(x: str | Lettre, y: str | Lettre) -> bool:
    """Deux lettres forment une porte si et seulement si elles sont distinctes."""
    return lettre(x) != lettre(y)


@overload
def tourner(objet: Lettre, crans: int, ordre: Ordre = ...) -> Lettre: ...
@overload
def tourner(objet: Operateur, crans: int, ordre: Ordre = ...) -> Operateur: ...
@overload
def tourner(objet: Porte, crans: int, ordre: Ordre = ...) -> Porte: ...
def tourner(objet, crans, ordre=Ordre.ALPHABETIQUE):
    """Tourne la roue de ``crans`` (positif : en avant, négatif : en arrière).

    Un opérateur garde son sens : X ⊗ Y devient X' ⊗ Y'. Une porte reste une
    paire non ordonnée.
    """
    if isinstance(objet, Lettre):
        c = cercle(ordre)
        return c[(position(objet, ordre) + crans) % TAILLE]
    if isinstance(objet, Operateur):
        return Operateur(tourner(objet.x, crans, ordre), tourner(objet.y, crans, ordre))
    if isinstance(objet, Porte):
        return Porte.de(tourner(objet.a, crans, ordre), tourner(objet.b, crans, ordre))
    raise TypeError(f"on tourne une lettre, un opérateur ou une porte, pas {type(objet).__name__}")


def distance(p: Porte, ordre: Ordre = Ordre.ALPHABETIQUE) -> int:
    """Écart entre les deux lettres d'une porte sur le cercle : de 1 à 11."""
    d = abs(position(p.a, ordre) - position(p.b, ordre))
    return min(d, TAILLE - d)


def orbites(ordre: Ordre = Ordre.ALPHABETIQUE) -> dict[int, tuple[Porte, ...]]:
    """Les portes regroupées par distance. La rotation garde la distance :
    chaque groupe est une orbite de la roue (10 orbites de 22 portes, et une de
    11 pour les lettres diamétralement opposées : 10 × 22 + 11 = 231)."""
    groupes: dict[int, list[Porte]] = {d: [] for d in range(1, TAILLE // 2 + 1)}
    for p in PORTES:
        groupes[distance(p, ordre)].append(p)
    return {d: tuple(ps) for d, ps in groupes.items()}
