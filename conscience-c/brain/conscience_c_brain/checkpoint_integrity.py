"""Validate checkpoints against a verified local journal, not self-supplied hashes.

This is NOT a signature, an independent attestation, or a full state replay.
The caller must keep the local journal and snapshot under trusted, single-writer
control. Historical bytes and their legacy hash encoding are not rewritten.
"""
from __future__ import annotations

import copy
import json
from typing import Any

from .ledger import _hash


RECEIPT_FIELDS = frozenset({
    "receipt_id", "label", "state", "checkpoint_hash",
    "continuity_structure_hash", "ledger_boundary", "checkpoint",
})
RECEIPT_METADATA = frozenset({"receipt_event_hash", "post_receipt_state"})


def equal_json(left: Any, right: Any) -> bool:
    """Compare complete JSON values without Python's True == 1 shortcut."""
    options = dict(ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return json.dumps(left, **options) == json.dumps(right, **options)


def verified_history(brain: Any) -> list[dict[str, Any]]:
    """Read once, verify the chain and require matching current state pointers."""
    rows = brain.ledger.read_verified()
    if not rows or rows[0]["event_type"] != "BOOTSTRAP_T0":
        raise ValueError("missing bootstrap boundary")
    for index, row in enumerate(rows[1:], 1):
        n = row["payload"].get("n")
        if type(n) is not int or n != index or row["event_type"] == "BOOTSTRAP_T0":
            raise ValueError("invalid transition sequence in checkpoint history")
    n = brain.state.get("n")
    if type(n) is not int or n != len(rows) - 1:
        raise ValueError("snapshot/ledger transition count mismatch")
    if brain.state.get("state_label") != f"C(t_{n})":
        raise ValueError("snapshot state label mismatch")
    if brain.state.get("last_event_hash") != rows[-1]["event_hash"]:
        raise ValueError("snapshot/ledger head mismatch")
    return rows


def validate_index(n: Any, current_n: int) -> None:
    if type(n) is not int or not 0 <= n <= current_n:
        raise ValueError("checkpoint index out of range")


def resolve_recorded_receipt(
    receipt: Any, rows: list[dict[str, Any]]
) -> tuple[dict[str, Any], int]:
    """Return the recorded receipt and its row index, or reject it.

    rows MUST come from read_verified()/verified_history(). A hash of the
    supplied checkpoint and the existence of its boundary alone are insufficient.
    Both original stored receipts and enriched return values remain accepted.
    """
    if not isinstance(receipt, dict):
        raise ValueError("receipt must be an object")
    keys = set(receipt)
    if not RECEIPT_FIELDS <= keys or keys - (RECEIPT_FIELDS | RECEIPT_METADATA):
        raise ValueError("invalid receipt fields")
    if not isinstance(receipt["receipt_id"], str) or not receipt["receipt_id"]:
        raise ValueError("invalid receipt identifier")
    candidates = []
    for index, row in enumerate(rows):
        stored = row["payload"].get("receipt")
        if (row["event_type"] == "CHECKPOINT_RECEIPT"
                and isinstance(stored, dict)
                and stored.get("receipt_id") == receipt["receipt_id"]):
            candidates.append((index, row, stored))
    if len(candidates) != 1:
        raise ValueError("receipt not uniquely recorded in this ledger")
    index, row, stored = candidates[0]
    submitted = {key: receipt[key] for key in RECEIPT_FIELDS}
    if set(stored) != RECEIPT_FIELDS or not equal_json(submitted, stored):
        raise ValueError("receipt differs from the recorded content")
    checkpoint = stored["checkpoint"]
    if not isinstance(checkpoint, dict):
        raise ValueError("invalid captured checkpoint")
    if index < 1 or type(row["payload"].get("n")) is not int or row["payload"]["n"] != index:
        raise ValueError("invalid receipt transition")
    if (stored["state"] != f"C(t_{index - 1})"
            or stored["state"] != checkpoint.get("state")):
        raise ValueError("captured state does not match receipt transition")
    if (stored["ledger_boundary"] != rows[index - 1]["event_hash"]
            or stored["ledger_boundary"] != row["prev_hash"]
            or stored["ledger_boundary"] != checkpoint.get("ledger_head")):
        raise ValueError("receipt is not bound to its immediately preceding boundary")
    if stored["continuity_structure_hash"] != checkpoint.get("continuity_structure_hash"):
        raise ValueError("receipt continuity hash mismatch")
    if stored["checkpoint_hash"] != _hash(checkpoint):
        raise ValueError("captured checkpoint hash mismatch")
    if "receipt_event_hash" in receipt and receipt["receipt_event_hash"] != row["event_hash"]:
        raise ValueError("receipt event metadata mismatch")
    if "post_receipt_state" in receipt and receipt["post_receipt_state"] != f"C(t_{index})":
        raise ValueError("receipt state metadata mismatch")
    return copy.deepcopy(stored), index
