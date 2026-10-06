import unittest

from conscience_c_brain.generator_ensemble import (
    GeneratorHypothesis,
    HypothesisFit,
    ProjectionClaim,
    ProjectionEvidence,
    assess_hypothesis,
    revise_hypothesis_space,
    validate_multiscale_hypothesis_space,
)
from conscience_c_brain.multiscale_coherence import CoherenceStatus, Scale


def hypothesis(
    hypothesis_id,
    *,
    scale=Scale.MICRO,
    observer="observer:a",
    scope="scope:a",
    claims=(("omega", "open"),),
    origin=None,
):
    return GeneratorHypothesis(
        hypothesis_id=hypothesis_id,
        scale=scale,
        observer_ref=observer,
        scope_ref=scope,
        projection_claims=tuple(ProjectionClaim(k, v) for k, v in claims),
        assumption_refs=(f"assumption:{hypothesis_id}",),
        origin_refs=(origin or f"origin:{hypothesis_id}",),
        provenance_bundle_refs=(f"prov:{hypothesis_id}",),
    )


def evidence(
    evidence_id="e1",
    *,
    scale=Scale.MICRO,
    observer="observer:a",
    scope="scope:a",
    observations=(("omega", "open"),),
):
    return ProjectionEvidence(
        evidence_id=evidence_id,
        scale=scale,
        observer_ref=observer,
        scope_ref=scope,
        observations=tuple(ProjectionClaim(k, v) for k, v in observations),
        trace_refs=(f"trace:{evidence_id}",),
    )


class GeneratorEnsembleTests(unittest.TestCase):
    def test_two_observationally_equivalent_hypotheses_keep_unknown_xi(self):
        h1 = hypothesis("xi:1", claims=(("omega", "open"), ("phi", "mature")))
        h2 = hypothesis("xi:2", claims=(("omega", "open"), ("phi", "regenerate")))
        rev = revise_hypothesis_space(
            revision_id="rev:1",
            scale=Scale.MICRO,
            current_hypotheses=(h1, h2),
            evidence=(evidence(observations=(("omega", "open"),)),),
        )
        self.assertEqual(rev.status, CoherenceStatus.INDETERMINATE)
        self.assertTrue(rev.unknown_xi)
        self.assertFalse(rev.out_of_model)
        self.assertIn(("xi:1", "xi:2"), rev.observational_equivalence_classes)

    def test_discriminating_trace_can_remove_one_without_proving_the_other_true(self):
        h1 = hypothesis("xi:1", claims=(("omega", "open"), ("phi", "mature")))
        h2 = hypothesis("xi:2", claims=(("omega", "open"), ("phi", "regenerate")))
        rev = revise_hypothesis_space(
            revision_id="rev:2",
            scale=Scale.MICRO,
            current_hypotheses=(h1, h2),
            evidence=(
                evidence(
                    observations=(("omega", "open"), ("phi", "mature")),
                ),
            ),
        )
        self.assertEqual(rev.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(rev.retained_hypothesis_ids, ("xi:1",))
        self.assertEqual(rev.rejected_hypothesis_ids, ("xi:2",))
        self.assertFalse(rev.unknown_xi)
        self.assertFalse(rev.independent_validation)
        self.assertFalse(rev.execution_authority)

    def test_no_fitting_hypothesis_is_out_of_model_not_forced_choice(self):
        h1 = hypothesis("xi:1", claims=(("omega", "closed"),))
        h2 = hypothesis("xi:2", claims=(("omega", "sealed"),))
        rev = revise_hypothesis_space(
            revision_id="rev:3",
            scale=Scale.MICRO,
            current_hypotheses=(h1, h2),
            evidence=(evidence(observations=(("omega", "open"),)),),
        )
        self.assertTrue(rev.out_of_model)
        self.assertFalse(rev.unknown_xi)
        self.assertEqual(rev.retained_hypothesis_ids, ())
        self.assertEqual(rev.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_XI_OUT_OF_MODEL", {x.code for x in rev.issues})

    def test_no_overlapping_projection_stays_underdetermined(self):
        h1 = hypothesis("xi:1", claims=(("phi", "mature"),))
        report = assess_hypothesis(
            h1,
            (evidence(observations=(("omega", "open"),)),),
        )
        self.assertEqual(report.fit, HypothesisFit.UNDERDETERMINED)

    def test_hypothesis_requires_explicit_projection_and_provenance(self):
        bad = GeneratorHypothesis(
            hypothesis_id="xi:bad",
            scale=Scale.MICRO,
            observer_ref="observer:a",
            scope_ref="scope:a",
            projection_claims=(),
            assumption_refs=(),
            origin_refs=(),
            provenance_bundle_refs=(),
        )
        report = assess_hypothesis(bad, (evidence(),))
        codes = {x.code for x in report.issues}
        self.assertIn("MS_XI_PROJECTION_REQUIRED", codes)
        self.assertIn("MS_XI_ASSUMPTION_REQUIRED", codes)
        self.assertIn("MS_XI_ORIGIN_REQUIRED", codes)
        self.assertIn("MS_XI_PROVENANCE_REQUIRED", codes)

    def test_revision_preserves_previous_and_rejected_ids(self):
        h1 = hypothesis("xi:1", claims=(("omega", "closed"),))
        h2 = hypothesis("xi:2", claims=(("omega", "open"),))
        rev = revise_hypothesis_space(
            revision_id="rev:4",
            scale=Scale.MICRO,
            current_hypotheses=(h1, h2),
            evidence=(evidence(),),
        )
        self.assertEqual(rev.previous_hypothesis_ids, ("xi:1", "xi:2"))
        self.assertEqual(rev.rejected_hypothesis_ids, ("xi:1",))
        self.assertEqual(rev.retained_hypothesis_ids, ("xi:2",))

    def test_new_hypothesis_is_recorded_as_added_but_not_privileged(self):
        old = hypothesis("xi:old", claims=(("omega", "closed"),))
        new = hypothesis("xi:new", claims=(("omega", "open"),))
        rev = revise_hypothesis_space(
            revision_id="rev:5",
            scale=Scale.MICRO,
            current_hypotheses=(old,),
            proposed_hypotheses=(new,),
            evidence=(evidence(),),
        )
        self.assertEqual(rev.added_hypothesis_ids, ("xi:new",))
        self.assertEqual(rev.retained_hypothesis_ids, ("xi:new",))
        self.assertFalse(rev.independent_validation)

    def test_same_contract_operates_at_all_four_scales(self):
        revisions = []
        for scale in Scale:
            observer = f"observer:{scale.value}"
            scope = f"scope:{scale.value}"
            h1 = hypothesis(
                f"{scale.value}:xi:1",
                scale=scale, observer=observer, scope=scope,
                claims=(("omega", "open"),),
            )
            h2 = hypothesis(
                f"{scale.value}:xi:2",
                scale=scale, observer=observer, scope=scope,
                claims=(("omega", "open"),),
            )
            revisions.append(
                revise_hypothesis_space(
                    revision_id=f"rev:{scale.value}",
                    scale=scale,
                    current_hypotheses=(h1, h2),
                    evidence=(
                        evidence(
                            evidence_id=f"e:{scale.value}",
                            scale=scale, observer=observer, scope=scope,
                            observations=(("omega", "open"),),
                        ),
                    ),
                )
            )
        multi = validate_multiscale_hypothesis_space(revisions)
        self.assertEqual(multi.status, CoherenceStatus.INDETERMINATE)
        self.assertTrue(multi.has_unknown_xi)
        self.assertFalse(multi.execution_authority)

    def test_lower_scale_out_of_model_cannot_be_masked(self):
        revisions = []
        for scale in Scale:
            observer = f"observer:{scale.value}"
            scope = f"scope:{scale.value}"
            predicted = "closed" if scale == Scale.MICRO else "open"
            h = hypothesis(
                f"{scale.value}:xi",
                scale=scale, observer=observer, scope=scope,
                claims=(("omega", predicted),),
            )
            revisions.append(
                revise_hypothesis_space(
                    revision_id=f"rev:{scale.value}",
                    scale=scale,
                    current_hypotheses=(h,),
                    evidence=(
                        evidence(
                            evidence_id=f"e:{scale.value}",
                            scale=scale, observer=observer, scope=scope,
                            observations=(("omega", "open"),),
                        ),
                    ),
                )
            )
        multi = validate_multiscale_hypothesis_space(revisions)
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertTrue(multi.has_out_of_model)

    def test_missing_scale_keeps_composite_partial(self):
        h = hypothesis("xi:1")
        rev = revise_hypothesis_space(
            revision_id="rev:single",
            scale=Scale.MICRO,
            current_hypotheses=(h,),
            evidence=(evidence(),),
        )
        multi = validate_multiscale_hypothesis_space((rev,))
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_XI_SCALE_MISSING", {x.code for x in multi.issues})


if __name__ == "__main__":
    unittest.main()
