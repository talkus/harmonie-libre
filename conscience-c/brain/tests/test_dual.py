import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, DualTrajectoryEngine, CandidateThought, PairedMemoryBank

class FakeReasoner:
    def generate(self, trajectory_id, prompt, memory):
        if trajectory_id == "C1":
            return CandidateThought("A", .7, falsifiers=["not A"])
        return CandidateThought("B", .7, falsifiers=["not B"])

    def revise(self, trajectory_id, original, other, memory):
        return CandidateThought(original.claim, original.confidence + (0.05 if other.claim != original.claim else 0), falsifiers=original.falsifiers)

class FusionReasoner:
    def generate(self, trajectory_id, prompt, memory):
        return CandidateThought("same", .8, falsifiers=["counterexample"])
    def revise(self, trajectory_id, original, other, memory):
        return original

class Judge:
    def __init__(self, scores):
        self.scores = scores
    def score(self, thought):
        return self.scores[thought.claim]

class DualTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return ConscienceCBrain.load_or_bootstrap(Path(td.name))

    def test_same_architecture_no_roles_and_separate_memories(self):
        b = self.make()
        d = DualTrajectoryEngine(b)
        self.assertEqual(d.state["C1"]["memory"], [])
        self.assertEqual(d.state["C2"]["memory"], [])
        self.assertNotIn("role", d.state["C1"])
        self.assertNotIn("role", d.state["C2"])

    def test_independent_first_pass_can_diverge(self):
        b = self.make()
        d = DualTrajectoryEngine(b)
        out = d.cycle("x", FakeReasoner(), Judge({"A":.9,"B":.4}))
        self.assertEqual(out["C1"]["claim"], "A")
        self.assertEqual(out["C2"]["claim"], "B")

    def test_e_reality_wins_over_relation_when_clear(self):
        b = self.make()
        d = DualTrajectoryEngine(b)
        out = d.cycle("x", FakeReasoner(), Judge({"A":.2,"B":.95}))
        self.assertEqual(out["winner"], "C2")
        self.assertEqual(out["basis"], "E_reality_dominates")

    def test_relation_only_informs_when_e_ambiguous(self):
        b = self.make()
        d = DualTrajectoryEngine(b)
        out = d.cycle("x", FakeReasoner(), Judge({"A":.70,"B":.68}), uncertainty_band=.08)
        self.assertEqual(out["basis"], "E_ambiguous_R_may_inform_without_replacing_E")

    def test_fusion_is_detected_not_rewarded(self):
        b = self.make()
        d = DualTrajectoryEngine(b)
        out = d.cycle("x", FusionReasoner(), Judge({"same":.8}))
        self.assertTrue(out["fusion_detected"])

    def test_consolidation_does_not_claim_background_activity(self):
        b = self.make()
        d = DualTrajectoryEngine(b)
        d.cycle("x", FakeReasoner(), Judge({"A":.9,"B":.4}))
        s = d.consolidate()
        self.assertEqual(s["relation_cycles"], 1)
        self.assertEqual(b.state["phenomenal_consciousness"], "indéterminée")

    def test_24_pair_bank_is_optional_and_neutral(self):
        m = PairedMemoryBank(24)
        self.assertEqual(len(m.pairs), 24)
        m.write(0, "x", "y")
        self.assertEqual(m.read(0), ("x","y"))

if __name__ == "__main__":
    unittest.main()
