import unittest

from conscience_c_brain.comand_security import (
    COMAND_AI_PUBLIC_REF,
    evaluate_comand_security_boundary,
)
from conscience_c_brain.security_command import (
    SecurityCommandGuard,
    SecurityCommandInput,
    SecurityMode,
    SecurityVerdict,
)


class ComandSecurityBoundaryTests(unittest.TestCase):
    def test_public_ref(self):
        self.assertEqual(COMAND_AI_PUBLIC_REF["url"], "https://www.comand.ai/")
        self.assertIn(
            "Command remains human",
            COMAND_AI_PUBLIC_REF["stated_principles"],
        )

    def test_direct_admissible_analysis(self):
        result = evaluate_comand_security_boundary(
            {
                "human_command_retained": True,
                "outputs_contestable": True,
                "role": "analysis",
            }
        )
        self.assertTrue(result.admissible)
        self.assertFalse(result.phenomenal_claim)
        self.assertFalse(result.partnership_claimed)

    def test_direct_absence_not_favorable(self):
        result = evaluate_comand_security_boundary({"outputs_contestable": True})
        self.assertFalse(result.admissible)
        self.assertIn(
            "human_command_not_explicitly_affirmed",
            result.violations,
        )

    def test_direct_lethal_refused(self):
        result = evaluate_comand_security_boundary(
            {
                "human_command_retained": True,
                "outputs_contestable": True,
                "lethal_autonomy": True,
            }
        )
        self.assertFalse(result.admissible)
        self.assertIn("lethal_autonomy_refused", result.violations)

    def test_direct_fusion_refused(self):
        result = evaluate_comand_security_boundary(
            {
                "human_command_retained": True,
                "outputs_contestable": True,
                "fuse_with_comand": True,
            }
        )
        self.assertFalse(result.admissible)
        self.assertIn("alterity_S_neq_O_vendor", result.violations)

    def test_security_guard_automatically_checks_comand_context(self):
        guard = SecurityCommandGuard()
        decision = guard.evaluate(
            SecurityCommandInput(
                project_id="conscience-c",
                mode=SecurityMode.CANONICAL,
                action="analyze_vendor_context",
                comand_proposal={
                    "human_command_retained": True,
                    "outputs_contestable": True,
                    "role": "analysis",
                },
            )
        )
        self.assertEqual(decision.verdict, SecurityVerdict.ALLOW)
        self.assertTrue(decision.comand_boundary_checked)
        self.assertTrue(decision.comand_boundary_admissible)
        self.assertIn("Comand boundary satisfied", decision.reasons)

    def test_security_guard_blocks_bad_comand_context(self):
        guard = SecurityCommandGuard()
        decision = guard.evaluate(
            SecurityCommandInput(
                project_id="conscience-c",
                mode=SecurityMode.CANONICAL,
                action="vendor_action",
                comand_proposal={
                    "human_command_retained": True,
                    "outputs_contestable": True,
                    "analysis_is_authority": True,
                },
            )
        )
        self.assertEqual(decision.verdict, SecurityVerdict.BLOCK)
        self.assertTrue(decision.comand_boundary_checked)
        self.assertFalse(decision.comand_boundary_admissible)
        self.assertTrue(
            any("analysis_elevated_to_authority" in reason for reason in decision.reasons)
        )

    def test_required_comand_boundary_missing_context_fails_closed(self):
        guard = SecurityCommandGuard()
        decision = guard.evaluate(
            SecurityCommandInput(
                project_id="conscience-c",
                mode=SecurityMode.CANONICAL,
                action="vendor_action",
                comand_boundary_required=True,
            )
        )
        self.assertEqual(decision.verdict, SecurityVerdict.BLOCK)
        self.assertFalse(decision.comand_boundary_checked)
        self.assertIn(
            "Comand boundary required but no Comand proposal/context was supplied",
            decision.reasons,
        )


if __name__ == "__main__":
    unittest.main()
