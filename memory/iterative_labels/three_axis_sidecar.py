"""Three-axis label sidecar for WORM exports. Candidate, not connected to the WORM journal."""
from __future__ import annotations
import hashlib
import json

AXES = ("DOMAINE", "SENS", "STATUT")

def digest(record):
    data = json.dumps(record, sort_keys=True, ensure_ascii=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("ascii")).hexdigest()

class ClosedTaxonomyLabels:
    """Append-only *in-memory* sidecar; read-only with respect to source journal.

    The caller must supply the complete authorized taxonomies and the IDs of
    existing journal entries. This component never reads, alters or attests WORM.
    """
    def __init__(self, entry_ids, taxonomies):
        if set(taxonomies) != set(AXES):
            raise ValueError("all and only three axes are required")
        if not all(isinstance(values, (set, frozenset, tuple, list))
                   and len(values) > 0 for values in taxonomies.values()):
            raise ValueError("empty or invalid closed taxonomy")
        self.entry_ids = frozenset(str(i) for i in entry_ids)
        self.taxonomies = {k: frozenset(v) for k, v in taxonomies.items()}
        self.records = []

    def _view_heads(self):
        heads = {}
        for record in self.records:
            heads[(record["entry_id"], record["axis"])] = record["hash"]
        return heads

    def append(self, *, entry_id, axis, value, source_ref, lineage_id, actor,
               reason, previous_hash=None, evidence_checked=False):
        entry_id = str(entry_id)
        if entry_id not in self.entry_ids:
            raise ValueError("unknown source journal entry")
        if axis not in AXES or value not in self.taxonomies[axis]:
            raise ValueError("unknown axis or label: fail-closed")
        if not all(isinstance(v, str) and v.strip()
                   for v in (source_ref, lineage_id, actor, reason)):
            raise ValueError("source, lineage, actor and reason required")
        heads = self._view_heads()
        if heads.get((entry_id, axis)) != previous_hash:
            raise ValueError("stale prior axis hash")
        record = dict(entry_id=entry_id, axis=axis, value=value,
                      source_ref=source_ref, lineage_id=lineage_id,
                      actor=actor, reason=reason, previous_hash=previous_hash,
                      previous_global_hash=self.records[-1]["hash"] if self.records else None,
                      sequence=len(self.records)+1, evidence_checked=bool(evidence_checked))
        record["hash"] = digest(record)
        self.records.append(record)
        return dict(record)

    def current(self, entry_id):
        entry_id = str(entry_id)
        history = [dict(r) for r in self.records if r["entry_id"] == entry_id]
        latest = {}
        for r in history:
            latest[r["axis"]] = r["value"]
        return dict(entry_id=entry_id, labels=latest, history=history,
                    lineage_count=len({r["lineage_id"] for r in history}),
                    historical_error_preserved=len(history) > len(latest),
                    source_journal_verified=False, automatic_authority=False)

    def audit(self):
        global_head = None
        heads = {}
        for position, original in enumerate(self.records, 1):
            if not isinstance(original, dict) or "hash" not in original:
                return False
            record = dict(original)
            hash_seen = record.pop("hash")
            entry = record.get("entry_id")
            axis = record.get("axis")
            if (entry not in self.entry_ids or axis not in AXES or
                record.get("value") not in self.taxonomies[axis] or
                record.get("sequence") != position or
                record.get("previous_global_hash") != global_head or
                record.get("previous_hash") != heads.get((entry, axis)) or
                digest(record) != hash_seen):
                return False
            global_head = hash_seen
            heads[(entry, axis)] = hash_seen
        return True

    def export_jsonl(self):
        if not self.audit():
            raise ValueError("integrity check failed")
        return "".join(json.dumps(r, sort_keys=True, ensure_ascii=True) + "\n"
                       for r in self.records)
