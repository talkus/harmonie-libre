"""Étape 4 : les opérateurs nommés dans le texte de mik (2026-10-02).

Chaque entrée est indexée par la paire *ordonnée* (X, Y), c'est-à-dire
l'opérateur X ⊗ Y tel que le texte le décrit. Le texte appelle « face » la
première lecture de chaque exemple ; ce module recalcule face et dos selon
l'ordre alphabétique (voir ``portes.py``). Pour trois exemples écrits dans
l'ordre inverse de l'alphabet (מ–ד, מ–ז, ש–ט), le sens de chaque opérateur est
gardé tel quel et seule l'étiquette face/dos change.

Statut : reconstruction analytique. Ces noms sont des lectures, pas des
données du Sefer Yetzirah.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Nommage:
    resultat: str  # « Canal », « Source »…
    fonction: str  # « | », « /dev/stdin »…
    glose: str


def _p(x, y, resultat_xy, fonction_xy, glose_xy, resultat_yx, fonction_yx, glose_yx):
    return {
        (x, y): Nommage(resultat_xy, fonction_xy, glose_xy),
        (y, x): Nommage(resultat_yx, fonction_yx, glose_yx),
    }


EXEMPLES: dict[tuple[str, str], Nommage] = {}
for _paire in (
    # Mère–Mère
    _p("א", "מ", "Canal", "|", "L'unité canalisée devient un flux.",
       "Source", "/dev/stdin", "Le flux ramené à l'unité devient une source."),
    _p("א", "ש", "Création", "new", "L'unité qui se transforme produit un acte pur.",
       "Retour", "return", "La transformation ramenée à l'unité rend son résultat."),
    _p("מ", "ש", "Traitement", "map()", "Le flux transformé.",
       "Génération", "yield", "La transformation qui produit un flux."),
    # Double–Double
    _p("ב", "ג", "Envoi", "send()", "Le contenant transporté est un paquet.",
       "Réception", "recv()", "Le transport qui remplit un contenant."),
    _p("ב", "ד", "Ouverture", "open()", "Le contenant auquel on accède.",
       "Fermeture", "close()", "L'accès qui referme le contenant."),
    _p("ד", "ת", "Authentification", "auth()", "L'accès vérifié.",
       "Autorisation", "grant()", "La vérification qui donne accès."),
    _p("כ", "פ", "Déréférencement", "*ptr", "La référence exprimée.",
       "Adressage", "&var", "L'expression qui donne une référence."),
    _p("ר", "ת", "Validation", "assert()", "Le contrôle vérifié.",
       "Décision", "if", "La vérification qui contrôle."),
    # Simple–Simple
    _p("ה", "ו", "Lecture liée", "readline() + append()", "Observer puis lier.",
       "Écriture liée", "printf() + fflush()", "Lier puis observer."),
    _p("ז", "ח", "Partition", "split()", "Couper dans une portée.",
       "Isolation", "sandbox()", "Enclore puis couper."),
    _p("ט", "י", "Itération", "for", "Boucler en appliquant.",
       "Récursion", "recurse()", "Appliquer en bouclant."),
    _p("ל", "נ", "Enseignement", "fork()", "Guider vers la multiplication.",
       "Évolution", "mutate()", "Multiplier puis guider."),
    _p("ס", "ע", "Stabilisation ciblée", "lock()", "Soutenir en focalisant.",
       "Attention soutenue", "watch()", "Focaliser en soutenant."),
    _p("צ", "ק", "Correction", "sanitize()", "Aligner en filtrant.",
       "Sélection", "select()", "Filtrer en alignant."),
    # Mère–Double
    _p("א", "ב", "Abstraction", "class", "L'unité dans un contenant.",
       "Déconstruction", "unwrap()", "Le contenant ramené à l'unité."),
    _p("מ", "ד", "Ouverture de flux", "fopen()", "Le flux auquel on accède.",
       "Fermeture de flux", "fclose()", "L'accès qui referme le flux."),
    _p("ש", "ת", "Preuve", "hash()", "La transformation vérifiée.",
       "Signature", "sign()", "La vérification qui transforme."),
    # Mère–Simple
    _p("א", "ה", "Conscience", "self", "L'unité qui observe.",
       "Réflexion", "reflect()", "L'observation ramenée à l'unité."),
    _p("מ", "ז", "Coupure de flux", "split()", "Le flux coupé.",
       "Dérivation", "tee", "La coupure qui produit un flux."),
    _p("ש", "ט", "Itération transformante", "map()", "Transformer en boucle.",
       "Fold", "reduce()", "Boucler en transformant."),
    # Double–Simple
    _p("ב", "ה", "Inspection", "inspect()", "Le contenant observé.",
       "Encapsulation", "encapsulate()", "Observer puis contenir."),
    _p("ג", "ז", "Routage", "route()", "Le transport coupé.",
       "Multiplexage", "mux()", "Couper puis transporter."),
    _p("ד", "ח", "Portée d'accès", "namespace", "L'accès dans une portée.",
       "Permission", "permission", "La portée qui donne accès."),
    _p("כ", "נ", "Pointeur de fonction", "callback", "La référence qui engendre.",
       "Closure", "closure", "Engendrer puis référencer."),
    _p("פ", "צ", "Formatage", "format()", "La sortie alignée.",
       "Rapport", "report()", "Aligner puis sortir."),
    _p("ר", "ש", "Compilation", "compile()", "Le contrôle qui transforme.",
       "Interprétation", "interpret()", "Transformer puis contrôler."),
):
    EXEMPLES.update(_paire)
