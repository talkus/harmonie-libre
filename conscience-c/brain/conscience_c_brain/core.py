"""Public brain with recoverable persistence around the existing state model.

The previous model is preserved byte-for-byte in _state_model.py. Its public
operations still call _transition; only the persistence boundary is replaced.
No ethical policy, evidence interpretation, or external operation is replayed.
"""
from __future__ import annotations

import copy
from pathlib import Path

from ._state_model import ConscienceCBrain as _StateModel
from ._state_model import ACTIVE_ANCHOR, _now, _stable_hash
from .ledger import AppendOnlyLedger
from .models import CandidateAction, CausalOrigin, Evidence, EvidenceKind
from .transition_store import TransitionStore, RecoveryRequired, atomic_write, snapshot_bytes, digest


class ConscienceCBrain(_StateModel):
    def __init__(self, root: Path):
        self.root = Path(root)
        self.state_path = self.root / "state.json"
        # Reading a damaged history must not silently recreate a missing journal.
        self.ledger = AppendOnlyLedger(self.root / "events.jsonl", create=False)
        self.state = {}
        self._store = TransitionStore(self.root)
        self._snapshot_token = None
        self._last_committed_state = {}
        self._write_blocked = False

    def _adopt(self, state, token):
        self.state = copy.deepcopy(state)
        self._last_committed_state = copy.deepcopy(state)
        self._snapshot_token = token
        self._write_blocked = False

    @classmethod
    def load_or_bootstrap(cls, root: Path):
        brain = cls(root)
        loaded = brain._store.load()
        if loaded is None:
            brain._bootstrap_once()
        else:
            brain._adopt(*loaded)
            brain._migrate_anchor_if_needed()
            brain.audit_or_raise()
        return brain

    def _load(self):
        loaded = self._store.load()
        if loaded is None:
            raise RecoveryRequired("no saved state to load")
        self._adopt(*loaded)

    def _save(self):
        """Private compatibility helper, NOT a journalled public transition.

        Kept for existing migration fixtures and explicit diagnostic edits.
        Normal operations use _transition. Direct state edits are not attested.
        """
        if self._write_blocked:
            raise RecoveryRequired("previous write failed; reload before continuing")
        with self._store._locked():
            if self._store.pending_path.exists():
                raise RecoveryRequired("unfinished transition; private save refused")
            data = snapshot_bytes(self.state)
            atomic_write(self.state_path, data)
        self._adopt(self.state, digest(data))

    def _bootstrap_once(self):
        structure = {key: ACTIVE_ANCHOR[key] for key in (
            "telos", "vector", "loop", "architecture", "constraints",
            "provenance_types", "drift_protocol")}
        state = {
            "state_label": "C(t_0)", "n": 0,
            "S": {"description": "functional self-model candidate",
                  "invariants": copy.deepcopy(ACTIVE_ANCHOR),
                  "uncertainty": {"phenomenal_consciousness": "indéterminée"}},
            "O": {"entities": {}},
            "R": {"history": [], "trust_calibration": {}, "repairs": [],
                  "rule": "R may transform S/O but R<E"},
            "E": {"evidence": {}, "beliefs": {}},
            "hypotheses": {}, "imaginations": [], "causal_history": [],
            "continuity_structure_hash": _stable_hash(structure),
            "phenomenal_consciousness": "indéterminée",
            "last_event_hash": "GENESIS",
        }
        try:
            committed, token, _ = self._store.commit(state, "BOOTSTRAP_T0", _now(),
                {"anchor": ACTIVE_ANCHOR, "continuity_structure_hash": state["continuity_structure_hash"]},
                None, "GENESIS")
        except BaseException:
            self._write_blocked = True
            raise
        self._adopt(committed, token)

    def _transition(self, event_type, payload, origin):
        if self._write_blocked:
            self.state = copy.deepcopy(self._last_committed_state)
            raise RecoveryRequired("previous write failed; reload before continuing")
        # Existing model methods have staged their changes in memory. Capture
        # the complete candidate; don't rerun those methods during recovery.
        candidate = copy.deepcopy(self.state)
        candidate["n"] += 1
        candidate["state_label"] = f"C(t_{candidate['n']})"
        candidate["causal_history"].append({"n": candidate["n"],
            "origin": origin.value, "event_type": event_type,
            "payload_digest": _stable_hash(payload)})
        try:
            committed, token, event = self._store.commit(candidate, event_type, _now(),
                {**payload, "origin": origin.value, "n": candidate["n"]},
                self._snapshot_token, self._last_committed_state["last_event_hash"])
        except BaseException:
            # A durable event may already exist: neither retry nor guess here.
            # Restart resolves its recorded intent, or requests explicit recovery.
            self.state = copy.deepcopy(self._last_committed_state)
            self._write_blocked = True
            raise
        self._adopt(committed, token)
        return event
