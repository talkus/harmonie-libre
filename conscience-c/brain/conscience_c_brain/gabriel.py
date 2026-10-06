"""Situated, bounded claim examination; reports never confer execution authority.

Gabriel is an architectural analogy. Its criteria are explicit and versioned,
not a truth oracle. Reports, objections and corrections are journal events.
Only the separately invoked repair handoff changes a claim's active status.
"""
from __future__ import annotations

import copy
from datetime import datetime, timezone

from ._state_model import _stable_hash
from .checkpoint_integrity import verified_history
from .models import CausalOrigin, EvidenceKind
from .multiscale_coherence import (
    Scale, ScaleReceipt, EvidenceStatus, CouplingRecord, DistinctionRecord,
    RelationRecord, UnknownBoundary, Contestation,
)
from .teshuvah import _text, _texts


GABRIEL_CRITERIA_VERSION = "1.0.0"
_CRITERIA = (
    "explicit claim link and stance required; a citation alone does not entail a claim",
    "exact declared scope and subject; unknown applicability stays unknown",
    "attested or consolidated evidence; provenance is not truth certification",
    "timezone-aware validity; malformed dates remain invalid data",
    "applicable contradiction or refuted basis requires review, not automatic replacement",
    "missing evidence is indeterminate; supported absence of a signal permits bounded HOLD",
)
_EVENTS = {"GABRIEL_EXAMINED", "GABRIEL_CONTESTED", "GABRIEL_CORRECTED"}
_OBSERVABLE = {EvidenceKind.ATTESTED_SOURCE.value, EvidenceKind.CONSOLIDATED_DERIVATION.value}
_TRIGGERS = ("new_relevant_evidence", "context_changed", "evidence_validity_changed",
             "criteria_changed", "contestation_or_correction")


def _instant(value):
    parsed = datetime.fromisoformat(_text(value, "datetime").replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("datetime must include a timezone")
    return parsed.astimezone(timezone.utc)


def _context(report):
    return {key: report[key] for key in ("scope_ref", "observer_ref", "subject_ref", "scale")}


class GabrielMixin:
    def classify_replay_event(self, row):
        if row.get("event_type") in _EVENTS:
            return "documentary_only"
        return super().classify_replay_event(row)

    def gabriel_examine(self, claim_id, *, scope_ref, observer_ref,
                        scale=Scale.MICRO, subject_ref=None, at_time=None):
        """Read-only: no state initialization, journal append or repair side effect."""
        _text(scope_ref, "scope_ref")
        _text(observer_ref, "observer_ref")
        if subject_ref is not None:
            _text(subject_ref, "subject_ref")
        scale = Scale(scale)
        at = _instant(at_time) if at_time is not None else datetime.now(timezone.utc)
        rows = verified_history(self)
        claim = self.state.get("teshuvah", {}).get("claims", {}).get(claim_id)
        if claim is None:
            raise ValueError(f"unknown claim_id: {claim_id}")
        evidence = self.state["E"]["evidence"]
        relevant = {eid: item for eid, item in evidence.items()
                    if item.get("claim_ref") == claim_id or eid in claim["facts"]}
        # Refuse unstaged caller edits instead of silently attesting them.
        committed = self._last_committed_state
        if (claim != committed.get("teshuvah", {}).get("claims", {}).get(claim_id)
                or evidence != committed["E"]["evidence"]):
            raise ValueError("uncommitted claim or evidence changes")
        traces = []
        for row in rows:
            payload = row["payload"]
            if ((row["event_type"] == "RECORD_CLAIM" and payload["claim"]["claim_id"] == claim_id)
                    or (row["event_type"] == "STATE_UPDATED" and payload["new_claim"]["claim_id"] == claim_id)
                    or (row["event_type"] == "TESHUVAH_REPAIR_APPLIED" and any(
                        c.get("replacement_claim_id") == claim_id
                        for c in payload["applied"]["corrections"]))):
                traces.append(row["event_hash"])
        if not traces:
            raise ValueError("claim has no recorded creation trace")
        recorded_hashes = {r["event_hash"] for r in rows}
        traces.extend(ref for ref in claim["facts"] if ref in recorded_hashes)
        support, contradictions, refuted, excluded, unknowns, evaluated = [], [], [], [], [], []
        invalid = False
        for eid, item in sorted(relevant.items()):
            trace = self._ingest_hash(rows, eid)
            if trace is None:
                raise ValueError(f"evidence {eid} has no recorded ingestion trace")
            traces.append(trace)
            reasons = []
            if item.get("scope") is None:
                reasons.append("scope_unknown")
            elif item["scope"] != scope_ref:
                reasons.append("scope_mismatch")
            if subject_ref is not None:
                if item.get("subject_ref") is None:
                    reasons.append("subject_unknown")
                elif item["subject_ref"] != subject_ref:
                    reasons.append("subject_mismatch")
            try:
                valid = _instant(item["valid_at"]) if item.get("valid_at") is not None else None
                expires = _instant(item["expires_at"]) if item.get("expires_at") is not None else None
                if valid and expires and valid > expires:
                    raise ValueError("inverted validity interval")
                if valid and at < valid:
                    reasons.append("not_yet_valid")
                if expires and at > expires:
                    reasons.append("expired")
            except (ValueError, TypeError):
                reasons.append("invalid_validity")
                invalid = True
            if item["kind"] not in _OBSERVABLE and item["kind"] != EvidenceKind.HISTORICAL_REFUTED.value:
                reasons.append("unassessed_evidence_kind")
            lineage = self.evidence_lineage(eid)
            for ancestor in lineage:
                ancestor_trace = self._ingest_hash(rows, ancestor["evidence_id"])
                if ancestor_trace is None:
                    raise ValueError("evidence ancestor has no recorded ingestion trace")
                traces.append(ancestor_trace)
                if (ancestor["evidence_id"] != eid
                        and ancestor["kind"] == EvidenceKind.HISTORICAL_REFUTED.value):
                    reasons.append("refuted_ancestor_requires_review")
            if item.get("claim_ref") != claim_id or item.get("stance") == "context":
                reasons.append("no_explicit_support_or_contradiction")
            entry = {"evidence_id": eid, "evidence": copy.deepcopy(item),
                     "trace_ref": trace, "lineage": lineage, "exclusion_reasons": reasons}
            evaluated.append(entry)
            if reasons:
                excluded.append({"evidence_id": eid, "reasons": reasons})
                definitely_outside = any(x in reasons for x in
                    ("scope_mismatch", "subject_mismatch", "not_yet_valid", "expired"))
                if not definitely_outside:
                    unknowns.append(f"applicability_or_support_unestablished:{eid}")
            if eid in claim["facts"] and item["kind"] == EvidenceKind.HISTORICAL_REFUTED.value:
                refuted.append(eid)
            elif not reasons:
                if item["kind"] == EvidenceKind.HISTORICAL_REFUTED.value:
                    unknowns.append(f"refuted_evidence_not_current:{eid}")
                elif item["stance"] == "supports":
                    support.append(eid)
                elif item["stance"] == "contradicts":
                    contradictions.append(eid)
        findings = []
        if contradictions:
            findings.append({"code": "applicable_contradiction", "evidence_refs": contradictions})
        if refuted:
            findings.append({"code": "refuted_basis", "evidence_refs": refuted})
        if not support:
            unknowns.append("no_explicit_applicable_support")
        if claim["status"] != "active":
            verdict = "NOT_APPLICABLE"
            findings.append({"code": "claim_not_active", "evidence_refs": []})
        elif findings:
            verdict = "REVIEW_REQUIRED"
        elif unknowns or invalid:
            verdict = "INDETERMINATE"
        else:
            verdict = "HOLD"
        evidence_status = ("INVALID_DATA" if invalid else "TRIGGERED" if findings
                           else "INSUFFICIENT_DATA" if unknowns else "NOT_TRIGGERED")
        basis = {
            "claim": copy.deepcopy(claim), "evaluated_evidence": evaluated,
            "scope_ref": scope_ref, "subject_ref": subject_ref,
            "observer_ref": observer_ref, "scale": scale.value,
            "criteria_version": GABRIEL_CRITERIA_VERSION, "criteria": list(_CRITERIA),
        }
        return {
            **basis, "claim_id": claim_id, "input_digest": _stable_hash(basis),
            "observed_at": at.isoformat(), "ledger_boundary": rows[-1]["event_hash"],
            "trace_refs": sorted(set(traces)), "verdict": verdict, "findings": findings,
            "support_refs": support, "contradiction_refs": contradictions,
            "excluded_evidence": excluded, "unknowns": sorted(set(unknowns)),
            "evidence_status": evidence_status, "revision_triggers": list(_TRIGGERS),
            "stop_condition": "one bounded examination; unchanged inputs do not append another report",
            "execution_authority": False, "independent_validation": False,
            "limits": ["declared evidence is not verified truth", "one claim and one declared context",
                       "no semantic entailment, external authentication or automatic repair"],
        }

    def gabriel_report(self, report_ref):
        """Resolve by recorded event hash, never by trusting a caller's report body."""
        rows = verified_history(self)
        reports = {r["event_hash"]: r for r in rows if r["event_type"] == "GABRIEL_EXAMINED"}
        if report_ref not in reports:
            raise ValueError("unknown Gabriel report reference")
        lineage = set()
        current = report_ref
        while current:
            if current in lineage or current not in reports:
                raise ValueError("invalid Gabriel report lineage")
            lineage.add(current)
            current = reports[current]["payload"]["report"].get("reexamines")
        # A new observer, context or scale must not hide an objection concerning
        # the same claim. Keep those objections until their target is corrected.
        claim_id = reports[report_ref]["payload"]["report"]["claim_id"]
        claim_reports = {ref for ref, row in reports.items()
                         if row["payload"]["report"]["claim_id"] == claim_id}
        corrections = [r for r in rows if r["event_type"] == "GABRIEL_CORRECTED"
                       and r["payload"]["report_ref"] in claim_reports]
        objections = [r for r in rows if r["event_type"] == "GABRIEL_CONTESTED"
                      and r["payload"]["report_ref"] in claim_reports]
        # A declared correction acknowledges earlier objections to that report;
        # their traces remain visible, and this is not independent verification.
        unresolved = [r["event_hash"] for r in objections if not any(
            c["payload"]["report_ref"] == r["payload"]["report_ref"] and c["seq"] > r["seq"]
            for c in corrections)]
        own_corrections = [r["event_hash"] for r in corrections if r["payload"]["report_ref"] == report_ref]
        superseding = [r["event_hash"] for r in reports.values()
                       if r["payload"]["report"].get("reexamines") == report_ref]
        repairs = [c["teshuvah_id"] for c in self.state.get("teshuvah", {}).get("cycles", {}).values()
                   if report_ref in c["origin"]["drift_events"]]
        status = ("corrected" if own_corrections else "superseded" if superseding
                  else "contested" if unresolved else "recorded")
        return {"report_ref": report_ref, "report": copy.deepcopy(reports[report_ref]["payload"]["report"]),
                "status": status, "contestation_refs": unresolved,
                "contestation_history_refs": [r["event_hash"] for r in objections],
                "correction_refs": [r["event_hash"] for r in corrections],
                "superseding_refs": superseding, "repair_refs": repairs}

    def record_gabriel_examination(self, claim_id, *, provenance, reexamines=None,
                                   revision_reason=None, **context):
        _text(provenance, "provenance")
        report = self.gabriel_examine(claim_id, **context)
        rows = verified_history(self)
        previous = None
        for row in reversed(rows):
            if row["event_type"] != "GABRIEL_EXAMINED":
                continue
            old = row["payload"]["report"]
            if old["claim_id"] == claim_id and old["scale"] == report["scale"]:
                previous = self.gabriel_report(row["event_hash"])
                break
        if reexamines is not None:
            if previous is None or reexamines != previous["report_ref"]:
                raise ValueError("reexamination must start from the latest report for this claim and scale")
            _text(revision_reason, "revision_reason")
        if previous and _context(previous["report"]) != _context(report):
            _text(revision_reason, "revision_reason for context change")
        if previous and previous["report"]["input_digest"] == report["input_digest"]:
            # An unchanged or challenged report stays stopped; correction must
            # not be laundered away by simply rerunning identical criteria.
            return previous
        report["reexamines"] = previous["report_ref"] if previous else None
        report["revision_reason"] = revision_reason or ("relevant_inputs_changed" if previous else "initial_examination")
        event = self._transition("GABRIEL_EXAMINED", {"report": report, "provenance": provenance}, CausalOrigin.SELF)
        return self.gabriel_report(event["event_hash"])

    def contest_gabriel(self, report_ref, *, reason, actor, provenance):
        self.gabriel_report(report_ref)
        payload = {"report_ref": report_ref, "reason": _text(reason, "reason"),
                   "actor": _text(actor, "actor"), "provenance": _text(provenance, "provenance")}
        return self._transition("GABRIEL_CONTESTED", payload, CausalOrigin.OTHER)

    def correct_gabriel(self, report_ref, *, reason, evidence_refs, actor, provenance):
        view = self.gabriel_report(report_ref)
        refs = _texts(evidence_refs, "evidence_refs")
        self._validate_claim_basis(refs)
        payload = {"report_ref": report_ref, "reason": _text(reason, "reason"),
                   "evidence_refs": refs, "actor": _text(actor, "actor"),
                   "provenance": _text(provenance, "provenance"),
                   "repair_refs_requiring_review": view["repair_refs"],
                   "independent_validation": False,
                   "status": "diagnosis_correction_declared_not_independently_verified"}
        event = self._transition("GABRIEL_CORRECTED", payload, CausalOrigin.MIXED)
        return {**payload, "event_hash": event["event_hash"]}

    def open_gabriel_repair(self, report_ref, *, requested_by, provenance):
        """Explicit local handoff; opens D only, never applies a replacement.

        The host must authorize this call. Actor/provenance strings are audit
        declarations, not authentication or permission credentials.
        """
        _text(requested_by, "requested_by")
        _text(provenance, "provenance")
        view = self.gabriel_report(report_ref)
        if view["status"] != "recorded":
            raise ValueError(f"Gabriel report is {view['status']}; review it before acting")
        if view["repair_refs"]:
            return self.teshuvah(view["repair_refs"][0])
        report = view["report"]
        current = self.gabriel_examine(report["claim_id"], **_context(report))
        if current["input_digest"] != report["input_digest"]:
            raise ValueError("stale Gabriel report; reexamine current inputs")
        if report["verdict"] != "REVIEW_REQUIRED":
            raise ValueError("only a review-required report can open repair")
        if self._open_cycles_for(report["claim_id"]):
            raise ValueError("existing repair must be reviewed instead of duplicated")
        drift_kind = "contradiction" if report["contradiction_refs"] else "reality_mismatch"
        return self.initiate_teshuvah(
            drift_kind, f"Gabriel review requested by {requested_by}; scope={report['scope_ref']}; "
            "stop after opening this single-claim review, then use the existing repair protocol.",
            provenance, claim_ids=[report["claim_id"]], drift_events=[report_ref])

    def gabriel_scale_receipt(self, report_ref):
        """Expose the same bounded evidence contract at any declared scale."""
        view = self.gabriel_report(report_ref)
        report = view["report"]
        traces = tuple(sorted(set([report_ref, *report["trace_refs"], *view["contestation_history_refs"],
                                   *view["correction_refs"], *view["superseding_refs"]])))
        kappa, delta, rho = (f"{report_ref}:{name}" for name in ("context", "finding", "review"))
        unknowns = list(report["unknowns"])
        if view["status"] in {"corrected", "superseded"}:
            unknowns.append("historical_report_not_current")
        current = self.gabriel_examine(report["claim_id"], **_context(report))
        if current["input_digest"] != report["input_digest"]:
            unknowns.append("stale_report_requires_reexamination")
        contestations = [Contestation(ref, report_ref, report["claim_id"], (ref,))
                        for ref in view["contestation_refs"]]
        if report["verdict"] == "REVIEW_REQUIRED":
            contestations.append(Contestation(f"{report_ref}:claim-review", report_ref,
                                              report["claim_id"], (report_ref,)))
        return ScaleReceipt(
            receipt_id=report_ref, scale=Scale(report["scale"]),
            couplings=(CouplingRecord(kappa, traces),),
            distinctions=(DistinctionRecord(delta, (kappa,), traces),),
            relations=(RelationRecord(rho, (delta,), traces),),
            trace_refs=traces,
            origin_refs=tuple(sorted({item["evidence"].get("source_ref") or item["trace_ref"]
                                      for item in report["evaluated_evidence"]} | {report["trace_refs"][0]})),
            property_ref="gabriel:bounded_claim_examination", property_version=report["criteria_version"],
            scope_ref=report["scope_ref"], observer_ref=report["observer_ref"],
            revision_triggers=tuple(report["revision_triggers"]),
            provenance_bundle_refs=(report_ref,), evidence_status=EvidenceStatus(report["evidence_status"]),
            unknowns=tuple(UnknownBoundary(f"{report_ref}:unknown:{i}", (kappa,), value)
                           for i, value in enumerate(unknowns)),
            contestations=tuple(contestations),
        )
