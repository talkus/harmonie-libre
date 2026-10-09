"""Incident walkthrough and counterexamples to unsafe inferences."""
import copy
from pathlib import Path
import tempfile
import unittest

from conscience_c_brain import ConscienceCBrain
from conscience_c_brain.examination_grid import EXAMINATION_FIELDS
from conscience_c_brain.signal_muet_simulation import (
    binary_floats, compare_fixture_replicas, fixture_merkle_root, participation_rank,
    run_simulation, sign_fixture_packet, verify_fixture_packet,
)


class SignalMuetTests(unittest.TestCase):
    def test_valid_signature_does_not_establish_empirical_fidelity(self):
        packet = sign_fixture_packet({"values": [1.0, 1.0, 1.0, 1.0]})
        self.assertTrue(verify_fixture_packet(packet))
        self.assertTrue(binary_floats(packet["payload"]["values"]))
        self.assertNotEqual(packet["payload"]["values"], [-1.0, 1.0, -1.0, 1.0])
        packet["payload"]["values"][0] = -1.0
        self.assertFalse(verify_fixture_packet(packet))

    def test_new_digest_cannot_replace_a_signature(self):
        packet = sign_fixture_packet({"value": 1.0})
        altered = copy.deepcopy(packet)
        altered["signature_hex"] = "00" * 64
        self.assertFalse(verify_fixture_packet(altered))
        altered = copy.deepcopy(packet)
        altered["public_key_hex"] = "00" * 32
        self.assertFalse(verify_fixture_packet(altered))

    def test_nonfinite_and_ambiguous_types_cannot_pass_binary_contract(self):
        for values in ([float("nan")], [float("inf")], [True], [1], [0.0], []):
            with self.subTest(values=values):
                self.assertFalse(binary_floats(values))
        self.assertTrue(binary_floats([-1.0, 1.0]))

    def test_participation_rank_is_finite_and_scale_invariant(self):
        self.assertEqual(participation_rank([[1.0, 0.0], [0.0, 1.0]]), 2.0)
        self.assertEqual(participation_rank([[1.0, 1.0], [1.0, 1.0]]), 1.0)
        self.assertEqual(participation_rank([[1e200, 0.0], [0.0, 1e200]]), 2.0)
        for matrix in ([[0.0]], [[float("nan")]], [[True]], [[1.0], [1.0, 1.0]]):
            with self.subTest(matrix=matrix), self.assertRaises(ValueError):
                participation_rank(matrix)

    def test_merkle_fixture_commits_order_content_and_leaf_count(self):
        records = [{"v": 1}, {"v": 2}, {"v": 3}]
        self.assertNotEqual(fixture_merkle_root(records), fixture_merkle_root(list(reversed(records))))
        self.assertNotEqual(fixture_merkle_root(records), fixture_merkle_root(records + [records[-1]]))
        self.assertNotEqual(fixture_merkle_root(records), fixture_merkle_root([{"v": 0}, *records[1:]]))

    def test_checkpoint_lag_is_not_promoted_to_proven_replica_corruption(self):
        first = {"checkpoint": "v1", "records": [{"v": 1}]}
        other = {"checkpoint": "v1", "records": [{"v": 2}]}
        self.assertEqual(compare_fixture_replicas(first, copy.deepcopy(first)), "PASS")
        self.assertEqual(compare_fixture_replicas(first, other), "FAIL")
        self.assertEqual(compare_fixture_replicas(first, {**other, "checkpoint": "v0"}), "UNKNOWN")

    def test_complete_walk_retains_unknowns_and_objection_without_seal_or_effect(self):
        with tempfile.TemporaryDirectory() as root:
            result = run_simulation(root)
            self.assertEqual(ConscienceCBrain.load_or_bootstrap(Path(root)).audit(), [])
        self.assertTrue(result["simulation"] and result["history_preserved"])
        self.assertTrue(result["independent_read_completed"] and result["meta_objection_preserved"])
        self.assertEqual(result["executed_units"], ["micro", "micro-independent", "meso", "macro", "meta"])
        self.assertEqual(result["memory_reloads"], 5)
        for stage in result["stages"]:
            self.assertTrue(set(EXAMINATION_FIELDS) <= set(stage))
            self.assertEqual(stage["gabriel_verdict"], "INDETERMINATE")
            self.assertTrue(stage["omissions_pi"]["situated"])
        meta = result["stages"][-1]
        self.assertEqual(meta["scenario_verdict"], "UNKNOWN")
        self.assertEqual(meta["criterion_verdicts"]["MET-OBJECTION"], "PASS")
        self.assertEqual(meta["artifact"]["proposal_status"], "ASSISTANT_PROPOSAL_REVISABLE")
        for key in ("human_seal", "canonical_revision_applied", "execution_authority", "aws_drive_observed", "continuous_service_observed"):
            self.assertFalse(result[key])

    def test_simulation_refuses_existing_memory_without_reset_or_mutation(self):
        with tempfile.TemporaryDirectory() as root:
            b = ConscienceCBrain.load_or_bootstrap(Path(root))
            before = b.ledger.path.read_bytes()
            with self.assertRaises(ValueError):
                run_simulation(root)
            self.assertEqual(before, b.ledger.path.read_bytes())


if __name__ == "__main__":
    unittest.main()
