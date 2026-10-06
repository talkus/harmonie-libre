"""Regression checks for incomplete relations and disconnected scale graphs."""
from dataclasses import replace
import unittest

from conscience_c_brain.multiscale_coherence import (
    CoherenceStatus, RelationRecord, Scale, validate_scale_receipt, validate_multiscale,
)
from test_multiscale_coherence import valid_receipt, linked_four_scale, valid_bridge


class MultiscaleAdmissionRegressions(unittest.TestCase):
    def test_relation_requires_a_distinction_reference(self):
        receipt = replace(valid_receipt(), relations=(RelationRecord("r1", (), ("trace:1",)),))
        report = validate_scale_receipt(receipt)
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_RHO_DELTA_REQUIRED", {issue.code for issue in report.issues})
        self.assertFalse(report.execution_authority)

    def test_four_disconnected_scales_do_not_pass_in_either_mode(self):
        receipts = tuple(valid_receipt(receipt_id=scale.value, scale=scale) for scale in Scale)
        for strict in (False, True):
            with self.subTest(strict=strict):
                report = validate_multiscale(receipts, require_explicit_bridges=strict)
                self.assertEqual(report.status, CoherenceStatus.PARTIAL)
                self.assertEqual(sum(issue.code == "MS_PARENT_REQUIRED" for issue in report.issues), 3)
                self.assertFalse(report.execution_authority)

    def test_one_disconnected_branch_is_visible_beside_a_complete_chain(self):
        receipts = linked_four_scale()
        disconnected = valid_receipt(receipt_id="orphan-micro", scale=Scale.MICRO)
        report = validate_multiscale((*receipts, disconnected))
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_PARENT_REQUIRED", {issue.code for issue in report.issues})

    def test_local_assessment_does_not_require_a_whole_scale_graph(self):
        self.assertEqual(validate_scale_receipt(valid_receipt()).status, CoherenceStatus.CANDIDATE_OK)

    def test_a_complete_chain_and_bridges_still_pass(self):
        receipts = linked_four_scale()
        by_hash = {r.digest(): r for r in receipts}
        bridges = tuple(valid_bridge(r, by_hash[r.parent_receipt_hash])
                        for r in receipts if r.parent_receipt_hash)
        report = validate_multiscale(receipts, bridges, require_explicit_bridges=True)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertFalse(report.issues)
