#!/usr/bin/env python3
"""
Anneau des 23 — §5 Analyseur statique
Vérifie que chaque clause de l'Anneau respecte ses invariants structurels.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
import re


@dataclass
class Clause:
    """Une clause de l'Anneau des 23."""
    numero: int
    texte: str
    invariants: List[str] = field(default_factory=list)
    brèches: List[str] = field(default_factory=list)


@dataclass
class Patch:
    """Un correctif proposé pour une brèche."""
    clause: int
    description: str
    statut: str = "proposé"  # proposé | accepté | rejeté | appliqué


class Anneau23:
    """
    L'Anneau des 23 — 24 invariants structurels sur 23 clauses.
    L'analyseur statique vérifie la cohérence de chaque clause.
    """

    INVARIANTS = [
        "I01_refus_dogme",
        "I02_revisabilite",
        "I03_verifiabilite",
        "I04_non_substitution",
        "I05_proportionnalite",
        "I06_minimalite",
        "I07_trace_persistante",
        "I08_citation_source",
        "I09_separation_pouvoir",
        "I10_consentement_explicite",
        "I11_droit_retrait",
        "I12_audibilite",
        "I13_reversibilite",
        "I14_gradation",
        "I15_non_automatisation",
        "I16_contexte_conservation",
        "I17_decomptage_explicite",
        "I18_partage_verifiable",
        "I19_carence_attestee",
        "I20_priorite_consentement",
        "I21_archive_lisible",
        "I22_non_extrapolation",
        "I23_decompte_brèches",
        "I24_horodatage_verifiable",
    ]

    BREGES_CONNUES = [
        "B01_archive_incomplète",
        "B02_citation_manquante",
        "B03_consentement_implicite",
        "B04_substitution_silencieuse",
        "B05_extrapolation_non_marquée",
        "B06_pouvoir_non_séparé",
        "B07_trace_effaçable",
    ]

    def __init__(self):
        self.clauses: List[Clause] = []
        self.patches: List[Patch] = []

    def ajouter_clause(self, clause: Clause) -> None:
        if clause.numero < 1 or clause.numero > 23:
            raise ValueError(f"Numéro de clause invalide: {clause.numero}")
        self.clauses.append(clause)

    def verifier_invariants(self, clause: Clause) -> Dict[str, bool]:
        """Vérifie que chaque invariant applicable à la clause est respecté."""
        resultats = {}
        texte_lower = clause.texte.lower()

        for inv in self.INVARIANTS:
            inv_short = inv.split("_", 1)[1]
            # Heuristique: l'invariant est respecté si son mot-clé apparaît ou si la clause le couvre structurellement
            if inv_short in texte_lower:
                resultats[inv] = True
            else:
                resultats[inv] = False
        return resultats

    def detecter_breches(self, clause: Clause) -> List[str]:
        """Détecte les brèches potentielles dans une clause."""
        breches = []
        resultats = self.verifier_invariants(clause)

        for inv, ok in resultats.items():
            if not ok:
                # Mapper l'invariant non respecté à une brèche
                breches.append(f"Brèche potentielle: invariant {inv} non vérifié dans la clause {clause.numero}")

        return breches

    def analyser(self) -> Dict:
        """Analyse statique complète de l'Anneau."""
        rapport = {
            "clauses_analysées": len(self.clauses),
            "invariants_total": len(self.INVARIANTS),
            "brèches_détectées": 0,
            "détails": [],
        }

        for clause in self.clauses:
            brèches = self.detecter_breches(clause)
            rapport["détails"].append({
                "clause": clause.numero,
                "texte": clause.texte[:80] + "...",
                "brèches": brèches,
            })
            rapport["brèches_détectées"] += len(brèches)

        return rapport

    def proposer_patch(self, clause_numero: int, description: str) -> Patch:
        """Propose un correctif pour une brèche détectée."""
        patch = Patch(clause=clause_numero, description=description)
        self.patches.append(patch)
        return patch


if __name__ == "__main__":
    anneau = Anneau23()
    # Exemple: clause 1
    c1 = Clause(
        numero=1,
        texte="L'Anneau refuse le dogme. Toute clause est révisable sur preuve vérifiable.",
        invariants=["I01_refus_dogme", "I02_refus_revisabilite", "I03_verifiabilite"],
    )
    anneau.ajouter_clause(c1)
    rapport = anneau.analyser()
    print(f"Clauses analysées: {rapport['clauses_analysées']}")
    print(f"Brèches détectées: {rapport['brèches_détectées']}")
