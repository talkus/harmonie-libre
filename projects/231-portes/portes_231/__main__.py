"""Usage :
  python -m portes_231            résumé et matrice des faces
  python -m portes_231 א מ        les deux lectures de la porte א–מ
  python -m portes_231 --nommes   les 52 opérateurs nommés dans le texte
  python -m portes_231 --table    la table des 231 portes (Markdown)
"""

from __future__ import annotations

import sys

from . import ALPHABET, OPERATEURS, PORTES, Porte, matrice


def _matrice() -> str:
    lignes = ["    " + " ".join(f"{l.glyphe:^5}" for l in ALPHABET)]
    for i, rang in enumerate(matrice()):
        cases = []
        for j, op in enumerate(rang):
            cases.append(f"{'—':^5}" if op is None or j < i else f"{op.x}–{op.y}".center(5))
        lignes.append(f"{ALPHABET[i].glyphe:<3} " + " ".join(cases))
    return "\n".join(lignes)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if args == ["--nommes"]:
        for op in OPERATEURS:
            if op.nommage:
                print(op)
        return 0
    if args == ["--table"]:
        from .table import markdown

        sys.stdout.write(markdown())
        return 0
    if len(args) == 2:
        p = Porte.de(*args)
        print(f"Porte {p}")
        for op in p:
            print(f"  {op}")
            if op.nommage:
                print(f"      {op.nommage.glose}")
        return 0
    if args:
        print(__doc__, file=sys.stderr)
        return 2
    print(f"{len(PORTES)} portes, {len(OPERATEURS)} opérateurs (face + dos)\n")
    print(_matrice())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
