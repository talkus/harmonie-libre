"""Evidence gaps must survive reconstruction and cross-scale aggregation."""
from dataclasses import replace
import unittest

from conscience_c_brain.fecundity_guard import validate_multiscale_fecundity
from conscience_c_brain.generator_ensemble import (
    HypothesisFit, assess_hypothesis, revise_hypothesis_space,
)
from conscience_c_brain.memory_flow import RecallMeasurement, validate_multiscale_memory_flow
from conscience_c_brain.multiscale_coherence import CoherenceStatus, EvidenceStatus, Scale
from test_fecundity_guard import assessment as fecundity, validate as validate_fecundity
from test_generator_ensemble import hypothesis, evidence
from test_memory_flow import assessment as memory, validate as validate_memory


class MultiscaleEvidenceRegressions(unittest.TestCase):
    def test_untraced_observation_cannot_reject_a_hypothesis(self):
        h = hypothesis("xi:1")
        untraced = replace(evidence(observations=(("omega", "closed"),)), trace_refs=())
        report = assess_hypothesis(h, (untraced,))
        self.assertEqual(report.fit, HypothesisFit.UNDERDETERMINED)
        revision = revise_hypothesis_space(revision_id="rev:1", scale=Scale.MICRO,
                                          current_hypotheses=(h,), evidence=(untraced,))
        self.assertEqual(revision.rejected_hypothesis_ids, ())
        self.assertTrue(revision.unknown_xi)
        self.assertFalse(revision.out_of_model)

    def test_conflicting_observations_remain_underdetermined_in_both_orders(self):
        first = evidence("e:1")
        second = evidence("e:2", observations=(("omega", "closed"),))
        for observations in ((first, second), (second, first)):
            with self.subTest(observations=observations):
                report = assess_hypothesis(hypothesis("xi:1"), observations)
                self.assertEqual(report.fit, HypothesisFit.UNDERDETERMINED)
                self.assertIn("MS_XI_EVIDENCE_INTERNAL_CONFLICT", {x.code for x in report.issues})

    def test_partial_memory_report_cannot_become_multiscale_success(self):
        reports = []
        for scale in Scale:
            item = memory(scale, exploration=EvidenceStatus.NOT_TRIGGERED)
            if scale == Scale.MICRO:
                item = replace(item, reconstruction_evidence_refs=())
            reports.append(validate_memory(item))
        self.assertEqual(reports[0].status, CoherenceStatus.PARTIAL)
        self.assertEqual(validate_multiscale_memory_flow(reports).status, CoherenceStatus.PARTIAL)

    def test_partial_fecundity_report_cannot_become_multiscale_success(self):
        reports = []
        for scale in Scale:
            item = fecundity(scale, fossilization_risk=EvidenceStatus.TRIGGERED)
            if scale == Scale.MICRO:
                item = replace(item, fossilization_evidence_refs=())
            reports.append(validate_fecundity(item))
        self.assertEqual(reports[0].status, CoherenceStatus.PARTIAL)
        self.assertEqual(validate_multiscale_fecundity(reports).status, CoherenceStatus.PARTIAL)

    def test_invalid_recall_metrics_are_reported_without_comparison_or_crash(self):
        for invalid in ("invalid", float("nan"), float("inf"), True):
            with self.subTest(invalid=invalid):
                report = validate_memory(memory(exploration=EvidenceStatus.TRIGGERED,
                    recall=RecallMeasurement(d_in=invalid, d_out=0.2,
                                             coherence=invalid, trace_refs=("trace:1",))))
                self.assertTrue(report.issues)
                self.assertIsNone(report.recall_improvement_observed)
                self.assertIsNone(report.recall_coherence)
                self.assertNotEqual(report.status, CoherenceStatus.CANDIDATE_OK)

    def test_untraced_recall_does_not_establish_an_observed_improvement(self):
        report = validate_memory(memory(exploration=EvidenceStatus.TRIGGERED,
            recall=RecallMeasurement(d_in=0.5, d_out=0.2, coherence=0.99)))
        self.assertIsNone(report.recall_improvement_observed)
        self.assertIsNone(report.recall_coherence)
        self.assertNotEqual(report.status, CoherenceStatus.CANDIDATE_OK)


if __name__ == "__main__":
    unittest.main()
