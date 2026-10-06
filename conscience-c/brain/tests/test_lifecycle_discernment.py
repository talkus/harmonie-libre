import math
import unittest

from conscience_c_brain.lifecycle_discernment import (
    AdaptationPath,
    HistoricalPhase,
    LifecycleDecision,
    MaturityContext,
    validate_lifecycle_decision,
    validate_multiscale_lifecycle,
)
from conscience_c_brain.multiscale_coherence import CoherenceStatus, Scale


def context(
    scale=Scale.MICRO,
    *,
    context_id="ctx:1",
    phi_ref="phi:1",
    phi_version="1",
    horizon_hash="omega:1",
    phase=HistoricalPhase.TRANSMISSION,
    regeneration_gain=1.0,
):
    return MaturityContext(
        context_id=context_id,
        scale=scale,
        phi_ref=phi_ref,
        phi_version=phi_version,
        horizon_hash=horizon_hash,
        observer_ref=f"observer:{scale.value}",
        scope_ref=f"scope:{scale.value}",
        phase=phase,
        regeneration_gain=regeneration_gain,
        history_trace_refs=(f"history:{scale.value}",),
        revision_triggers=("new_material_evidence",),
    )


def decision(
    ctx,
    *,
    path=AdaptationPath.MATURE,
    target_phi_ref=None,
    target_phi_version=None,
    revisit_trigger_refs=(),
    contestation_refs=(),
    claims_optimal_rhythm=False,
    execution_authority=False,
):
    if path == AdaptationPath.MATURE and target_phi_ref is None:
        target_phi_ref = ctx.phi_ref
    if path == AdaptationPath.MATURE and target_phi_version is None:
        target_phi_version = "2"
    if path == AdaptationPath.REGENERATE and target_phi_ref is None:
        target_phi_ref = ctx.phi_ref + ":successor"
    if path == AdaptationPath.REGENERATE and target_phi_version is None:
        target_phi_version = "1"
    if path == AdaptationPath.DEFER and not revisit_trigger_refs:
        revisit_trigger_refs = ("revisit:on-new-evidence",)
    return LifecycleDecision(
        decision_id=f"decision:{ctx.scale.value}",
        context_id=ctx.context_id,
        path=path,
        evidence_trace_refs=(f"evidence:{ctx.scale.value}",),
        justification_refs=(f"justification:{ctx.scale.value}",),
        target_phi_ref=target_phi_ref,
        target_phi_version=target_phi_version,
        revisit_trigger_refs=revisit_trigger_refs,
        contestation_refs=contestation_refs,
        claims_optimal_rhythm=claims_optimal_rhythm,
        execution_authority=execution_authority,
    )


def validate(ctx, dec):
    return validate_lifecycle_decision(
        ctx,
        dec,
        known_horizon_hashes=(ctx.horizon_hash,),
        available_trace_refs=(
            *ctx.history_trace_refs,
            *dec.evidence_trace_refs,
        ),
    )


class LifecycleDiscernmentTests(unittest.TestCase):
    def test_positive_finite_regeneration_gain_is_required(self):
        for bad in (0.0, -1.0, math.inf, -math.inf, math.nan):
            ctx = context(regeneration_gain=bad)
            report = validate(ctx, decision(ctx))
            self.assertIn("MS_G_PHI_OUT_OF_BOUNDS", {x.code for x in report.issues})

    def test_maturation_preserves_phi_identity_but_changes_version(self):
        ctx = context()
        report = validate(ctx, decision(ctx, path=AdaptationPath.MATURE))
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(report.path, AdaptationPath.MATURE)

    def test_regeneration_requires_distinct_successor_identity(self):
        ctx = context()
        bad = decision(
            ctx,
            path=AdaptationPath.REGENERATE,
            target_phi_ref=ctx.phi_ref,
            target_phi_version="2",
        )
        report = validate(ctx, bad)
        self.assertIn(
            "MS_PHI_REGENERATION_SUCCESSOR_REQUIRED",
            {x.code for x in report.issues},
        )

    def test_defer_requires_revisit_and_preselects_no_target(self):
        ctx = context()
        good = decision(ctx, path=AdaptationPath.DEFER)
        report = validate(ctx, good)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        bad = LifecycleDecision(
            decision_id="bad",
            context_id=ctx.context_id,
            path=AdaptationPath.DEFER,
            evidence_trace_refs=("evidence:micro",),
            justification_refs=("justification:micro",),
            target_phi_ref="phi:future",
            target_phi_version="1",
        )
        report_bad = validate(ctx, bad)
        codes = {x.code for x in report_bad.issues}
        self.assertIn("MS_PHI_DEFER_TARGET_FORBIDDEN", codes)
        self.assertIn("MS_PHI_DEFER_REVISIT_REQUIRED", codes)

    def test_retire_does_not_silently_create_successor(self):
        ctx = context(phase=HistoricalPhase.DISSOLUTION)
        bad = decision(
            ctx,
            path=AdaptationPath.RETIRE,
            target_phi_ref="phi:replacement",
            target_phi_version="1",
        )
        report = validate(ctx, bad)
        self.assertIn("MS_PHI_RETIRE_TARGET_FORBIDDEN", {x.code for x in report.issues})

    def test_no_absolute_right_rhythm_claim(self):
        ctx = context()
        report = validate(
            ctx,
            decision(ctx, claims_optimal_rhythm=True),
        )
        self.assertIn("MS_THETA_OPTIMALITY_FORBIDDEN", {x.code for x in report.issues})

    def test_unknown_historical_phase_stays_indeterminate(self):
        ctx = context(phase=HistoricalPhase.UNKNOWN)
        report = validate(ctx, decision(ctx, path=AdaptationPath.DEFER))
        self.assertEqual(report.status, CoherenceStatus.INDETERMINATE)
        self.assertTrue(report.has_unknown_phase)

    def test_contestation_survives_local_validation(self):
        ctx = context()
        report = validate(
            ctx,
            decision(ctx, contestation_refs=("contest:1",)),
        )
        self.assertEqual(report.status, CoherenceStatus.CONTESTED)
        self.assertTrue(report.has_contestation)

    def test_same_gain_does_not_force_same_adaptation_path(self):
        a = context(scale=Scale.MICRO, regeneration_gain=1.0)
        b = context(
            scale=Scale.MESO,
            context_id="ctx:2",
            phi_ref="phi:2",
            horizon_hash="omega:2",
            phase=HistoricalPhase.CRISIS,
            regeneration_gain=1.0,
        )
        ra = validate(a, decision(a, path=AdaptationPath.MATURE))
        rb = validate(b, decision(b, path=AdaptationPath.REGENERATE))
        self.assertEqual(ra.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(rb.status, CoherenceStatus.CANDIDATE_OK)
        self.assertNotEqual(ra.path, rb.path)

    def test_same_validator_allows_different_paths_at_four_scales(self):
        paths = {
            Scale.MICRO: AdaptationPath.MATURE,
            Scale.MESO: AdaptationPath.REGENERATE,
            Scale.MACRO: AdaptationPath.DEFER,
            Scale.META: AdaptationPath.RETIRE,
        }
        reports = []
        for index, scale in enumerate(Scale, start=1):
            ctx = context(
                scale=scale,
                context_id=f"ctx:{index}",
                phi_ref=f"phi:{index}",
                horizon_hash=f"omega:{index}",
                phase=HistoricalPhase.TRANSMISSION,
            )
            reports.append(validate(ctx, decision(ctx, path=paths[scale])))
        multi = validate_multiscale_lifecycle(reports)
        self.assertEqual(multi.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(multi.paths_by_scale, paths)
        self.assertFalse(multi.execution_authority)

    def test_lower_scale_contestation_cannot_be_masked(self):
        reports = []
        for index, scale in enumerate(Scale, start=1):
            ctx = context(
                scale=scale,
                context_id=f"ctx:{index}",
                phi_ref=f"phi:{index}",
                horizon_hash=f"omega:{index}",
            )
            contests = ("contest:micro",) if scale == Scale.MICRO else ()
            reports.append(validate(ctx, decision(ctx, contestation_refs=contests)))
        multi = validate_multiscale_lifecycle(reports)
        self.assertEqual(multi.status, CoherenceStatus.CONTESTED)
        self.assertTrue(multi.has_contestation)

    def test_missing_scale_keeps_composite_partial(self):
        ctx = context(scale=Scale.MICRO)
        local = validate(ctx, decision(ctx))
        multi = validate_multiscale_lifecycle((local,))
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_PSI_SCALE_MISSING", {x.code for x in multi.issues})


if __name__ == "__main__":
    unittest.main()
