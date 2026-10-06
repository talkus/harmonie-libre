"""Étapes 2, 3, 5 et 6 : les 231 portes et leurs 462 opérateurs.

Convention de lecture (tenue partout dans ce module) :

* une **porte** est une paire non ordonnée de deux lettres distinctes :
  C(22, 2) = 231 portes ;
* sa **face** est l'opérateur X ⊗ Y où X précède Y dans l'alphabet
  (case (i, j), i < j, de la matrice triangulaire de l'étape 5) ;
* son **dos** est l'opérateur Y ⊗ X (la transposée) ;
* X ⊗ Y ≠ Y ⊗ X : chaque porte porte deux opérateurs distincts, soit 462.

Le Sefer Yetzirah atteste les 231 portes et la paire face/dos (ענג en haut,
נגע en bas, 2:4). La règle de composition par catégories et les noms
d'opérateurs sont la reconstruction analytique de mik.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Iterator

from .exemples import EXEMPLES, Nommage
from .lettres import ALPHABET, Categorie, Lettre, lettre
from .statut import RECONSTRUCTION_ANALYTIQUE, SOURCE_ATTESTEE

_M, _D, _S = Categorie.MERE, Categorie.DOUBLE, Categorie.SIMPLE

class Lecture(str, Enum):
    FACE = "face"
    DOS = "dos"

@dataclass(frozen=True)
class Regle:
    """Une case du tableau 3×3 de l'étape 3, avec le gabarit de l'étape 6."""

    nom: str  # « État conditionnel »
    formule: str  # « Élément + Bit »
    gabarit: str  # « {a} si {b} »

    def appliquer(self, a: object, b: object) -> str:
        return f"{self.nom}: {self.gabarit.format(a=a, b=b)}"

# Clé : (catégorie de X, catégorie de Y). X = contexte, Y = mode.
REGLES: dict[tuple[Categorie, Categorie], Regle] = {
    (_M, _M): Regle("État fondamental", "Élément + Élément", "{a} ⊗ {b}"),
    (_M, _D): Regle("État conditionnel", "Élément + Bit", "{a} si {b}"),
    (_M, _S): Regle("Direction élémentaire", "Élément + Axe", "{a} vers {b}"),
    (_D, _M): Regle("Condition sur état", "Bit + Élément", "{a} sur {b}"),
    (_D, _D): Regle("Logique binaire", "Bit + Bit", "{a} ET {b}"),
    (_D, _S): Regle("Opération conditionnelle", "Bit + Axe", "si {a} alors {b}"),
    (_S, _M): Regle("Transformation élémentaire", "Axe + Élément", "{a} de {b}"),
    (_S, _D): Regle("Transformation conditionnelle", "Axe + Bit", "{a} si {b}"),
    (_S, _S): Regle("Composition d'axes", "Axe + Axe", "{a} puis {b}"),
}

@dataclass(frozen=True)
class Operateur:
    """X ⊗ Y : un opérateur binaire, appelable comme dans l'étape 6."""

    x: Lettre
    y: Lettre

    def __post_init__(self) -> None:
        if self.x == self.y:
            raise ValueError("une porte relie deux lettres distinctes")

    @property
    def lecture(self) -> Lecture:
        return Lecture.FACE if self.x.rang < self.y.rang else Lecture.DOS

    @property
    def regle(self) -> Regle:
        return REGLES[(self.x.categorie, self.y.categorie)]

    @property
    def nommage(self) -> Nommage | None:
        """Le nom donné dans l'étape 4, s'il existe (66 opérateurs sur 462 non)."""
        return EXEMPLES.get((self.x.glyphe, self.y.glyphe))

    @property
    def porte(self) -> "Porte":
        return Porte.de(self.x, self.y)

    @property
    def inverse(self) -> "Operateur":
        return Operateur(self.y, self.x)

    @property
    def signature(self) -> str:
        return f"{self.x.primitive} ⊗ {self.y.primitive}"

    # Statuts : la porte est attestée, sa lecture computationnelle ne l'est pas.
    statut_porte = SOURCE_ATTESTEE
    statut_lecture = RECONSTRUCTION_ANALYTIQUE

    def __call__(self, a: object, b: object) -> str:
        return self.regle.appliquer(a, b)

    def __str__(self) -> str:
        texte = f"{self.x}→{self.y} ({self.lecture.value}) : {self.signature} — {self.regle.nom}"
        if self.nommage:
            texte += f" → {self.nommage.resultat} [{self.nommage.fonction}]"
        return texte

@dataclass(frozen=True)
class Porte:
    """Une porte : deux lettres, rangées dans l'ordre alphabétique."""

    a: Lettre
    b: Lettre

    def __post_init__(self) -> None:
        if not self.a.rang < self.b.rang:
            raise ValueError("une Porte se construit avec Porte.de(x, y)")

    @classmethod
    def de(cls, x: str | Lettre, y: str | Lettre) -> "Porte":
        lx, ly = lettre(x), lettre(y)
        if lx == ly:
            raise ValueError("une porte relie deux lettres distinctes")
        return cls(*sorted((lx, ly), key=lambda l: l.rang))

    @property
    def face(self) -> Operateur:
        return Operateur(self.a, self.b)

    @property
    def dos(self) -> Operateur:
        return Operateur(self.b, self.a)

    @property
    def categories(self) -> frozenset[Categorie]:
        return frozenset((self.a.categorie, self.b.categorie))

    def __iter__(self) -> Iterator[Operateur]:
        yield self.face
        yield self.dos

    def __str__(self) -> str:
        return f"{self.a}–{self.b}"

PORTES: tuple[Porte, ...] = tuple(Porte(a, b) for a, b in combinations(ALPHABET, 2))
OPERATEURS: tuple[Operateur, ...] = tuple(op for p in PORTES for op in p)

def porte(x: str | Lettre, y: str | Lettre) -> Operateur:
    """L'opérateur X ⊗ Y, dans l'ordre donné (API de l'étape 6).

    >>> porte("א", "ב")("esprit", "contenant")
    'État conditionnel: esprit si contenant'
    """
    return Operateur(lettre(x), lettre(y))

def matrice() -> list[list[Operateur | None]]:
    """Étape 5 : la matrice 22×22. Au-dessus de la diagonale, les faces ;
    en dessous, les dos (la transposée) ; sur la diagonale, rien."""
    return [
        [None if i == j else Operateur(x, y) for j, y in enumerate(ALPHABET)]
        for i, x in enumerate(ALPHABET)
    ]

def par_categories(c1: Categorie, c2: Categorie) -> tuple[Porte, ...]:
    """Les portes qui relient une lettre de c1 à une lettre de c2."""
    voulu = frozenset((c1, c2))
    return tuple(p for p in PORTES if p.categories == voulu)

