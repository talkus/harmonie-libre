import dataclasses
import unittest

from conscience_c_brain.multiscale_coherence import (
    CoherenceVerdict,
    Contradiction,
    Coupling,
    Distinction,
    LiftedContradiction,
    Relation,
    Scale,
    ScaleReceipt,
    Trace,
    UnknownFrontier,
    assess_receipt,
    evaluate_multiscale,
    next_cycle_couplings,
)


def receipt(scale, unit_id, child_ids=(), local=(), lifted=(), unknown=None,
            authority_inherited=False):
    c = Coupling(
        coupling_id=f"{unit_id}:k1",
        scale=scale,
        participants=("a", "b"),
        source_refs=("trace:a", "trace:b"),
    )
    d = Distinction(
        distinction_id=f"{unit_id}:d1",
        scale=scale,
        label="difference supported by observed coupling",
        coupling_refs=(c.coupling_id,),
        source_refs=("trace:a", "trace:b"),
    )
    r = Relation(
        relation_id=f"{unit_id}:r1",
        scale=scale,
        label="stable relation candidate",
        distinction_refs=(d.distinction_id,),
        source_refs=("trace:a", "trace:b"),
    )
    t = Trace(
        trace_id=f"{unit_id}:t1",
        scale=scale,
        source_ref="trace:a",
    )
    return ScaleReceipt(
        unit_id=unit_id,
        scale=scale,
        couplings=(c,),
        distinctions=(d,),
        relations=(r,),
        traces=(t,),
        unknown=unknown or UnknownFrontier(),
        child_unit_ids=child_ids,
        local_contradictions=local,
        lifted_contradictions=lifted,
        authority_inherited=authority_inherited,
    )


class MultiScaleCoherenceTests(unittest.TestCase):
    def test_same_complete_motif_can_recur_at_all_scales(self):
        micro = receipt(Scale.MICRO, "micro:1")
        meso = receipt(Scale.MESO, "meso:1", child_ids=("micro:1",))
        macro = receipt(Scale.MACRO, "macro:1", child_ids=("meso:1",))
        meta = receipt(Scale.META, "meta:1", child_ids=("macro:1",))

        report = evaluate_multiscale((micro, meso, macro, meta))

        self.assertEqual(report.overall, CoherenceVerdict.META_THRESHOLD_ATTAINED)
        self.assertEqual(
            {a.scale for a in report.assessments},
            {Scale.MICRO, Scale.MESO, Scale.MACRO, Scale.META},
        )
        self.assertFalse(report.cross_scale_issues)

    def test_unknown_is_frontier_not_permission(self):
        base = receipt(Scale.MICRO, "micro:1")
        unknown = UnknownFrontier(
            coupling_refs=(base.couplings[0].coupling_id,),
            missing_distinctions=("which distinction matters?",),
            reason="pertinence not established",
        )
        item = dataclasses.replace(base, unknown=unknown)

        assessment = assess_receipt(item)

        self.assertEqual(assessment.verdict, CoherenceVerdict.INDETERMINATE)
        self.assertEqual(
            next_cycle_couplings(item),
            (base.couplings[0].coupling_id,),
        )

    def test_distinction_cannot_float_without_coupling_provenance(self):
        item = receipt(Scale.MICRO, "micro:1")
        bad = dataclasses.replace(
            item.distinctions[0],
            coupling_refs=("missing:kappa",),
        )
        item = dataclasses.replace(item, distinctions=(bad,))

        assessment = assess_receipt(item)

        self.assertEqual(assessment.verdict, CoherenceVerdict.FAIL)
        self.assertTrue(
            any("missing couplings" in issue for issue in assessment.issues)
        )

    def test_coupling_cannot_claim_causality_by_declaration(self):
        item = receipt(Scale.MICRO, "micro:1")
        bad = dataclasses.replace(
            item.couplings[0],
            interpretation="causal",
        )
        item = dataclasses.replace(item, couplings=(bad,))

        assessment = assess_receipt(item)

        self.assertEqual(assessment.verdict, CoherenceVerdict.FAIL)
        self.assertTrue(
            any("overclaims interpretation" in issue for issue in assessment.issues)
        )

    def test_parent_must_preserve_child_contradiction(self):
        contradiction = Contradiction(
            contradiction_id="x1",
            origin_scale=Scale.MICRO,
            origin_unit_id="micro:1",
            claim="P is contradicted by trace",
            source_refs=("trace:x",),
        )
        micro = receipt(
            Scale.MICRO,
            "micro:1",
            local=(contradiction,),
        )
        meso = receipt(
            Scale.MESO,
            "meso:1",
            child_ids=("micro:1",),
        )

        report = evaluate_multiscale((micro, meso))

        self.assertEqual(report.overall, CoherenceVerdict.FAIL)
        self.assertTrue(
            any("masks child contradiction x1" in issue
                for issue in report.cross_scale_issues)
        )

        meso_fixed = dataclasses.replace(
            meso,
            lifted_contradictions=(
                LiftedContradiction(
                    contradiction_id="x1",
                    origin_scale=Scale.MICRO,
                    origin_unit_id="micro:1",
                    source_refs=("trace:x",),
                ),
            ),
        )
        report_fixed = evaluate_multiscale((micro, meso_fixed))
        self.assertNotEqual(report_fixed.overall, CoherenceVerdict.FAIL)

    def test_authority_does_not_repeat_with_structure(self):
        item = receipt(
            Scale.MACRO,
            "macro:1",
            authority_inherited=True,
        )

        assessment = assess_receipt(item)

        self.assertEqual(assessment.verdict, CoherenceVerdict.FAIL)
        self.assertIn(
            "authority must not be inherited across scales",
            assessment.issues,
        )

    def test_receipts_are_immutable_and_report_has_no_scalar_score(self):
        item = receipt(Scale.META, "meta:1")
        report = evaluate_multiscale((item,))

        with self.assertRaises(dataclasses.FrozenInstanceError):
            item.unit_id = "rewritten"
        self.assertFalse(hasattr(report, "score"))
        self.assertEqual(report.assessments[0].dimensions["kappa"], 1)


if __name__ == "__main__":
    unittest.main()
