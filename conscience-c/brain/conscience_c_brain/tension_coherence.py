"""Tension/coherence field for Architecture C.

This module keeps coherence verdicts and tension states on separate axes.
It does not assume that tension implies incoherence, that coherence implies
tension-free structure, or that every tension is generative.

The same contract is applied at micro, meso, macro, and meta scales.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .multiscale_coherence import CoherenceStatus, Scale, ValidationIssue


class LocalCoherenceVerdict(str, Enum):
    COHERENT = "coherent"
    INCOHERENT = "incoherent"
    CONTESTED = "contested"
    INDETERMINATE = "indeterminate"


class TensionDisposition(str, Enum):
    CONSTITUTIVE = "constitutive"
    RESOLVABLE = "resolvable"
    INDETERMINATE = "indeterminate"
    OUT_OF_SCOPE = "out_of_scope"


class GenerativityStatus(str, Enum):
    UNESTABLISHED = "unestablished"
    SUPPORTED = "supported"
    CONTESTED = "contested"


@dataclass(frozen=True)
class TensionRecord:
    tension_id: str
    scale: Scale
    observer_ref: str
    scope_ref: str
    property_ref: str
    property_version: str
    relation_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    disposition: TensionDisposition
    justification_refs: tuple[str, ...]
    generativity_status: GenerativityStatus = GenerativityStatus.UNESTABLISHED
    generativity_evidence_refs: tuple[str, ...] = ()
    contestation_refs: tuple[str, ...] = ()


@dataclass(frozen=True)
class CoherenceClaim:
    claim_id: str
    scale: Scale
    observer_ref: str
    scope_ref: str
    property_ref: str
    property_version: str
    verdict: LocalCoherenceVerdict
    relation_refs: tuple[str, ...]
    trace_refs: tuple[str, ...]
    justification_refs: tuple[str, ...]
    claims_tension_exhaustiveness: bool = False


@dataclass(frozen=True)
class TensionCoherenceReport:
    scale: Scale
    coherence_verdict: LocalCoherenceVerdict
    status: CoherenceStatus
    tension_ids: tuple[str, ...]
    constitutive_ids: tuple[str, ...] = ()
    resolvable_ids: tuple[str, ...] = ()
    indeterminate_ids: tuple[str, ...] = ()
    out_of_scope_ids: tuple[str, ...] = ()
    generativity_supported_ids: tuple[str, ...] = ()
    issues: tuple[ValidationIssue, ...] = ()
    has_contestation: bool = False
    has_indeterminate: bool = False
    tension_exhaustive: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class MultiscaleTensionCoherenceReport:
    status: CoherenceStatus
    scale_reports: tuple[TensionCoherenceReport, ...]
    issues: tuple[ValidationIssue, ...] = ()
    has_contestation: bool = False
    has_indeterminate: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


def _same_contract(claim: CoherenceClaim, tension: TensionRecord) -> bool:
    return (
        claim.scale == tension.scale
        and claim.observer_ref == tension.observer_ref
        and claim.scope_ref == tension.scope_ref
        and claim.property_ref == tension.property_ref
        and claim.property_version == tension.property_version
    )


def validate_tension_coherence(
    claim: CoherenceClaim,
    tensions: Sequence[TensionRecord],
    *,
    available_trace_refs: Sequence[str],
    available_generativity_evidence_refs: Sequence[str] = (),
) -> TensionCoherenceReport:
    """Validate one local coherence/tension field without collapsing the axes."""
    issues: list[ValidationIssue] = []
    available_traces = set(available_trace_refs)
    available_generativity = set(available_generativity_evidence_refs)

    if not claim.observer_ref or not claim.scope_ref:
        issues.append(
            ValidationIssue(
                "MS_TC_CONTEXT_REQUIRED",
                "coherence claim requires observer and scope refs",
            )
        )
    if not claim.property_ref or not claim.property_version:
        issues.append(
            ValidationIssue(
                "MS_TC_PROPERTY_REQUIRED",
                "coherence claim requires property_ref and property_version",
            )
        )
    if not claim.trace_refs:
        issues.append(
            ValidationIssue(
                "MS_TC_COHERENCE_TRACE_REQUIRED",
                "coherence claim requires trace provenance",
            )
        )
    else:
        missing = set(claim.trace_refs) - available_traces
        if missing:
            issues.append(
                ValidationIssue(
                    "MS_TC_COHERENCE_TRACE_UNKNOWN",
                    f"coherence claim cites unavailable traces: {sorted(missing)}",
                )
            )
    if not claim.justification_refs:
        issues.append(
            ValidationIssue(
                "MS_TC_COHERENCE_JUSTIFICATION_REQUIRED",
                "coherence verdict requires explicit justification",
            )
        )
    if claim.claims_tension_exhaustiveness:
        issues.append(
            ValidationIssue(
                "MS_TC_TENSION_TOTALITY_FORBIDDEN",
                "a local coherence claim cannot certify that all relevant tensions are known",
            )
        )

    seen_ids: set[str] = set()
    constitutive: list[str] = []
    resolvable: list[str] = []
    indeterminate: list[str] = []
    out_of_scope: list[str] = []
    generativity_supported: list[str] = []
    has_contestation = claim.verdict == LocalCoherenceVerdict.CONTESTED
    has_indeterminate = claim.verdict == LocalCoherenceVerdict.INDETERMINATE

    for tension in tensions:
        if tension.tension_id in seen_ids:
            issues.append(
                ValidationIssue(
                    "MS_TC_TENSION_DUPLICATE",
                    f"duplicate tension id: {tension.tension_id}",
                )
            )
        seen_ids.add(tension.tension_id)

        if not _same_contract(claim, tension):
            issues.append(
                ValidationIssue(
                    "MS_TC_CONTRACT_MISMATCH",
                    f"tension {tension.tension_id} is outside the coherence claim contract",
                )
            )

        if len(tension.relation_refs) < 2:
            issues.append(
                ValidationIssue(
                    "MS_TC_RELATION_PLURALITY_REQUIRED",
                    f"tension {tension.tension_id} requires at least two relation refs",
                )
            )

        if not tension.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_TC_TENSION_TRACE_REQUIRED",
                    f"tension {tension.tension_id} has no trace provenance",
                )
            )
        else:
            missing_traces = set(tension.trace_refs) - available_traces
            if missing_traces:
                issues.append(
                    ValidationIssue(
                        "MS_TC_TENSION_TRACE_UNKNOWN",
                        f"tension {tension.tension_id} cites unavailable traces: {sorted(missing_traces)}",
                    )
                )

        if not tension.justification_refs:
            issues.append(
                ValidationIssue(
                    "MS_TC_TENSION_JUSTIFICATION_REQUIRED",
                    f"tension {tension.tension_id} requires explicit justification",
                )
            )

        if tension.disposition == TensionDisposition.CONSTITUTIVE:
            constitutive.append(tension.tension_id)
        elif tension.disposition == TensionDisposition.RESOLVABLE:
            resolvable.append(tension.tension_id)
        elif tension.disposition == TensionDisposition.INDETERMINATE:
            indeterminate.append(tension.tension_id)
            has_indeterminate = True
        elif tension.disposition == TensionDisposition.OUT_OF_SCOPE:
            out_of_scope.append(tension.tension_id)

        if tension.generativity_status == GenerativityStatus.SUPPORTED:
            if not tension.generativity_evidence_refs:
                issues.append(
                    ValidationIssue(
                        "MS_TC_GENERATIVITY_EVIDENCE_REQUIRED",
                        f"tension {tension.tension_id} claims generativity without evidence refs",
                    )
                )
            else:
                missing_generativity = (
                    set(tension.generativity_evidence_refs) - available_generativity
                )
                if missing_generativity:
                    issues.append(
                        ValidationIssue(
                            "MS_TC_GENERATIVITY_EVIDENCE_UNKNOWN",
                            f"tension {tension.tension_id} cites unavailable generativity evidence: {sorted(missing_generativity)}",
                        )
                    )
                else:
                    generativity_supported.append(tension.tension_id)
        elif tension.generativity_status == GenerativityStatus.CONTESTED:
            has_contestation = True

        if tension.contestation_refs:
            has_contestation = True

    if has_contestation:
        status = CoherenceStatus.CONTESTED
    elif has_indeterminate:
        status = CoherenceStatus.INDETERMINATE
    elif issues:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return TensionCoherenceReport(
        scale=claim.scale,
        coherence_verdict=claim.verdict,
        status=status,
        tension_ids=tuple(x.tension_id for x in tensions),
        constitutive_ids=tuple(constitutive),
        resolvable_ids=tuple(resolvable),
        indeterminate_ids=tuple(indeterminate),
        out_of_scope_ids=tuple(out_of_scope),
        generativity_supported_ids=tuple(generativity_supported),
        issues=tuple(issues),
        has_contestation=has_contestation,
        has_indeterminate=has_indeterminate,
        tension_exhaustive=False,
        independent_validation=False,
        execution_authority=False,
    )


def validate_multiscale_tension_coherence(
    reports: Sequence[TensionCoherenceReport],
) -> MultiscaleTensionCoherenceReport:
    """Repeat the same tension/coherence contract at all four scales."""
    issues: list[ValidationIssue] = []
    by_scale: dict[Scale, TensionCoherenceReport] = {}

    for report in reports:
        if report.scale in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_TC_SCALE_DUPLICATE",
                    f"duplicate tension/coherence report for {report.scale.value}",
                )
            )
        else:
            by_scale[report.scale] = report

    for scale in Scale:
        if scale not in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_TC_SCALE_MISSING",
                    f"missing tension/coherence report for {scale.value}",
                )
            )

    has_contestation = any(x.has_contestation for x in reports)
    has_indeterminate = any(x.has_indeterminate for x in reports)
    has_partial = any(x.status == CoherenceStatus.PARTIAL for x in reports)

    if has_contestation:
        status = CoherenceStatus.CONTESTED
    elif has_indeterminate:
        status = CoherenceStatus.INDETERMINATE
    elif issues or has_partial:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleTensionCoherenceReport(
        status=status,
        scale_reports=tuple(reports),
        issues=tuple(issues),
        has_contestation=has_contestation,
        has_indeterminate=has_indeterminate,
        independent_validation=False,
        execution_authority=False,
    )
