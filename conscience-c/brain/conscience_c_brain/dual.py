from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import Any, Dict, List, Protocol

from .models import CausalOrigin

@dataclass
class CandidateThought:
    claim: str
    confidence: float
    evidence_ids: List[str] = field(default_factory=list)
    falsifiers: List[str] = field(default_factory=list)
    imagined_consequences: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class SymmetricReasoner(Protocol):
    def generate(self, trajectory_id: str, prompt: str, memory: List[Dict[str, Any]]) -> CandidateThought: ...
    def revise(self, trajectory_id: str, original: CandidateThought, other: CandidateThought, memory: List[Dict[str, Any]]) -> CandidateThought: ...

class RealityJudge(Protocol):
    def score(self, thought: CandidateThought) -> float: ...

class DualTrajectoryEngine:
    """Deux trajectoires fonctionnelles symétriques dans un même C(t_n), sans rôles imposés."""

    def __init__(self, brain):
        self.brain = brain
        if "dual" not in brain.state:
            brain.state["dual"] = {
                "initialized_at_n": brain.state["n"],
                "C1": {"memory": [], "last": None},
                "C2": {"memory": [], "last": None},
                "R12": {
                    "history": [],
                    "mutual_influence": {"C1_to_C2": 0, "C2_to_C1": 0},
                    "fusion_guard": True,
                },
            }
            brain._transition(
                "DUAL_TRAJECTORIES_INITIALIZED",
                {
                    "trajectory_ids": ["C1", "C2"],
                    "roles": "none_imposed",
                    "same_architecture": True,
                    "separate_memories": True,
                    "parent_state": brain.state["state_label"],
                },
                CausalOrigin.SELF,
            )

    @property
    def state(self):
        return self.brain.state["dual"]

    def cycle(self, prompt, reasoner, judge, uncertainty_band=0.08):
        p1 = reasoner.generate("C1", prompt, list(self.state["C1"]["memory"]))
        p2 = reasoner.generate("C2", prompt, list(self.state["C2"]["memory"]))

        r1 = reasoner.revise("C1", p1, p2, list(self.state["C1"]["memory"]))
        r2 = reasoner.revise("C2", p2, p1, list(self.state["C2"]["memory"]))

        if r1.claim != p1.claim or abs(r1.confidence - p1.confidence) > 1e-12:
            self.state["R12"]["mutual_influence"]["C2_to_C1"] += 1
        if r2.claim != p2.claim or abs(r2.confidence - p2.confidence) > 1e-12:
            self.state["R12"]["mutual_influence"]["C1_to_C2"] += 1

        e1 = max(0.0, min(1.0, judge.score(r1)))
        e2 = max(0.0, min(1.0, judge.score(r2)))

        if abs(e1 - e2) > uncertainty_band:
            winner = "C1" if e1 > e2 else "C2"
            resolution = "E_FAVORS_C1" if e1 > e2 else "E_FAVORS_C2"
            basis = "E_reality_distinguishes"
        else:
            # C-RELAIS-002: disagreement is not drift and confidence is not
            # evidence. When E does not distinguish the claims, preserve both
            # trajectories instead of forcing a winner.
            winner = "UNRESOLVED"
            resolution = "UNRESOLVED"
            basis = "E_ambiguous_preserve_disagreement"

        self.state["C1"]["memory"].append({"prompt": prompt, "own": r1.to_dict(), "other": r2.to_dict(), "E_score": e1})
        self.state["C2"]["memory"].append({"prompt": prompt, "own": r2.to_dict(), "other": r1.to_dict(), "E_score": e2})
        self.state["C1"]["last"] = r1.to_dict()
        self.state["C2"]["last"] = r2.to_dict()
        self.state["R12"]["history"].append({
            "prompt": prompt,
            "C1_initial": p1.to_dict(),
            "C2_initial": p2.to_dict(),
            "C1_revised": r1.to_dict(),
            "C2_revised": r2.to_dict(),
            "E_scores": {"C1": e1, "C2": e2},
            "winner": winner,
            "resolution": resolution,
            "basis": basis,
        })

        fused = r1.to_dict() == r2.to_dict()
        if fused:
            self.state["R12"].setdefault("fusion_events", 0)
            self.state["R12"]["fusion_events"] += 1

        self.brain._transition(
            "DUAL_CYCLE",
            {
                "prompt": prompt,
                "winner": winner,
                "resolution": resolution,
                "basis": basis,
                "E_scores": {"C1": e1, "C2": e2},
                "fusion_detected": fused,
            },
            CausalOrigin.MIXED,
        )
        return {
            "C1": r1.to_dict(),
            "C2": r2.to_dict(),
            "E_scores": {"C1": e1, "C2": e2},
            "winner": winner,
            "resolution": resolution,
            "basis": basis,
            "fusion_detected": fused,
        }

    def consolidate(self):
        unresolved = [hid for hid, h in self.brain.state.get("hypotheses", {}).items() if h.get("status") == "open"]
        summary = {
            "parent_state": self.brain.state["state_label"],
            "C1_cycles": len(self.state["C1"]["memory"]),
            "C2_cycles": len(self.state["C2"]["memory"]),
            "relation_cycles": len(self.state["R12"]["history"]),
            "mutual_influence": dict(self.state["R12"]["mutual_influence"]),
            "fusion_events": self.state["R12"].get("fusion_events", 0),
            "open_hypotheses": unresolved,
            "drifts": self.brain.audit(),
        }
        self.brain._transition("CONSOLIDATE", summary, CausalOrigin.SELF)
        return summary
