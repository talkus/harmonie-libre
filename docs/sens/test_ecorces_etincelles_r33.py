"""Tests of exact E001..E288 archival content and symbolic non-fusion."""
import copy
import os
from pathlib import Path
import sys
import unittest
from collections import Counter

sys.path.insert(0,str(Path(__file__).resolve().parent))
from merkabah_qualitative_overlay import load_pinned
from model_integrer_ecorces_etincelles import load_matrix, build_full_model

class TestEcorcesEtincelles(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        source=os.environ.get("MERKABAH_EXPERIMENTAL_GRAPH")
        if not source: raise RuntimeError("Missing pinned graph path")
        cls.graph=load_pinned(source)
        cls.original=copy.deepcopy(cls.graph)
        cls.matrix=load_matrix()
        cls.model=build_full_model(cls.graph,cls.matrix)
        cls.symbolic=cls.model["symbolic_layer"]

    def test_72_doors_288_complete_no_duplicates(self):
        entries=self.matrix["entries"]
        doors=self.matrix["doors"]
        self.assertEqual(len(doors),72)
        self.assertEqual(len(entries),288)
        self.assertEqual([e["id"] for e in entries],[f"E{i:03d}" for i in range(1,289)])
        self.assertEqual([g["id"] for g in doors],[f"N{i:02d}" for i in range(1,73)])
        self.assertEqual(Counter(e["phase"] for e in entries),{f"D{d}":72 for d in range(1,5)})

    def test_every_gate_contains_exactly_four_distinct_entries(self):
        by_gate=Counter(x["gate_id"] for x in self.matrix["entries"])
        self.assertEqual(len(by_gate),72)
        self.assertTrue(all(x==4 for x in by_gate.values()))
        for k in range(1,73):
            a=self.matrix["entries"][4*(k-1):4*k]
            self.assertEqual([x["phase"] for x in a],["D1","D2","D3","D4"])

    def test_provenance_and_exact_sample_not_generative(self):
        self.assertEqual(self.matrix["entries"][1]["id"],"E002")
        self.assertIn("Invisibilité d'emprise",self.matrix["entries"][1]["text"])
        self.assertIn("Punition circulaire",self.matrix["entries"][285]["text"])
        self.assertIn("Clôture ouverte",self.matrix["entries"][-1]["text"])
        self.assertTrue(all(e["provenance_status"]=="RECONSTRUCTED_FROM_ARCHIVED_MATRIX" for e in self.matrix["entries"]))

    def test_biblical_nodes_and_edges_unchanged(self):
        self.assertEqual(self.graph,self.original)
        self.assertEqual(self.model["original_graph"]["nodes"],self.original["nodes"])
        self.assertEqual(self.model["original_graph"]["edges"],self.original["edges"])
        self.assertEqual(len(self.model["nodes"]),102)
        self.assertEqual(len(self.model["original_graph"]["edges"]),115)

    def test_symbolic_bridge_not_literal_eye_or_wheel(self):
        b=self.symbolic["bridge"]
        self.assertFalse(b["literal_identity"])
        self.assertFalse(b["wheel_1_equals_D1"])
        self.assertFalse(b["each_wheel_is_a_symbolic_individual_spark"])
        self.assertEqual(b["type"],"SYMBOLIC_VIEW_OF_SCINTILLATIONS_NOT_GRAPH_EDGE")
        self.assertEqual(len(b["linked_wheel_groups"]["ez1"]),4)
        self.assertEqual(len(b["linked_wheel_groups"]["ez10"]),4)
        self.assertEqual(self.symbolic["status"],"INTERPRETATIVE_ANALOGY_NOT_EZEKIEL_TEXT")

    def test_dimensions_with_four_virtues_are_archive_layers(self):
        phases=self.symbolic["phases"]
        self.assertEqual([(p,phases[p]["capteur"]) for p in ("D1","D2","D3","D4")],
                         [("D1","Humilité"),("D2","Pardon"),("D3","Reconnaissance"),("D4","Espérance")])
        self.assertTrue(all(len(phases[p]["entry_ids"])==72 for p in phases))

if __name__=="__main__":
    unittest.main()
