"""Record declared reviews without certifying their truth or independence.

The legacy validate_revalidation_item name remains callable, but its `resolved`
status means submission recorded ONLY. New callers use record_revalidation_review.
Historical rows and their original outcomes are never rewritten.
"""
from __future__ import annotations

import copy
from typing import Any

from .checkpoint_integrity import verified_history
from .models import CausalOrigin


_EVENT = "REVALIDATE_HISTORICAL_EVENT"  # Preserve the recorded event vocabulary.
_ITEM_REQUIRED = {"status", "event_hash", "event_type", "replay_class"}
_ITEM_ALLOWED = _ITEM_REQUIRED | {"required_action"}
_REPORT_REQUIRED = {"source_ref", "result"}
_REPORT_ALLOWED = _REPORT_REQUIRED | {"observed_at", "notes"}
_NOT_CHECKED = ["source_retrieval", "evidence_truth", "evidence_freshness",
                "reviewer_identity", "reviewer_independence", "canon_comparison"]


def _text(value: Any, field: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")


def _history(rows, historical_event_hash=None):
    """Project recorded reports; never reinterpret a legacy claim as verified."""
    known = {row["event_hash"] for row in rows}
    records = []
    for row in rows:
        if row["event_type"] != _EVENT:
            continue
        payload = row["payload"]
        target = payload.get("historical_event_hash")
        if historical_event_hash is not None and target != historical_event_hash:
            continue
        records.append({
            "event_hash": row["event_hash"], "timestamp": row["timestamp"],
            "historical_event_hash": target,
            "historical_event_found": isinstance(target, str) and target in known,
            "outcome": copy.deepcopy(payload.get("outcome")),
            "fresh_evidence": copy.deepcopy(payload.get("fresh_evidence")),
            "provenance": copy.deepcopy(payload.get("provenance")),
            "supersedes_revalidation_event_hash": payload.get("supersedes_revalidation_event_hash"),
            "recording_version": payload.get("recording_version", 1),
            "recording_status": ("recorded_not_verified" if payload.get("recording_version") == 2
                                 else "legacy_declaration_not_verified"),
            "verification_status": "not_performed",
            "automatic_replay_allowed": False,
        })
    return records


class RevalidationMixin:
    def classify_replay_event(self, row):
        if row.get("event_type") == _EVENT:
            # Re-reading a declaration must not become an automatic validation.
            return "documentary_only"
        return super().classify_replay_event(row)

    def revalidation_history(self, historical_event_hash=None):
        if historical_event_hash is not None:
            _text(historical_event_hash, "historical_event_hash")
        return _history(verified_history(self), historical_event_hash)

    def current_revalidation_view(self, historical_event_hash):
        history = self.revalidation_history(historical_event_hash)
        return copy.deepcopy(history[-1]) if history else None

    def record_revalidation_review(self, item, review, provenance):
        """Append a linked, declared review, not an authenticated verification.

        Accept only known external-review tasks. Canon checks need a separate
        implementation; neither a caller-selected class nor a supplied reference
        can perform them. Any rejection precedes state mutation and persistence.
        """
        if not isinstance(item, dict) or not _ITEM_REQUIRED <= set(item) or set(item) - _ITEM_ALLOWED:
            raise ValueError("invalid revalidation item fields")
        for name in _ITEM_REQUIRED:
            _text(item[name], name)
        if item["status"] != "pending":
            raise ValueError("only pending revalidation items can be recorded")
        if "required_action" in item:
            _text(item["required_action"], "required_action")
        _text(provenance, "provenance")
        if not isinstance(review, dict) or not _REPORT_REQUIRED <= set(review) or set(review) - _REPORT_ALLOWED:
            raise ValueError("review requires source_ref and result; only documented fields are accepted")
        for name, value in review.items():
            _text(value, f"review.{name}")

        rows = verified_history(self)
        matches = [row for row in rows if row["event_hash"] == item["event_hash"]]
        if len(matches) != 1:
            raise ValueError("historical event must be uniquely recorded in the verified journal")
        target = matches[0]
        replay_class = self.classify_replay_event(target)
        if item["event_type"] != target["event_type"] or item["replay_class"] != replay_class:
            raise ValueError("revalidation item differs from recorded event type or computed replay class")
        if replay_class != "requires_external_reverification":
            raise ValueError("this API records external review declarations only; no canon check or replay approval")

        prior = _history(rows, target["event_hash"])
        payload = {
            "recording_version": 2,
            "record_type": "declared_review",
            "historical_event_hash": target["event_hash"],
            "historical_event_type": target["event_type"],
            "replay_class": replay_class,
            "status": "recorded_not_verified",
            "outcome": "review_recorded_not_verified",
            "verification_status": "not_performed",
            "automatic_replay_allowed": False,
            "fresh_evidence": copy.deepcopy(review),  # Legacy field name, not a freshness claim.
            "provenance": provenance,
            "supersedes_revalidation_event_hash": prior[-1]["event_hash"] if prior else None,
            "checks_performed": ["journal_integrity", "recorded_event", "event_type", "replay_class", "report_shape"],
            "checks_not_performed": list(_NOT_CHECKED),
            "principle": "new verification is a new event; this event records a declaration, not verification; historical evidence and prior reviews are not rewritten",
        }
        event = self._transition(_EVENT, copy.deepcopy(payload), CausalOrigin.MIXED)
        result = copy.deepcopy(payload)
        result["review_event_hash"] = event["event_hash"]
        return result

    def validate_revalidation_item(self, item, fresh_evidence, provenance):
        """Compatibility adapter: resolved means recorded, NEVER proven true.

        Deprecated terminology is retained for existing clients. Use the explicit
        recording_status and verification_status, or record_revalidation_review.
        The stored event always says recorded_not_verified, never resolved.
        """
        result = self.record_revalidation_review(item, fresh_evidence, provenance)
        result["recording_status"] = result["status"]
        result["status"] = "resolved"
        result["legacy_status_semantics"] = "submission_recorded_only"
        result["event_hash"] = result["historical_event_hash"]
        result["event_type"] = result["historical_event_type"]
        return result
