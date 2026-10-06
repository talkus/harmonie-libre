"""Table étendue des 231 portes (CSV) : catégories, poids combinés, distances, cube.

Statut de chaque colonne :

* source_attestee : porte, lettres, noms, catégories ;
* derivation_consolidee : guematria_somme (valeurs traditionnelles, hors
  Sefer Yetzirah) ;
* reconstruction_analytique : poids (mère 3, double 2, simple 1), leurs somme
  et produit, distances sur la roue, cases du cube (conventions de ``cube.py``).
"""

from __future__ import annotations

import csv
import io

from .cube import NOMS_D_AXE, NOMS_DE_PLACE
from .lettres import Categorie
from .operations import Balance, shaqal
from .portes import PORTES
from .roue import Ordre, distance

COLONNES = (
    "n", "porte",
    "lettre_1", "nom_1", "categorie_1",
    "lettre_2", "nom_2", "categorie_2",
    "categories",
    "poids_1", "poids_2", "poids_somme", "poids_produit",
    "guematria_somme",
    "distance_alphabetique", "distance_categories",
    "cube_1", "cube_2",
)

STATUTS = {
    **dict.fromkeys(("n", "porte", "lettre_1", "nom_1", "categorie_1", "lettre_2", "nom_2",
                     "categorie_2", "categories"), "source_attestee"),
    "guematria_somme": "derivation_consolidee",
    **dict.fromkeys(("poids_1", "poids_2", "poids_somme", "poids_produit",
                     "distance_alphabetique", "distance_categories", "cube_1", "cube_2"),
                    "reconstruction_analytique"),
}


def _cube(l) -> str:
    return f"axe {NOMS_D_AXE[l]}" if l.categorie is Categorie.MERE else NOMS_DE_PLACE[l]


def rangees() -> list[dict[str, object]]:
    rangs = []
    for n, p in enumerate(PORTES, start=1):
        a, b = p.a, p.b
        pa, pb = shaqal(a), shaqal(b)
        rangs.append({
            "n": n, "porte": str(p),
            "lettre_1": a.glyphe, "nom_1": a.nom, "categorie_1": a.categorie.value,
            "lettre_2": b.glyphe, "nom_2": b.nom, "categorie_2": b.categorie.value,
            "categories": f"{a.categorie.value}-{b.categorie.value}",
            "poids_1": pa, "poids_2": pb, "poids_somme": pa + pb, "poids_produit": pa * pb,
            "guematria_somme": shaqal(a, Balance.GUEMATRIA) + shaqal(b, Balance.GUEMATRIA),
            "distance_alphabetique": distance(p, Ordre.ALPHABETIQUE),
            "distance_categories": distance(p, Ordre.CATEGORIES),
            "cube_1": _cube(a), "cube_2": _cube(b),
        })
    return rangs


def csv_texte() -> str:
    sortie = io.StringIO()
    ecrivain = csv.DictWriter(sortie, fieldnames=COLONNES, lineterminator="\n")
    ecrivain.writeheader()
    ecrivain.writerows(rangees())
    return sortie.getvalue()
