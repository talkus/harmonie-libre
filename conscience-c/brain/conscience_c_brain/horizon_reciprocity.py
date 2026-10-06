"""Local horizon / distinction reciprocity for the multiscale coherence candidate.

This module makes Omega explicitly local and derived. An horizon is not a
free-standing object and never denotes the boundary of reality itself.

Candidate relation:
    Omega_local <-> Delta_local

Operational reading:
- local forms/distinctions configure a local horizon;
- a changed observer/scope/property/distinction set may reconfigure that horizon;
- UNKNOWN is local to the current epistemic contract, never absolute impossibility;
- horizon transitions are traceable and non-authorizing.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Sequence

from .multiscale_coherence import (
    CoherenceStatus,
    Scale,
    ScaleReceipt,
    ValidationIssue,
)


@dataclass(frozen=True)
class LocalHorizon:
    source_receipt_hash: str
    scale: Scale
    observer_ref: str
    scope_ref: str
    property_ref: str
    property_version: str
    distinction_refs: tuple[str, ...]
    unknown_ids: tuple[str, ...]
    revision_triggers: tuple[str, ...]
    construction_trace_refs: tuple[str, ...]
    epistemic_scope: str = "local"
    totality_claim: bool = False

    def payload(self) -> dict:
        return {
            "source_receipt_hash": self.source_receipt_hash,
            "scale": self.scale.value,
            "observer_ref": self.observer_ref,
            "scope_ref": self.scope_ref,
            "property_ref": self.property_ref,
            "property_version": self.property_version,
            "distinction_refs": list(self.distinction_refs),
            "unknown_ids": list(self.unknown_ids),
            "revision_triggers": list(self.revision_triggers),
            "construction_trace_refs": list(self.construction_trace_refs),
            "epistemic_scope": self.epistemic_scope,
            "totality_claim": self.totality_claim,
        }

    def digest(self) -> str:
        raw = json.dumps(
            self.payload(),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()


@dataclass(frozen=True)
class HorizonReport:
    status: CoherenceStatus
    horizon_hash: str
    issues: tuple[ValidationIssue, ...] = ()
    execution_authority: bool = False


@dataclass(frozen=True)
class HorizonTransition:
    from_horizon_hash: str
    to_horizon_hash: str
    cause_trace_refs: tuple[str, ...]
    added_distinction_refs: tuple[str, ...] = ()
    removed_distinction_refs: tuple[str, ...] = ()
    opened_unknown_ids: tuple[str, ...] = ()
    resolved_unknown_ids: tuple[str, ...] = ()
    claims_exhaustive_possible_space: bool = False


@dataclass(frozen=True)
class HorizonTransitionReport:
    status: CoherenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    execution_authority: bool = False


def derive_local_horizon(receipt: ScaleReceipt) -> LocalHorizon:
    """Derive Omega from one local epistemic receipt.

    Symbolic labels are absent by construction. The horizon therefore cannot
    gain operational privilege from a symbolic renaming.
    """
    return LocalHorizon(
        source_receipt_hash=receipt.digest(),
        scale=receipt.scale,
        observer_ref=receipt.observer_ref,
        scope_ref=receipt.scope_ref,
        property_ref=receipt.property_ref,
        property_version=receipt.property_version,
        distinction_refs=tuple(x.distinction_id for x in receipt.distinctions),
        unknown_ids=tuple(x.unknown_id for x in receipt.unknowns),
        revision_triggers=receipt.revision_triggers,
        construction_trace_refs=receipt.trace_refs,
        epistemic_scope="local",
        totality_claim=False,
    )


def validate_local_horizon(
    horizon: LocalHorizon,
    source_receipt: ScaleReceipt,
) -> HorizonReport:
    """Validate that Omega remains a local derivative of the selected form."""
    issues: list[ValidationIssue] = []
    expected = derive_local_horizon(source_receipt)

    if horizon.source_receipt_hash != source_receipt.digest():
        issues.append(
            ValidationIssue(
                "MS_OMEGA_SOURCE_MISMATCH",
                "local horizon does not cite the exact source receipt",
            )
        )
    if horizon.scale != source_receipt.scale:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_SCALE_MISMATCH",
                "local horizon scale differs from its source receipt",
            )
        )
    if horizon.observer_ref != source_receipt.observer_ref:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_OBSERVER_MISMATCH",
                "local horizon observer differs from its source receipt",
            )
        )
    if horizon.scope_ref != source_receipt.scope_ref:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_SCOPE_MISMATCH",
                "local horizon scope differs from its source receipt",
            )
        )
    if (
        horizon.property_ref != source_receipt.property_ref
        or horizon.property_version != source_receipt.property_version
    ):
        issues.append(
            ValidationIssue(
                "MS_OMEGA_PROPERTY_MISMATCH",
                "local horizon property contract differs from its source receipt",
            )
        )
    if set(horizon.distinction_refs) != {x.distinction_id for x in source_receipt.distinctions}:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_DELTA_MISMATCH",
                "local horizon does not preserve the source distinction set",
            )
        )
    if set(horizon.unknown_ids) != {x.unknown_id for x in source_receipt.unknowns}:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_UNKNOWN_MISMATCH",
                "local horizon does not preserve the source UNKNOWN boundary",
            )
        )
    if set(horizon.construction_trace_refs) != set(source_receipt.trace_refs):
        issues.append(
            ValidationIssue(
                "MS_OMEGA_TRACE_MISMATCH",
                "local horizon does not preserve its construction trace set",
            )
        )
    if horizon.epistemic_scope != "local":
        issues.append(
            ValidationIssue(
                "MS_OMEGA_ABSOLUTE_SCOPE_FORBIDDEN",
                "UNKNOWN/horizon scope must remain local to the epistemic contract",
            )
        )
    if horizon.totality_claim:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_TOTALITY_FORBIDDEN",
                "a local horizon cannot claim to be the boundary of reality or of all possibility",
            )
        )

    if horizon.payload() != expected.payload() and not issues:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_DERIVATION_DRIFT",
                "local horizon differs from deterministic derivation",
            )
        )

    return HorizonReport(
        status=CoherenceStatus.PARTIAL if issues else CoherenceStatus.CANDIDATE_OK,
        horizon_hash=horizon.digest(),
        issues=tuple(issues),
        execution_authority=False,
    )


def derive_transition(
    before_receipt: ScaleReceipt,
    after_receipt: ScaleReceipt,
    *,
    cause_trace_refs: Sequence[str],
) -> HorizonTransition:
    """Build the explicit Omega reconfiguration caused by a local state change."""
    before = derive_local_horizon(before_receipt)
    after = derive_local_horizon(after_receipt)

    before_delta = set(before.distinction_refs)
    after_delta = set(after.distinction_refs)
    before_unknown = set(before.unknown_ids)
    after_unknown = set(after.unknown_ids)

    return HorizonTransition(
        from_horizon_hash=before.digest(),
        to_horizon_hash=after.digest(),
        cause_trace_refs=tuple(cause_trace_refs),
        added_distinction_refs=tuple(sorted(after_delta - before_delta)),
        removed_distinction_refs=tuple(sorted(before_delta - after_delta)),
        opened_unknown_ids=tuple(sorted(after_unknown - before_unknown)),
        resolved_unknown_ids=tuple(sorted(before_unknown - after_unknown)),
        claims_exhaustive_possible_space=False,
    )


def validate_horizon_transition(
    before_receipt: ScaleReceipt,
    after_receipt: ScaleReceipt,
    transition: HorizonTransition,
) -> HorizonTransitionReport:
    """Validate Delta <-> Omega co-reconfiguration without totalizing possibility."""
    issues: list[ValidationIssue] = []
    before = derive_local_horizon(before_receipt)
    after = derive_local_horizon(after_receipt)
    expected = derive_transition(
        before_receipt,
        after_receipt,
        cause_trace_refs=transition.cause_trace_refs,
    )

    if transition.from_horizon_hash != before.digest():
        issues.append(
            ValidationIssue(
                "MS_OMEGA_FROM_MISMATCH",
                "transition does not start at the derived prior horizon",
            )
        )
    if transition.to_horizon_hash != after.digest():
        issues.append(
            ValidationIssue(
                "MS_OMEGA_TO_MISMATCH",
                "transition does not end at the derived next horizon",
            )
        )

    for field_name in (
        "added_distinction_refs",
        "removed_distinction_refs",
        "opened_unknown_ids",
        "resolved_unknown_ids",
    ):
        if set(getattr(transition, field_name)) != set(getattr(expected, field_name)):
            issues.append(
                ValidationIssue(
                    "MS_OMEGA_RECONFIGURATION_MISMATCH",
                    f"{field_name} does not match the actual local reconfiguration",
                )
            )

    available_traces = set(before_receipt.trace_refs) | set(after_receipt.trace_refs)
    missing_causes = set(transition.cause_trace_refs) - available_traces
    if missing_causes:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_CAUSE_TRACE_UNKNOWN",
                f"horizon transition cites unknown cause traces: {sorted(missing_causes)}",
            )
        )

    if transition.claims_exhaustive_possible_space:
        issues.append(
            ValidationIssue(
                "MS_OMEGA_TOTALITY_FORBIDDEN",
                "a horizon transition cannot certify the exhaustive space of future possibility",
            )
        )

    return HorizonTransitionReport(
        status=CoherenceStatus.PARTIAL if issues else CoherenceStatus.CANDIDATE_OK,
        issues=tuple(issues),
        execution_authority=False,
    )
