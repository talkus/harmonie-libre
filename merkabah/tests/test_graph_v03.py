"""Contrôles Merkabah v0.3 candidat. Python standard library; aucun rendu ou exégèse certifié."""
import json
import pathlib
import unittest

PATH = pathlib.Path(__file__).resolve().parents[1] / "schema" / "merkabah_candidate_v0.3.json"

class TestMerkabahV03(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(PATH.read_text(encoding="utf-8"))
        cls.nodes = {n["id"]: n for n in cls.data["nodes"]}
        cls.edges = cls.data["edges"]

    def rel(self, node, typ):
        return [e["to"] for e in self.edges if e["from"] == node and e["type"] == typ]

    def test_unique_nodes(self):
        self.assertEqual(len(self.nodes), len(self.data["nodes"]))

    def test_endpoints(self):
        for e in self.edges:
            self.assertIn(e["from"], self.nodes)
            self.assertIn(e["to"], self.nodes)

    def test_provenance_complete(self):
        refs = {s["id"] for s in self.data["sources"]}
        for item in self.data["nodes"] + self.edges:
            self.assertIn(item["source"], refs)

    def test_four_beings_and_wheels(self):
        for kind in ("living_being", "wheel_within_wheel"):
            self.assertEqual(sum(n["type"] == kind for n in self.nodes.values()), 4)

    def test_each_being(self):
        forms = {"human", "lion", "ox", "eagle"}
        for i in range(1, 5):
            c = f"cherub_{i}"
            faces = self.rel(c, "has_face")
            self.assertEqual(len(faces), 4)
            self.assertEqual({self.nodes[x]["form"] for x in faces}, forms)
            self.assertEqual(len(self.rel(c, "has_wing")), 4)
            for kind in ("has_legs", "has_feet", "has_hands"):
                self.assertEqual(len(self.rel(c, kind)), 1)
            self.assertEqual(self.rel(c, "beside"), [f"wheel_{i}"])
            self.assertEqual(self.rel(f"wheel_{i}", "moves_with"), [c])
            self.assertTrue(self.nodes[f"wheel_{i}"]["eyes_on_rim"])

    def test_scenes_and_uncertainty(self):
        self.assertEqual(set(self.data["scenes"]), {"Ezekiel_1", "Ezekiel_10"})
        self.assertEqual(self.nodes["face_discrepancy_ez10_14"]["status"], "UNCERTAIN")
        self.assertEqual(len(self.rel("cherubim_ez10", "identity_with")), 4)

    def test_not_validated(self):
        self.assertEqual(self.data["status"], "PROPOSED_NOT_VALIDATED")

if __name__ == "__main__":
    unittest.main()
