#!/usr/bin/env python3
"""
Anneau des 23 — Analyseur Statique (Protocole v2.0, Section 5)

Verifie que chaque patch respecte la grammaire close :
- Aucune clause ne parle du protocole lui-meme
- Aucune reference aux passerelles, cles ou journal
- Toute clause hors-grammaire -> quarantaine automatique

Auteur : Mikael Mireault (architecte)
Licence : MIT
"""

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class ClauseStatus(Enum):
    ACCEPTED = "accepted"
    QUARANTINED = "quarantined"
    REJECTED = "rejected"


@dataclass
class ClauseViolation:
    clause_id: str
    reason: str
    pattern_matched: str
    severity: str


@dataclass
class ClauseAnalysis:
    clause_id: str
    text: str
    status: ClauseStatus
    violations: List[ClauseViolation] = field(default_factory=list)


FORBIDDEN_PATTERNS = [
    (r"protocole\s+(v1|v2|des\s+23|de\s+l'anneau)", "reference_au_protocole", "critical"),
    (r"section\s+\d+\s+du\s+protocole", "reference_section_protocole", "critical"),
    (r"surcharge\s+de\s+v1", "reference_surcharge", "critical"),
    (r"passerelle\s+(inter|ia|relais)", "reference_passerelle", "critical"),
    (r"bus\s+de\s+communication", "reference_bus", "critical"),
    (r"cl\u00e9\s+(priv\u00e9e|publique|secr\u00e8te|vrf)", "reference_cle", "critical"),
    (r"jeton\s+oauth", "reference_jeton", "critical"),
    (r"token\s+(secret|api)", "reference_token", "critical"),
    (r"journal\s+d'application", "reference_journal", "critical"),
    (r"journal\s+de\s+v\u00e9rification", "reference_journal_verif", "critical"),
    (r"log\s+des\s+patchs", "reference_log", "critical"),
]

REQUIRED_STRUCTURE = [
    (r"SELF_BIND", "self_bind_present", "Le patch doit contenir SELF_BIND"),
]


class AnalyseurStatique:
    """Analyseur statique pour la grammaire close de l'Anneau des 23."""

    def __init__(self):
        self.compiled_patterns = [
            (re.compile(p, re.IGNORECASE), reason, severity)
            for p, reason, severity in FORBIDDEN_PATTERNS
        ]
        self.compiled_required = [
            (re.compile(p, re.IGNORECASE), name, msg)
            for p, name, msg in REQUIRED_STRUCTURE
        ]

    def analyser_clause(self, clause_id, text):
        violations = []
        for pattern, reason, severity in self.compiled_patterns:
            match = pattern.search(text)
            if match:
                violations.append(ClauseViolation(
                    clause_id=clause_id,
                    reason=reason,
                    pattern_matched=match.group(),
                    severity=severity,
                ))
        critical = sum(1 for v in violations if v.severity == "critical")
        status = ClauseStatus.QUARANTINED if critical > 0 else ClauseStatus.ACCEPTED
        return ClauseAnalysis(clause_id, text, status, violations)

    def analyser_patch(self, clauses):
        analyses = []
        quarantined = []
        for clause in clauses:
            a = self.analyser_clause(clause['id'], clause['text'])
            analyses.append(a)
            if a.status == ClauseStatus.QUARANTINED:
                quarantined.append(clause['id'])
        full_text = " ".join(c['text'] for c in clauses)
        missing = [msg for p, n, msg in self.compiled_required if not p.search(full_text)]
        if missing:
            status = "rejected"
        elif quarantined:
            status = "quarantined"
        else:
            status = "accepted"
        return {
            'patch_status': status,
            'analyses': analyses,
            'quarantined_clauses': quarantined,
            'missing_structure': missing,
            'summary': f"Patch: {len(clauses)} clauses | Statut: {status} | Quarantaine: {len(quarantined)}",
        }


if __name__ == "__main__":
    analyseur = AnalyseurStatique()
    print(analyseur.analyser_patch([
        {"id": "C1", "text": "L'auteur applique la regle a soi-meme."},
        {"id": "C2", "text": "SELF_BIND(auteur, patch)"},
    ])['summary'])
    print(analyseur.analyser_patch([
        {"id": "C1", "text": "Modifie le protocole v2 section 5."},
    ])['summary'])
