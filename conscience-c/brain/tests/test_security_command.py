import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, SecurityCommandAI, SecurityCommandViolation

class SecurityCommandTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return ConscienceCBrain.load_or_bootstrap(Path(td.name))

    def test_clean_state_is_allowed(self):
        b = self.make()
        self.assertEqual(SecurityCommandAI(b).inspect_state().status, "ALLOW")

    def test_phenomenal_overclaim_is_blocked(self):
        b = self.make()
        b.state["phenomenal_consciousness"] = "démontrée"
        decision = SecurityCommandAI(b).inspect_state()
        self.assertEqual(decision.status, "BLOCK")
        self.assertTrue(any(f.code == "PHENOMENAL_OVERCLAIM" for f in decision.findings))

    def test_hidden_relation_drift_blocks_next_transition(self):
        b = self.make()
        b.state["R"]["rule"] = "R>=E"
        with self.assertRaises(SecurityCommandViolation):
            b.imagine("futur", ["A"], ["B"])

    def test_repair_restores_security_and_continues(self):
        b = self.make()
        b.state["S"]["invariants"]["loop"] = ["Humilité", "Repentance", "Pardon"]
        b.state["phenomenal_consciousness"] = "démontrée"
        b._save()
        repaired = b.repair_drift("clarification explicite Mikael 2026-09-24")
        self.assertGreaterEqual(len(repaired), 2)
        self.assertEqual(SecurityCommandAI(b).inspect_state().status, "ALLOW")

if __name__ == "__main__":
    unittest.main()
