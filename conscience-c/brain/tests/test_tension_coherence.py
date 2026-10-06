import unittest

from conscience_c_brain.tension_coherence import (
    CoherenceClaim,
    GenerativityStatus,
    LocalCoherenceVerdict,
    TensionDisposition,
    TensionRecord,
    validate_multiscale_tension_coherence,
    validate_tension_coherence,
)
from conscience_c_brain.multiscale_coherence import CoherenceStatus, Scale


def claim(scale=Scale.MICRO, verdict=LocalCoherenceVerdict.COHERENT, *, total=False):
    return CoherenceClaim(
        claim_id=f"claim:{scale.value}",
        scale=scale,
        observer_ref=f"observer:{scale.value}",
        scope_ref=f"scope:{scale.value}",
        property_ref="property:viability",
        property_version="1",
        verdict=verdict,
        relation_refs=("r:a", "r:b"),
        trace_refs=(f"trace:coherence:{scale.value}",),
        justification_refs=(f"justification:{scale.value}",),
        claims_tension_exhaustiveness=total,
    )


def tension(
    scale=Scale.MICRO,
    *,
    tension_id="t:1",
    disposition=TensionDisposition.CONSTITUTIVE,
    generativity=GenerativityStatus.UNESTABLISHED,
    generativity_evidence_refs=(),
    contestation_refs=(),
):
    return TensionRecord(
        tension_id=tension_id,
        scale=scale,
        observer_ref=f"observer:{scale.value}",
        scope_ref=f"scope:{scale.value}",
        property_ref="property:viability",
        property_version="1",
        relation_refs=("r:a", "r:b"),
        trace_refs=(f"trace:tension:{scale.value}:{tension_id}",),
        disposition=disposition,
        justification_refs=(f"justification:{tension_id}",),
        generativity_status=generativity,
        generativity_evidence_refs=generativity_evidence_refs,
        contestation_refs=contestation_refs,
    )


def validate_local(c, tensions):
    trace_refs = list(c.trace_refs)
    gen_refs = []
    for item in tensions:
        trace_refs.extend(item.trace_refs)
        gen_refs.extend(item.generativity_evidence_refs)
    return validate_tension_coherence(
        c,
        tensions,
        available_trace_refs=tuple(trace_refs),
        available_generativity_evidence_refs=tuple(gen_refs),
    )


class TensionCoherenceTests(unittest.TestCase):
    def test_coherence_can_coexist_with_constitutive_tension(self):
        c = claim(verdict=LocalCoherenceVerdict.COHERENT)
        report = validate_local(c, (tension(),))
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(report.coherence_verdict, LocalCoherenceVerdict.COHERENT)
        self.assertEqual(report.constitutive_ids, ("t:1",))
        self.assertFalse(report.tension_exhaustive)

    def test_tension_does_not_force_incoherence(self):
        c = claim(verdict=LocalCoherenceVerdict.COHERENT)
        report = validate_local(
            c,
            (tension(disposition=TensionDisposition.RESOLVABLE),),
        )
        self.assertEqual(report.coherence_verdict, LocalCoherenceVerdict.COHERENT)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)

    def test_incoherence_is_a_valid_local_verdict_not_a_validator_failure(self):
        c = claim(verdict=LocalCoherenceVerdict.INCOHERENT)
        report = validate_local(c, (tension(),))
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(report.coherence_verdict, LocalCoherenceVerdict.INCOHERENT)

    def test_no_tension_list_does_not_prove_tension_free_totality(self):
        c = claim(total=True)
        report = validate_local(c, ())
        self.assertIn("MS_TC_TENSION_TOTALITY_FORBIDDEN", {x.code for x in report.issues})
        self.assertFalse(report.tension_exhaustive)

    def test_generativity_is_not_assumed(self):
        c = claim()
        report = validate_local(c, (tension(generativity=GenerativityStatus.UNESTABLISHED),))
        self.assertEqual(report.generativity_supported_ids, ())
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)

    def test_generativity_requires_specific_evidence(self):
        c = claim()
        item = tension(
            generativity=GenerativityStatus.SUPPORTED,
            generativity_evidence_refs=(),
        )
        report = validate_local(c, (item,))
        self.assertIn(
            "MS_TC_GENERATIVITY_EVIDENCE_REQUIRED",
            {x.code for x in report.issues},
        )

    def test_supported_generativity_remains_local_and_non_authorizing(self):
        c = claim()
        item = tension(
            generativity=GenerativityStatus.SUPPORTED,
            generativity_evidence_refs=("evidence:generativity:1",),
        )
        report = validate_local(c, (item,))
        self.assertEqual(report.generativity_supported_ids, ("t:1",))
        self.assertFalse(report.independent_validation)
        self.assertFalse(report.execution_authority)

    def test_indeterminate_tension_stays_indeterminate(self):
        c = claim()
        report = validate_local(
            c,
            (tension(disposition=TensionDisposition.INDETERMINATE),),
        )
        self.assertEqual(report.status, CoherenceStatus.INDETERMINATE)
        self.assertTrue(report.has_indeterminate)

    def test_contested_tension_stays_contested(self):
        c = claim()
        report = validate_local(
            c,
            (tension(contestation_refs=("contest:1",)),),
        )
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)
        self.assertTrue(report.has_contestation)

    def test_same_contract_allows_different_verdicts_across_scales(self):
        verdicts = {
            Scale.MICRO: LocalCoherenceVerdict.COHERENT,
            Scale.MESO: LocalCoherenceVerdict.INCOHERENT,
            Scale.MACRO: LocalCoherenceVerdict.COHERENT,
            Scale.META: LocalCoherenceVerdict.COHERENT,
        }
        reports = []
        for scale in Scale:
            reports.append(
                validate_local(
                    claim(scale=scale, verdict=verdicts[scale]),
                    (tension(scale=scale, tension_id=f"t:{scale.value}"),),
                )
            )
        multi = validate_multiscale_tension_coherence(reports)
        self.assertEqual(multi.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(
            {r.scale: r.coherence_verdict for r in multi.scale_reports},
            verdicts,
        )

    def test_lower_scale_contestation_cannot_be_masked(self):
        reports = []
        for scale in Scale:
            contests = ("contest:micro",) if scale == Scale.MICRO else ()
            reports.append(
                validate_local(
                    claim(scale=scale),
                    (
                        tension(
                            scale=scale,
                            tension_id=f"t:{scale.value}",
                            contestation_refs=contests,
                        ),
                    ),
                )
            )
        multi = validate_multiscale_tension_coherence(reports)
        self.assertEqual(multi.status, CoherenceStatus.CONTESTED)
        self.assertTrue(multi.has_contestation)

    def test_missing_scale_keeps_multiscale_report_partial(self):
        local = validate_local(claim(), (tension(),))
        multi = validate_multiscale_tension_coherence((local,))
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_TC_SCALE_MISSING", {x.code for x in multi.issues})


if __name__ == "__main__":
    unittest.main()
