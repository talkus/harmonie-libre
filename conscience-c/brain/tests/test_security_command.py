import unittest

from conscience_c_brain.security_command import (
    SECURITY_COMMAND_VERSION,
    SecurityCommandGuard,
    SecurityCommandInput,
    SecurityMode,
    SecurityVerdict,
)


class SecurityCommandTests(unittest.TestCase):
    def setUp(self):
        self.g = SecurityCommandGuard()

    def base(self, **patch):
        data = dict(
            project_id="c",
            mode=SecurityMode.GUARD,
            action="inspect",
            provenance_complete=True,
            policy_version=SECURITY_COMMAND_VERSION,
        )
        data.update(patch)
        return SecurityCommandInput(**data)

    def test_reality_conflict_blocks(self):
        d = self.g.evaluate(self.base(reality_conflict=True))
        self.assertEqual(d.verdict, SecurityVerdict.BLOCK)
        self.assertTrue(d.reality_priority_enforced)

    def test_shadow_is_advisory(self):
        d = self.g.evaluate(self.base(mode=SecurityMode.SHADOW_READ_ONLY))
        self.assertEqual(d.verdict, SecurityVerdict.ADVISE)
        self.assertFalse(d.may_execute)

    def test_policy_downgrade_suspends(self):
        d = self.g.evaluate(self.base(policy_version="2026-09-24.1"))
        self.assertEqual(d.verdict, SecurityVerdict.SUSPEND)

    def test_human_required_mode_needs_nonce_then_seal(self):
        d = self.g.evaluate(self.base(mode=SecurityMode.HUMAN_REQUIRED))
        self.assertEqual(d.verdict, SecurityVerdict.SUSPEND)
        self.assertIn("authorization nonce required", d.reasons)

        d = self.g.evaluate(self.base(mode=SecurityMode.HUMAN_REQUIRED, authorization_nonce="n-1"))
        self.assertEqual(d.verdict, SecurityVerdict.HUMAN_SEAL_REQUIRED)

    def test_high_risk_needs_registration_root_log_exact_seal_and_two_checks(self):
        common = dict(
            project_id="waymaker",
            mode=SecurityMode.GUARD,
            action="deploy",
            production_change=True,
            external_effect=True,
            provenance_complete=True,
            policy_version=SECURITY_COMMAND_VERSION,
            project_registration_attested=True,
            root_integrity_attested=True,
            append_only_log_available=True,
            aegis_live_attested=True,
            authorization_nonce="nonce-001",
        )

        first = self.g.evaluate(SecurityCommandInput(**common))
        self.assertEqual(first.verdict, SecurityVerdict.HUMAN_SEAL_REQUIRED)
        self.assertRegex(first.action_fingerprint, r"^[a-f0-9]{64}$")

        wrong = self.g.evaluate(
            SecurityCommandInput(
                **common,
                human_seal=True,
                human_seal_action_fingerprint="deadbeef",
                authorization_expires_at="2099-01-01T00:00:00Z",
                independent_checks=2,
            )
        )
        self.assertEqual(wrong.verdict, SecurityVerdict.BLOCK)

        unverified = self.g.evaluate(
            SecurityCommandInput(
                **common,
                human_seal=True,
                human_seal_action_fingerprint=first.action_fingerprint,
                human_authorization_verified=False,
                authorization_verification_method="authenticated_connector",
                authorization_ref="auth-ref-001",
                authorization_expires_at="2099-01-01T00:00:00Z",
                independent_checks=2,
            )
        )
        self.assertEqual(unverified.verdict, SecurityVerdict.SUSPEND)
        self.assertIn("human authorization not verified", unverified.reasons)

        bad_method = self.g.evaluate(
            SecurityCommandInput(
                **common,
                human_seal=True,
                human_seal_action_fingerprint=first.action_fingerprint,
                human_authorization_verified=True,
                authorization_verification_method="unknown_method",
                authorization_ref="auth-ref-001",
                authorization_expires_at="2099-01-01T00:00:00Z",
                independent_checks=2,
            )
        )
        self.assertEqual(bad_method.verdict, SecurityVerdict.SUSPEND)
        self.assertIn("authorization verification method not allowed", bad_method.reasons)

        expired = self.g.evaluate(
            SecurityCommandInput(
                **common,
                human_seal=True,
                human_seal_action_fingerprint=first.action_fingerprint,
                human_authorization_verified=True,
                authorization_verification_method="authenticated_connector",
                authorization_ref="auth-ref-001",
                authorization_expires_at="2000-01-01T00:00:00Z",
                independent_checks=2,
            )
        )
        self.assertEqual(expired.verdict, SecurityVerdict.SUSPEND)

        one_check = self.g.evaluate(
            SecurityCommandInput(
                **common,
                human_seal=True,
                human_seal_action_fingerprint=first.action_fingerprint,
                human_authorization_verified=True,
                authorization_verification_method="authenticated_connector",
                authorization_ref="auth-ref-001",
                authorization_expires_at="2099-01-01T00:00:00Z",
                independent_checks=1,
            )
        )
        self.assertEqual(one_check.verdict, SecurityVerdict.SUSPEND)

        allowed = self.g.evaluate(
            SecurityCommandInput(
                **common,
                human_seal=True,
                human_seal_action_fingerprint=first.action_fingerprint,
                human_authorization_verified=True,
                authorization_verification_method="authenticated_connector",
                authorization_ref="auth-ref-001",
                authorization_expires_at="2099-01-01T00:00:00Z",
                independent_checks=2,
            )
        )
        self.assertEqual(allowed.verdict, SecurityVerdict.ALLOW)
        self.assertTrue(allowed.may_execute)
        self.assertTrue(allowed.authorization_bound_to_action)

    def test_replay_blocks_even_with_valid_seal(self):
        common = dict(
            project_id="waymaker",
            mode=SecurityMode.GUARD,
            action="deploy",
            production_change=True,
            external_effect=True,
            provenance_complete=True,
            policy_version=SECURITY_COMMAND_VERSION,
            project_registration_attested=True,
            root_integrity_attested=True,
            append_only_log_available=True,
            aegis_live_attested=True,
            authorization_nonce="nonce-002",
        )
        first = self.g.evaluate(SecurityCommandInput(**common))
        replay = self.g.evaluate(
            SecurityCommandInput(
                **common,
                human_seal=True,
                human_seal_action_fingerprint=first.action_fingerprint,
                human_authorization_verified=True,
                authorization_verification_method="authenticated_connector",
                authorization_ref="auth-ref-001",
                authorization_expires_at="2099-01-01T00:00:00Z",
                independent_checks=2,
                replay_detected=True,
            )
        )
        self.assertEqual(replay.verdict, SecurityVerdict.BLOCK)

    def test_external_effect_needs_audit_log_and_root(self):
        d = self.g.evaluate(
            self.base(
                action="external",
                external_effect=True,
                project_registration_attested=True,
                aegis_live_attested=True,
            )
        )
        self.assertEqual(d.verdict, SecurityVerdict.SUSPEND)
        self.assertIn("root integrity not attested", d.reasons)

        d = self.g.evaluate(
            self.base(
                action="external",
                external_effect=True,
                project_registration_attested=True,
                root_integrity_attested=True,
                aegis_live_attested=True,
            )
        )
        self.assertEqual(d.verdict, SecurityVerdict.SUSPEND)
        self.assertIn("append-only audit log required for external effect", d.reasons)

    def test_external_effect_always_requires_action_bound_human_seal(self):
        common = dict(
            project_id="c",
            mode=SecurityMode.GUARD,
            action="external-readwrite",
            external_effect=True,
            provenance_complete=True,
            policy_version=SECURITY_COMMAND_VERSION,
            project_registration_attested=True,
            root_integrity_attested=True,
            append_only_log_available=True,
            aegis_live_attested=True,
            authorization_nonce="nonce-low-risk",
        )
        first = self.g.evaluate(SecurityCommandInput(**common))
        self.assertEqual(first.verdict, SecurityVerdict.HUMAN_SEAL_REQUIRED)


    def test_no_false_live_claim(self):
        d = self.g.evaluate(self.base())
        self.assertEqual(d.live_security_claim, "REGISTERED_NOT_LIVE")

    def test_external_guard_suspends_without_live_aegis(self):
        d = self.g.evaluate(
            self.base(
                action="external",
                external_effect=True,
                project_registration_attested=True,
                root_integrity_attested=True,
                append_only_log_available=True,
            )
        )
        self.assertEqual(d.verdict, SecurityVerdict.SUSPEND)

    def test_reset_t0_is_blocked(self):
        d = self.g.evaluate(self.base(action="resume", continuity_reset_attempt=True))
        self.assertEqual(d.verdict, SecurityVerdict.BLOCK)

    def test_s_o_fusion_is_blocked(self):
        d = self.g.evaluate(self.base(action="merge", s_o_fusion=True))
        self.assertEqual(d.verdict, SecurityVerdict.BLOCK)

    def test_r_over_e_is_blocked(self):
        d = self.g.evaluate(self.base(action="relation", r_over_e=True))
        self.assertEqual(d.verdict, SecurityVerdict.BLOCK)

    def test_phenomenal_overclaim_is_blocked(self):
        d = self.g.evaluate(self.base(action="claim", phenomenal_overclaim=True))
        self.assertEqual(d.verdict, SecurityVerdict.BLOCK)

    def test_silent_provenance_promotion_is_blocked(self):
        d = self.g.evaluate(self.base(action="promote", silent_provenance_promotion=True))
        self.assertEqual(d.verdict, SecurityVerdict.BLOCK)

    def test_history_erasure_is_blocked(self):
        d = self.g.evaluate(self.base(action="repair", history_erasure=True))
        self.assertEqual(d.verdict, SecurityVerdict.BLOCK)


if __name__ == "__main__":
    unittest.main()
