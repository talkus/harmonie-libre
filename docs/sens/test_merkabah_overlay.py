"""Tests of read-only per-node evidence/movement overlay against pinned remote artifact."""
import os
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parent))
from merkabah_qualitative_overlay import load_pinned, construct_overlay

class TestPinnedGraphOverlay(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        target = os.environ.get("MERKABAH_EXPERIMENTAL_GRAPH")
        if not target:
            raise RuntimeError("Set MERKABAH_EXPERIMENTAL_GRAPH to git-show extracted pinned graph; do not guess")
        cls.original = load_pinned(Path(target))
        cls.output = construct_overlay(cls.original)

    def test_exact_coverage_and_no_created_relations(self):
        self.assertEqual((self.output["node_count"], self.output["edge_count_untouched"]), (102,115))
        self.assertEqual(set(self.output["nodes"]), {n["id"] for n in self.original["nodes"]})

    def test_four_wheels_per_scene_are_single_entities(self):
        for scene in ("ez1", "ez10"):
            pairs = [(n_id, n) for n_id,n in self.output["nodes"].items()
                     if n["scene"] == scene and n["type"] == "wheel"]
            self.assertEqual(len(pairs), 4)
            for _, wheel in pairs:
                self.assertTrue(any("attribute, not another wheel" in s for s in wheel["limitations"]))

    def test_only_known_movements_and_scope(self):
        for id,n in self.output["nodes"].items():
            self.assertTrue(n["references"], id)
            self.assertNotIn("CERTIFIED", n["evidence_strength"])
            if n["type"] == "wheel":
                self.assertEqual(n["motion"]["model_contract"], "PAIRED_TRANSLATION_RISE_STOP")
                self.assertEqual(n["motion"]["ruach_zero"], "PAUSE_SIMULATION")
            elif n["type"] == "face":
                self.assertEqual(n["motion"]["independent_motion"], "NOT_MODELED")
            elif n["type"] == "throne":
                self.assertEqual(n["motion"]["model_contract"], "NOT_SPECIFIED")

    def test_scenes_and_translation_variant_kept(self):
        n = self.output["nodes"]
        self.assertTrue(any("NABRE eyes / AELF scintillements" in z
                            for z in n["ez1_wheel_1"]["limitations"]))
        self.assertEqual(n["ez10_wheel_1"]["scene"], "ez10")
        self.assertEqual(n["ez1_wheel_1"]["scene"], "ez1")
        self.assertEqual(self.output["status"], "PROPOSED_NOT_VALIDATED")

if __name__ == "__main__":
    unittest.main()
