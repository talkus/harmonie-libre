"""Empreintes SHA-256 de la table canonique des 231 portes.

Demande du 2026-10-04 : sceller la table dans l'ordre alphabétique et dans
l'ordre par catégories (3-7-12), et sceller la bijection entre les deux.

Trois empreintes :

* ``table(ordre)`` : la table numérotée dans un ordre donné. Elle change avec
  l'ordre, puisque les numéros changent.
* ``portes()`` : les 231 portes écrites par leurs lettres, sans numéro. Elle
  ne dépend d'aucune numérotation. Si les deux tables, relues par leurs
  lettres, donnent cette même empreinte, elles décrivent les mêmes portes.
* ``bijection()`` : la correspondance entre les deux numérotations.

Une empreinte garantit qu'un contenu n'a pas changé d'une version à l'autre.
Elle ne dit rien de plus sur ce contenu.
"""

from __future__ import annotations

import hashlib

from .lettres import ALPHABET
from .portes import PORTES
from .roue import Ordre, cercle


def _sha256(texte: str) -> str:
    return hashlib.sha256(texte.encode("utf-8")).hexdigest()


def serialisation_table(ordre: Ordre = Ordre.ALPHABETIQUE) -> str:
    """Une ligne par porte : « i,j,X,Y », i < j dans l'ordre donné."""
    c = cercle(ordre)
    return "".join(
        f"{i},{j},{c[i].glyphe},{c[j].glyphe}\n" for i in range(22) for j in range(i + 1, 22)
    )


def serialisation_portes() -> str:
    """Une ligne par porte : ses deux lettres dans l'ordre alphabétique, sans numéro."""
    return "".join(f"{p.a.glyphe}{p.b.glyphe}\n" for p in PORTES)


def serialisation_bijection() -> str:
    """Une ligne par lettre : « glyphe,rang alphabétique,rang par catégories »."""
    return "".join(f"{l.glyphe},{l.rang},{l.opcode}\n" for l in ALPHABET)


def relire_par_lettres(serialisation: str) -> str:
    """Relit une table numérotée par ses seules lettres, rangées alphabétiquement."""
    from .portes import Porte

    portes = sorted(
        (Porte.de(x, y) for _, _, x, y in (ligne.split(",") for ligne in serialisation.splitlines())),
        key=lambda p: (p.a.rang, p.b.rang),
    )
    return "".join(f"{p.a.glyphe}{p.b.glyphe}\n" for p in portes)


def table(ordre: Ordre = Ordre.ALPHABETIQUE) -> str:
    return _sha256(serialisation_table(ordre))


def portes() -> str:
    return _sha256(serialisation_portes())


def bijection() -> str:
    return _sha256(serialisation_bijection())


def markdown() -> str:
    return "\n".join([
        "# Empreintes des 231 portes",
        "",
        "Fichier généré par `python -m portes_231 --empreintes` ; ne pas éditer à la main.",
        "Un test vérifie que ces valeurs correspondent toujours au code.",
        "",
        "| Contenu | Sérialisation | SHA-256 |",
        "|---|---|---|",
        f"| Table, ordre alphabétique | `i,j,X,Y` par ligne | `{table(Ordre.ALPHABETIQUE)}` |",
        f"| Table, ordre par catégories (3-7-12) | `i,j,X,Y` par ligne | `{table(Ordre.CATEGORIES)}` |",
        f"| Les 231 portes, sans numéro | `XY` par ligne, ordre alphabétique | `{portes()}` |",
        f"| Bijection entre les deux numérotations | `glyphe,rang,opcode` par ligne | `{bijection()}` |",
        "",
        "Les deux tables ont des empreintes différentes, puisque leurs numéros",
        "diffèrent. Relues par leurs seules lettres, elles donnent toutes deux",
        "l'empreinte des 231 portes sans numéro : c'est ce qui scelle qu'elles",
        "décrivent les mêmes portes. Chaque ligne se termine par un saut de ligne",
        "(`\\n`), et le texte est encodé en UTF-8.",
        "",
    ])
