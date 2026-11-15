"""Contrôles structurels du graphe candidat Merkabah. Exécution: python -m unittest discover -s merkabah/tests -v"""
import json
import pathlib
import unittest

DATA = pathlib.Path(__file__).resolve().parents[1] / "schema" / "merkabah_candidate_v0.1.json"

class TestMerkabah(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.graph = json.loads(DATA.read_text(encoding="utf-8"))
        cls.nodes = {node["id"]: node for node in cls.graph["nodes"]}
        cls.edges = cls.graph["edges"]

    def related(self, source, kind):
        return [e["to"] for e in self.edges if e["from"] == source and e["type"] == kind]

    def test_unique_identifiers(self):
        self.assertEqual(len(self.nodes), len(self.graph["nodes"]))

    def test_edge_endpoints_exist(self):
        for edge in self.edges:
            self.assertIn(edge["from"], self.nodes)
            self.assertIn(edge["to"], self.nodes)

    def test_four_beings_and_wheels(self):
        self.assertEqual(sum(n["type"] == "living_being" for n in self.nodes.values()), 4)
        self.assertEqual(sum(n["type"] == "wheel_within_wheel" for n in self.nodes.values()), 4)

    def test_four_faces_each(self):
        expected = {"human", "lion", "ox", "eagle"}
        for i in range(1, 5):
            faces = self.related(f"cherub_{i}", "has_face")
            self.assertEqual(len(faces), 4)
            self.assertEqual({self.nodes[f]["form"] for f in faces}, expected)

    def test_four_wings_each(self):
        for i in range(1, 5):
            self.assertEqual(len(self.related(f"cherub_{i}", "has_wing")), 4)

    def test_each_wheel_beside_one_being(self):
        for i in range(1, 5):
            self.assertEqual(self.related(f"cherub_{i}", "beside"), [f"wheel_{i}"])
            self.assertEqual(self.related(f"wheel_{i}", "moves_with"), [f"cherub_{i}"])

    def test_wheels_have_eyes(self):
        for i in range(1, 5):
            self.assertTrue(self.nodes[f"wheel_{i}"]["eyes_on_rim"])

    def test_provenance(self):
        sources = {s["id"] for s in self.graph["sources"]}
        for node in self.nodes.values():
            self.assertIn(node["source"], sources)
        for edge in self.edges:
            self.assertIn(edge["source"], sources)

    def test_status_not_approved(self):
        self.assertEqual(self.graph["status"], "PROPOSED_NOT_VALIDATED")

if __name__ == "__main__":
    unittest.main()
