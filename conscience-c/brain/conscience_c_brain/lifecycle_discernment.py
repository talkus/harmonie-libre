"""Local lifecycle discernment for Phi without infinite meta-regulator regress.

Conceptual labels Theta and Psi are not runtime authorities here.
The executable layer only validates a local, traceable choice among:
- MATURE: deepen the current Phi identity;
- REGENERATE: create a successor Phi;
- DEFER: postpone the choice under an explicit revisit condition;
- RETIRE: stop using Phi without silently inventing a successor.

The same contract applies at micro, meso, macro, and meta scales.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Mapping, Sequence

from .multiscale_coherence import CoherenceStatus, Scale, ValidationIssue


class HistoricalPhase(str, Enum):
    FOUNDING = "founding"
    TRANSMISSION = "transmission"
    CRISIS = "crisis"
    DISSOLUTION = "dissolution"
    UNKNOWN = "unknown"


class AdaptationPath(str, Enum):
    MATURE = "mature"
    REGENERATE = "regenerate"
    DEFER = "defer"
    RETIRE = "retire"


@dataclass(frozen=True)
class MaturityContext:
    context_id: str
    scale: Scale
    phi_ref: str
    phi_version: str
    horizon_hash: str
    observer_ref: str
    scope_ref: str
    phase: HistoricalPhase
    regeneration_gain: float
    history_trace_refs: tuple[str, ...]
    revision_triggers: tuple[str, ...]


@dataclass(frozen=True)
class LifecycleDecision:
    decision_id: str
    context_id: str
    path: AdaptationPath
    evidence_trace_refs: tuple[str, ...]
    justification_refs: tuple[str, ...]
    target_phi_ref: str | None = None
    target_phi_version: str | None = None
    revisit_trigger_refs: tuple[str, ...] = ()
    contestation_refs: tuple[str, ...] = ()
    claims_optimal_rhythm: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class LifecycleReport:
    scale: Scale
    path: AdaptationPath
    status: CoherenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    has_unknown_phase: bool = False
    has_contestation: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class MultiscaleLifecycleReport:
    status: CoherenceStatus
    scale_reports: tuple[LifecycleReport, ...]
    issues: tuple[ValidationIssue, ...] = ()
    paths_by_scale: Mapping[Scale, AdaptationPath] | None = None
    has_unknown_phase: bool = False
    has_contestation: bool = False
    execution_authority: bool = False


def _valid_gain(value: float) -> bool:
    try:
        return math.isfinite(float(value)) and float(value) > 0.0
    except (TypeError, ValueError):
        return False


def validate_lifecycle_decision(
    context: MaturityContext,
    decision: LifecycleDecision,
    *,
    known_horizon_hashes: Sequence[str],
    available_trace_refs: Sequence[str],
) -> LifecycleReport:
    """Validate a local adaptation choice without selecting it automatically."""
    issues: list[ValidationIssue] = []
    available = set(available_trace_refs)

    if decision.context_id != context.context_id:
        issues.append(
            ValidationIssue(
                "MS_LAMBDA_CONTEXT_MISMATCH",
                "decision does not cite the exact maturity context",
            )
        )

    if context.horizon_hash not in set(known_horizon_hashes):
        issues.append(
            ValidationIssue(
                "MS_LAMBDA_HORIZON_UNKNOWN",
                "maturity context cites an unknown local horizon",
            )
        )

    if not _valid_gain(context.regeneration_gain):
        issues.append(
            ValidationIssue(
                "MS_G_PHI_OUT_OF_BOUNDS",
                "regeneration gain must satisfy 0 < G_phi < infinity",
            )
        )

    if not context.history_trace_refs:
        issues.append(
            ValidationIssue(
                "MS_LAMBDA_HISTORY_REQUIRED",
                "local historical maturity requires trace provenance",
            )
        )
    else:
        missing_history = set(context.history_trace_refs) - available
        if missing_history:
            issues.append(
                ValidationIssue(
                    "MS_LAMBDA_HISTORY_UNKNOWN",
                    f"maturity context cites unavailable history traces: {sorted(missing_history)}",
                )
            )

    if not context.revision_triggers:
        issues.append(
            ValidationIssue(
                "MS_LAMBDA_REVISION_TRIGGER_REQUIRED",
                "maturity context must remain explicitly reopenable",
            )
        )

    if not decision.evidence_trace_refs:
        issues.append(
            ValidationIssue(
                "MS_PSI_EVIDENCE_REQUIRED",
                "maturation/regeneration choice requires evidence traces",
            )
        )
    else:
        missing_evidence = set(decision.evidence_trace_refs) - available
        if missing_evidence:
            issues.append(
                ValidationIssue(
                    "MS_PSI_EVIDENCE_UNKNOWN",
                    f"decision cites unavailable evidence traces: {sorted(missing_evidence)}",
                )
            )

    if not decision.justification_refs:
        issues.append(
            ValidationIssue(
                "MS_PSI_JUSTIFICATION_REQUIRED",
                "adaptation choice requires an explicit justification ref",
            )
        )

    if decision.claims_optimal_rhythm:
        issues.append(
            ValidationIssue(
                "MS_THETA_OPTIMALITY_FORBIDDEN",
                "the runtime cannot certify an absolute or final right rhythm",
            )
        )

    if decision.execution_authority:
        issues.append(
            ValidationIssue(
                "MS_PSI_AUTHORITY_FORBIDDEN",
                "lifecycle discernment never carries execution authority",
            )
        )

    if decision.path == AdaptationPath.MATURE:
        if decision.target_phi_ref != context.phi_ref:
            issues.append(
                ValidationIssue(
                    "MS_PHI_MATURATION_IDENTITY_REQUIRED",
                    "maturation must preserve the current Phi identity",
                )
            )
        if not decision.target_phi_version or decision.target_phi_version == context.phi_version:
            issues.append(
                ValidationIssue(
                    "MS_PHI_MATURATION_VERSION_REQUIRED",
                    "maturation requires a distinct target version of the same Phi",
                )
            )

    elif decision.path == AdaptationPath.REGENERATE:
        if not decision.target_phi_ref or decision.target_phi_ref == context.phi_ref:
            issues.append(
                ValidationIssue(
                    "MS_PHI_REGENERATION_SUCCESSOR_REQUIRED",
                    "regeneration requires a distinct successor Phi identity",
                )
            )
        if not decision.target_phi_version:
            issues.append(
                ValidationIssue(
                    "MS_PHI_REGENERATION_VERSION_REQUIRED",
                    "regeneration requires an explicit successor version",
                )
            )

    elif decision.path == AdaptationPath.DEFER:
        if decision.target_phi_ref is not None or decision.target_phi_version is not None:
            issues.append(
                ValidationIssue(
                    "MS_PHI_DEFER_TARGET_FORBIDDEN",
                    "defer must not silently preselect a successor or matured target",
                )
            )
        if not decision.revisit_trigger_refs:
            issues.append(
                ValidationIssue(
                    "MS_PHI_DEFER_REVISIT_REQUIRED",
                    "defer requires an explicit revisit trigger",
                )
            )

    elif decision.path == AdaptationPath.RETIRE:
        if decision.target_phi_ref is not None or decision.target_phi_version is not None:
            issues.append(
                ValidationIssue(
                    "MS_PHI_RETIRE_TARGET_FORBIDDEN",
                    "retire must not silently create a successor",
                )
            )

    has_unknown_phase = context.phase == HistoricalPhase.UNKNOWN
    has_contestation = bool(decision.contestation_refs)

    if has_contestation:
        status = CoherenceStatus.CONTESTED
    elif has_unknown_phase:
        status = CoherenceStatus.INDETERMINATE
    elif issues:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return LifecycleReport(
        scale=context.scale,
        path=decision.path,
        status=status,
        issues=tuple(issues),
        has_unknown_phase=has_unknown_phase,
        has_contestation=has_contestation,
        execution_authority=False,
    )


def validate_multiscale_lifecycle(
    reports: Sequence[LifecycleReport],
) -> MultiscaleLifecycleReport:
    """Aggregate lifecycle reports without requiring identical paths."""
    issues: list[ValidationIssue] = []
    by_scale: dict[Scale, LifecycleReport] = {}

    for report in reports:
        if report.scale in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_PSI_SCALE_DUPLICATE",
                    f"duplicate lifecycle report for scale {report.scale.value}",
                )
            )
        else:
            by_scale[report.scale] = report

    for scale in Scale:
        if scale not in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_PSI_SCALE_MISSING",
                    f"missing lifecycle report for scale {scale.value}",
                )
            )

    has_contestation = any(x.status == CoherenceStatus.CONTESTED for x in reports)
    has_unknown_phase = any(x.status == CoherenceStatus.INDETERMINATE for x in reports)
    has_partial = any(x.status == CoherenceStatus.PARTIAL for x in reports)

    if has_contestation:
        status = CoherenceStatus.CONTESTED
    elif has_unknown_phase:
        status = CoherenceStatus.INDETERMINATE
    elif issues or has_partial:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleLifecycleReport(
        status=status,
        scale_reports=tuple(reports),
        issues=tuple(issues),
        paths_by_scale={x.scale: x.path for x in reports},
        has_unknown_phase=has_unknown_phase,
        has_contestation=has_contestation,
        execution_authority=False,
    )
