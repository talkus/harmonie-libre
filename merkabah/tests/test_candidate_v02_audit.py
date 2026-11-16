"""Independent candidate-v0.2 structural checks. No claim of biblical fidelity.
Run: python -m unittest discover -s merkabah/tests -p 'test_candidate_v02_audit.py' -v
"""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
DATA = ROOT / "schema" / "merkabah_candidate_v0.2.json"

class CandidateV02Audit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(DATA.read_text(encoding="utf-8"))
        cls.nodes = {n["id"]: n for n in cls.data["nodes"]}
        cls.edges = cls.data["edges"]

    def related(self, src, relation):
        return [e["to"] for e in self.edges if e["from"] == src and e["type"] == relation]

    def test_unique_nodes_and_valid_endpoints(self):
        self.assertEqual(len(self.nodes), len(self.data["nodes"]))
        for e in self.edges:
            self.assertIn(e["from"], self.nodes)
            self.assertIn(e["to"], self.nodes)

    def test_four_distinct_beings_and_wheels(self):
        self.assertEqual(sum(n["type"] == "living_being" for n in self.nodes.values()), 4)
        self.assertEqual(sum(n["type"] == "wheel_within_wheel" for n in self.nodes.values()), 4)

    def test_per_being_components(self):
        forms = {"human", "lion", "ox", "eagle"}
        for i in range(1, 5):
            c = f"cherub_{i}"
            faces = self.related(c, "has_face")
            self.assertEqual(len(faces), 4, c)
            self.assertEqual({self.nodes[f]["form"] for f in faces}, forms, c)
            self.assertEqual(len(self.related(c, "has_wing")), 4, c)
            self.assertEqual(self.related(c, "beside"), [f"wheel_{i}"])
            self.assertEqual(self.related(f"wheel_{i}", "moves_with"), [c])
            self.assertTrue(self.nodes[f"wheel_{i}"].get("eyes_on_rim"))
            for part in ("legs", "feet", "hands"):
                self.assertEqual(self.related(c, f"has_{part}"), [f"{c}_{part}"])

    def test_scene_distinction_and_unresolved_faces(self):
        self.assertIn("Ezekiel_1", self.data["scenes"])
        self.assertIn("Ezekiel_10", self.data["scenes"])
        self.assertEqual(self.nodes["face_discrepancy_ez10_14"]["status"], "UNCERTAIN")
        self.assertEqual(len(self.related("cherubim_ez10", "identity_with")), 4)

    def test_source_identifiers_resolvable(self):
        """This intentionally detects the v0.2 provenance defect until repaired."""
        sources = {s["id"] for s in self.data["sources"]}
        for item in self.data["nodes"] + self.edges:
            self.assertIn(item["source"], sources, item.get("id", item.get("type")))

    def test_not_approved(self):
        self.assertEqual(self.data["status"], "PROPOSED_NOT_VALIDATED")

if __name__ == "__main__":
    unittest.main()
