import unittest

from conscience_c_brain.memory_flow import (
    MemoryFlowAssessment,
    MemoryFlowVerdict,
    RecallMeasurement,
    validate_memory_flow,
    validate_multiscale_memory_flow,
)
from conscience_c_brain.multiscale_coherence import CoherenceStatus, EvidenceStatus, Scale


def assessment(
    scale=Scale.MICRO,
    *,
    reconstruction=EvidenceStatus.TRIGGERED,
    exploration=EvidenceStatus.INSUFFICIENT_DATA,
    continuity=EvidenceStatus.TRIGGERED,
    capture=EvidenceStatus.NOT_TRIGGERED,
    diffusion=EvidenceStatus.NOT_TRIGGERED,
    recall=None,
    contestation_refs=(),
):
    return MemoryFlowAssessment(
        assessment_id=f"mem:{scale.value}",
        scale=scale,
        form_ref=f"form:{scale.value}",
        observer_ref=f"observer:{scale.value}",
        scope_ref=f"scope:{scale.value}",
        property_ref="property:memory-flow",
        property_version="1",
        reconstruction_status=reconstruction,
        reconstruction_evidence_refs=(f"evidence:reconstruction:{scale.value}",),
        exploration_status=exploration,
        exploration_evidence_refs=(f"evidence:exploration:{scale.value}",),
        continuity_status=continuity,
        continuity_evidence_refs=(f"evidence:continuity:{scale.value}",),
        capture_risk=capture,
        capture_evidence_refs=(f"evidence:capture:{scale.value}",),
        diffusion_risk=diffusion,
        diffusion_evidence_refs=(f"evidence:diffusion:{scale.value}",),
        recall_measurement=recall,
        revision_triggers=("new_structured_novelty",),
        contestation_refs=contestation_refs,
    )


def validate(item):
    evidence = (
        *item.reconstruction_evidence_refs,
        *item.exploration_evidence_refs,
        *item.continuity_evidence_refs,
        *item.capture_evidence_refs,
        *item.diffusion_evidence_refs,
    )
    traces = () if item.recall_measurement is None else item.recall_measurement.trace_refs
    return validate_memory_flow(
        item,
        available_evidence_refs=evidence,
        available_trace_refs=traces,
    )


class MemoryFlowTests(unittest.TestCase):
    def test_hebbian_like_recall_does_not_establish_exploration(self):
        item = assessment(
            exploration=EvidenceStatus.INSUFFICIENT_DATA,
            recall=RecallMeasurement(
                d_in=0.55,
                d_out=0.20,
                coherence=0.99,
                trace_refs=("trace:hebb:1",),
            ),
        )
        report = validate(item)
        self.assertTrue(report.reconstruction_established)
        self.assertFalse(report.exploration_established)
        self.assertTrue(report.recall_improvement_observed)
        self.assertEqual(report.recall_coherence, 0.99)
        self.assertEqual(report.verdict, MemoryFlowVerdict.INDETERMINATE)

    def test_dual_capacity_requires_separate_exploration_evidence(self):
        item = assessment(
            exploration=EvidenceStatus.TRIGGERED,
        )
        report = validate(item)
        self.assertEqual(report.verdict, MemoryFlowVerdict.DUAL_CAPACITY)
        self.assertTrue(report.reconstruction_established)
        self.assertTrue(report.exploration_established)
        self.assertTrue(report.continuity_established)

    def test_reconstruction_dominant_is_distinct_from_capture(self):
        item = assessment(
            exploration=EvidenceStatus.NOT_TRIGGERED,
            capture=EvidenceStatus.TRIGGERED,
        )
        report = validate(item)
        self.assertEqual(report.verdict, MemoryFlowVerdict.RECONSTRUCTION_DOMINANT)

    def test_exploration_dominant_is_distinct_from_diffusion(self):
        item = assessment(
            reconstruction=EvidenceStatus.NOT_TRIGGERED,
            exploration=EvidenceStatus.TRIGGERED,
            diffusion=EvidenceStatus.TRIGGERED,
        )
        report = validate(item)
        self.assertEqual(report.verdict, MemoryFlowVerdict.EXPLORATION_DOMINANT)

    def test_high_coherence_alone_never_proves_dual_capacity(self):
        item = assessment(
            exploration=EvidenceStatus.INSUFFICIENT_DATA,
            recall=RecallMeasurement(
                d_in=0.58,
                d_out=0.19,
                coherence=0.99,
                trace_refs=("trace:hebb:2",),
            ),
        )
        report = validate(item)
        self.assertNotEqual(report.verdict, MemoryFlowVerdict.DUAL_CAPACITY)

    def test_contestation_survives(self):
        report = validate(assessment(contestation_refs=("contest:1",)))
        self.assertEqual(report.verdict, MemoryFlowVerdict.CONTESTED)
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)

    def test_same_contract_operates_at_four_scales(self):
        reports = [
            validate(
                assessment(scale=scale, exploration=EvidenceStatus.TRIGGERED)
            )
            for scale in Scale
        ]
        multi = validate_multiscale_memory_flow(reports)
        self.assertEqual(multi.verdict, MemoryFlowVerdict.DUAL_CAPACITY)
        self.assertEqual(multi.status, CoherenceStatus.CANDIDATE_OK)
        self.assertIsNone(multi.scalar_score)
        self.assertFalse(multi.execution_authority)

    def test_lower_scale_indeterminacy_cannot_be_masked(self):
        reports = []
        for scale in Scale:
            exploration = (
                EvidenceStatus.INSUFFICIENT_DATA
                if scale == Scale.MICRO
                else EvidenceStatus.TRIGGERED
            )
            reports.append(validate(assessment(scale=scale, exploration=exploration)))
        multi = validate_multiscale_memory_flow(reports)
        self.assertEqual(multi.verdict, MemoryFlowVerdict.INDETERMINATE)

    def test_missing_scale_keeps_composite_partial(self):
        local = validate(assessment(exploration=EvidenceStatus.TRIGGERED))
        multi = validate_multiscale_memory_flow((local,))
        self.assertEqual(multi.verdict, MemoryFlowVerdict.INDETERMINATE)
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_MEM_SCALE_MISSING", {x.code for x in multi.issues})


if __name__ == "__main__":
    unittest.main()
