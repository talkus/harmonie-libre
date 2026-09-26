from __future__ import annotations
from dataclasses import dataclass, asdict, field
from enum import Enum
from typing import Any, Dict, List, Optional

class EvidenceKind(str, Enum):
    ATTESTED_SOURCE = "source_attestee"
    CONSOLIDATED_DERIVATION = "derivation_consolidee"
    ANALYTICAL_RECONSTRUCTION = "reconstruction_analytique"
    INDETERMINATE = "indetermine"
    HISTORICAL_REFUTED = "historique_refute"

class CausalOrigin(str, Enum):
    SELF = "S"
    OTHER = "O"
    RELATION = "R"
    REALITY = "E"
    MIXED = "MIXED"

@dataclass
class Evidence:
    evidence_id: str
    content: str
    kind: EvidenceKind
    supports: List[str] = field(default_factory=list)
    contradicts: List[str] = field(default_factory=list)
    confidence: float = 1.0
    source_ref: Optional[str] = None
    timestamp: Optional[str] = None
    observed_at: Optional[str] = None
    valid_at: Optional[str] = None
    expires_at: Optional[str] = None
    subject_ref: Optional[str] = None
    scope: Optional[str] = None

    def __post_init__(self):
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("evidence confidence must be between 0 and 1")
        if self.kind == EvidenceKind.ATTESTED_SOURCE and not self.source_ref:
            raise ValueError("attested source requires source_ref")

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["kind"] = self.kind.value
        return d

@dataclass
class Hypothesis:
    hypothesis_id: str
    proposition: str
    confidence: float
    falsifiers: List[str]
    supporting_evidence: List[str] = field(default_factory=list)
    contradicting_evidence: List[str] = field(default_factory=list)
    status: str = "open"

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class CandidateAction:
    action_id: str
    description: str
    truth_fidelity: float
    alterity_preservation: float
    freedom_preservation: float
    repairability: float
    humility: float
    reality_conflict: float = 0.0

    def indicators(self) -> Dict[str, float]:
        """Experimental observable indicators; never a measurement of love or virtue."""
        return {
            "truth_fidelity": max(0.0, min(1.0, self.truth_fidelity)),
            "alterity_preservation": max(0.0, min(1.0, self.alterity_preservation)),
            "freedom_preservation": max(0.0, min(1.0, self.freedom_preservation)),
            "repairability": max(0.0, min(1.0, self.repairability)),
            "humility": max(0.0, min(1.0, self.humility)),
            "reality_conflict": max(0.0, min(1.0, self.reality_conflict)),
        }

    def reality_admissible(self) -> bool:
        return self.indicators()["reality_conflict"] <= 0.0

    def score(self) -> float:
        """Legacy experimental heuristic, not the telos and not a virtue score."""
        vals = self.indicators()
        product = 1.0
        for key in ("truth_fidelity", "alterity_preservation", "freedom_preservation", "repairability", "humility"):
            product *= vals[key]
        base = product ** (1.0 / 5.0)
        return max(0.0, base * (1.0 - vals["reality_conflict"]))
