import unittest

from conscience_c_brain.horizon_plurality import (
    HorizonAssessment,
    HorizonStance,
    validate_horizon_family,
    validate_multiscale_horizon_reports,
)
from conscience_c_brain.horizon_reciprocity import derive_local_horizon
from conscience_c_brain.multiscale_coherence import (
    CoherenceStatus,
    CouplingRecord,
    DistinctionRecord,
    EvidenceStatus,
    RelationRecord,
    Scale,
    ScaleReceipt,
)


def receipt(scale, receipt_id, observer, origin):
    return ScaleReceipt(
        receipt_id=receipt_id,
        scale=scale,
        couplings=(CouplingRecord("k1", ("trace:1",)),),
        distinctions=(DistinctionRecord("d1", ("k1",), ("trace:1",)),),
        relations=(RelationRecord("rho1", ("d1",), ("trace:1",)),),
        trace_refs=("trace:1",),
        origin_refs=(origin,),
        property_ref="property:coherence",
        property_version="1",
        scope_ref="scope:a",
        observer_ref=observer,
        revision_triggers=("new_evidence",),
        provenance_bundle_refs=(f"prov:{origin}",),
        evidence_status=EvidenceStatus.TRIGGERED,
    )


def assessment(horizon, *, aid, stance, origin, provenance, distinction="d1"):
    return HorizonAssessment(
        assessment_id=aid,
        scale=horizon.scale,
        horizon_hash=horizon.digest(),
        observer_ref=horizon.observer_ref,
        property_ref=horizon.property_ref,
        property_version=horizon.property_version,
        distinction_ref=distinction,
        stance=stance,
        evidence_trace_refs=(f"evidence:{aid}",),
        origin_refs=(origin,),
        provenance_bundle_refs=(provenance,),
    )


class HorizonPluralityTests(unittest.TestCase):
    def test_distinct_cross_horizon_support_is_structural_not_truth(self):
        h1 = derive_local_horizon(receipt(Scale.MICRO, "r1", "observer:a", "origin:a"))
        h2 = derive_local_horizon(receipt(Scale.MICRO, "r2", "observer:b", "origin:b"))
        horizons = {h1.digest(): h1, h2.digest(): h2}
        report = validate_horizon_family(
            horizons,
            (
                assessment(h1, aid="a1", stance=HorizonStance.SUPPORT, origin="origin:a", provenance="prov:a"),
                assessment(h2, aid="a2", stance=HorizonStance.SUPPORT, origin="origin:b", provenance="prov:b"),
            ),
        )
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertTrue(report.structurally_distinct_support)
        self.assertFalse(report.independent_validation)
        self.assertFalse(report.execution_authority)

    def test_same_origin_mirrors_do_not_count_as_distinct_support(self):
        h1 = derive_local_horizon(receipt(Scale.MICRO, "r1", "observer:a", "origin:same"))
        h2 = derive_local_horizon(receipt(Scale.MICRO, "r2", "observer:b", "origin:same"))
        horizons = {h1.digest(): h1, h2.digest(): h2}
        report = validate_horizon_family(
            horizons,
            (
                assessment(h1, aid="a1", stance=HorizonStance.SUPPORT, origin="origin:same", provenance="prov:a"),
                assessment(h2, aid="a2", stance=HorizonStance.SUPPORT, origin="origin:same", provenance="prov:b"),
            ),
        )
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_HORIZON_SUPPORT_NOT_DISTINCT", {x.code for x in report.issues})

    def test_shared_provenance_does_not_count_as_distinct_support(self):
        h1 = derive_local_horizon(receipt(Scale.MESO, "r1", "observer:a", "origin:a"))
        h2 = derive_local_horizon(receipt(Scale.MESO, "r2", "observer:b", "origin:b"))
        horizons = {h1.digest(): h1, h2.digest(): h2}
        report = validate_horizon_family(
            horizons,
            (
                assessment(h1, aid="a1", stance=HorizonStance.SUPPORT, origin="origin:a", provenance="prov:shared"),
                assessment(h2, aid="a2", stance=HorizonStance.SUPPORT, origin="origin:b", provenance="prov:shared"),
            ),
        )
        self.assertEqual(report.status, CoherenceStatus.PARTIAL)

    def test_challenge_is_preserved_instead_of_majority_vote(self):
        h1 = derive_local_horizon(receipt(Scale.MACRO, "r1", "observer:a", "origin:a"))
        h2 = derive_local_horizon(receipt(Scale.MACRO, "r2", "observer:b", "origin:b"))
        h3 = derive_local_horizon(receipt(Scale.MACRO, "r3", "observer:c", "origin:c"))
        horizons = {x.digest(): x for x in (h1, h2, h3)}
        report = validate_horizon_family(
            horizons,
            (
                assessment(h1, aid="a1", stance=HorizonStance.SUPPORT, origin="origin:a", provenance="prov:a"),
                assessment(h2, aid="a2", stance=HorizonStance.SUPPORT, origin="origin:b", provenance="prov:b"),
                assessment(h3, aid="a3", stance=HorizonStance.CHALLENGE, origin="origin:c", provenance="prov:c"),
            ),
        )
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)
        self.assertEqual(report.challenge_ids, ("a3",))

    def test_indeterminate_is_not_collapsed_into_support(self):
        h1 = derive_local_horizon(receipt(Scale.META, "r1", "observer:a", "origin:a"))
        h2 = derive_local_horizon(receipt(Scale.META, "r2", "observer:b", "origin:b"))
        horizons = {h1.digest(): h1, h2.digest(): h2}
        report = validate_horizon_family(
            horizons,
            (
                assessment(h1, aid="a1", stance=HorizonStance.SUPPORT, origin="origin:a", provenance="prov:a"),
                assessment(h2, aid="a2", stance=HorizonStance.INDETERMINATE, origin="origin:b", provenance="prov:b"),
            ),
        )
        self.assertEqual(report.status, CoherenceStatus.INDETERMINATE)

    def test_same_validator_operates_at_all_four_scales(self):
        reports = []
        for scale in Scale:
            h1 = derive_local_horizon(receipt(scale, f"{scale.value}-1", f"{scale.value}:a", f"{scale.value}:origin:a"))
            h2 = derive_local_horizon(receipt(scale, f"{scale.value}-2", f"{scale.value}:b", f"{scale.value}:origin:b"))
            horizons = {h1.digest(): h1, h2.digest(): h2}
            reports.append(
                validate_horizon_family(
                    horizons,
                    (
                        assessment(h1, aid=f"{scale.value}:a1", stance=HorizonStance.SUPPORT, origin=f"{scale.value}:origin:a", provenance=f"{scale.value}:prov:a"),
                        assessment(h2, aid=f"{scale.value}:a2", stance=HorizonStance.SUPPORT, origin=f"{scale.value}:origin:b", provenance=f"{scale.value}:prov:b"),
                    ),
                )
            )
        multi = validate_multiscale_horizon_reports(reports)
        self.assertEqual(multi.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual({x.scale for x in multi.scale_reports}, set(Scale))
        self.assertFalse(multi.independent_validation)
        self.assertFalse(multi.execution_authority)

    def test_lower_scale_challenge_cannot_be_masked_by_higher_scales(self):
        reports = []
        for scale in Scale:
            h1 = derive_local_horizon(receipt(scale, f"{scale.value}-1", f"{scale.value}:a", f"{scale.value}:origin:a"))
            h2 = derive_local_horizon(receipt(scale, f"{scale.value}-2", f"{scale.value}:b", f"{scale.value}:origin:b"))
            horizons = {h1.digest(): h1, h2.digest(): h2}
            second_stance = HorizonStance.CHALLENGE if scale == Scale.MICRO else HorizonStance.SUPPORT
            reports.append(
                validate_horizon_family(
                    horizons,
                    (
                        assessment(h1, aid=f"{scale.value}:a1", stance=HorizonStance.SUPPORT, origin=f"{scale.value}:origin:a", provenance=f"{scale.value}:prov:a"),
                        assessment(h2, aid=f"{scale.value}:a2", stance=second_stance, origin=f"{scale.value}:origin:b", provenance=f"{scale.value}:prov:b"),
                    ),
                )
            )
        multi = validate_multiscale_horizon_reports(reports)
        self.assertEqual(multi.status, CoherenceStatus.CONTESTED)
        self.assertTrue(multi.has_challenge)

    def test_missing_scale_keeps_multiscale_report_partial(self):
        scale = Scale.MICRO
        h1 = derive_local_horizon(receipt(scale, "r1", "observer:a", "origin:a"))
        h2 = derive_local_horizon(receipt(scale, "r2", "observer:b", "origin:b"))
        horizons = {h1.digest(): h1, h2.digest(): h2}
        local = validate_horizon_family(
            horizons,
            (
                assessment(h1, aid="a1", stance=HorizonStance.SUPPORT, origin="origin:a", provenance="prov:a"),
                assessment(h2, aid="a2", stance=HorizonStance.SUPPORT, origin="origin:b", provenance="prov:b"),
            ),
        )
        multi = validate_multiscale_horizon_reports((local,))
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_HORIZON_SCALE_REPORT_MISSING", {x.code for x in multi.issues})


if __name__ == "__main__":
    unittest.main()
