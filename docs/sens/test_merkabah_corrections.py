"""Check epistemic reconciliation, NOT biblical accuracy or user's local run."""
import json
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parent / "correspondances_sens_v01.json"

class TestMerkabahCorrections(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.v = json.loads(PATH.read_text(encoding="utf-8"))["merkabah_reconciliation"]

    def test_no_eight_wheels(self):
        self.assertIn("Four literal wheels", self.v["identity_of_model"])
        self.assertIn("attribute", self.v["identity_of_model"].replace("characteristic","attribute"))

    def test_provenance_not_flattened(self):
        src=self.v["sources"]
        self.assertEqual((src["github_v03"]["nodes"],src["github_v03"]["relations"]),(61,76))
        self.assertEqual((src["user_v03"]["nodes"],src["user_v03"]["relations"]),(78,152))
        self.assertEqual(src["user_v03"]["verification"],"NOT_INDEPENDENTLY_REPRODUCED")
        self.assertEqual(src["drive_v02"]["verification"],"DOCUMENTARY_CLAIM_NOT_FILE_RECOUNTED")
        self.assertEqual(sum(src["user_v03"]["split"].values()),152)

    def test_experimental_branch_not_conflated(self):
        sources=self.v["sources"]
        exp=sources["github_v03_experimental"]
        self.assertEqual((exp["nodes"],exp["relations"]),(102,115))
        self.assertEqual((exp["by_scene"]["ez1"]["nodes"],exp["by_scene"]["ez10"]["nodes"]),(52,50))
        self.assertEqual(exp["by_scene"]["ez1"]["wheels"],4)
        self.assertEqual(exp["by_scene"]["ez10"]["wheels"],4)
        self.assertEqual(exp["wheel_inside_wheel_representation"],"BOOLEAN_ATTRIBUTE_OF_EACH_SCENE_WHEEL")
        self.assertEqual(sum(exp["edge_status_counts"].values()),115)
        self.assertNotEqual(exp["blob_sha"],sources["github_v03"].get("blob_sha"))

    def test_two_biblical_scenes_and_eyes(self):
        b=self.v["bible"]
        self.assertIn("bœuf",b["chapter1"]["faces"])
        self.assertIn("chérubin",b["chapter10"]["faces"])
        self.assertTrue(b["chapter10"]["eyes_bodies_hands_wings_and_wheels"])
        self.assertTrue(b["chapter1"]["body_and_wing_eyes_not_attested_in_chapter1"])
        self.assertIn("Ez 10:13",b["chapter10"]["galgal_wheelwork"])

    def test_record_blender_and_logic_only_godot(self):
        e=self.v["executed_observations"]
        self.assertEqual(e["github_blender"]["status"],"SUCCESS")
        self.assertEqual(e["godot"]["status"],"EXECUTED_HEADLESS_LOGIC_ONLY")
        self.assertIn("logic", e["godot"]["scope"].lower())
        self.assertEqual(len(self.v["new_scope_only"]),2)

if __name__=="__main__":
    unittest.main()
