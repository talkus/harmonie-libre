import unittest
from dataclasses import replace

from conscience_c_brain.horizon_reciprocity import (
    DistinctionProposal,
    derive_local_horizon,
    derive_transition,
    validate_horizon_conditioned_distinction,
    validate_horizon_transition,
    validate_local_horizon,
)
from conscience_c_brain.multiscale_coherence import (
    CoherenceStatus,
    CouplingRecord,
    DistinctionRecord,
    EvidenceStatus,
    RelationRecord,
    Scale,
    ScaleReceipt,
    UnknownBoundary,
)


def receipt(
    *,
    receipt_id="r1",
    scale=Scale.MICRO,
    observer_ref="observer:a",
    scope_ref="scope:a",
    distinctions=None,
    unknowns=(),
    symbolic_labels=None,
    trace_refs=("trace:1",),
):
    distinctions = distinctions or (
        DistinctionRecord("d1", ("k1",), ("trace:1",)),
    )
    return ScaleReceipt(
        receipt_id=receipt_id,
        scale=scale,
        couplings=(CouplingRecord("k1", ("trace:1",)),),
        distinctions=distinctions,
        relations=(
            RelationRecord(
                "rho1",
                tuple(x.distinction_id for x in distinctions),
                ("trace:1",),
            ),
        ),
        trace_refs=trace_refs,
        origin_refs=("origin:1",),
        property_ref="property:coherence",
        property_version="1",
        scope_ref=scope_ref,
        observer_ref=observer_ref,
        revision_triggers=("new_material_evidence",),
        provenance_bundle_refs=("prov:1",),
        evidence_status=EvidenceStatus.TRIGGERED,
        unknowns=unknowns,
        external_witness_refs=("witness:1",),
        symbolic_labels=symbolic_labels or {},
    )


class HorizonReciprocityTests(unittest.TestCase):
    def test_horizon_is_derived_from_local_form(self):
        src = receipt()
        omega = derive_local_horizon(src)
        report = validate_local_horizon(omega, src)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(omega.source_receipt_hash, src.digest())
        self.assertEqual(omega.epistemic_scope, "local")
        self.assertFalse(report.execution_authority)

    def test_symbolic_renaming_does_not_reconfigure_horizon(self):
        a = receipt(symbolic_labels={"opening": "Keter", "separator": "Nehar"})
        b = receipt(symbolic_labels={"opening": "ROOT", "separator": "FILTER"})
        self.assertEqual(a.digest(), b.digest())
        self.assertEqual(derive_local_horizon(a).digest(), derive_local_horizon(b).digest())

    def test_observer_change_reconfigures_local_horizon(self):
        a = receipt(observer_ref="observer:a")
        b = receipt(receipt_id="r2", observer_ref="observer:b")
        self.assertNotEqual(derive_local_horizon(a).digest(), derive_local_horizon(b).digest())

    def test_scope_change_reconfigures_local_horizon(self):
        a = receipt(scope_ref="scope:a")
        b = receipt(receipt_id="r2", scope_ref="scope:b")
        self.assertNotEqual(derive_local_horizon(a).digest(), derive_local_horizon(b).digest())

    def test_new_distinction_reconfigures_horizon(self):
        a = receipt()
        b = receipt(
            receipt_id="r2",
            distinctions=(
                DistinctionRecord("d1", ("k1",), ("trace:1",)),
                DistinctionRecord("d2", ("k1",), ("trace:1",)),
            ),
        )
        transition = derive_transition(a, b, cause_trace_refs=("trace:1",))
        self.assertEqual(transition.added_distinction_refs, ("d2",))
        report = validate_horizon_transition(a, b, transition)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)

    def test_unknown_boundary_reconfigures_horizon_without_becoming_absolute(self):
        a = receipt()
        b = receipt(
            receipt_id="r2",
            unknowns=(UnknownBoundary("u1", ("k1",), "question not yet well formed"),),
        )
        omega = derive_local_horizon(b)
        self.assertEqual(omega.unknown_ids, ("u1",))
        self.assertEqual(omega.epistemic_scope, "local")
        transition = derive_transition(a, b, cause_trace_refs=("trace:1",))
        self.assertEqual(transition.opened_unknown_ids, ("u1",))

    def test_totality_claim_is_rejected(self):
        src = receipt()
        omega = derive_local_horizon(src)
        bad = replace(omega, totality_claim=True)
        report = validate_local_horizon(bad, src)
        self.assertIn("MS_OMEGA_TOTALITY_FORBIDDEN", {x.code for x in report.issues})
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_absolute_epistemic_scope_is_rejected(self):
        src = receipt()
        omega = derive_local_horizon(src)
        bad = replace(omega, epistemic_scope="absolute")
        report = validate_local_horizon(bad, src)
        self.assertIn("MS_OMEGA_ABSOLUTE_SCOPE_FORBIDDEN", {x.code for x in report.issues})

    def test_free_floating_horizon_fails_source_check(self):
        src = receipt()
        omega = derive_local_horizon(src)
        bad = replace(omega, source_receipt_hash="0" * 64)
        report = validate_local_horizon(bad, src)
        self.assertIn("MS_OMEGA_SOURCE_MISMATCH", {x.code for x in report.issues})

    def test_transition_must_report_actual_delta_changes(self):
        a = receipt()
        b = receipt(
            receipt_id="r2",
            distinctions=(
                DistinctionRecord("d1", ("k1",), ("trace:1",)),
                DistinctionRecord("d2", ("k1",), ("trace:1",)),
            ),
        )
        transition = derive_transition(a, b, cause_trace_refs=("trace:1",))
        bad = replace(transition, added_distinction_refs=())
        report = validate_horizon_transition(a, b, bad)
        self.assertIn("MS_OMEGA_RECONFIGURATION_MISMATCH", {x.code for x in report.issues})

    def test_transition_cannot_claim_exhaustive_future_possibility(self):
        a = receipt()
        b = receipt(receipt_id="r2")
        transition = derive_transition(a, b, cause_trace_refs=("trace:1",))
        bad = replace(transition, claims_exhaustive_possible_space=True)
        report = validate_horizon_transition(a, b, bad)
        self.assertIn("MS_OMEGA_TOTALITY_FORBIDDEN", {x.code for x in report.issues})
        self.assertFalse(report.execution_authority)

    def test_transition_requires_known_cause_trace(self):
        a = receipt()
        b = receipt(receipt_id="r2")
        transition = derive_transition(a, b, cause_trace_refs=("trace:missing",))
        report = validate_horizon_transition(a, b, transition)
        self.assertIn("MS_OMEGA_CAUSE_TRACE_UNKNOWN", {x.code for x in report.issues})

    def test_two_local_horizons_may_coexist_at_same_scale(self):
        a = derive_local_horizon(receipt(observer_ref="observer:a"))
        b = derive_local_horizon(receipt(receipt_id="r2", observer_ref="observer:b"))
        self.assertEqual(a.scale, b.scale)
        self.assertNotEqual(a.digest(), b.digest())


class HorizonToDistinctionTests(unittest.TestCase):
    def test_horizon_conditions_but_does_not_prove_candidate_distinction(self):
        src = receipt()
        omega = derive_local_horizon(src)
        proposal = DistinctionProposal(
            proposal_id="p1",
            source_horizon_hash=omega.digest(),
            distinction_id="d2",
            coupling_refs=("k2",),
            evidence_trace_refs=("trace:2",),
        )
        report = validate_horizon_conditioned_distinction(
            omega, src, proposal,
            available_coupling_refs=("k1", "k2"),
            available_trace_refs=("trace:1", "trace:2"),
        )
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertTrue(report.admissible_for_review)
        self.assertFalse(report.execution_authority)

    def test_horizon_alone_cannot_supply_evidence(self):
        src = receipt()
        omega = derive_local_horizon(src)
        proposal = DistinctionProposal(
            proposal_id="p1",
            source_horizon_hash=omega.digest(),
            distinction_id="d2",
            coupling_refs=("k1",),
            evidence_trace_refs=(),
        )
        report = validate_horizon_conditioned_distinction(
            omega, src, proposal,
            available_coupling_refs=("k1",),
            available_trace_refs=("trace:1",),
        )
        self.assertIn(
            "MS_DELTA_PROPOSAL_EVIDENCE_REQUIRED",
            {x.code for x in report.issues},
        )
        self.assertFalse(report.admissible_for_review)

    def test_candidate_cannot_promote_itself_to_truth_or_authority(self):
        src = receipt()
        omega = derive_local_horizon(src)
        proposal = DistinctionProposal(
            proposal_id="p1",
            source_horizon_hash=omega.digest(),
            distinction_id="d2",
            coupling_refs=("k1",),
            evidence_trace_refs=("trace:1",),
            claims_truth=True,
            execution_authority=True,
        )
        report = validate_horizon_conditioned_distinction(
            omega, src, proposal,
            available_coupling_refs=("k1",),
            available_trace_refs=("trace:1",),
        )
        codes = {x.code for x in report.issues}
        self.assertIn("MS_DELTA_PROPOSAL_TRUTH_CLAIM_FORBIDDEN", codes)
        self.assertIn("MS_DELTA_PROPOSAL_AUTHORITY_FORBIDDEN", codes)

    def test_candidate_must_cite_exact_horizon(self):
        src = receipt()
        omega = derive_local_horizon(src)
        proposal = DistinctionProposal(
            proposal_id="p1",
            source_horizon_hash="0" * 64,
            distinction_id="d2",
            coupling_refs=("k1",),
            evidence_trace_refs=("trace:1",),
        )
        report = validate_horizon_conditioned_distinction(
            omega, src, proposal,
            available_coupling_refs=("k1",),
            available_trace_refs=("trace:1",),
        )
        self.assertIn(
            "MS_DELTA_PROPOSAL_HORIZON_MISMATCH",
            {x.code for x in report.issues},
        )

    def test_candidate_cannot_fake_resolution_of_foreign_unknown(self):
        src = receipt(
            unknowns=(UnknownBoundary("u1", ("k1",), "open question"),)
        )
        omega = derive_local_horizon(src)
        proposal = DistinctionProposal(
            proposal_id="p1",
            source_horizon_hash=omega.digest(),
            distinction_id="d2",
            coupling_refs=("k1",),
            evidence_trace_refs=("trace:1",),
            addresses_unknown_ids=("u2",),
        )
        report = validate_horizon_conditioned_distinction(
            omega, src, proposal,
            available_coupling_refs=("k1",),
            available_trace_refs=("trace:1",),
        )
        self.assertIn(
            "MS_DELTA_PROPOSAL_UNKNOWN_TARGET_MISMATCH",
            {x.code for x in report.issues},
        )

    def test_existing_distinction_is_not_reintroduced_as_novel(self):
        src = receipt()
        omega = derive_local_horizon(src)
        proposal = DistinctionProposal(
            proposal_id="p1",
            source_horizon_hash=omega.digest(),
            distinction_id="d1",
            coupling_refs=("k1",),
            evidence_trace_refs=("trace:1",),
        )
        report = validate_horizon_conditioned_distinction(
            omega, src, proposal,
            available_coupling_refs=("k1",),
            available_trace_refs=("trace:1",),
        )
        self.assertIn(
            "MS_DELTA_PROPOSAL_ALREADY_PRESENT",
            {x.code for x in report.issues},
        )

if __name__ == "__main__":
    unittest.main()
