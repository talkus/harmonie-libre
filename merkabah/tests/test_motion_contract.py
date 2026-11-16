"""Tests du contrat de mouvement ; echec attendu sur mutations volontairement fautives."""
import copy
import json
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "motion"))
from contract import example_track, graph_pairs, validate_track

DATA = ROOT / "schema" / "merkabah_candidate_v0.1.json"

class TestMotion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(DATA.read_text(encoding="utf-8"))

    def setUp(self):
        self.track = example_track(self.graph)

    def test_pairs(self):
        self.assertEqual(len(graph_pairs(self.graph)), 4)

    def test_baseline(self):
        self.assertEqual(validate_track(self.graph, self.track), [])

    def test_unrotated_turn(self):
        self.track["frames"][2]["poses"]["cherub_1"]["yaw"] = 0.5
        self.assertIn("TURNED:2:cherub_1", validate_track(self.graph, self.track))

    def test_wheel_lag(self):
        self.track["frames"][1]["poses"]["wheel_1"]["p"][0] -= 0.5
        self.assertTrue(any("UNSYNCED:1:wheel_1" == e for e in validate_track(self.graph, self.track)))

    def test_unwanted_fifth_wheel(self):
        self.track["frames"][1]["poses"]["wheel_center"] = {"p": [0, 0, 0], "yaw": 0}
        self.assertIn("OBJECT_SET:1", validate_track(self.graph, self.track))

    def test_diagonal_without_command(self):
        for pose in self.track["frames"][1]["poses"].values():
            pose["p"][1] += 1.0
        self.assertIn("COMMAND_MISMATCH:1:east", validate_track(self.graph, self.track))

    def test_stop_must_stop_all(self):
        for pose in self.track["frames"][4]["poses"].values():
            pose["p"][2] += 1.0
        self.assertIn("COMMAND_MISMATCH:4:stop", validate_track(self.graph, self.track))

    def test_ez10_not_validated_by_ez1(self):
        self.track["scene"] = "Ezekiel_10"
        self.assertIn("SCENE_NOT_MODELED:Ez10_requires_separate_provenance", validate_track(self.graph, self.track))

    def test_missing_ruach_relation(self):
        graph = copy.deepcopy(self.graph)
        graph["edges"] = [e for e in graph["edges"] if not (e.get("from") == "cherub_1" and e["type"] == "directed_by")]
        self.assertTrue(validate_track(graph, self.track)[0].startswith("INVALID_GRAPH:"))

    def test_reversed_clock(self):
        self.track["frames"][3]["t"] = 0
        self.assertIn("TIME_NOT_INCREASING:3", validate_track(self.graph, self.track))

if __name__ == "__main__":
    unittest.main()