"""D'autres systèmes combinatoires, comparés aux 231 portes (voir COMPARAISON.md).

Chaque système est décrit par ses éléments et sa manière de les combiner ; le
nombre de combinaisons est calculé, pas recopié.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import comb, perm


@dataclass(frozen=True)
class Systeme:
    nom: str
    elements: int
    taille: int  # nombre d'éléments par combinaison
    ordre_compte: bool
    repetition: bool
    source: str

    @property
    def combinaisons(self) -> int:
        n, k = self.elements, self.taille
        if self.ordre_compte:
            return n**k if self.repetition else perm(n, k)
        return comb(n + k - 1, k) if self.repetition else comb(n, k)


SYSTEMES: tuple[Systeme, ...] = (
    Systeme("231 portes (face seule)", 22, 2, False, False, "Sefer Yetzirah 2:4"),
    Systeme("462 opérateurs (face et dos)", 22, 2, True, False, "Sefer Yetzirah 2:4, lecture de mik"),
    Systeme("Trigrammes du Yi Jing", 2, 3, True, True, "Yi Jing (Livre des mutations)"),
    Systeme("Hexagrammes du Yi Jing", 2, 6, True, True, "Yi Jing (Livre des mutations)"),
    Systeme("Hexagrammes comme paires de trigrammes", 8, 2, True, True, "Yi Jing (Livre des mutations)"),
    Systeme("Paires de sefirot possibles", 10, 2, False, False, "calcul : K₁₀"),
    Systeme("Troisième figure de Lulle", 9, 2, False, False, "Raymond Lulle, Ars brevis"),
    Systeme("Codons du code génétique", 4, 3, True, True, "biologie moléculaire"),
)

# L'arbre des sefirot n'est pas une combinaison complète : il retient 22 des
# 45 paires possibles, et ce sont les lettres qui en sont les sentiers.
SENTIERS_DE_L_ARBRE = 22
VOIES_DE_SAGESSE = 10 + 22  # Sefer Yetzirah 1:1 : 32 voies = 10 sefirot + 22 lettres
