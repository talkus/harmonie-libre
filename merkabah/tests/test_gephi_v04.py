"""Negative controls for the Merkabah v0.4 Gephi export.

Execute: python -m unittest discover -s merkabah/tests -p 'test*.py' -v
"""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "export_gephi_v04.py"
SOURCE = ROOT / "schema" / "merkabah_candidate_v0.4.json"
spec = importlib.util.spec_from_file_location("merkabah_export_gephi_v04", MODULE)
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


class TestMerkabahGephiV04(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads(SOURCE.read_text(encoding="utf-8"))

    def test_graph_is_a_candidate_and_keeps_discrepancy(self):
        graph = exporter.build_graph(self.data)
        self.assertEqual(graph.number_of_nodes(), 61)
        self.assertEqual(graph.number_of_edges(), 76)
        self.assertEqual(graph.graph["epistemic_status"], "PROPOSED_NOT_VALIDATED")
        self.assertEqual(graph.nodes["face_discrepancy_ez10_14"]["epistemic_status"], "UNCERTAIN")
        self.assertTrue(all("betweenness_brandes_directed_projection" in node
                            for _, node in graph.nodes(data=True)))

    def test_gexf_roundtrip(self):
        import networkx as nx
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "candidate.gexf"
            exporter.export(self.data, out)
            loaded = nx.read_gexf(out)
            self.assertEqual(loaded.number_of_edges(), 76)
            self.assertEqual(loaded.nodes["face_discrepancy_ez10_14"]["epistemic_status"], "UNCERTAIN")

    def test_duplicate_node_rejected(self):
        bad = deepcopy(self.data)
        bad["nodes"][0]["id"] = bad["nodes"][1]["id"]
        with self.assertRaises(ValueError):
            exporter.build_graph(bad)

    def test_missing_wheel_rejected(self):
        bad = deepcopy(self.data)
        bad["nodes"] = [n for n in bad["nodes"] if n["id"] != "wheel_1"]
        with self.assertRaises(ValueError):
            exporter.build_graph(bad)

    def test_unknown_edge_endpoint_rejected(self):
        bad = deepcopy(self.data)
        bad["edges"][0]["to"] = "missing-node"
        with self.assertRaises(ValueError):
            exporter.build_graph(bad)

    def test_unknown_evidence_rejected(self):
        bad = deepcopy(self.data)
        bad["edges"][0]["source"] = "fabricated-source"
        with self.assertRaises(ValueError):
            exporter.build_graph(bad)

    def test_verse_inventory_mutation_rejected(self):
        bad = deepcopy(self.data)
        note = next(n for n in bad["nodes"] if n["id"] == "face_discrepancy_ez10_14")
        note["verse_comparison"]["Ezekiel_10"][0] = "ox"
        with self.assertRaises(ValueError):
            exporter.build_graph(bad)

    def test_status_promotion_rejected(self):
        bad = deepcopy(self.data)
        bad["status"] = "VALIDATED"
        with self.assertRaises(ValueError):
            exporter.build_graph(bad)


if __name__ == "__main__":
    unittest.main()
