import unittest

from conscience_c_brain.nonclosure_guard import (
    ClosureState,
    PresentationEnvelope,
    validate_multiscale_nonclosure,
    validate_presentation_closure,
)
from conscience_c_brain.multiscale_coherence import CoherenceStatus, Scale


def envelope(
    scale=Scale.MICRO,
    *,
    presentation_id="p:1",
    unresolved_refs=(),
    claims_scope_exhaustiveness=False,
    claims_global_exhaustiveness=False,
    bounded_domain_ref=None,
    closure_criterion_ref=None,
    closure_proof_refs=(),
    reopening_triggers=("new_evidence",),
):
    return PresentationEnvelope(
        presentation_id=presentation_id,
        scale=scale,
        observer_ref=f"observer:{scale.value}",
        scope_ref=f"scope:{scale.value}",
        property_ref="property:coherence",
        property_version="1",
        trace_refs=(f"trace:{scale.value}",),
        unresolved_refs=unresolved_refs,
        bounded_domain_ref=bounded_domain_ref,
        closure_criterion_ref=closure_criterion_ref,
        closure_proof_refs=closure_proof_refs,
        claims_scope_exhaustiveness=claims_scope_exhaustiveness,
        claims_global_exhaustiveness=claims_global_exhaustiveness,
        reopening_triggers=reopening_triggers,
    )


def validate(item):
    return validate_presentation_closure(
        item,
        available_trace_refs=item.trace_refs,
        available_proof_refs=("proof:finite-enumeration",),
    )


class NonClosureGuardTests(unittest.TestCase):
    def test_open_by_default_is_valid_without_totality_claim(self):
        report = validate(envelope())
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(report.state, ClosureState.OPEN)
        self.assertFalse(report.locally_exhaustive)
        self.assertFalse(report.globally_exhaustive)

    def test_global_exhaustiveness_is_always_rejected(self):
        report = validate(envelope(claims_global_exhaustiveness=True))
        self.assertIn("MS_NC_GLOBAL_CLOSURE_FORBIDDEN", {x.code for x in report.issues})
        self.assertFalse(report.globally_exhaustive)

    def test_local_closure_requires_bounded_domain_criterion_and_proof(self):
        report = validate(envelope(claims_scope_exhaustiveness=True))
        codes = {x.code for x in report.issues}
        self.assertIn("MS_NC_BOUNDED_DOMAIN_REQUIRED", codes)
        self.assertIn("MS_NC_CLOSURE_CRITERION_REQUIRED", codes)
        self.assertIn("MS_NC_CLOSURE_PROOF_REQUIRED", codes)
        self.assertFalse(report.locally_exhaustive)

    def test_bounded_local_closure_can_be_structurally_admissible(self):
        item = envelope(
            claims_scope_exhaustiveness=True,
            bounded_domain_ref="domain:finite-v1",
            closure_criterion_ref="criterion:enumerated-all-members",
            closure_proof_refs=("proof:finite-enumeration",),
        )
        report = validate(item)
        self.assertEqual(report.status, CoherenceStatus.CANDIDATE_OK)
        self.assertEqual(report.state, ClosureState.LOCALLY_CLOSED)
        self.assertTrue(report.locally_exhaustive)
        self.assertFalse(report.globally_exhaustive)
        self.assertFalse(report.independent_validation)
        self.assertFalse(report.execution_authority)

    def test_unresolved_items_block_local_exhaustiveness(self):
        item = envelope(
            unresolved_refs=("unknown:1",),
            claims_scope_exhaustiveness=True,
            bounded_domain_ref="domain:finite-v1",
            closure_criterion_ref="criterion:enumerated-all-members",
            closure_proof_refs=("proof:finite-enumeration",),
        )
        report = validate(item)
        self.assertIn("MS_NC_UNRESOLVED_CONFLICTS_WITH_CLOSURE", {x.code for x in report.issues})
        self.assertFalse(report.locally_exhaustive)

    def test_unresolved_open_presentation_is_indeterminate(self):
        report = validate(envelope(unresolved_refs=("unknown:1",)))
        self.assertEqual(report.status, CoherenceStatus.INDETERMINATE)
        self.assertEqual(report.state, ClosureState.INDETERMINATE)

    def test_every_presentation_requires_reopening_trigger(self):
        report = validate(envelope(reopening_triggers=()))
        self.assertIn("MS_NC_REOPEN_TRIGGER_REQUIRED", {x.code for x in report.issues})

    def test_four_local_closures_never_become_global_closure(self):
        reports = []
        for scale in Scale:
            item = envelope(
                scale=scale,
                presentation_id=f"p:{scale.value}",
                claims_scope_exhaustiveness=True,
                bounded_domain_ref=f"domain:{scale.value}",
                closure_criterion_ref="criterion:enumerated-all-members",
                closure_proof_refs=("proof:finite-enumeration",),
            )
            reports.append(validate(item))
        multi = validate_multiscale_nonclosure(reports)
        self.assertEqual(multi.status, CoherenceStatus.CANDIDATE_OK)
        self.assertTrue(multi.all_scales_locally_closed)
        self.assertFalse(multi.globally_exhaustive)
        self.assertFalse(multi.execution_authority)

    def test_missing_scale_keeps_multiscale_report_partial(self):
        multi = validate_multiscale_nonclosure((validate(envelope()),))
        self.assertEqual(multi.status, CoherenceStatus.PARTIAL)
        self.assertIn("MS_NC_SCALE_MISSING", {x.code for x in multi.issues})

    def test_indeterminate_lower_scale_remains_visible(self):
        reports = []
        for scale in Scale:
            unresolved = ("unknown:micro",) if scale == Scale.MICRO else ()
            reports.append(validate(envelope(scale=scale, unresolved_refs=unresolved)))
        multi = validate_multiscale_nonclosure(reports)
        self.assertEqual(multi.status, CoherenceStatus.INDETERMINATE)
        self.assertFalse(multi.globally_exhaustive)


if __name__ == "__main__":
    unittest.main()
