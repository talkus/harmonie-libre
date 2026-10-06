import unittest

from conscience_c_brain.multiscale_coherence import (
    CoherenceStatus,
    Contestation,
    CouplingRecord,
    DistinctionRecord,
    EvidenceStatus,
    RelationRecord,
    Scale,
    ScaleReceipt,
    UnknownBoundary,
    stutter_equivalent,
    validate_multiscale,
    validate_scale_receipt,
)


def valid_receipt(
    *,
    receipt_id="micro-1",
    scale=Scale.MICRO,
    origin_refs=("origin:1",),
    evidence_status=EvidenceStatus.TRIGGERED,
    unknowns=(),
    contestations=(),
    parent_receipt_hash=None,
    symbolic_labels=None,
    external_witness_refs=(),
    property_ref="property:coherence",
    property_version="1",
    scope_ref="scope:local",
    observer_ref="observer:test",
    revision_triggers=("new-material-evidence",),
    provenance_bundle_refs=("prov:bundle:1",),
):
    return ScaleReceipt(
        receipt_id=receipt_id,
        scale=scale,
        couplings=(CouplingRecord("k1", ("trace:1",)),),
        distinctions=(DistinctionRecord("d1", ("k1",), ("trace:1",)),),
        relations=(RelationRecord("r1", ("d1",), ("trace:1",)),),
        trace_refs=("trace:1",),
        origin_refs=origin_refs,
        property_ref=property_ref,
        property_version=property_version,
        scope_ref=scope_ref,
        observer_ref=observer_ref,
        revision_triggers=revision_triggers,
        provenance_bundle_refs=provenance_bundle_refs,
        evidence_status=evidence_status,
        unknowns=unknowns,
        contestations=contestations,
        external_witness_refs=external_witness_refs,
        parent_receipt_hash=parent_receipt_hash,
        symbolic_labels=symbolic_labels or {},
    )


def linked_four_scale():
    meta = valid_receipt(
        receipt_id="meta-1",
        scale=Scale.META,
        origin_refs=("origin:1", "origin:2"),
    )
    macro = valid_receipt(
        receipt_id="macro-1",
        scale=Scale.MACRO,
        origin_refs=("origin:1", "origin:2"),
        parent_receipt_hash=meta.digest(),
    )
    meso = valid_receipt(
        receipt_id="meso-1",
        scale=Scale.MESO,
        origin_refs=("origin:1", "origin:2"),
        parent_receipt_hash=macro.digest(),
    )
    micro_a = valid_receipt(
        receipt_id="micro-a",
        scale=Scale.MICRO,
        origin_refs=("origin:1",),
        parent_receipt_hash=meso.digest(),
    )
    micro_b = valid_receipt(
        receipt_id="micro-b",
        scale=Scale.MICRO,
        origin_refs=("origin:2",),
        parent_receipt_hash=meso.digest(),
    )
    return meta, macro, meso, micro_a, micro_b


class MultiscaleCoherenceTests(unittest.TestCase):
    def test_valid_receipt_is_candidate_not_authority(self):
        report = validate_scale_receipt(valid_receipt())
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertFalse(report.independent_validation)
        self.assertFalse(report.execution_authority)

    def test_external_witness_declaration_does_not_become_independent_validation(self):
        report = validate_scale_receipt(
            valid_receipt(external_witness_refs=("witness:declared",))
        )
        self.assertTrue(report.external_witness_declared)
        self.assertFalse(report.independent_validation)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)

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
        self.assertTrue(report.has_unknown)
        self.assertFalse(report.execution_authority)

    def test_insufficient_data_is_not_no_change(self):
        report = validate_scale_receipt(
            valid_receipt(evidence_status=EvidenceStatus.INSUFFICIENT_DATA)
        )
        self.assertEqual(report.status, CoherenceStatus.INDETERMINATE)
        self.assertTrue(report.has_unknown)

    def test_invalid_data_stays_distinct_from_unknown(self):
        report = validate_scale_receipt(
            valid_receipt(evidence_status=EvidenceStatus.INVALID_DATA)
        )
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)
        self.assertFalse(report.has_unknown)
        self.assertIn("MS_INVALID_DATA", {x.code for x in report.issues})

    def test_not_triggered_can_still_be_structurally_valid(self):
        report = validate_scale_receipt(
            valid_receipt(evidence_status=EvidenceStatus.NOT_TRIGGERED)
        )
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertFalse(report.has_unknown)

    def test_distinction_requires_coupling_and_trace_provenance(self):
        receipt = ScaleReceipt(
            receipt_id="bad-delta",
            scale=Scale.MICRO,
            couplings=(CouplingRecord("k1", ("trace:1",)),),
            distinctions=(DistinctionRecord("d1", (), ()),),
            relations=(),
            trace_refs=("trace:1",),
            origin_refs=("origin:1",),
            property_ref="property:coherence",
            property_version="1",
            scope_ref="scope:local",
            observer_ref="observer:test",
            revision_triggers=("new-material-evidence",),
            provenance_bundle_refs=("prov:bundle:1",),
        )
        report = validate_scale_receipt(receipt)
        codes = {issue.code for issue in report.issues}
        self.assertIn("MS_DELTA_KAPPA_REQUIRED", codes)
        self.assertIn("MS_DELTA_TRACE_REQUIRED", codes)
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_source_origin_is_required_and_not_double_counted(self):
        missing = validate_scale_receipt(valid_receipt(origin_refs=()))
        self.assertIn("MS_ORIGIN_REQUIRED", {x.code for x in missing.issues})

        duplicate = validate_scale_receipt(
            valid_receipt(origin_refs=("origin:1", "origin:1"))
        )
        self.assertIn("MS_ORIGIN_DUPLICATE", {x.code for x in duplicate.issues})

    def test_property_scope_observer_and_revision_contract_are_explicit(self):
        report = validate_scale_receipt(
            valid_receipt(
                property_ref="",
                property_version="",
                scope_ref="",
                observer_ref="",
                revision_triggers=(),
            )
        )
        codes = {x.code for x in report.issues}
        self.assertIn("MS_PROPERTY_REQUIRED", codes)
        self.assertIn("MS_PROPERTY_VERSION_REQUIRED", codes)
        self.assertIn("MS_SCOPE_REQUIRED", codes)
        self.assertIn("MS_OBSERVER_REQUIRED", codes)
        self.assertIn("MS_REVISION_TRIGGER_REQUIRED", codes)
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_external_witness_requires_provenance_of_provenance(self):
        report = validate_scale_receipt(
            valid_receipt(
                external_witness_refs=("witness:declared",),
                provenance_bundle_refs=(),
            )
        )
        self.assertIn("MS_WITNESS_PROVENANCE_REQUIRED", {x.code for x in report.issues})
        self.assertFalse(report.independent_validation)

    def test_stutter_equivalence_ignores_receipt_identity_and_parent_pointer(self):
        a = valid_receipt(receipt_id="micro-a", parent_receipt_hash=None)
        b = valid_receipt(receipt_id="micro-b", parent_receipt_hash="f" * 64)
        self.assertNotEqual(a.digest(), b.digest())
        self.assertEqual(a.state_digest(), b.state_digest())
        self.assertTrue(stutter_equivalent(a, b))
        self.assertEqual(
            validate_scale_receipt(a).status,
            validate_scale_receipt(b).status,
        )

    def test_coupling_does_not_become_causality_without_evidence(self):
        with self.assertRaises(ValueError):
            CouplingRecord("k1", ("trace:1",), causal_status="supported")

    def test_symbolic_label_renaming_has_no_operational_effect(self):
        a = valid_receipt(symbolic_labels={"orientation": "Keter", "repair": "Raphael"})
        b = valid_receipt(symbolic_labels={"orientation": "ROOT", "repair": "HEAL"})
        self.assertEqual(a.digest(), b.digest())
        self.assertEqual(
            validate_scale_receipt(a).status,
            validate_scale_receipt(b).status,
        )

    def test_multiple_units_per_scale_are_allowed(self):
        receipts = linked_four_scale()
        report = validate_multiscale(receipts)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertNotIn("MS_DUPLICATE_SCALE", {x.code for x in report.issues})

    def test_origin_union_must_survive_upward(self):
        meta = valid_receipt(receipt_id="meta-1", scale=Scale.META, origin_refs=("origin:1",))
        macro = valid_receipt(
            receipt_id="macro-1",
            scale=Scale.MACRO,
            origin_refs=("origin:1",),
            parent_receipt_hash=meta.digest(),
        )
        meso = valid_receipt(
            receipt_id="meso-1",
            scale=Scale.MESO,
            origin_refs=("origin:1",),
            parent_receipt_hash=macro.digest(),
        )
        micro = valid_receipt(
            receipt_id="micro-1",
            scale=Scale.MICRO,
            origin_refs=("origin:1", "origin:2"),
            parent_receipt_hash=meso.digest(),
        )
        report = validate_multiscale((meta, macro, meso, micro))
        self.assertIn("MS_ORIGIN_NOT_PROPAGATED", {x.code for x in report.issues})
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_provenance_bundle_union_must_survive_upward(self):
        meta = valid_receipt(
            receipt_id="meta-1",
            scale=Scale.META,
            provenance_bundle_refs=("prov:bundle:1",),
        )
        macro = valid_receipt(
            receipt_id="macro-1",
            scale=Scale.MACRO,
            provenance_bundle_refs=("prov:bundle:1",),
            parent_receipt_hash=meta.digest(),
        )
        meso = valid_receipt(
            receipt_id="meso-1",
            scale=Scale.MESO,
            provenance_bundle_refs=("prov:bundle:1",),
            parent_receipt_hash=macro.digest(),
        )
        micro = valid_receipt(
            receipt_id="micro-1",
            scale=Scale.MICRO,
            provenance_bundle_refs=("prov:bundle:1", "prov:bundle:2"),
            parent_receipt_hash=meso.digest(),
        )
        report = validate_multiscale((meta, macro, meso, micro))
        self.assertIn("MS_PROVENANCE_BUNDLE_NOT_PROPAGATED", {x.code for x in report.issues})
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_non_adjacent_parent_fails(self):
        meta = valid_receipt(receipt_id="meta-1", scale=Scale.META)
        meso = valid_receipt(
            receipt_id="meso-1",
            scale=Scale.MESO,
            parent_receipt_hash=meta.digest(),
        )
        macro = valid_receipt(receipt_id="macro-1", scale=Scale.MACRO)
        micro = valid_receipt(receipt_id="micro-1", scale=Scale.MICRO)
        report = validate_multiscale((meta, macro, meso, micro))
        self.assertIn("MS_NON_ADJACENT_PARENT", {x.code for x in report.issues})

    def test_meta_cannot_have_parent(self):
        macro = valid_receipt(receipt_id="macro-1", scale=Scale.MACRO)
        meta = valid_receipt(
            receipt_id="meta-1",
            scale=Scale.META,
            parent_receipt_hash=macro.digest(),
        )
        meso = valid_receipt(receipt_id="meso-1", scale=Scale.MESO)
        micro = valid_receipt(receipt_id="micro-1", scale=Scale.MICRO)
        report = validate_multiscale((meta, macro, meso, micro))
        self.assertIn("MS_META_PARENT_FORBIDDEN", {x.code for x in report.issues})

    def test_stale_or_missing_parent_fails_closed(self):
        meta = valid_receipt(receipt_id="meta-1", scale=Scale.META)
        macro = valid_receipt(
            receipt_id="macro-1",
            scale=Scale.MACRO,
            parent_receipt_hash=meta.digest(),
        )
        meso = valid_receipt(
            receipt_id="meso-1",
            scale=Scale.MESO,
            parent_receipt_hash="0" * 64,
        )
        micro = valid_receipt(receipt_id="micro-1", scale=Scale.MICRO)
        report = validate_multiscale((meta, macro, meso, micro))
        self.assertIn("MS_PARENT_UNKNOWN", {x.code for x in report.issues})

    def test_duplicate_receipt_id_is_rejected(self):
        meta = valid_receipt(receipt_id="same", scale=Scale.META)
        macro = valid_receipt(receipt_id="same", scale=Scale.MACRO)
        meso = valid_receipt(receipt_id="meso", scale=Scale.MESO)
        micro = valid_receipt(receipt_id="micro", scale=Scale.MICRO)
        report = validate_multiscale((meta, macro, meso, micro))
        self.assertIn("MS_DUPLICATE_RECEIPT_ID", {x.code for x in report.issues})

    def test_child_can_contest_parent_without_rewriting_parent(self):
        meta, macro, meso, micro_a, micro_b = linked_four_scale()
        parent_hash_before = meso.digest()
        contested_child = valid_receipt(
            receipt_id="micro-contested",
            scale=Scale.MICRO,
            origin_refs=("origin:1",),
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
        report = validate_multiscale((meta, macro, meso, contested_child, micro_b))
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)
        self.assertTrue(report.has_contestation)
        self.assertEqual(meso.digest(), parent_hash_before)
        self.assertFalse(report.execution_authority)

    def test_unknown_and_contestation_remain_separately_visible(self):
        meta, macro, meso, _, micro_b = linked_four_scale()
        parent_hash = meso.digest()
        child = valid_receipt(
            receipt_id="micro-both",
            scale=Scale.MICRO,
            origin_refs=("origin:1",),
            parent_receipt_hash=parent_hash,
            evidence_status=EvidenceStatus.INSUFFICIENT_DATA,
            contestations=(
                Contestation("c1", parent_hash, "d1", ("trace:1",)),
            ),
        )
        report = validate_multiscale((meta, macro, meso, child, micro_b))
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)
        self.assertTrue(report.has_contestation)
        self.assertTrue(report.has_unknown)

    def test_higher_scale_cannot_mask_lower_scale_partial(self):
        meta, macro, meso, _, micro_b = linked_four_scale()
        broken_micro = valid_receipt(
            receipt_id="micro-broken",
            scale=Scale.MICRO,
            origin_refs=("origin:1",),
            property_ref="",
            parent_receipt_hash=meso.digest(),
        )
        report = validate_multiscale((meta, macro, meso, broken_micro, micro_b))
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)
        self.assertTrue(any(r.status == CoherenceStatus.PARTIAL for r in report.scale_reports))
        self.assertFalse(report.execution_authority)

    def test_full_multiscale_requires_all_four_scales(self):
        receipt = valid_receipt(scale=Scale.MICRO)
        report = validate_multiscale((receipt,))
        self.assertIn("MS_SCALE_MISSING", {x.code for x in report.issues})
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_same_validator_operates_at_each_scale(self):
        receipts = linked_four_scale()
        report = validate_multiscale(receipts)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(len(report.scale_reports), 5)
        self.assertTrue(all(x.status == CoherenceStatus.CANDIDATE_OK for x in report.scale_reports))


if __name__ == "__main__":
    unittest.main()
