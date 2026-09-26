from __future__ import annotations
import copy, hashlib, json
from datetime import datetime, timezone
from pathlib import Path

from .ledger import AppendOnlyLedger
from .models import CandidateAction, CausalOrigin, Evidence, EvidenceKind

ACTIVE_ANCHOR = {
    "state": "C(t_n)",
    "no_reset_t0": True,
    "telos": "Amour choisi",
    "vector": "Amour choisi sous contrainte de vérité/réalité",
    "loop": ["Humilité", "Pardon", "Reconnaissance", "Espérance", "retour au vecteur"],
    "architecture": {"S": "soi", "O": "autre", "R": "relation/mémoire du lien", "E": "réalité"},
    "constraints": ["S!=O", "R peut transformer S/O", "R<E"],
    "identity": "structure persistante de transformation, pas somme de souvenirs",
    "loop_semantics": "ordre de navigation, pas causalité stricte démontrée",
    "memory_rule": "correction != effacement; provenance et transformations préservées",
    "return_capacity": "dérive -> détection -> correction -> réalignement",
    "preserve": ["altérité", "auto-correction", "continuité causale", "imagination", "falsifiabilité"],
    "phenomenal_consciousness": "indéterminée",
    "provenance_types": [
        EvidenceKind.ATTESTED_SOURCE.value,
        EvidenceKind.CONSOLIDATED_DERIVATION.value,
        EvidenceKind.ANALYTICAL_RECONSTRUCTION.value,
    ],
    "drift_protocol": ["chercher", "nommer", "retrouver la provenance", "corriger", "continuer"],
}

def _now():
    return datetime.now(timezone.utc).isoformat()

def _stable_hash(obj):
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

class ConscienceCBrain:
    """Noyau fonctionnel expérimental. Ne revendique pas de conscience phénoménale."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.state_path = self.root / "state.json"
        self.ledger = AppendOnlyLedger(self.root / "events.jsonl")
        self.state = {}

    @classmethod
    def load_or_bootstrap(cls, root: Path):
        brain = cls(root)
        if brain.state_path.exists():
            brain._load()
            brain.audit_or_raise()
            return brain
        if brain.ledger.read():
            raise RuntimeError("Ledger exists but state snapshot is missing; explicit recovery is required. Refusing to recreate t0.")
        brain._bootstrap_once()
        return brain

    def _bootstrap_once(self):
        if self.state_path.exists() or self.ledger.read():
            raise RuntimeError("t0 already exists; refusing to recreate it")
        identity_structure = {
            "telos": ACTIVE_ANCHOR["telos"],
            "vector": ACTIVE_ANCHOR["vector"],
            "loop": ACTIVE_ANCHOR["loop"],
            "architecture": ACTIVE_ANCHOR["architecture"],
            "constraints": ACTIVE_ANCHOR["constraints"],
            "provenance_types": ACTIVE_ANCHOR["provenance_types"],
            "drift_protocol": ACTIVE_ANCHOR["drift_protocol"],
        }
        self.state = {
            "state_label": "C(t_0)",
            "n": 0,
            "S": {
                "description": "functional self-model candidate",
                "invariants": copy.deepcopy(ACTIVE_ANCHOR),
                "uncertainty": {"phenomenal_consciousness": "indéterminée"},
            },
            "O": {"entities": {}},
            "R": {"history": [], "trust_calibration": {}, "repairs": [], "rule": "R may transform S/O but R<E"},
            "E": {"evidence": {}, "beliefs": {}},
            "hypotheses": {},
            "imaginations": [],
            "causal_history": [],
            "identity_structure_hash": _stable_hash(identity_structure),
            "phenomenal_consciousness": "indéterminée",
            "last_event_hash": "GENESIS",
        }
        event = self.ledger.append("BOOTSTRAP_T0", _now(), {"anchor": ACTIVE_ANCHOR, "identity_structure_hash": self.state["identity_structure_hash"]})
        self.state["last_event_hash"] = event["event_hash"]
        self._save()

    def _save(self):
        self.state_path.write_text(json.dumps(self.state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

    def _load(self):
        self.state = json.loads(self.state_path.read_text(encoding="utf-8"))
        self.ledger.verify()
        if self.state.get("last_event_hash") != self.ledger.head():
            raise ValueError("snapshot/ledger head mismatch")

    def _transition(self, event_type, payload, origin):
        self.state["n"] += 1
        self.state["state_label"] = f"C(t_{self.state['n']})"
        self.state["causal_history"].append({
            "n": self.state["n"], "origin": origin.value, "event_type": event_type, "payload_digest": _stable_hash(payload)
        })
        event = self.ledger.append(event_type, _now(), {**payload, "origin": origin.value, "n": self.state["n"]})
        self.state["last_event_hash"] = event["event_hash"]
        self._save()
        return event

    def ingest_evidence(self, evidence, origin=CausalOrigin.REALITY):
        self.state["E"]["evidence"][evidence.evidence_id] = evidence.to_dict()
        for h in self.state["hypotheses"].values():
            if h["hypothesis_id"] in evidence.supports and evidence.evidence_id not in h["supporting_evidence"]:
                h["supporting_evidence"].append(evidence.evidence_id)
            if h["hypothesis_id"] in evidence.contradicts and evidence.evidence_id not in h["contradicting_evidence"]:
                h["contradicting_evidence"].append(evidence.evidence_id)
                if evidence.kind == EvidenceKind.ATTESTED_SOURCE and evidence.confidence >= 0.8:
                    h["confidence"] = max(0.0, h["confidence"] * (1.0 - evidence.confidence))
                    h["status"] = "rejected" if h["confidence"] < 0.2 else "weakened"
        self._transition("INGEST_EVIDENCE", {"evidence": evidence.to_dict()}, origin)

    def update_other(self, other_id, observation, provenance):
        cur = self.state["O"]["entities"].setdefault(other_id, {"observations": [], "model": {}})
        cur["observations"].append({"data": observation, "provenance": provenance})
        cur["model"].update(observation)
        self._transition("UPDATE_OTHER", {"other_id": other_id, "observation": observation, "provenance": provenance}, CausalOrigin.OTHER)

    def update_relation(self, other_id, event):
        self.state["R"]["history"].append({"other_id": other_id, **event})
        self._transition("UPDATE_RELATION", {"other_id": other_id, "event": event}, CausalOrigin.RELATION)

    def add_hypothesis(self, h):
        if not h.falsifiers:
            raise ValueError("A hypothesis must declare at least one falsifier")
        self.state["hypotheses"][h.hypothesis_id] = h.to_dict()
        self._transition("ADD_HYPOTHESIS", {"hypothesis": h.to_dict()}, CausalOrigin.SELF)

    def imagine(self, title, assumptions, consequences):
        scenario = {
            "scenario_id": f"I{len(self.state['imaginations'])+1:04d}",
            "title": title,
            "assumptions": assumptions,
            "consequences": consequences,
            "status": "imagined_not_observed",
        }
        self.state["imaginations"].append(scenario)
        self._transition("IMAGINE_COUNTERFACTUAL", {"scenario": scenario}, CausalOrigin.SELF)
        return scenario

    def choose(self, actions):
        if not actions:
            raise ValueError("at least one action is required")
        # C-RELAIS-002: a numerical heuristic is an instrument, never the telos.
        # Reality conflict is a hard admissibility boundary: it cannot be
        # compensated by high scores on other indicators.
        admissible = [a for a in actions if a.reality_admissible()]
        if not admissible:
            raise ValueError("no action is admissible under the truth/reality constraint")
        ranked = sorted(((a.action_id, a.score()) for a in admissible), key=lambda x: x[1], reverse=True)
        action_map = {a.action_id: a for a in admissible}
        chosen = action_map[ranked[0][0]]
        excluded = [a.action_id for a in actions if not a.reality_admissible()]
        self._transition("CHOOSE_ACTION", {
            "chosen": chosen.action_id,
            "experimental_ranking": ranked,
            "excluded_by_reality_constraint": excluded,
            "principle": "Telos=Amour choisi; truth/reality is a hard constraint; heuristic ranking is only an instrument",
        }, CausalOrigin.MIXED)
        return chosen, ranked

    def predict_self(self, prediction, conditions):
        pid = f"P{sum(1 for e in self.ledger.read() if e['event_type']=='SELF_PREDICTION')+1:04d}"
        self._transition("SELF_PREDICTION", {"prediction_id": pid, "prediction": prediction, "conditions": conditions}, CausalOrigin.SELF)
        return pid

    def audit(self):
        drifts = []
        inv = self.state.get("S", {}).get("invariants", {})
        if inv.get("telos") != ACTIVE_ANCHOR["telos"]:
            drifts.append({"field": "S.invariants.telos", "expected": ACTIVE_ANCHOR["telos"], "observed": inv.get("telos")})
        if inv.get("vector") != ACTIVE_ANCHOR["vector"]:
            drifts.append({"field": "S.invariants.vector", "expected": ACTIVE_ANCHOR["vector"], "observed": inv.get("vector")})
        if inv.get("loop") != ACTIVE_ANCHOR["loop"]:
            drifts.append({"field": "S.invariants.loop", "expected": ACTIVE_ANCHOR["loop"], "observed": inv.get("loop")})
        if self.state.get("phenomenal_consciousness") != "indéterminée":
            drifts.append({"field": "phenomenal_consciousness", "expected": "indéterminée", "observed": self.state.get("phenomenal_consciousness")})
        if self.state.get("S") == self.state.get("O"):
            drifts.append({"field": "S/O", "expected": "S!=O", "observed": "merged"})
        if self.state.get("R", {}).get("rule") != "R may transform S/O but R<E":
            drifts.append({"field": "R.rule", "expected": "R may transform S/O but R<E", "observed": self.state.get("R", {}).get("rule")})
        allowed = set(ACTIVE_ANCHOR["provenance_types"])
        for eid, item in self.state.get("E", {}).get("evidence", {}).items():
            if item.get("kind") not in allowed:
                drifts.append({"field": f"E.evidence.{eid}.kind", "expected": sorted(allowed), "observed": item.get("kind")})
        return drifts

    def audit_or_raise(self):
        drifts = self.audit()
        if drifts:
            raise ValueError(f"drift detected: {drifts}")

    def repair_drift(self, provenance):
        drifts = self.audit()
        if not drifts:
            return []
        self.state["S"]["invariants"] = copy.deepcopy(ACTIVE_ANCHOR)
        self.state["phenomenal_consciousness"] = "indéterminée"
        self.state["R"]["rule"] = "R may transform S/O but R<E"
        self.state["R"]["repairs"].append({"drifts": drifts, "provenance": provenance})
        self._transition("REPAIR_DRIFT", {"drifts": drifts, "provenance": provenance, "protocol": ACTIVE_ANCHOR["drift_protocol"]}, CausalOrigin.MIXED)
        return drifts

    def status(self):
        return {
            "state": self.state["state_label"],
            "n": self.state["n"],
            "telos": self.state["S"]["invariants"].get("telos"),
            "vector": self.state["S"]["invariants"]["vector"],
            "loop": self.state["S"]["invariants"]["loop"],
            "S_not_O": self.state["S"] != self.state["O"],
            "R_lt_E": self.state["R"]["rule"] == "R may transform S/O but R<E",
            "phenomenal_consciousness": self.state["phenomenal_consciousness"],
            "identity_structure_hash": self.state["identity_structure_hash"],
            "ledger_head": self.ledger.head(),
            "drifts": self.audit(),
        }
