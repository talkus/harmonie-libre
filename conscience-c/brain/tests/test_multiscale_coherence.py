import unittest

from conscience_c_brain.multiscale_coherence import (
    CoherenceStatus,
    Contestation,
    CouplingRecord,
    DistinctionRecord,
    RelationRecord,
    Scale,
    ScaleReceipt,
    UnknownBoundary,
    validate_multiscale,
    validate_scale_receipt,
)


def valid_receipt(
    *,
    receipt_id="micro-1",
    scale=Scale.MICRO,
    unknowns=(),
    contestations=(),
    parent_receipt_hash=None,
    symbolic_labels=None,
    independent_witness_refs=("witness:independent",),
):
    return ScaleReceipt(
        receipt_id=receipt_id,
        scale=scale,
        couplings=(CouplingRecord("k1", ("trace:1",)),),
        distinctions=(DistinctionRecord("d1", ("k1",), ("trace:1",)),),
        relations=(RelationRecord("r1", ("d1",), ("trace:1",)),),
        trace_refs=("trace:1",),
        unknowns=unknowns,
        contestations=contestations,
        independent_witness_refs=independent_witness_refs,
        parent_receipt_hash=parent_receipt_hash,
        symbolic_labels=symbolic_labels or {},
    )


class MultiscaleCoherenceTests(unittest.TestCase):
    def test_valid_receipt_is_candidate_not_authority(self):
        report = validate_scale_receipt(valid_receipt())
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertFalse(report.execution_authority)

    def test_unknown_is_fail_closed_indeterminate(self):
        receipt = valid_receipt(
            unknowns=(
                UnknownBoundary(
                    "u1",
                    ("k1",),
                    "Which distinction is relevant?",
                    ("d:missing",),
                ),
            )
        )
        report = validate_scale_receipt(receipt)
        self.assertEqual(report.status, CoherenceStatus.INDETERMINATE)
        self.assertFalse(report.execution_authority)

    def test_distinction_requires_coupling_and_trace_provenance(self):
        receipt = ScaleReceipt(
            receipt_id="bad-delta",
            scale=Scale.MICRO,
            couplings=(CouplingRecord("k1", ("trace:1",)),),
            distinctions=(DistinctionRecord("d1", (), ()),),
            relations=(),
            trace_refs=("trace:1",),
            independent_witness_refs=("witness:independent",),
        )
        report = validate_scale_receipt(receipt)
        codes = {issue.code for issue in report.issues}
        self.assertIn("MS_DELTA_KAPPA_REQUIRED", codes)
        self.assertIn("MS_DELTA_TRACE_REQUIRED", codes)
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_coupling_does_not_become_causality_without_evidence(self):
        with self.assertRaises(ValueError):
            CouplingRecord("k1", ("trace:1",), causal_status="supported")

    def test_auto_verification_is_not_independent_validation(self):
        report = validate_scale_receipt(
            valid_receipt(independent_witness_refs=())
        )
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_symbolic_label_renaming_has_no_operational_effect(self):
        a = valid_receipt(symbolic_labels={"orientation": "Keter", "repair": "Raphael"})
        b = valid_receipt(symbolic_labels={"orientation": "ROOT", "repair": "HEAL"})
        self.assertEqual(a.digest(), b.digest())
        self.assertEqual(
            validate_scale_receipt(a).status,
            validate_scale_receipt(b).status,
        )

    def test_child_can_contest_parent_without_rewriting_parent(self):
        parent = valid_receipt(receipt_id="macro-1", scale=Scale.MACRO)
        parent_hash_before = parent.digest()
        child = valid_receipt(
            receipt_id="meso-1",
            scale=Scale.MESO,
            parent_receipt_hash=parent_hash_before,
            contestations=(
                Contestation(
                    "c1",
                    parent_hash_before,
                    "d1",
                    ("trace:1",),
                ),
            ),
        )
        report = validate_multiscale((parent, child))
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)
        self.assertEqual(parent.digest(), parent_hash_before)
        self.assertFalse(report.execution_authority)

    def test_parent_link_must_resolve_inside_composition(self):
        child = valid_receipt(
            receipt_id="meso-1",
            scale=Scale.MESO,
            parent_receipt_hash="0" * 64,
        )
        report = validate_multiscale((child,))
        self.assertIn("MS_PARENT_UNKNOWN", {x.code for x in report.issues})
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_same_validator_operates_at_each_scale(self):
        receipts = tuple(
            valid_receipt(receipt_id=f"{scale.value}-1", scale=scale)
            for scale in Scale
        )
        report = validate_multiscale(receipts)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(len(report.scale_reports), 4)
        self.assertTrue(all(x.status == CoherenceStatus.CANDIDATE_OK for x in report.scale_reports))


if __name__ == "__main__":
    unittest.main()
