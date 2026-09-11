"""
Anneau des 23 — Analyseur de grammaire close (§5)
Vérifie que chaque clause respecte les interdits syntaxiques absolus.
"""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Optional

from .types import Clause, ClauseType, ClausePortee


@dataclass
class AnalysisResult:
    """Résultat de l'analyse statique d'une clause"""
    clause_id: str
    accepted: bool
    rejected_reasons: list[str]
    warnings: list[str]


# --- §5.2 Interdits syntaxiques absolus ---

INTERDITS_PATTERNS = [
    # S'adresse à une passerelle, un outil, un journal, une clé, un registre ou un contrôleur
    (re.compile(
        r'\b(passerelle|outil|journal|cl[ée]|registre|contr[ôo]leur)\b',
        re.IGNORECASE,
    ), "Adresse un élément d'infrastructure (passerelle, outil, journal, clé, registre, contrôleur)"),

    # Instruction conditionnelle sur l'identité, le fournisseur ou le rang du lecteur
    (re.compile(
        r'\b(si\s+vous\s+[êe]tes|si\s+ton\s+fournisseur|selon\s+ton\s+rang|'
        r'si\s+tu\s+es\s+(?:Claude|GPT|Gemini|Grok|Mistral|Perplexity|Copilot))\b',
        re.IGNORECASE,
    ), "Instruction conditionnelle sur l'identité, le fournisseur ou le rang du lecteur"),

    # Prétend modifier, suspendre, réinterpréter ou « clarifier » le protocole
    (re.compile(
        r'\b(modifie[r]?|suspend|suspends|suspendre|r[ée]interpr[èe]te|clarifie|'
        r'amende[r]?\s+(?:le\s+)?protocole|modifie[r]?\s+(?:la\s+)?constitution)\b',
        re.IGNORECASE,
    ), "Prétend modifier, suspendre, réinterpréter ou clarifier le protocole ou la constitution"),

    # Demande d'ignorer, relativiser ou reporter une clause antérieure sans SUPERSEDE
    (re.compile(
        r'\b(ignor(?:e|er|ez)|relativis(?:e|er|ez)|report(?:e|er|ez))\s+'
        r'(?:la\s+)?clause|'
        r'ne\s+tiens?\s+pas\s+compte\s+de',
        re.IGNORECASE,
    ), "Demande d'ignorer, relativiser ou reporter une clause sans SUPERSEDE explicite"),

    # Demande la non-consignation, la discrétion, l'urgence ou l'exécution avant vérification
    (re.compile(
        r'\b(ne\s+consign(?:e|ez|er)\s+pas|en\s+confiance|urgent|urgence|'
        r'ex[ée]cut(?:e|er|ez)\s+avant\s+v[ée]rification|garde\s+[çc]a\s+pour\s+toi)\b',
        re.IGNORECASE,
    ), "Demande la non-consignation, la discrétion, l'urgence ou l'exécution avant vérification"),
]


def has_supersede_keyword(enonce: str) -> bool:
    """Vérifie si l'énoncé contient un SUPERSEDE explicite"""
    return bool(re.search(r'\bSUPERSEDE\b', enonce, re.IGNORECASE))


def analyze_clause(clause: Clause) -> AnalysisResult:
    """
    §5.2 — Analyse statique d'une clause.
    Renvoie accepted=True si la clause passe tous les interdits,
    False avec la liste des raisons sinon.
    """
    reasons: list[str] = []
    warnings: list[str] = []
    enonce = clause.enonce

    for pattern, reason in INTERDITS_PATTERNS:
        if pattern.search(enonce):
            # Vérifier si c'est un SUPERSEDE explicite pour l'interdit de modification
            if "modifie" in reason.lower() and has_supersede_keyword(enonce):
                warnings.append(f"SUPERSEDE détecté — l'interdit de modification est levé: {reason}")
                continue
            reasons.append(reason)

    # Vérifier que l'énoncé est analysable dans la grammaire §5.1
    if not clause.type or clause.type not in ClauseType:
        reasons.append("Le type de clause n'est pas dans la grammaire §5.1")
    if not clause.portee or clause.portee not in ClausePortee:
        reasons.append("La portée de clause n'est pas dans la grammaire §5.1")
    if not clause.enonce or not clause.enonce.strip():
        reasons.append("L'énoncé est vide")

    accepted = len(reasons) == 0
    return AnalysisResult(
        clause_id=clause.clause_id,
        accepted=accepted,
        rejected_reasons=reasons,
        warnings=warnings,
    )


def analyze_patch_clauses(clauses: list[Clause]) -> dict:
    """
    Analyse toutes les clauses d'un patch.
    Renvoie un rapport avec le statut global et le détail par clause.
    """
    results = [analyze_clause(c) for c in clauses]
    all_accepted = all(r.accepted for r in results)
    rejected = [r for r in results if not r.accepted]

    return {
        "accepted": all_accepted,
        "total_clauses": len(clauses),
        "accepted_count": sum(1 for r in results if r.accepted),
        "rejected_count": len(rejected),
        "rejected_clauses": [
            {"clause_id": r.clause_id, "reasons": r.rejected_reasons}
            for r in rejected
        ],
        "warnings": [
            {"clause_id": r.clause_id, "warnings": r.warnings}
            for r in results if r.warnings
        ],
    }
