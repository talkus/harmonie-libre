"""Test du candidat Merkabah v0.4 avec NetworkX, sans validation exégétique."""
import json
from pathlib import Path
import unittest
try:
    import networkx as nx
except ImportError:
    nx = None  # Exécution de secours explicite ; le CI dédié installe NetworkX.

GRAPH = Path(__file__).resolve().parents[1] / "schema" / "merkabah_candidate_v0.4.json"

class TestMerkabahV04(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(GRAPH.read_text(encoding="utf-8"))
        cls.nodes = {n["id"]: n for n in cls.data["nodes"]}
        cls.graph = nx.MultiDiGraph() if nx is not None else None
        if cls.graph is not None:
            for n in cls.data["nodes"]:
                cls.graph.add_node(n["id"], **n)
            for e in cls.data["edges"]:
                cls.graph.add_edge(e["from"], e["to"], key=e["type"], **{"source_ref":e["source"]})

    def has_edge(self, u, v, key):
        if self.graph is not None:
            return self.graph.has_edge(u, v, key=key)
        return any(e["from"]==u and e["to"]==v and e["type"]==key for e in self.data["edges"])

    def test_cardinality_and_identity(self):
        self.assertEqual(len(self.data["nodes"]), 61)
        self.assertEqual(len(self.nodes), 61, "Node identifiers must be unique")
        self.assertEqual(len(self.data["edges"]), 76)
        if self.graph is not None:
            self.assertEqual(self.graph.number_of_nodes(), 61)
            self.assertEqual(self.graph.number_of_edges(), 76)

    def test_endpoint_and_source_integrity(self):
        sources = {s["id"] for s in self.data["sources"]}
        self.assertEqual(len(sources), len(self.data["sources"]))
        for e in self.data["edges"]:
            self.assertIn(e["from"], self.nodes)
            self.assertIn(e["to"], self.nodes)
        for item in self.data["nodes"] + self.data["edges"]:
            self.assertIn(item["source"], sources)

    def test_being_groups_and_adjacency(self):
        for i in range(1, 5):
            c, w = f"cherub_{i}", f"wheel_{i}"
            self.assertTrue(self.has_edge(c, w, key="beside"))
            self.assertTrue(self.has_edge(w, c, key="moves_with"))
            for relation, count in [("has_face",4), ("has_wing",4), ("has_hands",1), ("has_legs",1), ("has_feet",1)]:
                actual = [e for e in self.data["edges"] if e["from"]==c and e["type"]==relation]
                self.assertEqual(len(actual), count, f"{c}: {relation}")
            self.assertTrue(self.nodes[w]["eyes_on_rim"])

    def test_verse_10_14_corrected_but_unresolved(self):
        n = self.nodes["face_discrepancy_ez10_14"]
        self.assertEqual(n["status"], "UNCERTAIN")
        self.assertEqual(n["verse_comparison"]["Ezekiel_1"],["human","lion","ox","eagle"])
        self.assertEqual(n["verse_comparison"]["Ezekiel_10"],["cherub","human","lion","eagle"])
        self.assertIn("bœuf",n["note"])
        for i in range(1, 5):
            self.assertTrue(self.has_edge("face_discrepancy_ez10_14",f"cherub_{i}_face_ox",key="questions"))
            self.assertFalse(self.has_edge("face_discrepancy_ez10_14",f"cherub_{i}_face_human",key="questions"))

    def test_status_and_scenes(self):
        self.assertEqual(self.data["status"],"PROPOSED_NOT_VALIDATED")
        self.assertEqual(set(self.data["scenes"]), {"Ezekiel_1","Ezekiel_10"})

if __name__ == "__main__":
    unittest.main()
