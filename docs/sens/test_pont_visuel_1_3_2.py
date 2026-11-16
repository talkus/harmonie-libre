"""Static safeguards for user-supplied 1-3-2 symbolic figure; does not validate its SVG rendering."""
import json
from pathlib import Path
import unittest

DATA=Path(__file__).with_name("pont_visuel_1_3_2_candidat.json")

class TestSixFormesSymbolique(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=json.loads(DATA.read_text(encoding="utf-8"))

    def test_counts_and_meanings(self):
        self.assertEqual(cls.d["status"],"PROPOSED_NOT_VALIDATED")
        self.assertEqual([t["count"] for t in cls.d["tiers"]],[1,3,2])
        self.assertEqual(len(cls.d["boxes"]),6)
        self.assertEqual(len({b["id"] for b in cls.d["boxes"]}),6)
        self.assertEqual([b["label"] for b in cls.d["boxes"] if b["level"]==1],
                         ["Je compte","Tu comptes","Nos choix comptent"])

    def test_exact_separation_of_sources(self):
        boundaries=cls.d["boundaries"]
        self.assertEqual(boundaries["biblical_vision_and_interpretive_virtues"],"NOT_IDENTICAL")
        self.assertEqual(boundaries["original_merka_python_core"]["status"],"CANON_NOT_VERIFIED")
        self.assertEqual(boundaries["biblical_wheels_per_scene"],4)
        self.assertIn("NOT_BIBLICAL",boundaries["k_calibration"]["status"])
        self.assertEqual(boundaries["spark_count"]["sparks"],72*4)
        self.assertEqual(boundaries["spark_cycle"][1],"D2_ECORCE")
        self.assertEqual(boundaries["spark_cycle"][2],"D3_ACTE_RECONNAISSANCE")

    def test_line_graph_math_and_unknown_report(self):
        g=cls.d["boundaries"]["topology"]
        self.assertEqual(g["K22_edges"],22*21//2)
        self.assertEqual(g["L_K22_vertices"],231)
        self.assertEqual(g["L_K22_edges"],231*40//2)
        self.assertEqual(g["L_K22_edges"],4620)
        self.assertNotEqual(g["corpus_declared_export_edges"],g["L_K22_edges"])
        self.assertEqual(g["export_subgraph_identity"],"DERIVED_GRAPH_ON_72_PORTES_WITH_SHARED_LETTER_PIVOTS_NOT_THE_FULL_LINE_GRAPH_L_K22")
        self.assertEqual(g["export_node_count_declared"],72)
        self.assertEqual(round(100*g["corpus_declared_export_edges"]/(72*71//2),2),g["export_density_declared_percent"])
        self.assertEqual(g["projected_inter_spark_couplings_declared"],1225*16)
        self.assertEqual(g["export_edge_evidence_status"],"DECLARED_IN_ARCHIVE_NOT_RECOUNTED_FROM_GEXF")
        self.assertEqual(g["corpus_reported_no_isolates_scope"],"72_PORTES_NOT_288_SPARKS")

    def test_arrows_do_not_make_new_biblical_relations(self):
        ids={b["id"] for b in cls.d["boxes"]}
        self.assertEqual(len(cls.d["diagram_directed_links"]),8)
        self.assertTrue(all(a in ids and b in ids for a,b in cls.d["diagram_directed_links"]))
        self.assertEqual(cls.d["kind"],"SYMBOLIC_INTERPRETATION_NOT_BIBLICAL_GRAPH")

if __name__=="__main__":
    unittest.main()
