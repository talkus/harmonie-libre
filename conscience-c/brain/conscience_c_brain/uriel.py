"""Situated, reference-only projection of recorded Gabriel examinations.

Uriel is an architectural analogy, not an oracle or an outside observer.
Projection scales do not replace source scales. Shared origins, unresolved
objections and UNKNOWN survive every explicit scale bridge. Reading creates
no event, repairs nothing and grants no authority or independent validation.
"""
from __future__ import annotations

from dataclasses import asdict, replace
from datetime import datetime, timezone
import json

from ._state_model import _stable_hash
from .checkpoint_integrity import equal_json, verified_history
from .gabriel import _context, _instant
from .multiscale_coherence import (
    Scale, ScaleReceipt, ScaleBridge, EvidenceStatus, CouplingRecord,
    DistinctionRecord, RelationRecord, UnknownBoundary, Contestation,
    validate_multiscale,
)
from .teshuvah import _text, _texts


URIEL_CRITERIA_VERSION = "1.0.0"
_PROPERTY = "uriel:situated_trace_projection"
_TRIGGERS = ("selected_reports_changed", "source_inputs_or_validity_changed",
             "objection_correction_or_repair_changed", "reader_context_changed",
             "projection_criteria_changed")
_LIMITS = ("selection_is_not_the_whole_flow", "declared_reader_is_not_authenticated",
           "structural_coherence_is_not_semantic_truth")
_CRITERIA = (
    "resolve sources from recorded Gabriel event references at an unchanged local boundary",
    "keep source coordinates distinct from projection coordinates",
    "retain historical evidence and diagnose current applicability separately",
    "union source ancestry, UNKNOWN and objections without independent witness inflation",
    "declare omitted detail; do not promote a situated map to the flow itself",
    "reopen on relevant inputs, context, objection, validity or criteria changes",
)


def _unique(values):
    return tuple(sorted(set(values)))


def _records(items, field, id_field):
    """Retain distinct records; reject competing meanings for the same local id."""
    by_id = {}
    for item in items:
        for record in getattr(item, field):
            key = getattr(record, id_field)
            if key in by_id and by_id[key] != record:
                raise ValueError("conflicting projected record: " + key)
            by_id[key] = record
    return tuple(by_id[key] for key in sorted(by_id))


def _evidence_summary(statuses):
    # Compact evidence flag only. Literal local statuses remain in sources and
    # the scale reports; TRIGGERED does not erase an UNKNOWN or an objection.
    statuses = set(statuses)
    return next(status for status in (EvidenceStatus.INVALID_DATA, EvidenceStatus.TRIGGERED,
                 EvidenceStatus.INSUFFICIENT_DATA, EvidenceStatus.NOT_TRIGGERED) if status in statuses)


def _receipt(receipt_id, scale, traces, origins, observer, scope, *,
             status=EvidenceStatus.INSUFFICIENT_DATA, unknowns=(), contestations=()):
    kappa, delta, rho = (f"{receipt_id}:{name}" for name in ("context", "distinction", "reading"))
    return ScaleReceipt(
        receipt_id=receipt_id, scale=scale,
        couplings=(CouplingRecord(kappa, traces),),
        distinctions=(DistinctionRecord(delta, (kappa,), traces),),
        relations=(RelationRecord(rho, (delta,), traces),),
        trace_refs=traces, origin_refs=origins, property_ref=_PROPERTY,
        property_version=URIEL_CRITERIA_VERSION, scope_ref=scope, observer_ref=observer,
        revision_triggers=_TRIGGERS, provenance_bundle_refs=(), evidence_status=status,
        unknowns=tuple(UnknownBoundary(f"{receipt_id}:unknown:{code}", (kappa,), code)
                       for code in _unique((*_LIMITS, *unknowns))),
        contestations=tuple(contestations),
    )


def _aggregate(receipt_id, scale, children, observer, scope):
    traces = _unique(ref for child in children for ref in child.trace_refs)
    origins = _unique(ref for child in children for ref in child.origin_refs)
    own = _receipt(receipt_id, scale, traces, origins, observer, scope,
                   status=_evidence_summary(child.evidence_status for child in children))
    items = (*children, own)
    return replace(own,
        couplings=_records(items, "couplings", "coupling_id"),
        distinctions=_records(items, "distinctions", "distinction_id"),
        relations=_records(items, "relations", "relation_id"),
        unknowns=_records(items, "unknowns", "unknown_id"),
        contestations=_records(items, "contestations", "contestation_id"),
        provenance_bundle_refs=_unique(ref for child in children for ref in child.provenance_bundle_refs))


def _bridge(child, parent):
    return ScaleBridge(
        bridge_id=f"{child.receipt_id}:to:{parent.receipt_id}",
        child_receipt_hash=child.digest(), parent_receipt_hash=parent.digest(),
        transform_ref=f"uriel:{URIEL_CRITERIA_VERSION}:union_without_authority",
        preserved_origin_refs=child.origin_refs,
        preserved_provenance_bundle_refs=child.provenance_bundle_refs,
        carried_unknown_ids=tuple(x.unknown_id for x in child.unknowns),
        carried_contestation_ids=tuple(x.contestation_id for x in child.contestations),
        carried_evidence_status=child.evidence_status,
    )


class UrielMixin:
    def _uriel_boundary(self):
        if self._write_blocked:
            raise ValueError("unfinished write; read-only projection requires explicit recovery")
        if not equal_json(self.state, self._last_committed_state):
            raise ValueError("uncommitted state cannot be projected as recorded reality")
        self.audit_or_raise()
        persisted, token = self._store.inspect()
        if token != self._snapshot_token or not equal_json(persisted, self.state):
            raise ValueError("snapshot boundary changed; reload before reading")
        return token, persisted["n"], persisted["last_event_hash"]

    def _uriel_evidence(self, report, rows):
        evidence = []
        for item in report["evaluated_evidence"]:
            data = item["evidence"]
            evidence.append({"evidence_id": item["evidence_id"], "kind": data["kind"],
                "source_ref": data.get("source_ref"), "trace_ref": item["trace_ref"],
                "scope": data.get("scope"), "subject_ref": data.get("subject_ref"),
                "stance": data.get("stance"), "exclusion_reasons": item["exclusion_reasons"],
                "lineage": [{"evidence_id": x["evidence_id"], "kind": x["kind"],
                             "source_ref": x.get("source_ref"),
                             "trace_ref": self._ingest_hash(rows, x["evidence_id"])}
                            for x in item["lineage"]]})
        return evidence

    def _uriel_source(self, ref, rows, at):
        view = self.gabriel_report(ref)
        report = view["report"]
        current = self.gabriel_examine(report["claim_id"], **_context(report), at_time=at)
        stale = current["input_digest"] != report["input_digest"]
        unknowns = list(report["unknowns"])
        if stale:
            unknowns.append("stale_report_requires_reexamination")
            unknowns.extend(f"current:{code}" for code in current["unknowns"])
        if view["status"] in {"corrected", "superseded"}:
            unknowns.append("historical_report_not_current")
        repairs = []
        for tid in view["repair_refs"]:
            cycle = self.state["teshuvah"]["cycles"][tid]
            # Do not call teshuvah()/teshuvah_trace(): their compatibility state
            # initializer can mutate a legacy snapshot while merely reading it.
            repairs.append({"teshuvah_id": tid, "phase": cycle["phase"],
                "verification_status": cycle["verification"]["status"],
                "trace_refs": [r["event_hash"] for r in rows if r["payload"].get("teshuvah_id") == tid],
                "independent_validation": False, "execution_authority": False})
        evidence = self._uriel_evidence(report, rows)
        current_evidence = self._uriel_evidence(current, rows)
        def origins(items):
            return list(_unique(ancestor["source_ref"] or ancestor["trace_ref"]
                                for item in items for ancestor in item["lineage"])) or [ref]
        historical_origins, current_origins = origins(evidence), origins(current_evidence)
        traces = _unique((ref, *report["trace_refs"], *current["trace_refs"], *view["contestation_history_refs"],
                         *view["correction_refs"], *view["superseding_refs"],
                         *(trace for repair in repairs for trace in repair["trace_refs"])))
        return {
            "report_ref": ref, "claim_id": report["claim_id"], **_context(report),
            "criteria_version": report["criteria_version"], "observed_at": report["observed_at"],
            "input_digest": report["input_digest"], "current_input_digest": current["input_digest"],
            "verdict": report["verdict"], "status": view["status"], "stale": stale,
            "evidence_status": report["evidence_status"],
            "current_evidence_status": current["evidence_status"],
            "projection_evidence_status": _evidence_summary((EvidenceStatus(report["evidence_status"]),
                                                            EvidenceStatus(current["evidence_status"]))).value,
            "current_examination": {"evidence": current_evidence, **{key: current[key] for key in (
                "verdict", "evidence_status", "unknowns", "support_refs", "contradiction_refs",
                "excluded_evidence", "trace_refs", "criteria_version")}},
            "unknowns": list(_unique(unknowns)), "evidence": evidence,
            "contestation_refs": view["contestation_refs"],
            "contestation_history_refs": view["contestation_history_refs"],
            "correction_refs": view["correction_refs"], "superseding_refs": view["superseding_refs"],
            "repairs": repairs, "trace_refs": list(traces),
            "historical_origin_refs": historical_origins, "current_origin_refs": current_origins,
            "origin_refs": list(_unique((*historical_origins, *current_origins))),
            "independent_validation": False, "execution_authority": False,
        }

    def uriel_read(self, report_refs, *, observer_ref, scope_ref, at_time=None):
        """Project selected recorded reports at four scales, with no side effects.

        Scope and reader describe this projection, not source diagnostics.
        At one shared timezone-aware instant, current applicability is compared
        with historical inputs. Wall-clock passage alone creates no new content
        identity. Use at_time for reproducible validity checks across expiry.
        References-only output is data minimization, not access control.
        """
        refs = _texts(report_refs, "report_refs")
        if len(refs) != len(set(refs)):
            raise ValueError("duplicate report_refs")
        observer_ref, scope_ref = _text(observer_ref, "observer_ref"), _text(scope_ref, "scope_ref")
        at = (_instant(at_time) if at_time is not None else datetime.now(timezone.utc)).isoformat()
        boundary = self._uriel_boundary()
        rows = verified_history(self)
        sources = [self._uriel_source(ref, rows, at) for ref in sorted(refs)]
        claims = {source["claim_id"] for source in sources}
        recorded_claims = {row["event_hash"]: row["payload"]["report"]["claim_id"]
                          for row in rows if row["event_type"] == "GABRIEL_EXAMINED"}
        omitted = sorted(ref for ref, claim in recorded_claims.items() if claim in claims and ref not in refs)
        for source in sources:
            source["omitted_same_claim_report_refs"] = [ref for ref in omitted
                                                       if recorded_claims[ref] == source["claim_id"]]
        all_traces = _unique((*omitted, *(ref for source in sources for ref in source["trace_refs"])))
        all_origins = _unique(ref for source in sources for ref in source["origin_refs"])
        # Stable contract target avoids circular content hashes (child hashes
        # contain parent hashes). Each objection retains its original journal
        # target below; the projected target questions this contract's reading
        # of that exact assertion, never silently retargeting the source event.
        contract = _receipt("uriel:reader-contract", Scale.META, all_traces, all_origins,
                            observer_ref, scope_ref)
        targets = {r["event_hash"]: r["payload"]["report_ref"] for r in rows
                   if r["event_type"] == "GABRIEL_CONTESTED"}
        groups = {}
        for source in sources:
            ref = source["report_ref"]
            objections = [Contestation(f"{ref}:projection:{c}", contract.digest(),
                          f"gabriel-report:{targets[c]}#claim:{source['claim_id']}", (c,))
                          for c in source["contestation_refs"]]
            if source["verdict"] == "REVIEW_REQUIRED":
                objections.append(Contestation(f"{ref}:projection:claim-review", contract.digest(),
                                               f"gabriel-report:{ref}#claim:{source['claim_id']}", (ref,)))
            if source["stale"] and source["current_examination"]["verdict"] == "REVIEW_REQUIRED":
                objections.append(Contestation(f"{ref}:projection:current-claim-review", contract.digest(),
                    f"gabriel-current:{source['current_input_digest']}#claim:{source['claim_id']}",
                    tuple(source["current_examination"]["trace_refs"])))
            unknowns = list(source["unknowns"])
            if source["omitted_same_claim_report_refs"]:
                unknowns.append("same_claim_reports_outside_selection")
            leaf = _receipt(f"uriel:micro:{ref}", Scale.MICRO, tuple(source["trace_refs"]),
                tuple(source["origin_refs"]), observer_ref, scope_ref,
                status=EvidenceStatus(source["projection_evidence_status"]),
                unknowns=unknowns, contestations=objections)
            key = (source["claim_id"], source["scope_ref"], source["subject_ref"])
            groups.setdefault(key, []).append(leaf)
        mesos = [_aggregate("uriel:meso:" + _stable_hash(key), Scale.MESO, children, observer_ref, scope_ref)
                 for key, children in sorted(groups.items(), key=lambda pair: _stable_hash(pair[0]))]
        macro = _aggregate("uriel:macro:selection", Scale.MACRO, mesos, observer_ref, scope_ref)
        meta = _aggregate("uriel:meta:projection", Scale.META, (macro, contract), observer_ref, scope_ref)
        macro = replace(macro, parent_receipt_hash=meta.digest())
        mesos = [replace(item, parent_receipt_hash=macro.digest()) for item in mesos]
        receipts, bridges = [], []
        ordered_groups = sorted(groups.items(), key=lambda pair: _stable_hash(pair[0]))
        for meso, (_, children) in zip(mesos, ordered_groups):
            for child in children:
                child = replace(child, parent_receipt_hash=meso.digest())
                receipts.append(child)
                bridges.append(_bridge(child, meso))
            bridges.append(_bridge(meso, macro))
        bridges.append(_bridge(macro, meta))
        receipts.extend((*mesos, macro, meta, contract))
        losses = [{"report_ref": source["report_ref"],
                   "omitted_fields": ["claim.statement", "evidence.content", "objection.reason", "repair.details"],
                   "justification_ref": f"uriel:{URIEL_CRITERIA_VERSION}:references_only"}
                  for source in sources]
        view = {
            "criteria_version": URIEL_CRITERIA_VERSION, "observer_ref": observer_ref, "scope_ref": scope_ref,
            "criteria": list(_CRITERIA),
            "time_query": {"mode": "explicit" if at_time is not None else "current_applicability",
                           "at_time": at if at_time is not None else None},
            "projection_mode": "references_only", "sources": sources,
            "ledger_boundary": {"state": self.state["state_label"], "event_hash": boundary[2],
                                "snapshot_hash": boundary[0]},
            "coverage": {"selected_report_refs": sorted(refs), "omitted_same_claim_report_refs": omitted,
                         "complete_flow_observation": False},
            "source_contestation_targets": {c: targets[c] for c in sorted({ref for source in sources
                                                    for ref in source["contestation_history_refs"]})},
            "declared_losses": losses,
            "receipts": [{**item.canonical_payload(), "receipt_hash": item.digest()} for item in receipts],
            "bridges": [asdict(item) for item in bridges],
            "validation": asdict(validate_multiscale(receipts, bridges, require_explicit_bridges=True)),
            "limits": list(_LIMITS), "revision_triggers": list(_TRIGGERS),
            "independent_validation": False, "execution_authority": False,
        }
        # Boundary must stay fixed through all source resolution and projection.
        if self._uriel_boundary() != boundary:
            raise ValueError("snapshot boundary changed during projection")
        view["projection_state_ref"] = "uriel-state:" + _stable_hash({
            key: value for key, value in view.items() if key not in {"ledger_boundary", "time_query"}})
        view["reading_ref"] = "uriel:" + _stable_hash(view)
        # Own all output containers and return only JSON-native values.
        return json.loads(json.dumps(view, ensure_ascii=False, allow_nan=False))
