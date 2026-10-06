"""Les 3 Mères comme axes, les 7 Doubles comme opérateurs bistables sur ces axes.

Demande de mik (2026-10-04). Le Sefer Yetzirah atteste 3 mères (air, eau,
feu) et 7 doubles, chacune dure ou douce. Il ne dit pas comment une double agit
sur une mère : la correspondance ci-dessous est une reconstruction analytique.

Pourquoi elle tient : trois axes binaires ont exactement 2³ − 1 = 7 parties non
vides. Chaque double reçoit une partie distincte des axes. En état dagesh (1),
elle bascule ces axes ; en état raphe (0), elle les laisse. Sur Z₂, appliquer
deux fois la même double ramène l'état de départ : c'est ce qui fait d'elle un
opérateur bistable. Les 7 doubles et l'identité forment alors le groupe Z₂³.

Convention d'attribution : les axes (א, מ, ש) valent les bits (1, 2, 4), et les
doubles, dans l'ordre בגדכפרת, reçoivent les parties 1 à 7 :
ב={א}, ג={מ}, ד={א,מ}, כ={ש}, פ={א,ש}, ר={מ,ש}, ת={א,מ,ש}.

Le module accepte aussi Z₃³ (``modulo=3``), proposé par mik ; la double y
avance ses axes d'un cran sans revenir au bout de deux applications.
"""

from __future__ import annotations

from dataclasses import dataclass

from .lettres import DAGESH, DOUBLES, MERES, RAPHE, Categorie, Lettre, lettre

AXES: tuple[Lettre, ...] = MERES  # א (air), מ (eau), ש (feu)


def axes_de(double: str | Lettre) -> frozenset[Lettre]:
    """Les mères sur lesquelles agit une double."""
    d = lettre(double)
    if d.categorie is not Categorie.DOUBLE:
        raise ValueError(f"{d.nom} n'est pas une double")
    masque = DOUBLES.index(d) + 1
    return frozenset(m for i, m in enumerate(AXES) if masque >> i & 1)


@dataclass(frozen=True)
class Etat:
    """Un point de l'espace des mères : une coordonnée par axe."""

    air: int = 0
    eau: int = 0
    feu: int = 0
    modulo: int = 2

    def __post_init__(self) -> None:
        if self.modulo < 2:
            raise ValueError("le modulo vaut au moins 2")
        for v in self.coordonnees:
            if not 0 <= v < self.modulo:
                raise ValueError(f"coordonnée hors de Z{self.modulo}")

    @property
    def coordonnees(self) -> tuple[int, int, int]:
        return (self.air, self.eau, self.feu)

    def appliquer(self, double: str | Lettre, etat_double: int = DAGESH) -> "Etat":
        """Fait agir une double, dans son état raphe (0) ou dagesh (1)."""
        if etat_double not in (RAPHE, DAGESH):
            raise ValueError("une double vaut 0 (raphe) ou 1 (dagesh)")
        cibles = axes_de(double)
        if etat_double == RAPHE:
            return self
        nouv = [
            (v + 1) % self.modulo if m in cibles else v
            for v, m in zip(self.coordonnees, AXES)
        ]
        return Etat(*nouv, modulo=self.modulo)

    def __str__(self) -> str:
        return "(" + ", ".join(f"{m}={v}" for m, v in zip(AXES, self.coordonnees)) + ")"


def espace(modulo: int = 2) -> tuple[Etat, ...]:
    """Tous les états : 8 sur Z₂³, 27 sur Z₃³."""
    return tuple(Etat(a, e, f, modulo) for a in range(modulo) for e in range(modulo) for f in range(modulo))
