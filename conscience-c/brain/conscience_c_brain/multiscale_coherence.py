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
class ScaleBridge:
    """First-class transformation contract between adjacent scales.

    The bridge records what a parent received from one child. It is a
    provenance/contestability object, never an authority channel.
    """

    bridge_id: str
    child_receipt_hash: str
    parent_receipt_hash: str
    transform_ref: str
    preserved_origin_refs: tuple[str, ...] = ()
    preserved_provenance_bundle_refs: tuple[str, ...] = ()
    carried_unknown_ids: tuple[str, ...] = ()
    carried_contestation_ids: tuple[str, ...] = ()
    carried_evidence_status: EvidenceStatus | None = None
    declared_loss_refs: tuple[str, ...] = ()
    loss_justification_refs: tuple[str, ...] = ()
    authority_transfer: bool = False


@dataclass(frozen=True)
class ValidationIssue:
    code: str
    message: str


@dataclass(frozen=True)
class BridgeReport:
    bridge_id: str
    issues: tuple[ValidationIssue, ...] = ()
    execution_authority: bool = False


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
    property_ref: str
    property_version: str
    scope_ref: str
    observer_ref: str
    revision_triggers: tuple[str, ...]
    provenance_bundle_refs: tuple[str, ...]
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
            "property_ref": self.property_ref,
            "property_version": self.property_version,
            "scope_ref": self.scope_ref,
            "observer_ref": self.observer_ref,
            "revision_triggers": list(self.revision_triggers),
            "provenance_bundle_refs": list(self.provenance_bundle_refs),
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

    def state_payload(self) -> dict:
        """Relevant local state for stutter-equivalence checks.

        Receipt identity and the cross-scale parent pointer are transport/history
        coordinates, not part of the local epistemic state. Symbolic labels are
        already excluded by canonical_payload().
        """
        payload = dict(self.canonical_payload())
        payload.pop("receipt_id", None)
        payload.pop("parent_receipt_hash", None)
        return payload

    def state_digest(self) -> str:
        raw = json.dumps(
            self.state_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()

    def digest(self) -> str:
        raw = json.dumps(
            self.canonical_payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


def stutter_equivalent(left: ScaleReceipt, right: ScaleReceipt) -> bool:
    """True when two receipts expose the same relevant state at one scale.

    This is a deliberately narrow analogue of stuttering invariance: changing
    only receipt identity or the cross-scale parent pointer does not create a
    new local epistemic state.
    """
    return left.scale == right.scale and left.state_digest() == right.state_digest()


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

    if not receipt.property_ref:
        issues.append(ValidationIssue("MS_PROPERTY_REQUIRED", "property_ref must be explicit"))
    if not receipt.property_version:
        issues.append(
            ValidationIssue("MS_PROPERTY_VERSION_REQUIRED", "property_version must be explicit")
        )
    if not receipt.scope_ref:
        issues.append(ValidationIssue("MS_SCOPE_REQUIRED", "scope_ref must be explicit"))
    if not receipt.observer_ref:
        issues.append(ValidationIssue("MS_OBSERVER_REQUIRED", "observer_ref must be explicit"))

    if not receipt.revision_triggers:
        issues.append(
            ValidationIssue(
                "MS_REVISION_TRIGGER_REQUIRED",
                "at least one reopening/revision trigger must be explicit",
            )
        )
    elif len(set(receipt.revision_triggers)) != len(receipt.revision_triggers):
        issues.append(
            ValidationIssue(
                "MS_REVISION_TRIGGER_DUPLICATE",
                "duplicate revision triggers add no independent condition",
            )
        )

    if len(set(receipt.provenance_bundle_refs)) != len(receipt.provenance_bundle_refs):
        issues.append(
            ValidationIssue(
                "MS_PROVENANCE_BUNDLE_DUPLICATE",
                "duplicate provenance-bundle refs add no independent provenance",
            )
        )
    if receipt.external_witness_refs and not receipt.provenance_bundle_refs:
        issues.append(
            ValidationIssue(
                "MS_WITNESS_PROVENANCE_REQUIRED",
                "declared external witnesses require provenance-of-provenance refs",
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
    bridge_reports: tuple[BridgeReport, ...] = ()
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



def validate_scale_bridge(
    bridge: ScaleBridge,
    receipts_by_hash: Mapping[str, ScaleReceipt],
) -> BridgeReport:
    """Validate one explicit adjacent-scale transformation contract.

    A bridge may transform or summarize local material, but it must not erase
    provenance, uncertainty, or contestation, and it can never transmit
    execution authority.
    """
    issues: list[ValidationIssue] = []
    child = receipts_by_hash.get(bridge.child_receipt_hash)
    parent = receipts_by_hash.get(bridge.parent_receipt_hash)

    if not bridge.transform_ref:
        issues.append(
            ValidationIssue(
                "MS_BRIDGE_TRANSFORM_REQUIRED",
                f"bridge {bridge.bridge_id} has no transform_ref",
            )
        )

    if bridge.authority_transfer:
        issues.append(
            ValidationIssue(
                "MS_BRIDGE_AUTHORITY_TRANSFER",
                f"bridge {bridge.bridge_id} attempts to transfer execution authority",
            )
        )

    if bridge.declared_loss_refs and not bridge.loss_justification_refs:
        issues.append(
            ValidationIssue(
                "MS_BRIDGE_LOSS_UNJUSTIFIED",
                f"bridge {bridge.bridge_id} declares information loss without justification",
            )
        )

    if child is None:
        issues.append(
            ValidationIssue(
                "MS_BRIDGE_CHILD_UNKNOWN",
                f"bridge {bridge.bridge_id} cites a child receipt outside this composition",
            )
        )
    if parent is None:
        issues.append(
            ValidationIssue(
                "MS_BRIDGE_PARENT_UNKNOWN",
                f"bridge {bridge.bridge_id} cites a parent receipt outside this composition",
            )
        )

    if child is not None and parent is not None:
        if child.parent_receipt_hash != bridge.parent_receipt_hash:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_PARENT_MISMATCH",
                    f"bridge {bridge.bridge_id} does not match the child's declared parent",
                )
            )

        if _SCALE_RANK[parent.scale] != _SCALE_RANK[child.scale] + 1:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_NON_ADJACENT",
                    f"bridge {bridge.bridge_id} must connect adjacent scales",
                )
            )

        child_origins = set(child.origin_refs)
        preserved_origins = set(bridge.preserved_origin_refs)
        missing_origins = child_origins - preserved_origins
        invented_origins = preserved_origins - child_origins
        if missing_origins:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_ORIGIN_DROPPED",
                    f"bridge {bridge.bridge_id} drops child origins: {sorted(missing_origins)}",
                )
            )
        if invented_origins:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_ORIGIN_INVENTED",
                    f"bridge {bridge.bridge_id} invents origins: {sorted(invented_origins)}",
                )
            )
        not_in_parent = preserved_origins - set(parent.origin_refs)
        if not_in_parent:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_ORIGIN_NOT_IN_PARENT",
                    f"bridge {bridge.bridge_id} preserves origins absent from parent: {sorted(not_in_parent)}",
                )
            )

        child_bundles = set(child.provenance_bundle_refs)
        preserved_bundles = set(bridge.preserved_provenance_bundle_refs)
        missing_bundles = child_bundles - preserved_bundles
        invented_bundles = preserved_bundles - child_bundles
        if missing_bundles:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_PROVENANCE_DROPPED",
                    f"bridge {bridge.bridge_id} drops provenance bundles: {sorted(missing_bundles)}",
                )
            )
        if invented_bundles:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_PROVENANCE_INVENTED",
                    f"bridge {bridge.bridge_id} invents provenance bundles: {sorted(invented_bundles)}",
                )
            )
        bundles_not_in_parent = preserved_bundles - set(parent.provenance_bundle_refs)
        if bundles_not_in_parent:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_PROVENANCE_NOT_IN_PARENT",
                    f"bridge {bridge.bridge_id} preserves bundles absent from parent: {sorted(bundles_not_in_parent)}",
                )
            )

        unknown_ids = {x.unknown_id for x in child.unknowns}
        carried_unknowns = set(bridge.carried_unknown_ids)
        missing_unknowns = unknown_ids - carried_unknowns
        invented_unknowns = carried_unknowns - unknown_ids
        if missing_unknowns:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_UNKNOWN_DROPPED",
                    f"bridge {bridge.bridge_id} drops UNKNOWN ids: {sorted(missing_unknowns)}",
                )
            )
        if invented_unknowns:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_UNKNOWN_INVENTED",
                    f"bridge {bridge.bridge_id} invents UNKNOWN ids: {sorted(invented_unknowns)}",
                )
            )

        contestation_ids = {x.contestation_id for x in child.contestations}
        carried_contestations = set(bridge.carried_contestation_ids)
        missing_contestations = contestation_ids - carried_contestations
        invented_contestations = carried_contestations - contestation_ids
        if missing_contestations:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_CONTESTATION_DROPPED",
                    f"bridge {bridge.bridge_id} drops contestations: {sorted(missing_contestations)}",
                )
            )
        if invented_contestations:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_CONTESTATION_INVENTED",
                    f"bridge {bridge.bridge_id} invents contestations: {sorted(invented_contestations)}",
                )
            )

        if bridge.carried_evidence_status is None:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_EVIDENCE_STATUS_REQUIRED",
                    f"bridge {bridge.bridge_id} does not carry the child's evidence status",
                )
            )
        elif bridge.carried_evidence_status != child.evidence_status:
            issues.append(
                ValidationIssue(
                    "MS_BRIDGE_EVIDENCE_STATUS_MISMATCH",
                    f"bridge {bridge.bridge_id} changes child evidence status "
                    f"{child.evidence_status.value} -> {bridge.carried_evidence_status.value}",
                )
            )

    return BridgeReport(
        bridge_id=bridge.bridge_id,
        issues=tuple(issues),
        execution_authority=False,
    )

def validate_multiscale(
    receipts: Sequence[ScaleReceipt],
    bridges: Sequence[ScaleBridge] = (),
    *,
    require_explicit_bridges: bool = False,
) -> MultiscaleReport:
    """Validate composition without collapsing local conclusions into one score.

    Multiple units per scale are allowed. A full composition needs all four
    scales, parent links move exactly one scale upward, source origins survive
    aggregation, and the parent graph must remain acyclic. Optional first-class
    bridges make each transformation auditable; strict mode requires one bridge
    for every child→parent edge.
    """
    issues: list[ValidationIssue] = []
    reports = tuple(validate_scale_receipt(x) for x in receipts)

    hashes = [x.digest() for x in receipts]
    receipts_by_hash = {x.digest(): x for x in receipts}
    bridge_reports = tuple(validate_scale_bridge(x, receipts_by_hash) for x in bridges)

    bridge_ids = [x.bridge_id for x in bridges]
    if len(set(bridge_ids)) != len(bridge_ids):
        issues.append(
            ValidationIssue(
                "MS_DUPLICATE_BRIDGE_ID",
                "one composition cannot contain competing versions of the same bridge_id",
            )
        )

    bridge_pairs = [(x.child_receipt_hash, x.parent_receipt_hash) for x in bridges]
    if len(set(bridge_pairs)) != len(bridge_pairs):
        issues.append(
            ValidationIssue(
                "MS_DUPLICATE_BRIDGE",
                "more than one bridge describes the same child→parent edge",
            )
        )

    if require_explicit_bridges:
        declared_pairs = set(bridge_pairs)
        for receipt in receipts:
            if receipt.parent_receipt_hash and (receipt.digest(), receipt.parent_receipt_hash) not in declared_pairs:
                issues.append(
                    ValidationIssue(
                        "MS_BRIDGE_MISSING",
                        f"strict bridge mode: {receipt.receipt_id} has no explicit child→parent bridge",
                    )
                )

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

                missing_bundles = set(receipt.provenance_bundle_refs) - set(parent.provenance_bundle_refs)
                if missing_bundles:
                    issues.append(
                        ValidationIssue(
                            "MS_PROVENANCE_BUNDLE_NOT_PROPAGATED",
                            f"parent {parent.receipt_id} omits child provenance bundles: {sorted(missing_bundles)}",
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
    elif (
        issues
        or any(x.status == CoherenceStatus.PARTIAL for x in reports)
        or any(x.issues for x in bridge_reports)
    ):
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleReport(
        status=status,
        scale_reports=reports,
        issues=tuple(issues),
        bridge_reports=bridge_reports,
        has_unknown=has_unknown,
        has_contestation=has_contestation,
        independent_validation=False,
        execution_authority=False,
    )
