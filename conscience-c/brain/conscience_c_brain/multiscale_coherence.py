"""Candidate multi-scale structural coherence primitives.

This module is deliberately epistemic, not an authorization engine.

Runtime motif:
    kappa -> delta -> rho -> tau -> UNKNOWN -> kappa'

The same validation structure can be instantiated at micro, meso, macro,
and meta scales. Structural self-similarity does not imply that conclusions,
authority, permissions, or evidence weight propagate across scales.
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


_SCALE_RANK = {
    Scale.MICRO: 0,
    Scale.MESO: 1,
    Scale.MACRO: 2,
    Scale.META: 3,
}


class CoherenceStatus(str, Enum):
    CANDIDATE_OK = "CANDIDATE_OK"
    PARTIAL = "PARTIAL"
    INDETERMINATE = "INDETERMINATE"
    CONTESTED = "CONTESTED"


class EvidenceStatus(str, Enum):
    TRIGGERED = "TRIGGERED"
    NOT_TRIGGERED = "NOT_TRIGGERED"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INVALID_DATA = "INVALID_DATA"


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
    evidence_status: EvidenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    has_unknown: bool = False
    has_contestation: bool = False
    external_witness_declared: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class ScaleReceipt:
    receipt_id: str
    scale: Scale
    couplings: tuple[CouplingRecord, ...]
    distinctions: tuple[DistinctionRecord, ...]
    relations: tuple[RelationRecord, ...]
    trace_refs: tuple[str, ...]
    origin_refs: tuple[str, ...]
    evidence_status: EvidenceStatus = EvidenceStatus.TRIGGERED
    unknowns: tuple[UnknownBoundary, ...] = ()
    contestations: tuple[Contestation, ...] = ()
    external_witness_refs: tuple[str, ...] = ()
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
            "origin_refs": list(self.origin_refs),
            "evidence_status": self.evidence_status.value,
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
            "external_witness_refs": list(self.external_witness_refs),
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
    """Validate one scale using the same structural rules used at every scale.

    CANDIDATE_OK means that this local structural contract passed. It is not
    an independent validation and never grants execution authority.
    """
    issues: list[ValidationIssue] = []
    trace_ids = set(receipt.trace_refs)
    coupling_ids = {x.coupling_id for x in receipt.couplings}
    distinction_ids = {x.distinction_id for x in receipt.distinctions}

    if not receipt.trace_refs:
        issues.append(ValidationIssue("MS_TRACE_REQUIRED", "scale has no local trace provenance"))

    if not receipt.origin_refs:
        issues.append(ValidationIssue("MS_ORIGIN_REQUIRED", "scale has no source-origin provenance"))
    elif len(set(receipt.origin_refs)) != len(receipt.origin_refs):
        issues.append(
            ValidationIssue(
                "MS_ORIGIN_DUPLICATE",
                "duplicate origin refs do not count as additional evidence",
            )
        )

    if receipt.evidence_status == EvidenceStatus.INVALID_DATA:
        issues.append(ValidationIssue("MS_INVALID_DATA", "evidence is explicitly marked invalid"))

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

    has_unknown = bool(receipt.unknowns) or receipt.evidence_status == EvidenceStatus.INSUFFICIENT_DATA
    has_contestation = bool(receipt.contestations)

    # Governance and epistemic uncertainty remain separately visible even
    # though a compact headline status is returned.
    if has_contestation:
        status = CoherenceStatus.CONTESTED
    elif has_unknown:
        status = CoherenceStatus.INDETERMINATE
    elif issues:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return ValidationReport(
        status=status,
        receipt_hash=receipt.digest(),
        evidence_status=receipt.evidence_status,
        issues=tuple(issues),
        has_unknown=has_unknown,
        has_contestation=has_contestation,
        external_witness_declared=bool(receipt.external_witness_refs),
        independent_validation=False,
        execution_authority=False,
    )


@dataclass(frozen=True)
class MultiscaleReport:
    status: CoherenceStatus
    scale_reports: tuple[ValidationReport, ...]
    issues: tuple[ValidationIssue, ...]
    has_unknown: bool = False
    has_contestation: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


def _cycle_nodes(receipts_by_hash: Mapping[str, ScaleReceipt]) -> set[str]:
    """Return receipt hashes involved in a parent-link cycle."""
    cycle_nodes: set[str] = set()

    for start in receipts_by_hash:
        path: list[str] = []
        index: dict[str, int] = {}
        current = start

        while current in receipts_by_hash:
            if current in index:
                cycle_nodes.update(path[index[current] :])
                break
            index[current] = len(path)
            path.append(current)
            parent = receipts_by_hash[current].parent_receipt_hash
            if not parent:
                break
            current = parent

    return cycle_nodes


def validate_multiscale(receipts: Sequence[ScaleReceipt]) -> MultiscaleReport:
    """Validate composition without collapsing local conclusions into one score.

    Multiple units per scale are allowed. A full composition needs all four
    scales, parent links move exactly one scale upward, source origins survive
    aggregation, and the parent graph must remain acyclic.
    """
    issues: list[ValidationIssue] = []
    reports = tuple(validate_scale_receipt(x) for x in receipts)

    hashes = [x.digest() for x in receipts]
    receipts_by_hash = {x.digest(): x for x in receipts}

    if len(set(hashes)) != len(hashes):
        issues.append(ValidationIssue("MS_DUPLICATE_RECEIPT", "duplicate operational receipts"))

    receipt_ids = [x.receipt_id for x in receipts]
    if len(set(receipt_ids)) != len(receipt_ids):
        issues.append(
            ValidationIssue(
                "MS_DUPLICATE_RECEIPT_ID",
                "one composition cannot contain competing versions of the same receipt_id",
            )
        )

    present_scales = {x.scale for x in receipts}
    for scale in Scale:
        if scale not in present_scales:
            issues.append(
                ValidationIssue(
                    "MS_SCALE_MISSING",
                    f"full multiscale composition is missing scale {scale.value}",
                )
            )

    for receipt in receipts:
        if receipt.scale == Scale.META and receipt.parent_receipt_hash:
            issues.append(
                ValidationIssue(
                    "MS_META_PARENT_FORBIDDEN",
                    f"meta receipt {receipt.receipt_id} cannot have a higher-scale parent",
                )
            )

        if receipt.parent_receipt_hash:
            parent = receipts_by_hash.get(receipt.parent_receipt_hash)
            if parent is None:
                issues.append(
                    ValidationIssue(
                        "MS_PARENT_UNKNOWN",
                        f"{receipt.receipt_id} cites a parent receipt not present in this composition",
                    )
                )
            else:
                if _SCALE_RANK[parent.scale] != _SCALE_RANK[receipt.scale] + 1:
                    issues.append(
                        ValidationIssue(
                            "MS_NON_ADJACENT_PARENT",
                            f"{receipt.receipt_id} ({receipt.scale.value}) must link only to the next scale, not {parent.scale.value}",
                        )
                    )

                missing_origins = set(receipt.origin_refs) - set(parent.origin_refs)
                if missing_origins:
                    issues.append(
                        ValidationIssue(
                            "MS_ORIGIN_NOT_PROPAGATED",
                            f"parent {parent.receipt_id} omits child origins: {sorted(missing_origins)}",
                        )
                    )

        for contestation in receipt.contestations:
            if contestation.target_receipt_hash not in receipts_by_hash:
                issues.append(
                    ValidationIssue(
                        "MS_CONTEST_TARGET_UNKNOWN",
                        f"{contestation.contestation_id} targets a receipt outside this composition",
                    )
                )

    cycle_nodes = _cycle_nodes(receipts_by_hash)
    if cycle_nodes:
        issues.append(
            ValidationIssue(
                "MS_PARENT_CYCLE",
                f"parent graph contains a cycle involving {len(cycle_nodes)} receipt(s)",
            )
        )

    has_contestation = any(x.has_contestation for x in reports)
    has_unknown = any(x.has_unknown for x in reports)

    if has_contestation:
        status = CoherenceStatus.CONTESTED
    elif has_unknown:
        status = CoherenceStatus.INDETERMINATE
    elif issues or any(x.status == CoherenceStatus.PARTIAL for x in reports):
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleReport(
        status=status,
        scale_reports=reports,
        issues=tuple(issues),
        has_unknown=has_unknown,
        has_contestation=has_contestation,
        independent_validation=False,
        execution_authority=False,
    )
