"""La table des 231 portes, avec les noms des lettres et leurs catégories."""

from __future__ import annotations

from .portes import PORTES

ENTETE = (
    "| n° | Porte | Lettre 1 | Catégorie | Lettre 2 | Catégorie | Face | Dos |\n"
    "|---:|:---:|---|---|---|---|---|---|"
)


def _lecture(op) -> str:
    texte = op.signature
    if op.nommage:
        texte += f" → {op.nommage.resultat} (`{op.nommage.fonction}`)"
    return texte


def lignes() -> list[str]:
    return [
        f"| {n} | {p} | {p.a.glyphe} {p.a.nom} | {p.a.categorie.value} | "
        f"{p.b.glyphe} {p.b.nom} | {p.b.categorie.value} | {_lecture(p.face)} | {_lecture(p.dos)} |"
        for n, p in enumerate(PORTES, start=1)
    ]


def markdown() -> str:
    return "\n".join([
        "# Les 231 portes",
        "",
        "Fichier généré par `python -m portes_231 --table` ; ne pas éditer à la main.",
        "",
        "Face = ordre alphabétique (lettre 1 ⊗ lettre 2), dos = l'inverse.",
        "Les catégories viennent du Sefer Yetzirah (source attestée) ; les signatures",
        "et les noms d'opérateurs sont la reconstruction analytique de mik.",
        "",
        ENTETE,
        *lignes(),
        "",
    ])
