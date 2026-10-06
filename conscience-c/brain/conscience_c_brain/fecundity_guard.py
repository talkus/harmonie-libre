"""Sustainable fecundity guard for Architecture C.

Fecundity is deliberately non-scalar.  The runtime does not maximize a score.
It checks whether a local form still supports recovery, generation, reopening,
and non-destructive path stewardship while keeping fossilization and
dissolution risks visible.

This module detects loss of fecundity; it does not authorize transformation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .multiscale_coherence import CoherenceStatus, EvidenceStatus, Scale, ValidationIssue


class FecundityVerdict(str, Enum):
    SUSTAINED = "sustained"
    DEGRADED = "degraded"
    INDETERMINATE = "indeterminate"
    CONTESTED = "contested"


class PathImpactState(str, Enum):
    PRESERVED = "preserved"
    OPENED = "opened"
    CLOSED = "closed"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class PathImpact:
    path_ref: str
    state: PathImpactState
    trace_refs: tuple[str, ...]
    justification_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class FecundityAssessment:
    assessment_id: str
    scale: Scale
    form_ref: str
    observer_ref: str
    scope_ref: str
    property_ref: str
    property_version: str
    reprise_status: EvidenceStatus
    reprise_evidence_refs: tuple[str, ...]
    generation_status: EvidenceStatus
    generation_evidence_refs: tuple[str, ...]
    reopening_status: EvidenceStatus
    reopening_evidence_refs: tuple[str, ...]
    fossilization_risk: EvidenceStatus
    fossilization_evidence_refs: tuple[str, ...]
    dissolution_risk: EvidenceStatus
    dissolution_evidence_refs: tuple[str, ...]
    path_impacts: tuple[PathImpact, ...]
    revision_triggers: tuple[str, ...]
    contestation_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class FecundityReport:
    scale: Scale
    verdict: FecundityVerdict
    status: CoherenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    preserved_path_refs: tuple[str, ...] = ()
    opened_path_refs: tuple[str, ...] = ()
    closed_path_refs: tuple[str, ...] = ()
    unknown_path_refs: tuple[str, ...] = ()
    fossilization_triggered: bool = False
    dissolution_triggered: bool = False
    scalar_score: None = None
    optimality_claim: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class MultiscaleFecundityReport:
    verdict: FecundityVerdict
    status: CoherenceStatus
    scale_reports: tuple[FecundityReport, ...]
    issues: tuple[ValidationIssue, ...] = ()
    scalar_score: None = None
    optimality_claim: bool = False
    execution_authority: bool = False


def _validate_signal(
    *,
    name: str,
    status: EvidenceStatus,
    evidence_refs: Sequence[str],
    available_evidence_refs: set[str],
    issues: list[ValidationIssue],
) -> None:
    if status in {EvidenceStatus.TRIGGERED, EvidenceStatus.NOT_TRIGGERED}:
        if not evidence_refs:
            issues.append(
                ValidationIssue(
                    f"MS_FEC_{name}_EVIDENCE_REQUIRED",
                    f"{name} status requires explicit evidence refs",
                )
            )
        missing = set(evidence_refs) - available_evidence_refs
        if missing:
            issues.append(
                ValidationIssue(
                    f"MS_FEC_{name}_EVIDENCE_UNKNOWN",
                    f"{name} cites unavailable evidence refs: {sorted(missing)}",
                )
            )


def validate_fecundity(
    assessment: FecundityAssessment,
    *,
    available_trace_refs: Sequence[str],
    available_evidence_refs: Sequence[str],
) -> FecundityReport:
    """Assess durable fecundity without computing or maximizing a scalar."""
    issues: list[ValidationIssue] = []
    traces = set(available_trace_refs)
    evidence = set(available_evidence_refs)

    if not assessment.observer_ref or not assessment.scope_ref:
        issues.append(
            ValidationIssue(
                "MS_FEC_CONTEXT_REQUIRED",
                "fecundity assessment requires observer and scope refs",
            )
        )
    if not assessment.property_ref or not assessment.property_version:
        issues.append(
            ValidationIssue(
                "MS_FEC_PROPERTY_REQUIRED",
                "fecundity assessment requires property_ref and property_version",
            )
        )
    if not assessment.revision_triggers:
        issues.append(
            ValidationIssue(
                "MS_FEC_REVISION_TRIGGER_REQUIRED",
                "fecundity assessment must remain explicitly reopenable",
            )
        )

    _validate_signal(
        name="REPRISE",
        status=assessment.reprise_status,
        evidence_refs=assessment.reprise_evidence_refs,
        available_evidence_refs=evidence,
        issues=issues,
    )
    _validate_signal(
        name="GENERATION",
        status=assessment.generation_status,
        evidence_refs=assessment.generation_evidence_refs,
        available_evidence_refs=evidence,
        issues=issues,
    )
    _validate_signal(
        name="REOPENING",
        status=assessment.reopening_status,
        evidence_refs=assessment.reopening_evidence_refs,
        available_evidence_refs=evidence,
        issues=issues,
    )
    _validate_signal(
        name="FOSSILIZATION",
        status=assessment.fossilization_risk,
        evidence_refs=assessment.fossilization_evidence_refs,
        available_evidence_refs=evidence,
        issues=issues,
    )
    _validate_signal(
        name="DISSOLUTION",
        status=assessment.dissolution_risk,
        evidence_refs=assessment.dissolution_evidence_refs,
        available_evidence_refs=evidence,
        issues=issues,
    )

    preserved: list[str] = []
    opened: list[str] = []
    closed: list[str] = []
    unknown: list[str] = []

    seen_paths: set[str] = set()
    for impact in assessment.path_impacts:
        if impact.path_ref in seen_paths:
            issues.append(
                ValidationIssue(
                    "MS_FEC_PATH_DUPLICATE",
                    f"duplicate path impact: {impact.path_ref}",
                )
            )
        seen_paths.add(impact.path_ref)

        if not impact.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_FEC_PATH_TRACE_REQUIRED",
                    f"path {impact.path_ref} requires trace provenance",
                )
            )
        else:
            missing = set(impact.trace_refs) - traces
            if missing:
                issues.append(
                    ValidationIssue(
                        "MS_FEC_PATH_TRACE_UNKNOWN",
                        f"path {impact.path_ref} cites unavailable traces: {sorted(missing)}",
                    )
                )

        if impact.state == PathImpactState.PRESERVED:
            preserved.append(impact.path_ref)
        elif impact.state == PathImpactState.OPENED:
            opened.append(impact.path_ref)
        elif impact.state == PathImpactState.CLOSED:
            closed.append(impact.path_ref)
            if not impact.justification_refs:
                issues.append(
                    ValidationIssue(
                        "MS_FEC_PATH_CLOSURE_UNJUSTIFIED",
                        f"closed viable path {impact.path_ref} requires explicit justification",
                    )
                )
        elif impact.state == PathImpactState.UNKNOWN:
            unknown.append(impact.path_ref)

    statuses = (
        assessment.reprise_status,
        assessment.generation_status,
        assessment.reopening_status,
        assessment.fossilization_risk,
        assessment.dissolution_risk,
    )
    has_invalid = any(x == EvidenceStatus.INVALID_DATA for x in statuses)
    has_insufficient = any(x == EvidenceStatus.INSUFFICIENT_DATA for x in statuses)
    has_contestation = bool(assessment.contestation_refs)
    fossilization_triggered = assessment.fossilization_risk == EvidenceStatus.TRIGGERED
    dissolution_triggered = assessment.dissolution_risk == EvidenceStatus.TRIGGERED

    capability_loss = (
        assessment.reprise_status == EvidenceStatus.NOT_TRIGGERED
        or assessment.reopening_status == EvidenceStatus.NOT_TRIGGERED
    )
    unjustified_closure = any(
        x.code == "MS_FEC_PATH_CLOSURE_UNJUSTIFIED" for x in issues
    )

    if has_contestation:
        verdict = FecundityVerdict.CONTESTED
        status = CoherenceStatus.CONTESTED
    elif has_invalid or has_insufficient or unknown:
        verdict = FecundityVerdict.INDETERMINATE
        status = CoherenceStatus.INDETERMINATE
    elif fossilization_triggered or dissolution_triggered or capability_loss or unjustified_closure:
        verdict = FecundityVerdict.DEGRADED
        status = CoherenceStatus.PARTIAL if issues else CoherenceStatus.CANDIDATE_OK
    elif issues:
        verdict = FecundityVerdict.INDETERMINATE
        status = CoherenceStatus.PARTIAL
    else:
        verdict = FecundityVerdict.SUSTAINED
        status = CoherenceStatus.CANDIDATE_OK

    return FecundityReport(
        scale=assessment.scale,
        verdict=verdict,
        status=status,
        issues=tuple(issues),
        preserved_path_refs=tuple(preserved),
        opened_path_refs=tuple(opened),
        closed_path_refs=tuple(closed),
        unknown_path_refs=tuple(unknown),
        fossilization_triggered=fossilization_triggered,
        dissolution_triggered=dissolution_triggered,
        scalar_score=None,
        optimality_claim=False,
        execution_authority=False,
    )


def validate_multiscale_fecundity(
    reports: Sequence[FecundityReport],
) -> MultiscaleFecundityReport:
    """Repeat the same non-scalar fecundity contract at all four scales."""
    issues: list[ValidationIssue] = []
    by_scale: dict[Scale, FecundityReport] = {}

    for report in reports:
        if report.scale in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_FEC_SCALE_DUPLICATE",
                    f"duplicate fecundity report for {report.scale.value}",
                )
            )
        else:
            by_scale[report.scale] = report

    for scale in Scale:
        if scale not in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_FEC_SCALE_MISSING",
                    f"missing fecundity report for {scale.value}",
                )
            )

    verdicts = [x.verdict for x in reports]
    if FecundityVerdict.CONTESTED in verdicts:
        verdict = FecundityVerdict.CONTESTED
        status = CoherenceStatus.CONTESTED
    elif FecundityVerdict.INDETERMINATE in verdicts:
        verdict = FecundityVerdict.INDETERMINATE
        status = CoherenceStatus.INDETERMINATE
    elif FecundityVerdict.DEGRADED in verdicts:
        verdict = FecundityVerdict.DEGRADED
        status = CoherenceStatus.PARTIAL if issues else CoherenceStatus.CANDIDATE_OK
    elif issues:
        verdict = FecundityVerdict.INDETERMINATE
        status = CoherenceStatus.PARTIAL
    else:
        verdict = FecundityVerdict.SUSTAINED
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleFecundityReport(
        verdict=verdict,
        status=status,
        scale_reports=tuple(reports),
        issues=tuple(issues),
        scalar_score=None,
        optimality_claim=False,
        execution_authority=False,
    )
