"""Cross-horizon, multi-scale coherence without consensus laundering.

The same contract is applied at micro, meso, macro, and meta scales:
- each assessment is local to one explicit LocalHorizon;
- support from mirrors of the same origin is not independent corroboration;
- agreement never becomes truth or execution authority;
- challenge and indeterminacy remain visible across scale aggregation.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Mapping, Sequence

from .horizon_reciprocity import LocalHorizon
from .multiscale_coherence import CoherenceStatus, Scale, ValidationIssue


class HorizonStance(str, Enum):
    SUPPORT = "support"
    CHALLENGE = "challenge"
    INDETERMINATE = "indeterminate"


@dataclass(frozen=True)
class HorizonAssessment:
    assessment_id: str
    scale: Scale
    horizon_hash: str
    observer_ref: str
    property_ref: str
    property_version: str
    distinction_ref: str
    stance: HorizonStance
    evidence_trace_refs: tuple[str, ...]
    origin_refs: tuple[str, ...]
    provenance_bundle_refs: tuple[str, ...]


@dataclass(frozen=True)
class HorizonFamilyReport:
    scale: Scale
    property_ref: str
    property_version: str
    distinction_ref: str
    status: CoherenceStatus
    issues: tuple[ValidationIssue, ...] = ()
    assessment_ids: tuple[str, ...] = ()
    support_ids: tuple[str, ...] = ()
    challenge_ids: tuple[str, ...] = ()
    indeterminate_ids: tuple[str, ...] = ()
    structurally_distinct_support: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


@dataclass(frozen=True)
class MultiscaleHorizonReport:
    status: CoherenceStatus
    scale_reports: tuple[HorizonFamilyReport, ...]
    issues: tuple[ValidationIssue, ...] = ()
    has_challenge: bool = False
    has_indeterminate: bool = False
    independent_validation: bool = False
    execution_authority: bool = False


def _overlap(left: Sequence[str], right: Sequence[str]) -> bool:
    return bool(set(left) & set(right))


def _has_structurally_distinct_support(
    support: Sequence[HorizonAssessment],
) -> bool:
    """Require two supports separated by horizon, observer, origin and provenance.

    This establishes only structural separation of supporting evidence paths.
    It does not prove statistical, institutional, or causal independence.
    """
    for i, left in enumerate(support):
        for right in support[i + 1 :]:
            if left.horizon_hash == right.horizon_hash:
                continue
            if left.observer_ref == right.observer_ref:
                continue
            if _overlap(left.origin_refs, right.origin_refs):
                continue
            if _overlap(left.provenance_bundle_refs, right.provenance_bundle_refs):
                continue
            return True
    return False


def validate_horizon_family(
    horizons: Mapping[str, LocalHorizon],
    assessments: Sequence[HorizonAssessment],
) -> HorizonFamilyReport:
    """Apply one cross-horizon contract at one scale/property/distinction."""
    if not assessments:
        raise ValueError("at least one assessment is required")

    issues: list[ValidationIssue] = []
    first = assessments[0]
    scale = first.scale
    property_ref = first.property_ref
    property_version = first.property_version
    distinction_ref = first.distinction_ref

    seen_assessment_ids: set[str] = set()
    seen_horizon_stance: set[tuple[str, HorizonStance]] = set()

    for item in assessments:
        if item.assessment_id in seen_assessment_ids:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_DUPLICATE",
                    f"duplicate assessment id: {item.assessment_id}",
                )
            )
        seen_assessment_ids.add(item.assessment_id)

        if item.scale != scale:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_SCALE_MIXED",
                    "one horizon family cannot mix scales",
                )
            )
        if item.property_ref != property_ref or item.property_version != property_version:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_PROPERTY_MIXED",
                    "one horizon family cannot mix property contracts",
                )
            )
        if item.distinction_ref != distinction_ref:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_DISTINCTION_MIXED",
                    "one horizon family cannot mix local distinction refs",
                )
            )

        horizon = horizons.get(item.horizon_hash)
        if horizon is None:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_UNKNOWN_HORIZON",
                    f"assessment {item.assessment_id} cites an unknown horizon",
                )
            )
            continue

        if horizon.scale != item.scale:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_SCALE_MISMATCH",
                    f"assessment {item.assessment_id} scale differs from horizon",
                )
            )
        if horizon.observer_ref != item.observer_ref:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_OBSERVER_MISMATCH",
                    f"assessment {item.assessment_id} observer differs from horizon",
                )
            )
        if (
            horizon.property_ref != item.property_ref
            or horizon.property_version != item.property_version
        ):
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_PROPERTY_MISMATCH",
                    f"assessment {item.assessment_id} property differs from horizon",
                )
            )

        if not item.evidence_trace_refs:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_EVIDENCE_REQUIRED",
                    f"assessment {item.assessment_id} has no evidence trace refs",
                )
            )
        if not item.origin_refs:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_ORIGIN_REQUIRED",
                    f"assessment {item.assessment_id} has no origin refs",
                )
            )
        if not item.provenance_bundle_refs:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_ASSESSMENT_PROVENANCE_REQUIRED",
                    f"assessment {item.assessment_id} has no provenance bundle refs",
                )
            )

        key = (item.horizon_hash, item.stance)
        if key in seen_horizon_stance:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_STANCE_DUPLICATE",
                    "repeating the same stance from the same horizon adds no corroboration",
                )
            )
        seen_horizon_stance.add(key)

    support = [x for x in assessments if x.stance == HorizonStance.SUPPORT]
    challenge = [x for x in assessments if x.stance == HorizonStance.CHALLENGE]
    indeterminate = [x for x in assessments if x.stance == HorizonStance.INDETERMINATE]
    distinct_support = _has_structurally_distinct_support(support)

    if len(support) >= 2 and not distinct_support:
        issues.append(
            ValidationIssue(
                "MS_HORIZON_SUPPORT_NOT_DISTINCT",
                "multiple supports share horizon/observer/origin/provenance and do not count as structurally distinct corroboration",
            )
        )

    if challenge:
        status = CoherenceStatus.CONTESTED
    elif indeterminate:
        status = CoherenceStatus.INDETERMINATE
    elif issues:
        status = CoherenceStatus.PARTIAL
    elif distinct_support:
        status = CoherenceStatus.CANDIDATE_OK
    else:
        status = CoherenceStatus.PARTIAL
        issues.append(
            ValidationIssue(
                "MS_HORIZON_CORROBORATION_INSUFFICIENT",
                "no structurally distinct cross-horizon support pair is present",
            )
        )

    return HorizonFamilyReport(
        scale=scale,
        property_ref=property_ref,
        property_version=property_version,
        distinction_ref=distinction_ref,
        status=status,
        issues=tuple(issues),
        assessment_ids=tuple(x.assessment_id for x in assessments),
        support_ids=tuple(x.assessment_id for x in support),
        challenge_ids=tuple(x.assessment_id for x in challenge),
        indeterminate_ids=tuple(x.assessment_id for x in indeterminate),
        structurally_distinct_support=distinct_support,
        independent_validation=False,
        execution_authority=False,
    )


def validate_multiscale_horizon_reports(
    scale_reports: Sequence[HorizonFamilyReport],
) -> MultiscaleHorizonReport:
    """Aggregate four scale-local reports without forcing equal conclusions."""
    issues: list[ValidationIssue] = []
    by_scale: dict[Scale, HorizonFamilyReport] = {}

    for report in scale_reports:
        if report.scale in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_SCALE_REPORT_DUPLICATE",
                    f"multiple family reports supplied for scale {report.scale.value}",
                )
            )
        else:
            by_scale[report.scale] = report

    for scale in Scale:
        if scale not in by_scale:
            issues.append(
                ValidationIssue(
                    "MS_HORIZON_SCALE_REPORT_MISSING",
                    f"missing horizon-family report for scale {scale.value}",
                )
            )

    has_challenge = any(x.status == CoherenceStatus.CONTESTED for x in scale_reports)
    has_indeterminate = any(x.status == CoherenceStatus.INDETERMINATE for x in scale_reports)
    has_partial = any(x.status == CoherenceStatus.PARTIAL for x in scale_reports)

    if has_challenge:
        status = CoherenceStatus.CONTESTED
    elif has_indeterminate:
        status = CoherenceStatus.INDETERMINATE
    elif issues or has_partial:
        status = CoherenceStatus.PARTIAL
    else:
        status = CoherenceStatus.CANDIDATE_OK

    return MultiscaleHorizonReport(
        status=status,
        scale_reports=tuple(scale_reports),
        issues=tuple(issues),
        has_challenge=has_challenge,
        has_indeterminate=has_indeterminate,
        independent_validation=False,
        execution_authority=False,
    )
