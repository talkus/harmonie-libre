"""Exploration/reconstruction memory guard for Architecture C.

Hebbian-style recall and exploration are treated as distinct capacities.
High recall coherence or perturbation recovery does not establish exploration.
The same non-scalar contract is applied at micro, meso, macro, and meta scales.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import math
from typing import Sequence

from .multiscale_coherence import CoherenceStatus, EvidenceStatus, Scale, ValidationIssue


class MemoryFlowVerdict(str, Enum):
    DUAL_CAPACITY = "dual_capacity"
    RECONSTRUCTION_DOMINANT = "reconstruction_dominant"
    EXPLORATION_DOMINANT = "exploration_dominant"
    INDETERMINATE = "indeterminate"
    CONTESTED = "contested"


@dataclass(frozen=True)
class RecallMeasurement:
    d_in: float | None = None
    d_out: float | None = None
    coherence: float | None = None
    trace_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class MemoryFlowAssessment:
    assessment_id: str
    scale: Scale
    form_ref: str
    observer_ref: str
    scope_ref: str
    property_ref: str
    property_version: str
    reconstruction_status: EvidenceStatus
    reconstruction_evidence_refs: tuple[str, ...]
    exploration_status: EvidenceStatus
    exploration_evidence_refs: tuple[str, ...]
    continuity_status: EvidenceStatus
    continuity_evidence_refs: tuple[str, ...]
    capture_risk: EvidenceStatus
    capture_evidence_refs: tuple[str, ...]
    diffusion_risk: EvidenceStatus
    diffusion_evidence_refs: tuple[str, ...]
    recall_measurement: RecallMeasurement | None = None
    revision_triggers: tuple[str, ...] = ()
    contestation_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class MemoryFlowReport:
    scale: Scale
    verdict: MemoryFlowVerdict
    status: CoherenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    reconstruction_established: bool = False
    exploration_established: bool = False
    continuity_established: bool = False
    recall_improvement_observed: bool | None = None
    recall_coherence: float | None = None
    scalar_score: None = None
    execution_authority: bool = False


@dataclass(frozen=True)
class MultiscaleMemoryFlowReport:
    verdict: MemoryFlowVerdict
    status: CoherenceStatus
    scale_reports: tuple[MemoryFlowReport, ...]
    issues: tuple[ValidationIssue, ...] = ()
    scalar_score: None = None
    execution_authority: bool = False


def _validate_signal(
    *,
    name: str,
    status: EvidenceStatus,
    refs: Sequence[str],
    available: set[str],
    issues: list[ValidationIssue],
) -> None:
    if status in {EvidenceStatus.TRIGGERED, EvidenceStatus.NOT_TRIGGERED}:
        if not refs:
            issues.append(
                ValidationIssue(
                    f"MS_MEM_{name}_EVIDENCE_REQUIRED",
                    f"{name} status requires evidence refs",
                )
            )
        missing = set(refs) - available
        if missing:
            issues.append(
                ValidationIssue(
                    f"MS_MEM_{name}_EVIDENCE_UNKNOWN",
                    f"{name} cites unavailable evidence refs: {sorted(missing)}",
                )
            )


def _valid_metric(value: float | None) -> bool:
    return value is None or (
        not isinstance(value, bool)
        and isinstance(value, (int, float))
        and math.isfinite(value)
    )


def validate_memory_flow(
    assessment: MemoryFlowAssessment,
    *,
    available_evidence_refs: Sequence[str],
    available_trace_refs: Sequence[str],
) -> MemoryFlowReport:
    """Validate recall and exploration as separate memory capacities."""
    issues: list[ValidationIssue] = []
    evidence = set(available_evidence_refs)
    traces = set(available_trace_refs)

    if not assessment.observer_ref or not assessment.scope_ref:
        issues.append(
            ValidationIssue(
                "MS_MEM_CONTEXT_REQUIRED",
                "memory-flow assessment requires observer and scope refs",
            )
        )
    if not assessment.property_ref or not assessment.property_version:
        issues.append(
            ValidationIssue(
                "MS_MEM_PROPERTY_REQUIRED",
                "memory-flow assessment requires property_ref and property_version",
            )
        )
    if not assessment.revision_triggers:
        issues.append(
            ValidationIssue(
                "MS_MEM_REVISION_TRIGGER_REQUIRED",
                "memory-flow assessment must remain reopenable",
            )
        )

    _validate_signal(
        name="RECONSTRUCTION",
        status=assessment.reconstruction_status,
        refs=assessment.reconstruction_evidence_refs,
        available=evidence,
        issues=issues,
    )
    _validate_signal(
        name="EXPLORATION",
        status=assessment.exploration_status,
        refs=assessment.exploration_evidence_refs,
        available=evidence,
        issues=issues,
    )
    _validate_signal(
        name="CONTINUITY",
        status=assessment.continuity_status,
        refs=assessment.continuity_evidence_refs,
        available=evidence,
        issues=issues,
    )
    _validate_signal(
        name="CAPTURE",
        status=assessment.capture_risk,
        refs=assessment.capture_evidence_refs,
        available=evidence,
        issues=issues,
    )
    _validate_signal(
        name="DIFFUSION",
        status=assessment.diffusion_risk,
        refs=assessment.diffusion_evidence_refs,
        available=evidence,
        issues=issues,
    )

    recall_improvement: bool | None = None
    recall_coherence: float | None = None
    if assessment.recall_measurement is not None:
        measurement = assessment.recall_measurement
        for label, value in (
            ("D_IN", measurement.d_in),
            ("D_OUT", measurement.d_out),
            ("COHERENCE", measurement.coherence),
        ):
            if not _valid_metric(value):
                issues.append(
                    ValidationIssue(
                        f"MS_MEM_{label}_INVALID",
                        f"{label} must be finite when provided",
                    )
                )
        if not measurement.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_MEM_RECALL_TRACE_REQUIRED",
                    "recall measurement requires trace provenance",
                )
            )
        missing_traces = set(measurement.trace_refs) - traces
        if measurement.trace_refs and missing_traces:
            issues.append(
                ValidationIssue(
                    "MS_MEM_RECALL_TRACE_UNKNOWN",
                    f"recall measurement cites unavailable traces: {sorted(missing_traces)}",
                )
            )
        traced = bool(measurement.trace_refs) and not missing_traces
        if (traced and measurement.d_in is not None and measurement.d_out is not None
                and _valid_metric(measurement.d_in) and _valid_metric(measurement.d_out)):
            recall_improvement = float(measurement.d_out) < float(measurement.d_in)
        if traced and _valid_metric(measurement.coherence):
            recall_coherence = measurement.coherence

    reconstruction_established = assessment.reconstruction_status == EvidenceStatus.TRIGGERED
    exploration_established = assessment.exploration_status == EvidenceStatus.TRIGGERED
    continuity_established = assessment.continuity_status == EvidenceStatus.TRIGGERED

    statuses = (
        assessment.reconstruction_status,
        assessment.exploration_status,
        assessment.continuity_status,
        assessment.capture_risk,
        assessment.diffusion_risk,
    )
    has_invalid = any(x == EvidenceStatus.INVALID_DATA for x in statuses)
    has_insufficient = any(x == EvidenceStatus.INSUFFICIENT_DATA for x in statuses)
    has_contestation = bool(assessment.contestation_refs)
    capture_triggered = assessment.capture_risk == EvidenceStatus.TRIGGERED
    diffusion_triggered = assessment.diffusion_risk == EvidenceStatus.TRIGGERED

    if has_contestation:
        verdict = MemoryFlowVerdict.CONTESTED
        status = CoherenceStatus.CONTESTED
    elif has_invalid or has_insufficient:
        verdict = MemoryFlowVerdict.INDETERMINATE
        status = CoherenceStatus.INDETERMINATE
    elif reconstruction_established and exploration_established and continuity_established:
        if capture_triggered or diffusion_triggered:
            verdict = MemoryFlowVerdict.INDETERMINATE
            status = CoherenceStatus.PARTIAL
        elif issues:
            verdict = MemoryFlowVerdict.INDETERMINATE
            status = CoherenceStatus.PARTIAL
        else:
            verdict = MemoryFlowVerdict.DUAL_CAPACITY
            status = CoherenceStatus.CANDIDATE_OK
    elif reconstruction_established and assessment.exploration_status == EvidenceStatus.NOT_TRIGGERED:
        verdict = MemoryFlowVerdict.RECONSTRUCTION_DOMINANT
        status = CoherenceStatus.CANDIDATE_OK if not issues else CoherenceStatus.PARTIAL
    elif exploration_established and assessment.reconstruction_status == EvidenceStatus.NOT_TRIGGERED:
        verdict = MemoryFlowVerdict.EXPLORATION_DOMINANT
        status = CoherenceStatus.CANDIDATE_OK if not issues else CoherenceStatus.PARTIAL
    else:
        verdict = MemoryFlowVerdict.INDETERMINATE
        status = CoherenceStatus.INDETERMINATE if not issues else CoherenceStatus.PARTIAL

    return MemoryFlowReport(
        scale=assessment.scale,
        verdict=verdict,
        status=status,
        issues=tuple(issues),
        reconstruction_established=reconstruction_established,
        exploration_established=exploration_established,
        continuity_established=continuity_established,
        recall_improvement_observed=recall_improvement,
        recall_coherence=recall_coherence,
        scalar_score=None,
        execution_authority=False,
    )


def validate_multiscale_memory_flow(
    reports: Sequence[MemoryFlowReport],
) -> MultiscaleMemoryFlowReport:
    """Repeat the reconstruction/exploration contract at all four scales."""
    issues: list[ValidationIssue] = []
    by_scale: dict[Scale, MemoryFlowReport] = {}

    for report in reports:
        if report.status == CoherenceStatus.PARTIAL:
            issues.append(
                ValidationIssue(
                    "MS_MEM_LOCAL_PARTIAL",
                    f"memory-flow report for {report.scale.value} remains partial",
                )
            )
        if report.scale in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_MEM_SCALE_DUPLICATE",
                    f"duplicate memory-flow report for {report.scale.value}",
                )
            )
        else:
            by_scale[report.scale] = report

    for scale in Scale:
        if scale not in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_MEM_SCALE_MISSING",
                    f"missing memory-flow report for {scale.value}",
                )
            )

    verdicts = [x.verdict for x in reports]
    if MemoryFlowVerdict.CONTESTED in verdicts:
        verdict = MemoryFlowVerdict.CONTESTED
        status = CoherenceStatus.CONTESTED
    elif MemoryFlowVerdict.INDETERMINATE in verdicts:
        verdict = MemoryFlowVerdict.INDETERMINATE
        status = CoherenceStatus.INDETERMINATE if not issues else CoherenceStatus.PARTIAL
    elif issues:
        verdict = MemoryFlowVerdict.INDETERMINATE
        status = CoherenceStatus.PARTIAL
    elif all(x == MemoryFlowVerdict.DUAL_CAPACITY for x in verdicts):
        verdict = MemoryFlowVerdict.DUAL_CAPACITY
        status = CoherenceStatus.CANDIDATE_OK
    elif MemoryFlowVerdict.RECONSTRUCTION_DOMINANT in verdicts:
        verdict = MemoryFlowVerdict.RECONSTRUCTION_DOMINANT
        status = CoherenceStatus.CANDIDATE_OK
    elif MemoryFlowVerdict.EXPLORATION_DOMINANT in verdicts:
        verdict = MemoryFlowVerdict.EXPLORATION_DOMINANT
        status = CoherenceStatus.CANDIDATE_OK
    else:
        verdict = MemoryFlowVerdict.INDETERMINATE
        status = CoherenceStatus.INDETERMINATE

    return MultiscaleMemoryFlowReport(
        verdict=verdict,
        status=status,
        scale_reports=tuple(reports),
        issues=tuple(issues),
        scalar_score=None,
        execution_authority=False,
    )
