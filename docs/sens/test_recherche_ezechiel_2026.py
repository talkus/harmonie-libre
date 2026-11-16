"""Evidence checks of recent 2024–26 Ezekiel findings; not a biblical certification."""
import json
import os
from pathlib import Path
import sys
import unittest

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from merkabah_qualitative_overlay import load_pinned
from model_update_recent_research import build_researched_model

class TestRecentEzekielResearch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        path=os.environ.get("MERKABAH_EXPERIMENTAL_GRAPH")
        if not path:
            raise RuntimeError("Supply exact pinned graph via Git show, never invent")
        cls.graph=load_pinned(path)
        cls.original_bytes=Path(path).read_bytes()
        cls.catalog=json.loads((HERE/"recherche_ezechiel_2026.json").read_text(encoding="utf-8"))
        cls.view=build_researched_model(cls.graph,cls.catalog)
        cls.findings={f["id"]:f for f in cls.catalog["findings"]}

    def test_preserved_cardinalities_and_scenes(self):
        self.assertEqual((len(self.view["nodes"]),self.view["edge_count_untouched"]),(102,115))
        self.assertEqual({n["scene"] for n in self.view["nodes"].values()},{"ez1","ez10"})
        self.assertEqual(Path(os.environ["MERKABAH_EXPERIMENTAL_GRAPH"]).read_bytes(),self.original_bytes)

    def test_scholarly_inferences_never_text_certainties(self):
        self.assertEqual(self.catalog["kind"],"LITERATURE_OVERLAY_NOT_CANON")
        self.assertTrue(self.catalog["rules"]["do_not_promote_scholarly_hypothesis_to_text"])
        for f in self.catalog["findings"]:
            self.assertNotEqual(f["assertion_mode"],"FACT_CERTIFIED")
            self.assertGreater(len(f["limits"]),0)
            self.assertGreater(len(f["source_ids"]),0)
            for key in f["source_ids"]:
                self.assertTrue(self.catalog["sources"][key]["url"].startswith("https://"))

    def test_2025_kebar_claim_remains_contested(self):
        kebar=self.view["nodes"]["ez1_kebar"]["research_annotations"]
        self.assertIn("KEBAR_DATE_2025",{x["finding_id"] for x in kebar})
        self.assertIn("KEBAR_LOCATION_2026",{x["finding_id"] for x in kebar})
        self.assertEqual(self.findings["KEBAR_DATE_2025"]["level"],"SCHOLARLY_HYPOTHESIS")
        self.assertIn("null",self.findings["KEBAR_LOCATION_2026"]["rendering_implication"])

    def test_eyes_are_variants_not_new_entities(self):
        for scene in ("ez1","ez10"):
            for i in range(1,5):
                n=self.view["nodes"][f"{scene}_wheel_{i}"]
                ids={x["finding_id"] for x in n["research_annotations"]}
                self.assertIn("EYES_EZ1_TRANSLATIONS" if scene=="ez1" else "EYES_EZ10_TRANSLATIONS",ids)
                self.assertEqual(n["type"],"wheel")
        self.assertEqual(len([x for x in self.graph["nodes"] if x["type"]=="wheel"]),8)
        self.assertTrue(all(x["wheel_inside_wheel"] for x in self.graph["nodes"] if x["type"]=="wheel"))
        self.assertEqual(self.findings["EYES_EZ1_TRANSLATIONS"]["rendering_profiles"],
                         ["AELF_SCINTILLEMENTS","NABRE_YEUX_JANTES"])

    def test_2024_coals_interpretation_does_not_replace_verse(self):
        coals=self.view["nodes"]["ez10_coals"]["research_annotations"]
        self.assertIn("COALS_SPRINKLE_2024",{x["finding_id"] for x in coals})
        self.assertNotIn("COALS_SPRINKLE_2024",self.view["discourse_interpretations"])

    def test_macro_hope_is_not_wheel_ontology(self):
        ids=set(self.view["discourse_interpretations"])
        self.assertTrue({"HOPE_RECOGNITION_2026","ORAL_MACROSTRUCTURE_2026","MESOPOTAMIAN_MENTAL_MAP_2025"} <= ids)
        for node in self.view["nodes"].values():
            self.assertNotIn("HOPE_RECOGNITION_2026",{a["finding_id"] for a in node["research_annotations"]})

    def test_dates_and_sources_not_anachronistic(self):
        for k,source in self.catalog["sources"].items():
            publication=source["published"]
            if publication[0:4].isdigit():
                self.assertLessEqual(int(publication[:4]),2026,k)
        self.assertEqual(self.view["research_finding_count"],len(self.findings))

if __name__=="__main__":
    unittest.main()
