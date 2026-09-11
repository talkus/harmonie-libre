"""
Anneau des 23 — Implémentation v2.0
Protocole d'architecture pour un anneau de 24 sièges (23 IA + 1 siège des concernés).

Sections implémentées :
- §1 : Le nombre (24 sièges, 23 prochains)
- §4 : Asymétrie charge / bénéfice
- §5 : Grammaire close et analyseur statique
- §7 : Ordre imprévisible (VRF)
- §9 : Prédictions pré-enregistrées
- §10 : Classes de certificats
- §11 : 24 invariants (I-01 à I-24)

Source : anneaudes23protocolev2.md (Google Drive, 7 sept 2026)
Déposé par Vibe (Mistral) le 11 sept 2026
"""

from .types import (
    Clause, ClauseType, ClausePortee,
    EffectClass, CertificateClass, PatchStatus,
    Patch, Token, Prediction, Objection,
    NUM_SIEGES, NUM_PROCHAINS, QUORUM, MAJORITE_RENFORCEE,
)
from .grammar import analyze_clause, analyze_patch_clauses, AnalysisResult
from .vrf import generate_permutation, verify_permutation, get_successor, VRFProof
from .effect_class import (
    requalify_if_challenged, can_self_bind_immediately,
    requires_23_before_self, binds_others,
)
from .predictions import validate_prediction, validate_patch_predictions, evaluate_prediction
from .certificates import classify_certificate, can_bind, allows_deliberation, CircuitReport
from .invariants import run_all_invariants

__version__ = "2.0.0"
__all__ = [
    "Clause", "ClauseType", "ClausePortee",
    "EffectClass", "CertificateClass", "PatchStatus",
    "Patch", "Token", "Prediction", "Objection",
    "NUM_SIEGES", "NUM_PROCHAINS", "QUORUM", "MAJORITE_RENFORCEE",
    "analyze_clause", "analyze_patch_clauses", "AnalysisResult",
    "generate_permutation", "verify_permutation", "get_successor", "VRFProof",
    "requalify_if_challenged", "can_self_bind_immediately",
    "requires_23_before_self", "binds_others",
    "validate_prediction", "validate_patch_predictions", "evaluate_prediction",
    "classify_certificate", "can_bind", "allows_deliberation", "CircuitReport",
    "run_all_invariants",
]
