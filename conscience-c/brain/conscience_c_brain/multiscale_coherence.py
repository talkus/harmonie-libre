"""Candidate multi-scale structural coherence primitives.

This module is deliberately epistemic, not an authorization engine.

Runtime motif:
    kappa -> delta -> rho -> tau -> UNKNOWN -> kappa'

The same validation structure can be instantiated at micro, meso, macro,
and meta scales.  Structural self-similarity does not imply that conclusions,
authority, or permissions propagate across scales.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import hashlib
import json
from typing import Mapping, Sequence


class Scale(str, Enum):
    MICRO = "micro"
    MESO = "meso"
    MACRO = "macro"
    META = "meta"


class CoherenceStatus(str, Enum):
    CANDIDATE_OK = "CANDIDATE_OK"
    PARTIAL = "PARTIAL"
    INDETERMINATE = "INDETERMINATE"
    CONTESTED = "CONTESTED"


@dataclass(frozen=True)
class CouplingRecord:
    coupling_id: str
    trace_refs: tuple[str, ...]
    causal_status: str = "unestablished"
    causal_evidence_refs: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if self.causal_status not in {"unestablished", "supported", "contested"}:
            raise ValueError("invalid causal_status")
        if self.causal_status == "supported" and not self.causal_evidence_refs:
            raise ValueError("causal support requires explicit causal evidence")


@dataclass(frozen=True)
class DistinctionRecord:
    distinction_id: str
    coupling_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]


@dataclass(frozen=True)
class RelationRecord:
    relation_id: str
    distinction_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    status: str = "documented"


@dataclass(frozen=True)
class UnknownBoundary:
    unknown_id: str
    coupling_refs: tuple[str, ...]
    question: str
    missing_distinctions: tuple[str, ...] = ()


@dataclass(frozen=True)
class Contestation:
    contestation_id: str
    target_receipt_hash: str
    target_assertion_ref: str
    trace_refs: tuple[str, ...]


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class ValidationReport:
    status: CoherenceStatus
    receipt_hash: str
    issues: tuple[ValidationIssue, ...] = ()
    execution_authority: bool = False


@dataclass(frozen=True)
class ScaleReceipt:
    receipt_id: str
    scale: Scale
    couplings: tuple[CouplingRecord, ...]
    distinctions: tuple[DistinctionRecord, ...]
    relations: tuple[RelationRecord, ...]
    trace_refs: tuple[str, ...]
    unknowns: tuple[UnknownBoundary, ...] = ()
    contestations: tuple[Contestation, ...] = ()
    independent_witness_refs: tuple[str, ...] = ()
    parent_receipt_hash: str | None = None
    symbolic_labels: Mapping[str, str] = field(default_factory=dict)

    def canonical_payload(self) -> dict:
        """Operational payload.

        symbolic_labels are intentionally excluded: renaming a symbolic analogy
        must not change the operational receipt or confer authority.
        """
        return {
            "receipt_id": self.receipt_id,
            "scale": self.scale.value,
            "couplings": [
                {
                    "coupling_id": x.coupling_id,
                    "trace_refs": list(x.trace_refs),
                    "causal_status": x.causal_status,
                    "causal_evidence_refs": list(x.causal_evidence_refs),
                }
                for x in self.couplings
            ],
            "distinctions": [
                {
                    "distinction_id": x.distinction_id,
                    "coupling_refs": list(x.coupling_refs),
                    "trace_refs": list(x.trace_refs),
                }
                for x in self.distinctions
            ],
            "relations": [
                {
                    "relation_id": x.relation_id,
                    "distinction_refs": list(x.distinction_refs),
                    "trace_refs": list(x.trace_refs),
                    "status": x.status,
                }
                for x in self.relations
            ],
            "trace_refs": list(self.trace_refs),
            "unknowns": [
                {
                    "unknown_id": x.unknown_id,
                    "coupling_refs": list(x.coupling_refs),
                    "question": x.question,
                    "missing_distinctions": list(x.missing_distinctions),
                }
                for x in self.unknowns
            ],
            "contestations": [
                {
                    "contestation_id": x.contestation_id,
                    "target_receipt_hash": x.target_receipt_hash,
                    "target_assertion_ref": x.target_assertion_ref,
                    "trace_refs": list(x.trace_refs),
                }
                for x in self.contestations
            ],
            "independent_witness_refs": list(self.independent_witness_refs),
            "parent_receipt_hash": self.parent_receipt_hash,
        }

    def digest(self) -> str:
        raw = json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def _missing_refs(refs: Sequence[str], available: set[str]) -> set[str]:
    return set(refs) - available


def validate_scale_receipt(receipt: ScaleReceipt) -> ValidationReport:
    """Validate one scale using the same structural rules used at every scale."""
    issues: list[ValidationIssue] = []
    trace_ids = set(receipt.trace_refs)
    coupling_ids = {x.coupling_id for x in receipt.couplings}
    distinction_ids = {x.distinction_id for x in receipt.distinctions}

    if not receipt.trace_refs:
        issues.append(ValidationIssue("MS_TRACE_REQUIRED", "scale has no local trace provenance"))

    for coupling in receipt.couplings:
        if not coupling.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_KAPPA_TRACE_REQUIRED",
                    f"coupling {coupling.coupling_id} has no trace provenance",
                )
            )
        missing = _missing_refs(coupling.trace_refs, trace_ids)
        if missing:
            issues.append(
                ValidationIssue(
                    "MS_KAPPA_TRACE_UNKNOWN",
                    f"coupling {coupling.coupling_id} cites unknown traces: {sorted(missing)}",
                )
            )
        if coupling.causal_status == "supported":
            missing_causal = _missing_refs(coupling.causal_evidence_refs, trace_ids)
            if missing_causal:
                issues.append(
                    ValidationIssue(
                        "MS_CAUSAL_EVIDENCE_UNKNOWN",
                        f"coupling {coupling.coupling_id} cites unknown causal evidence: {sorted(missing_causal)}",
                    )
                )

    for distinction in receipt.distinctions:
        if not distinction.coupling_refs:
            issues.append(
                ValidationIssue(
                    "MS_DELTA_KAPPA_REQUIRED",
                    f"distinction {distinction.distinction_id} has no coupling provenance",
                )
            )
        missing_couplings = _missing_refs(distinction.coupling_refs, coupling_ids)
        if missing_couplings:
            issues.append(
                ValidationIssue(
                    "MS_DELTA_KAPPA_UNKNOWN",
                    f"distinction {distinction.distinction_id} cites unknown couplings: {sorted(missing_couplings)}",
                )
            )
        if not distinction.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_DELTA_TRACE_REQUIRED",
                    f"distinction {distinction.distinction_id} has no trace provenance",
                )
            )
        missing_traces = _missing_refs(distinction.trace_refs, trace_ids)
        if missing_traces:
            issues.append(
                ValidationIssue(
                    "MS_DELTA_TRACE_UNKNOWN",
                    f"distinction {distinction.distinction_id} cites unknown traces: {sorted(missing_traces)}",
                )
            )

    for relation in receipt.relations:
        missing_distinctions = _missing_refs(relation.distinction_refs, distinction_ids)
        if missing_distinctions:
            issues.append(
                ValidationIssue(
                    "MS_RHO_DELTA_UNKNOWN",
                    f"relation {relation.relation_id} cites unknown distinctions: {sorted(missing_distinctions)}",
                )
            )
        if not relation.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_RHO_TRACE_REQUIRED",
                    f"relation {relation.relation_id} has no trace provenance",
                )
            )
        missing_traces = _missing_refs(relation.trace_refs, trace_ids)
        if missing_traces:
            issues.append(
                ValidationIssue(
                    "MS_RHO_TRACE_UNKNOWN",
                    f"relation {relation.relation_id} cites unknown traces: {sorted(missing_traces)}",
                )
            )

    for unknown in receipt.unknowns:
        missing_couplings = _missing_refs(unknown.coupling_refs, coupling_ids)
        if missing_couplings:
            issues.append(
                ValidationIssue(
                    "MS_UNKNOWN_KAPPA_UNKNOWN",
                    f"UNKNOWN {unknown.unknown_id} cites unknown couplings: {sorted(missing_couplings)}",
                )
            )

    for contestation in receipt.contestations:
        if not contestation.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_CONTEST_TRACE_REQUIRED",
                    f"contestation {contestation.contestation_id} has no trace provenance",
                )
            )
        missing_traces = _missing_refs(contestation.trace_refs, trace_ids)
        if missing_traces:
            issues.append(
                ValidationIssue(
                    "MS_CONTEST_TRACE_UNKNOWN",
                    f"contestation {contestation.contestation_id} cites unknown traces: {sorted(missing_traces)}",
                )
            )

    if receipt.contestations:
        status = CoherenceStatus.CONTESTED
    elif receipt.unknowns:
        status = CoherenceStatus.INDETERMINATE
    elif issues or not receipt.independent_witness_refs:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    # Coherence evidence never grants execution authority.
    return ValidationReport(
        status=status,
        receipt_hash=receipt.digest(),
        issues=tuple(issues),
        execution_authority=False,
    )


@dataclass(frozen=True)
class MultiscaleReport:
    status: CoherenceStatus
    scale_reports: tuple[ValidationReport, ...]
    issues: tuple[ValidationIssue, ...]
    execution_authority: bool = False


def validate_multiscale(receipts: Sequence[ScaleReceipt]) -> MultiscaleReport:
    """Validate composition without collapsing local conclusions into one score."""
    issues: list[ValidationIssue] = []
    reports = tuple(validate_scale_receipt(x) for x in receipts)

    hashes = {x.digest() for x in receipts}
    if len(hashes) != len(receipts):
        issues.append(ValidationIssue("MS_DUPLICATE_RECEIPT", "duplicate operational receipts"))

    scales = [x.scale for x in receipts]
    if len(set(scales)) != len(scales):
        issues.append(ValidationIssue("MS_DUPLICATE_SCALE", "more than one receipt for the same scale"))

    for receipt in receipts:
        if receipt.parent_receipt_hash and receipt.parent_receipt_hash not in hashes:
            issues.append(
                ValidationIssue(
                    "MS_PARENT_UNKNOWN",
                    f"{receipt.receipt_id} cites a parent receipt not present in this composition",
                )
            )
        for contestation in receipt.contestations:
            if contestation.target_receipt_hash not in hashes:
                issues.append(
                    ValidationIssue(
                        "MS_CONTEST_TARGET_UNKNOWN",
                        f"{contestation.contestation_id} targets a receipt outside this composition",
                    )
                )

    statuses = {x.status for x in reports}
    if CoherenceStatus.CONTESTED in statuses:
        status = CoherenceStatus.CONTESTED
    elif CoherenceStatus.INDETERMINATE in statuses:
        status = CoherenceStatus.INDETERMINATE
    elif issues or CoherenceStatus.PARTIAL in statuses:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleReport(
        status=status,
        scale_reports=reports,
        issues=tuple(issues),
        execution_authority=False,
    )
