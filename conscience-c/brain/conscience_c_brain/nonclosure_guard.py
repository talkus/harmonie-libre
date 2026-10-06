"""Non-closure guard for Architecture C.

Operational principle:
    no local presentation may claim global exhaustiveness.

A presentation may be structurally accepted as locally closed only relative to
an explicit bounded domain, closure criterion, proof refs, and reopening
triggers.  Local closure never implies global closure, truth, independent
validation, or execution authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .multiscale_coherence import CoherenceStatus, Scale, ValidationIssue


class ClosureState(str, Enum):
    OPEN = "open"
    LOCALLY_CLOSED = "locally_closed"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class PresentationEnvelope:
    presentation_id: str
    scale: Scale
    observer_ref: str
    scope_ref: str
    property_ref: str
    property_version: str
    trace_refs: tuple[str, ...]
    unresolved_refs: tuple[str, ...] = ()
    bounded_domain_ref: str | None = None
    closure_criterion_ref: str | None = None
    closure_proof_refs: tuple[str, ...] = ()
    claims_scope_exhaustiveness: bool = False
    claims_global_exhaustiveness: bool = False
    reopening_triggers: tuple[str, ...] = ()


@dataclass(frozen=True)
class ClosureReport:
    scale: Scale
    state: ClosureState
    status: CoherenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    locally_exhaustive: bool = False
    globally_exhaustive: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class MultiscaleClosureReport:
    status: CoherenceStatus
    scale_reports: tuple[ClosureReport, ...]
    issues: tuple[ValidationIssue, ...] = ()
    all_scales_locally_closed: bool = False
    globally_exhaustive: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


def validate_presentation_closure(
    envelope: PresentationEnvelope,
    *,
    available_trace_refs: Sequence[str],
    available_proof_refs: Sequence[str],
) -> ClosureReport:
    """Validate one local presentation without promoting it to totality."""
    issues: list[ValidationIssue] = []
    traces = set(available_trace_refs)
    proofs = set(available_proof_refs)

    if not envelope.observer_ref:
        issues.append(ValidationIssue("MS_NC_OBSERVER_REQUIRED", "observer_ref is required"))
    if not envelope.scope_ref:
        issues.append(ValidationIssue("MS_NC_SCOPE_REQUIRED", "scope_ref is required"))
    if not envelope.property_ref or not envelope.property_version:
        issues.append(
            ValidationIssue(
                "MS_NC_PROPERTY_REQUIRED",
                "property_ref and property_version are required",
            )
        )
    if not envelope.trace_refs:
        issues.append(
            ValidationIssue(
                "MS_NC_TRACE_REQUIRED",
                "presentation requires trace provenance",
            )
        )
    else:
        missing_traces = set(envelope.trace_refs) - traces
        if missing_traces:
            issues.append(
                ValidationIssue(
                    "MS_NC_TRACE_UNKNOWN",
                    f"presentation cites unavailable traces: {sorted(missing_traces)}",
                )
            )

    if not envelope.reopening_triggers:
        issues.append(
            ValidationIssue(
                "MS_NC_REOPEN_TRIGGER_REQUIRED",
                "every presentation must remain explicitly reopenable",
            )
        )

    if envelope.claims_global_exhaustiveness:
        issues.append(
            ValidationIssue(
                "MS_NC_GLOBAL_CLOSURE_FORBIDDEN",
                "no local presentation may claim to exhaust reality or all possible presentations",
            )
        )

    locally_exhaustive = False
    if envelope.claims_scope_exhaustiveness:
        if not envelope.bounded_domain_ref:
            issues.append(
                ValidationIssue(
                    "MS_NC_BOUNDED_DOMAIN_REQUIRED",
                    "local exhaustiveness requires an explicit bounded domain",
                )
            )
        if not envelope.closure_criterion_ref:
            issues.append(
                ValidationIssue(
                    "MS_NC_CLOSURE_CRITERION_REQUIRED",
                    "local exhaustiveness requires an explicit closure criterion",
                )
            )
        if not envelope.closure_proof_refs:
            issues.append(
                ValidationIssue(
                    "MS_NC_CLOSURE_PROOF_REQUIRED",
                    "local exhaustiveness requires explicit closure proof refs",
                )
            )
        else:
            missing_proofs = set(envelope.closure_proof_refs) - proofs
            if missing_proofs:
                issues.append(
                    ValidationIssue(
                        "MS_NC_CLOSURE_PROOF_UNKNOWN",
                        f"closure cites unavailable proof refs: {sorted(missing_proofs)}",
                    )
                )
        if envelope.unresolved_refs:
            issues.append(
                ValidationIssue(
                    "MS_NC_UNRESOLVED_CONFLICTS_WITH_CLOSURE",
                    "a locally exhaustive claim cannot silently retain unresolved items",
                )
            )
        locally_exhaustive = not any(
            issue.code in {
                "MS_NC_BOUNDED_DOMAIN_REQUIRED",
                "MS_NC_CLOSURE_CRITERION_REQUIRED",
                "MS_NC_CLOSURE_PROOF_REQUIRED",
                "MS_NC_CLOSURE_PROOF_UNKNOWN",
                "MS_NC_UNRESOLVED_CONFLICTS_WITH_CLOSURE",
            }
            for issue in issues
        )

    if envelope.unresolved_refs and not envelope.claims_scope_exhaustiveness:
        state = ClosureState.INDETERMINATE
    elif locally_exhaustive:
        state = ClosureState.LOCALLY_CLOSED
    else:
        state = ClosureState.OPEN

    if issues:
        status = CoherenceStatus.PARTIAL
    elif state == ClosureState.INDETERMINATE:
        status = CoherenceStatus.INDETERMINATE
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return ClosureReport(
        scale=envelope.scale,
        state=state,
        status=status,
        issues=tuple(issues),
        locally_exhaustive=locally_exhaustive,
        globally_exhaustive=False,
        independent_validation=False,
        execution_authority=False,
    )


def validate_multiscale_nonclosure(
    reports: Sequence[ClosureReport],
) -> MultiscaleClosureReport:
    """Compose closure reports without laundering local closure into global closure."""
    issues: list[ValidationIssue] = []
    by_scale: dict[Scale, ClosureReport] = {}

    for report in reports:
        if report.scale in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_NC_SCALE_DUPLICATE",
                    f"duplicate closure report for {report.scale.value}",
                )
            )
        else:
            by_scale[report.scale] = report

    for scale in Scale:
        if scale not in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_NC_SCALE_MISSING",
                    f"missing closure report for {scale.value}",
                )
            )

    all_local = len(by_scale) == len(Scale) and all(
        report.locally_exhaustive for report in by_scale.values()
    )
    has_indeterminate = any(
        report.status == CoherenceStatus.INDETERMINATE for report in reports
    )
    has_partial = any(
        report.status == CoherenceStatus.PARTIAL for report in reports
    )

    if issues or has_partial:
        status = CoherenceStatus.PARTIAL
    elif has_indeterminate:
        status = CoherenceStatus.INDETERMINATE
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleClosureReport(
        status=status,
        scale_reports=tuple(reports),
        issues=tuple(issues),
        all_scales_locally_closed=all_local,
        globally_exhaustive=False,
        independent_validation=False,
        execution_authority=False,
    )
