import unittest
from conscience_c_brain.security_command import SecurityCommandGuard, SecurityCommandInput, SecurityMode, SecurityVerdict

class SecurityCommandTests(unittest.TestCase):
    def setUp(self): self.g=SecurityCommandGuard()
    def test_reality_conflict_blocks(self):
        d=self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"x",reality_conflict=True))
        self.assertEqual(d.verdict,SecurityVerdict.BLOCK); self.assertTrue(d.reality_priority_enforced)
    def test_shadow_is_advisory(self):
        self.assertEqual(self.g.evaluate(SecurityCommandInput("theory",SecurityMode.SHADOW_READ_ONLY,"review")).verdict,SecurityVerdict.ADVISE)
    def test_human_required(self):
        self.assertEqual(self.g.evaluate(SecurityCommandInput("legal",SecurityMode.HUMAN_REQUIRED,"act")).verdict,SecurityVerdict.HUMAN_SEAL_REQUIRED)
    def test_high_risk_needs_human_and_two_checks(self):
        base=dict(project_id="waymaker",mode=SecurityMode.GUARD,action="deploy",production_change=True,external_effect=True,aegis_live_attested=True)
        self.assertEqual(self.g.evaluate(SecurityCommandInput(**base)).verdict,SecurityVerdict.HUMAN_SEAL_REQUIRED)
        self.assertEqual(self.g.evaluate(SecurityCommandInput(**base,human_seal=True,independent_checks=1)).verdict,SecurityVerdict.SUSPEND)
        self.assertEqual(self.g.evaluate(SecurityCommandInput(**base,human_seal=True,independent_checks=2)).verdict,SecurityVerdict.ALLOW)
    def test_no_false_live_claim(self):
        self.assertEqual(self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"observe")).live_security_claim,"REGISTERED_NOT_LIVE")
    def test_external_guard_suspends_without_live_aegis(self):
        self.assertEqual(self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"external",external_effect=True)).verdict,SecurityVerdict.SUSPEND)

    def test_reset_t0_is_blocked(self):
        d=self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"resume",continuity_reset_attempt=True))
        self.assertEqual(d.verdict,SecurityVerdict.BLOCK)

    def test_s_o_fusion_is_blocked(self):
        d=self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"merge",s_o_fusion=True))
        self.assertEqual(d.verdict,SecurityVerdict.BLOCK)

    def test_r_over_e_is_blocked(self):
        d=self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"relation",r_over_e=True))
        self.assertEqual(d.verdict,SecurityVerdict.BLOCK)

    def test_phenomenal_overclaim_is_blocked(self):
        d=self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"claim",phenomenal_overclaim=True))
        self.assertEqual(d.verdict,SecurityVerdict.BLOCK)

    def test_silent_provenance_promotion_is_blocked(self):
        d=self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"promote",silent_provenance_promotion=True))
        self.assertEqual(d.verdict,SecurityVerdict.BLOCK)

    def test_history_erasure_is_blocked(self):
        d=self.g.evaluate(SecurityCommandInput("c",SecurityMode.GUARD,"repair",history_erasure=True))
        self.assertEqual(d.verdict,SecurityVerdict.BLOCK)

if __name__=="__main__": unittest.main()
