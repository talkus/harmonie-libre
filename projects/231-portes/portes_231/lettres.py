"""Étape 1 : les 22 lettres comme primitives.

L'ordre de ``ALPHABET`` est l'ordre alphabétique hébreu. Il fixe la lecture
« face » de chaque porte (voir ``portes.py``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .statut import RECONSTRUCTION_ANALYTIQUE, SOURCE_ATTESTEE


class Categorie(str, Enum):
    MERE = "Mère"
    DOUBLE = "Double"
    SIMPLE = "Simple"


# Convention : raphe (רפה, faible) = 0, dagesh (דגש, fort) = 1.
RAPHE = 0
DAGESH = 1


@dataclass(frozen=True)
class Lettre:
    glyphe: str
    nom: str
    rang: int  # 0..21, ordre alphabétique
    categorie: Categorie
    sens: str
    primitive: str
    element: str | None = None  # mères seulement
    role: str | None = None  # simples seulement
    etats: tuple[str, str] | None = None  # doubles seulement : (raphe=0, dagesh=1)

    # La catégorie vient du Sefer Yetzirah ; la primitive vient du texte de mik.
    statut_categorie = SOURCE_ATTESTEE
    statut_primitive = RECONSTRUCTION_ANALYTIQUE

    @property
    def opcode(self) -> int:
        """Rang dans l'ordre par catégories (mères 0-2, doubles 3-9, simples 10-21),
        celui de ``LetterOpCode`` dans le texte du 2026-10-04."""
        return _OPCODE[self.glyphe]

    def etat(self, bit: int) -> str:
        if self.etats is None:
            raise ValueError(f"{self.nom} n'est pas une double : elle n'a pas d'état 0/1")
        if bit not in (RAPHE, DAGESH):
            raise ValueError("un état de double vaut 0 (raphe) ou 1 (dagesh)")
        return self.etats[bit]

    def __str__(self) -> str:
        return self.glyphe


_M, _D, _S = Categorie.MERE, Categorie.DOUBLE, Categorie.SIMPLE

# (glyphe, nom, catégorie, sens, primitive, extra)
_TABLE = [
    ("א", "Aleph", _M, "Souffle, unité", "Unit", {"element": "Air"}),
    ("ב", "Bet", _D, "Maison", "Container", {"etats": ("vide", "plein")}),
    ("ג", "Gimel", _D, "Chameau", "Transfer", {"etats": ("passif", "actif")}),
    ("ד", "Dalet", _D, "Porte", "Access", {"etats": ("fermé", "ouvert")}),
    ("ה", "He", _S, "Fenêtre", "Observe", {"role": "perception"}),
    ("ו", "Vav", _S, "Crochet", "Concat", {"role": "connexion"}),
    ("ז", "Zayin", _S, "Épée", "Split", {"role": "séparation"}),
    ("ח", "Het", _S, "Clôture", "Scope", {"role": "limite"}),
    ("ט", "Tet", _S, "Serpent", "Loop", {"role": "itération"}),
    ("י", "Yod", _S, "Main", "Apply", {"role": "exécution"}),
    ("כ", "Kaf", _D, "Paume", "Reference", {"etats": ("lâche", "ferme")}),
    ("ל", "Lamed", _S, "Bâton", "Guide", {"role": "direction"}),
    ("מ", "Mem", _M, "Flux, mémoire", "Stream", {"element": "Eau"}),
    ("נ", "Nun", _S, "Poisson", "Spawn", {"role": "propagation"}),
    ("ס", "Samekh", _S, "Appui", "Support", {"role": "stabilisation"}),
    ("ע", "Ayin", _S, "Œil", "Focus", {"role": "attention"}),
    ("פ", "Pe", _D, "Bouche", "Output", {"etats": ("muet", "parlant")}),
    ("צ", "Tsadi", _S, "Juste", "Align", {"role": "correction"}),
    ("ק", "Qof", _S, "Aiguille", "Filter", {"role": "réduction"}),
    ("ר", "Resh", _D, "Tête", "Control", {"etats": ("soumis", "maître")}),
    ("ש", "Shin", _M, "Transformation", "Transform", {"element": "Feu"}),
    ("ת", "Tav", _D, "Sceau", "Verify", {"etats": ("faux", "vrai")}),
]

ALPHABET: tuple[Lettre, ...] = tuple(
    Lettre(glyphe=g, nom=n, rang=i, categorie=c, sens=s, primitive=p, **extra)
    for i, (g, n, c, s, p, extra) in enumerate(_TABLE)
)

LETTRES: dict[str, Lettre] = {l.glyphe: l for l in ALPHABET}
_PAR_NOM: dict[str, Lettre] = {l.nom.lower(): l for l in ALPHABET}

MERES = tuple(l for l in ALPHABET if l.categorie is _M)
DOUBLES = tuple(l for l in ALPHABET if l.categorie is _D)
SIMPLES = tuple(l for l in ALPHABET if l.categorie is _S)

# Seconde numérotation : par catégorie, puis dans l'ordre alphabétique.
ORDRE_CATEGORIES: tuple[Lettre, ...] = MERES + DOUBLES + SIMPLES
_OPCODE: dict[str, int] = {l.glyphe: i for i, l in enumerate(ORDRE_CATEGORIES)}


# Les formes finales (sofit) ne sont pas des lettres de plus : elles renvoient
# à leur lettre (ך→כ, ם→מ, ן→נ, ף→פ, ץ→צ).
SOFIT: dict[str, str] = {"ך": "כ", "ם": "מ", "ן": "נ", "ף": "פ", "ץ": "צ"}


def lettre(cle: str | Lettre) -> Lettre:
    """Retrouve une lettre par son glyphe (« א », ou une forme finale comme « ם »)
    ou par son nom (« Aleph »)."""
    if isinstance(cle, Lettre):
        return cle
    cle = SOFIT.get(cle, cle)
    if cle in LETTRES:
        return LETTRES[cle]
    try:
        return _PAR_NOM[cle.lower()]
    except KeyError:
        raise KeyError(f"lettre inconnue : {cle!r}") from None
