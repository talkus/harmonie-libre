"""Candidate generator-ensemble reconstruction for Architecture C.

Xi is never treated as a directly observed or unique underlying dynamics.
The runtime maintains a revisable set of generator hypotheses reconstructed
from local projection claims and trace-backed observations.

No scalar ranking, truth promotion, or execution authority is provided.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .multiscale_coherence import CoherenceStatus, Scale, ValidationIssue


class HypothesisFit(str, Enum):
    COMPATIBLE = "compatible"
    INCOMPATIBLE = "incompatible"
    UNDERDETERMINED = "underdetermined"


@dataclass(frozen=True)
class ProjectionClaim:
    dimension: str
    value_ref: str


@dataclass(frozen=True)
class GeneratorHypothesis:
    hypothesis_id: str
    scale: Scale
    observer_ref: str
    scope_ref: str
    projection_claims: tuple[ProjectionClaim, ...]
    assumption_refs: tuple[str, ...]
    origin_refs: tuple[str, ...]
    provenance_bundle_refs: tuple[str, ...]


@dataclass(frozen=True)
class ProjectionEvidence:
    evidence_id: str
    scale: Scale
    observer_ref: str
    scope_ref: str
    observations: tuple[ProjectionClaim, ...]
    trace_refs: tuple[str, ...]


@dataclass(frozen=True)
class HypothesisAssessment:
    hypothesis_id: str
    fit: HypothesisFit
    matched_dimensions: tuple[str, ...] = ()
    conflicting_dimensions: tuple[str, ...] = ()
    unobserved_claim_dimensions: tuple[str, ...] = ()
    issues: tuple[ValidationIssue, ...] = ()
    execution_authority: bool = False


@dataclass(frozen=True)
class HypothesisSpaceRevision:
    revision_id: str
    scale: Scale
    previous_hypothesis_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    retained_hypothesis_ids: tuple[str, ...]
    underdetermined_hypothesis_ids: tuple[str, ...]
    rejected_hypothesis_ids: tuple[str, ...]
    added_hypothesis_ids: tuple[str, ...]
    observational_equivalence_classes: tuple[tuple[str, ...], ...]
    unknown_xi: bool
    out_of_model: bool
    status: CoherenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    independent_validation: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class MultiscaleHypothesisReport:
    status: CoherenceStatus
    revisions: tuple[HypothesisSpaceRevision, ...]
    issues: tuple[ValidationIssue, ...] = ()
    has_unknown_xi: bool = False
    has_out_of_model: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


def _claims_map(claims: Sequence[ProjectionClaim]) -> tuple[dict[str, str], list[ValidationIssue]]:
    values: dict[str, str] = {}
    issues: list[ValidationIssue] = []
    for claim in claims:
        if not claim.dimension:
            issues.append(
                ValidationIssue(
                    "MS_XI_DIMENSION_REQUIRED",
                    "projection dimension must be explicit",
                )
            )
            continue
        if claim.dimension in values and values[claim.dimension] != claim.value_ref:
            issues.append(
                ValidationIssue(
                    "MS_XI_DIMENSION_CONFLICT",
                    f"dimension {claim.dimension} has conflicting values in one record",
                )
            )
        values[claim.dimension] = claim.value_ref
    return values, issues


def validate_generator_hypothesis(hypothesis: GeneratorHypothesis) -> tuple[ValidationIssue, ...]:
    issues: list[ValidationIssue] = []
    if not hypothesis.projection_claims:
        issues.append(
            ValidationIssue(
                "MS_XI_PROJECTION_REQUIRED",
                "generator hypothesis requires at least one explicit projection claim",
            )
        )
    _, claim_issues = _claims_map(hypothesis.projection_claims)
    issues.extend(claim_issues)
    if not hypothesis.assumption_refs:
        issues.append(
            ValidationIssue(
                "MS_XI_ASSUMPTION_REQUIRED",
                "generator hypothesis must expose at least one assumption ref",
            )
        )
    if not hypothesis.origin_refs:
        issues.append(
            ValidationIssue(
                "MS_XI_ORIGIN_REQUIRED",
                "generator hypothesis requires origin provenance",
            )
        )
    if not hypothesis.provenance_bundle_refs:
        issues.append(
            ValidationIssue(
                "MS_XI_PROVENANCE_REQUIRED",
                "generator hypothesis requires a provenance bundle ref",
            )
        )
    return tuple(issues)


def assess_hypothesis(
    hypothesis: GeneratorHypothesis,
    evidence: Sequence[ProjectionEvidence],
) -> HypothesisAssessment:
    issues: list[ValidationIssue] = list(validate_generator_hypothesis(hypothesis))
    hypothesis_map, _ = _claims_map(hypothesis.projection_claims)
    observed: dict[str, str] = {}

    for item in evidence:
        if item.scale != hypothesis.scale:
            issues.append(
                ValidationIssue(
                    "MS_XI_EVIDENCE_SCALE_MISMATCH",
                    f"evidence {item.evidence_id} is from another scale",
                )
            )
            continue
        if item.observer_ref != hypothesis.observer_ref:
            issues.append(
                ValidationIssue(
                    "MS_XI_EVIDENCE_OBSERVER_MISMATCH",
                    f"evidence {item.evidence_id} is from another observer contract",
                )
            )
            continue
        if item.scope_ref != hypothesis.scope_ref:
            issues.append(
                ValidationIssue(
                    "MS_XI_EVIDENCE_SCOPE_MISMATCH",
                    f"evidence {item.evidence_id} is from another scope",
                )
            )
            continue
        if not item.trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_XI_EVIDENCE_TRACE_REQUIRED",
                    f"evidence {item.evidence_id} has no trace provenance",
                )
            )
        values, evidence_issues = _claims_map(item.observations)
        issues.extend(evidence_issues)
        for dimension, value_ref in values.items():
            if dimension in observed and observed[dimension] != value_ref:
                issues.append(
                    ValidationIssue(
                        "MS_XI_EVIDENCE_INTERNAL_CONFLICT",
                        f"evidence disagrees with itself on dimension {dimension}",
                    )
                )
            observed[dimension] = value_ref

    overlap = sorted(set(hypothesis_map) & set(observed))
    conflicts = tuple(
        dimension
        for dimension in overlap
        if hypothesis_map[dimension] != observed[dimension]
    )
    matches = tuple(
        dimension
        for dimension in overlap
        if hypothesis_map[dimension] == observed[dimension]
    )
    unobserved = tuple(sorted(set(hypothesis_map) - set(observed)))

    if conflicts:
        fit = HypothesisFit.INCOMPATIBLE
    elif not overlap:
        fit = HypothesisFit.UNDERDETERMINED
    elif issues:
        fit = HypothesisFit.UNDERDETERMINED
    else:
        fit = HypothesisFit.COMPATIBLE

    return HypothesisAssessment(
        hypothesis_id=hypothesis.hypothesis_id,
        fit=fit,
        matched_dimensions=matches,
        conflicting_dimensions=conflicts,
        unobserved_claim_dimensions=unobserved,
        issues=tuple(issues),
        execution_authority=False,
    )


def _observation_signature(
    hypothesis: GeneratorHypothesis,
    evidence: Sequence[ProjectionEvidence],
) -> tuple[tuple[str, str], ...]:
    observed_dimensions: set[str] = set()
    for item in evidence:
        if (
            item.scale == hypothesis.scale
            and item.observer_ref == hypothesis.observer_ref
            and item.scope_ref == hypothesis.scope_ref
        ):
            observed_dimensions.update(x.dimension for x in item.observations)
    claims, _ = _claims_map(hypothesis.projection_claims)
    return tuple(
        sorted(
            (dimension, claims[dimension])
            for dimension in observed_dimensions
            if dimension in claims
        )
    )


def revise_hypothesis_space(
    *,
    revision_id: str,
    scale: Scale,
    current_hypotheses: Sequence[GeneratorHypothesis],
    evidence: Sequence[ProjectionEvidence],
    proposed_hypotheses: Sequence[GeneratorHypothesis] = (),
) -> HypothesisSpaceRevision:
    """Revise X-space without selecting a unique hidden generator by default."""
    issues: list[ValidationIssue] = []
    all_hypotheses = tuple(current_hypotheses) + tuple(proposed_hypotheses)

    ids = [x.hypothesis_id for x in all_hypotheses]
    if len(ids) != len(set(ids)):
        issues.append(
            ValidationIssue(
                "MS_XI_HYPOTHESIS_ID_DUPLICATE",
                "hypothesis ids must be unique within one revision",
            )
        )

    if any(x.scale != scale for x in all_hypotheses):
        issues.append(
            ValidationIssue(
                "MS_XI_HYPOTHESIS_SCALE_MIXED",
                "one hypothesis-space revision cannot mix scales",
            )
        )

    if not evidence:
        issues.append(
            ValidationIssue(
                "MS_XI_EVIDENCE_REQUIRED",
                "hypothesis-space revision requires at least one observation bundle",
            )
        )

    assessments = {
        x.hypothesis_id: assess_hypothesis(x, evidence)
        for x in all_hypotheses
    }
    for report in assessments.values():
        issues.extend(report.issues)

    retained = tuple(
        x.hypothesis_id
        for x in all_hypotheses
        if assessments[x.hypothesis_id].fit == HypothesisFit.COMPATIBLE
    )
    underdetermined = tuple(
        x.hypothesis_id
        for x in all_hypotheses
        if assessments[x.hypothesis_id].fit == HypothesisFit.UNDERDETERMINED
    )
    rejected = tuple(
        x.hypothesis_id
        for x in all_hypotheses
        if assessments[x.hypothesis_id].fit == HypothesisFit.INCOMPATIBLE
    )

    admissible_ids = set(retained) | set(underdetermined)
    out_of_model = len(admissible_ids) == 0
    unknown_xi = (
        not out_of_model
        and (len(admissible_ids) != 1 or bool(underdetermined))
    )

    signature_groups: dict[tuple[tuple[str, str], ...], list[str]] = {}
    hypothesis_by_id = {x.hypothesis_id: x for x in all_hypotheses}
    for hypothesis_id in sorted(admissible_ids):
        signature = _observation_signature(hypothesis_by_id[hypothesis_id], evidence)
        signature_groups.setdefault(signature, []).append(hypothesis_id)

    equivalence_classes = tuple(
        tuple(group)
        for _, group in sorted(signature_groups.items(), key=lambda item: repr(item[0]))
        if len(group) > 1
    )

    if out_of_model:
        issues.append(
            ValidationIssue(
                "MS_XI_OUT_OF_MODEL",
                "no current or proposed generator hypothesis remains compatible with the evidence",
            )
        )
        status = CoherenceStatus.PARTIAL
    elif unknown_xi:
        status = CoherenceStatus.INDETERMINATE
    elif issues:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return HypothesisSpaceRevision(
        revision_id=revision_id,
        scale=scale,
        previous_hypothesis_ids=tuple(x.hypothesis_id for x in current_hypotheses),
        evidence_ids=tuple(x.evidence_id for x in evidence),
        retained_hypothesis_ids=retained,
        underdetermined_hypothesis_ids=underdetermined,
        rejected_hypothesis_ids=rejected,
        added_hypothesis_ids=tuple(x.hypothesis_id for x in proposed_hypotheses),
        observational_equivalence_classes=equivalence_classes,
        unknown_xi=unknown_xi,
        out_of_model=out_of_model,
        status=status,
        issues=tuple(issues),
        independent_validation=False,
        execution_authority=False,
    )


def validate_multiscale_hypothesis_space(
    revisions: Sequence[HypothesisSpaceRevision],
) -> MultiscaleHypothesisReport:
    """Apply the same X-space revision contract at all four scales."""
    issues: list[ValidationIssue] = []
    by_scale: dict[Scale, HypothesisSpaceRevision] = {}

    for revision in revisions:
        if revision.scale in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_XI_SCALE_DUPLICATE",
                    f"duplicate hypothesis-space revision for {revision.scale.value}",
                )
            )
        else:
            by_scale[revision.scale] = revision

    for scale in Scale:
        if scale not in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_XI_SCALE_MISSING",
                    f"missing hypothesis-space revision for {scale.value}",
                )
            )

    has_out_of_model = any(x.out_of_model for x in revisions)
    has_unknown_xi = any(x.unknown_xi for x in revisions)
    has_partial = any(x.status == CoherenceStatus.PARTIAL for x in revisions)

    if has_out_of_model:
        status = CoherenceStatus.PARTIAL
    elif has_unknown_xi:
        status = CoherenceStatus.INDETERMINATE
    elif issues or has_partial:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleHypothesisReport(
        status=status,
        revisions=tuple(revisions),
        issues=tuple(issues),
        has_unknown_xi=has_unknown_xi,
        has_out_of_model=has_out_of_model,
        independent_validation=False,
        execution_authority=False,
    )
