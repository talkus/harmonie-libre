import unittest

from conscience_c_brain.fecundity_guard import (
    FecundityAssessment,
    FecundityVerdict,
    PathImpact,
    PathImpactState,
    validate_fecundity,
    validate_multiscale_fecundity,
)
from conscience_c_brain.multiscale_coherence import (
    CoherenceStatus,
    EvidenceStatus,
    Scale,
)


def assessment(
    scale=Scale.MICRO,
    *,
    generation_status=EvidenceStatus.TRIGGERED,
    reprise_status=EvidenceStatus.TRIGGERED,
    reopening_status=EvidenceStatus.TRIGGERED,
    fossilization_risk=EvidenceStatus.NOT_TRIGGERED,
    dissolution_risk=EvidenceStatus.NOT_TRIGGERED,
    path_impacts=None,
    contestation_refs=(),
):
    if path_impacts is None:
        path_impacts = (
            PathImpact(
                path_ref=f"path:existing:{scale.value}",
                state=PathImpactState.PRESERVED,
                trace_refs=(f"trace:path:{scale.value}",),
            ),
            PathImpact(
                path_ref=f"path:new:{scale.value}",
                state=PathImpactState.OPENED,
                trace_refs=(f"trace:new:{scale.value}",),
            ),
        )
    return FecundityAssessment(
        assessment_id=f"fec:{scale.value}",
        scale=scale,
        form_ref=f"form:{scale.value}",
        observer_ref=f"observer:{scale.value}",
        scope_ref=f"scope:{scale.value}",
        property_ref="property:fecundity",
        property_version="1",
        reprise_status=reprise_status,
        reprise_evidence_refs=(f"evidence:reprise:{scale.value}",),
        generation_status=generation_status,
        generation_evidence_refs=(f"evidence:generation:{scale.value}",),
        reopening_status=reopening_status,
        reopening_evidence_refs=(f"evidence:reopening:{scale.value}",),
        fossilization_risk=fossilization_risk,
        fossilization_evidence_refs=(f"evidence:fossilization:{scale.value}",),
        dissolution_risk=dissolution_risk,
        dissolution_evidence_refs=(f"evidence:dissolution:{scale.value}",),
        path_impacts=path_impacts,
        revision_triggers=("new_material_evidence",),
        contestation_refs=contestation_refs,
    )


def validate(item):
    traces = tuple(ref for impact in item.path_impacts for ref in impact.trace_refs)
    evidence = (
        *item.reprise_evidence_refs,
        *item.generation_evidence_refs,
        *item.reopening_evidence_refs,
        *item.fossilization_evidence_refs,
        *item.dissolution_evidence_refs,
    )
    return validate_fecundity(
        item,
        available_trace_refs=traces,
        available_evidence_refs=evidence,
    )


class FecundityGuardTests(unittest.TestCase):
    def test_sustained_fecundity_is_non_scalar(self):
        report = validate(assessment())
        self.assertEqual(report.verdict, FecundityVerdict.SUSTAINED)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertIsNone(report.scalar_score)
        self.assertFalse(report.optimality_claim)
        self.assertFalse(report.execution_authority)

    def test_generation_without_reprise_is_degraded_not_fecund(self):
        report = validate(
            assessment(
                generation_status=EvidenceStatus.TRIGGERED,
                reprise_status=EvidenceStatus.NOT_TRIGGERED,
            )
        )
        self.assertEqual(report.verdict, FecundityVerdict.DEGRADED)

    def test_fossilization_risk_degrades_fecundity(self):
        report = validate(assessment(fossilization_risk=EvidenceStatus.TRIGGERED))
        self.assertEqual(report.verdict, FecundityVerdict.DEGRADED)
        self.assertTrue(report.fossilization_triggered)

    def test_dissolution_risk_degrades_fecundity(self):
        report = validate(assessment(dissolution_risk=EvidenceStatus.TRIGGERED))
        self.assertEqual(report.verdict, FecundityVerdict.DEGRADED)
        self.assertTrue(report.dissolution_triggered)

    def test_closed_viable_path_requires_justification(self):
        item = assessment(
            path_impacts=(
                PathImpact(
                    path_ref="path:closed",
                    state=PathImpactState.CLOSED,
                    trace_refs=("trace:path:closed",),
                ),
            )
        )
        report = validate(item)
        self.assertEqual(report.verdict, FecundityVerdict.DEGRADED)
        self.assertIn("MS_FEC_PATH_CLOSURE_UNJUSTIFIED", {x.code for x in report.issues})

    def test_justified_path_closure_is_not_automatically_degraded(self):
        item = assessment(
            path_impacts=(
                PathImpact(
                    path_ref="path:closed",
                    state=PathImpactState.CLOSED,
                    trace_refs=("trace:path:closed",),
                    justification_refs=("decision:bounded-harm",),
                ),
            )
        )
        report = validate(item)
        self.assertEqual(report.verdict, FecundityVerdict.SUSTAINED)

    def test_unknown_path_impact_keeps_fecundity_indeterminate(self):
        item = assessment(
            path_impacts=(
                PathImpact(
                    path_ref="path:unknown",
                    state=PathImpactState.UNKNOWN,
                    trace_refs=("trace:path:unknown",),
                ),
            )
        )
        report = validate(item)
        self.assertEqual(report.verdict, FecundityVerdict.INDETERMINATE)
        self.assertEqual(report.status, CoherenceStatus.INDETERMINATE)

    def test_insufficient_evidence_is_not_absence_of_risk(self):
        report = validate(
            assessment(fossilization_risk=EvidenceStatus.INSUFFICIENT_DATA)
        )
        self.assertEqual(report.verdict, FecundityVerdict.INDETERMINATE)

    def test_contestation_survives(self):
        report = validate(assessment(contestation_refs=("contest:1",)))
        self.assertEqual(report.verdict, FecundityVerdict.CONTESTED)
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)

    def test_no_compulsory_novelty(self):
        item = assessment(
            generation_status=EvidenceStatus.NOT_TRIGGERED,
            path_impacts=(
                PathImpact(
                    path_ref="path:existing",
                    state=PathImpactState.PRESERVED,
                    trace_refs=("trace:path:existing",),
                ),
            ),
        )
        report = validate(item)
        self.assertEqual(report.verdict, FecundityVerdict.SUSTAINED)

    def test_same_contract_operates_at_four_scales(self):
        reports = [validate(assessment(scale=scale)) for scale in Scale]
        multi = validate_multiscale_fecundity(reports)
        self.assertEqual(multi.verdict, FecundityVerdict.SUSTAINED)
        self.assertEqual(multi.status, CoherenceStatus.CANDIDATE_OK)
        self.assertIsNone(multi.scalar_score)
        self.assertFalse(multi.execution_authority)

    def test_lower_scale_degradation_cannot_be_masked(self):
        reports = []
        for scale in Scale:
            fossil = EvidenceStatus.TRIGGERED if scale == Scale.MICRO else EvidenceStatus.NOT_TRIGGERED
            reports.append(validate(assessment(scale=scale, fossilization_risk=fossil)))
        multi = validate_multiscale_fecundity(reports)
        self.assertEqual(multi.verdict, FecundityVerdict.DEGRADED)

    def test_missing_scale_keeps_composite_indeterminate(self):
        multi = validate_multiscale_fecundity((validate(assessment()),))
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertEqual(multi.verdict, FecundityVerdict.INDETERMINATE)
        self.assertIn("MS_FEC_SCALE_MISSING", {x.code for x in multi.issues})


if __name__ == "__main__":
    unittest.main()
