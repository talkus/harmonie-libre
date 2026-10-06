"""Candidate multi-scale structural coherence layer for Conscience C.

This module operationalizes the same inspectable motif at every scale:

    kappa -> delta -> rho -> tau -> UNKNOWN -> next kappa

It is deliberately conservative:
- coupling is association/interaction, never causality by declaration;
- every distinction cites couplings and sources;
- every relation cites distinctions;
- traces are append-only references;
- UNKNOWN is an explicit frontier, not permission;
- child contradictions must remain visible to parents;
- authority is never inherited automatically across scales;
- reports remain dimensional and never collapse into one scalar score.

This is an analytical candidate. It does not modify E, prove consciousness, or
promote an interpretation to attested truth.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Iterable, List, Tuple


class Scale(str, Enum):
    MICRO = "micro"
    MESO = "meso"
    MACRO = "macro"
    META = "meta"


_SCALE_ORDER = {
    Scale.MICRO: 0,
    Scale.MESO: 1,
    Scale.MACRO: 2,
    Scale.META: 3,
}


class CoherenceVerdict(str, Enum):
    FAIL = "FAIL"
    PARTIAL = "PARTIEL"
    META_THRESHOLD_ATTAINED = "META_THRESHOLD_ATTAINED"
    INDETERMINATE = "INDETERMINATE"


@dataclass(frozen=True)
class Coupling:
    coupling_id: str
    scale: Scale
    participants: Tuple[str, ...]
    source_refs: Tuple[str, ...]
    interpretation: str = "association_not_causality"


@dataclass(frozen=True)
class Distinction:
    distinction_id: str
    scale: Scale
    label: str
    coupling_refs: Tuple[str, ...]
    source_refs: Tuple[str, ...]


@dataclass(frozen=True)
class Relation:
    relation_id: str
    scale: Scale
    label: str
    distinction_refs: Tuple[str, ...]
    source_refs: Tuple[str, ...]


@dataclass(frozen=True)
class Trace:
    trace_id: str
    scale: Scale
    source_ref: str
    append_only: bool = True


@dataclass(frozen=True)
class UnknownFrontier:
    coupling_refs: Tuple[str, ...] = ()
    missing_distinctions: Tuple[str, ...] = ()
    reason: str = ""


@dataclass(frozen=True)
class Contradiction:
    contradiction_id: str
    origin_scale: Scale
    origin_unit_id: str
    claim: str
    source_refs: Tuple[str, ...]


@dataclass(frozen=True)
class LiftedContradiction:
    contradiction_id: str
    origin_scale: Scale
    origin_unit_id: str
    source_refs: Tuple[str, ...]


@dataclass(frozen=True)
class ScaleReceipt:
    unit_id: str
    scale: Scale
    couplings: Tuple[Coupling, ...] = ()
    distinctions: Tuple[Distinction, ...] = ()
    relations: Tuple[Relation, ...] = ()
    traces: Tuple[Trace, ...] = ()
    unknown: UnknownFrontier = field(default_factory=UnknownFrontier)
    child_unit_ids: Tuple[str, ...] = ()
    local_contradictions: Tuple[Contradiction, ...] = ()
    lifted_contradictions: Tuple[LiftedContradiction, ...] = ()
    authority_inherited: bool = False


@dataclass(frozen=True)
class ScaleAssessment:
    unit_id: str
    scale: Scale
    verdict: CoherenceVerdict
    issues: Tuple[str, ...]
    dimensions: Dict[str, int]


@dataclass(frozen=True)
class MultiScaleReport:
    assessments: Tuple[ScaleAssessment, ...]
    cross_scale_issues: Tuple[str, ...]
    overall: CoherenceVerdict

    def by_scale(self) -> Dict[Scale, Tuple[ScaleAssessment, ...]]:
        grouped: Dict[Scale, List[ScaleAssessment]] = {s: [] for s in Scale}
        for item in self.assessments:
            grouped[item.scale].append(item)
        return {scale: tuple(items) for scale, items in grouped.items()}


def _ids(items: Iterable[object], attr: str) -> set[str]:
    return {getattr(item, attr) for item in items}


def assess_receipt(receipt: ScaleReceipt) -> ScaleAssessment:
    """Validate one scale without borrowing truth or authority from another."""
    issues: List[str] = []
    coupling_ids = _ids(receipt.couplings, "coupling_id")
    distinction_ids = _ids(receipt.distinctions, "distinction_id")

    for coupling in receipt.couplings:
        if coupling.scale != receipt.scale:
            issues.append(f"coupling {coupling.coupling_id} has wrong scale")
        if not coupling.participants:
            issues.append(f"coupling {coupling.coupling_id} has no participants")
        if not coupling.source_refs:
            issues.append(f"coupling {coupling.coupling_id} has no provenance")
        if coupling.interpretation != "association_not_causality":
            issues.append(
                f"coupling {coupling.coupling_id} overclaims interpretation"
            )

    for distinction in receipt.distinctions:
        if distinction.scale != receipt.scale:
            issues.append(f"distinction {distinction.distinction_id} has wrong scale")
        if not distinction.coupling_refs:
            issues.append(
                f"distinction {distinction.distinction_id} cites no coupling"
            )
        missing = set(distinction.coupling_refs) - coupling_ids
        if missing:
            issues.append(
                f"distinction {distinction.distinction_id} cites missing couplings: "
                + ",".join(sorted(missing))
            )
        if not distinction.source_refs:
            issues.append(
                f"distinction {distinction.distinction_id} has no provenance"
            )

    for relation in receipt.relations:
        if relation.scale != receipt.scale:
            issues.append(f"relation {relation.relation_id} has wrong scale")
        if not relation.distinction_refs:
            issues.append(f"relation {relation.relation_id} cites no distinction")
        missing = set(relation.distinction_refs) - distinction_ids
        if missing:
            issues.append(
                f"relation {relation.relation_id} cites missing distinctions: "
                + ",".join(sorted(missing))
            )
        if not relation.source_refs:
            issues.append(f"relation {relation.relation_id} has no provenance")

    for trace in receipt.traces:
        if trace.scale != receipt.scale:
            issues.append(f"trace {trace.trace_id} has wrong scale")
        if not trace.source_ref:
            issues.append(f"trace {trace.trace_id} has no source_ref")
        if not trace.append_only:
            issues.append(f"trace {trace.trace_id} is not append-only")

    unknown_missing = set(receipt.unknown.coupling_refs) - coupling_ids
    if unknown_missing:
        issues.append(
            "UNKNOWN cites missing couplings: " + ",".join(sorted(unknown_missing))
        )

    if receipt.authority_inherited:
        issues.append("authority must not be inherited across scales")

    dimensions = {
        "kappa": len(receipt.couplings),
        "delta": len(receipt.distinctions),
        "rho": len(receipt.relations),
        "tau": len(receipt.traces),
        "unknown": len(receipt.unknown.coupling_refs)
        + len(receipt.unknown.missing_distinctions),
        "contradictions": len(receipt.local_contradictions)
        + len(receipt.lifted_contradictions),
    }

    hard_fail = bool(issues)
    frontier_open = (
        dimensions["unknown"] > 0
        or dimensions["contradictions"] > 0
        or bool(receipt.unknown.reason)
    )
    structurally_complete = all(
        dimensions[key] > 0 for key in ("kappa", "delta", "rho", "tau")
    )

    if hard_fail:
        verdict = CoherenceVerdict.FAIL
    elif frontier_open:
        verdict = CoherenceVerdict.INDETERMINATE
    elif structurally_complete:
        verdict = CoherenceVerdict.META_THRESHOLD_ATTAINED
    else:
        verdict = CoherenceVerdict.PARTIAL

    return ScaleAssessment(
        unit_id=receipt.unit_id,
        scale=receipt.scale,
        verdict=verdict,
        issues=tuple(issues),
        dimensions=dimensions,
    )


def evaluate_multiscale(receipts: Iterable[ScaleReceipt]) -> MultiScaleReport:
    """Evaluate local receipts plus non-erasure/propagation between scales."""
    receipts = tuple(receipts)
    assessments = tuple(assess_receipt(receipt) for receipt in receipts)
    by_id = {receipt.unit_id: receipt for receipt in receipts}
    cross: List[str] = []

    if len(by_id) != len(receipts):
        cross.append("duplicate unit_id across receipts")

    for parent in receipts:
        for child_id in parent.child_unit_ids:
            child = by_id.get(child_id)
            if child is None:
                cross.append(f"{parent.unit_id} cites missing child {child_id}")
                continue
            if _SCALE_ORDER[child.scale] >= _SCALE_ORDER[parent.scale]:
                cross.append(
                    f"{parent.unit_id} child {child_id} is not at a lower scale"
                )

            lifted_ids = {
                item.contradiction_id for item in parent.lifted_contradictions
            }
            for contradiction in child.local_contradictions:
                if contradiction.contradiction_id not in lifted_ids:
                    cross.append(
                        f"{parent.unit_id} masks child contradiction "
                        f"{contradiction.contradiction_id}"
                    )

    verdicts = {assessment.verdict for assessment in assessments}
    if cross or CoherenceVerdict.FAIL in verdicts:
        overall = CoherenceVerdict.FAIL
    elif CoherenceVerdict.INDETERMINATE in verdicts:
        overall = CoherenceVerdict.INDETERMINATE
    elif receipts and verdicts == {CoherenceVerdict.META_THRESHOLD_ATTAINED}:
        overall = CoherenceVerdict.META_THRESHOLD_ATTAINED
    else:
        overall = CoherenceVerdict.PARTIAL

    return MultiScaleReport(
        assessments=assessments,
        cross_scale_issues=tuple(cross),
        overall=overall,
    )


def next_cycle_couplings(receipt: ScaleReceipt) -> Tuple[str, ...]:
    """Return only observed unresolved couplings; never invent the next kappa."""
    return tuple(dict.fromkeys(receipt.unknown.coupling_refs))
