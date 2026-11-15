"""Tests adversariaux : les échecs doivent être détectés, pas maquillés."""
import copy
import json
import sys
import unittest
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from audit_candidate import audit

class TestMerkabahAdversarial(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = json.loads((ROOT/"schema"/"merkabah_candidate_v0.1.json").read_text(encoding="utf-8"))
    def codes(self, graph):
        return {f["code"]: f["level"] for f in audit(graph)}
    def test_candidate_has_gaps_not_blockers(self):
        codes = self.codes(self.g)
        self.assertNotIn("BLOCKER", codes.values())
        self.assertEqual(codes["VERSE_PROVENANCE"], "GAP")
        self.assertEqual(codes["EZ10_VARIANTS"], "GAP")
    def test_orphan_link(self):
        g=copy.deepcopy(self.g)
        g["edges"].append({"from":"ghost","to":"ruach","type":"directed_by","source":"ez1"})
        self.assertEqual(self.codes(g)["DANGLING_EDGE"],"BLOCKER")
    def test_missing_face(self):
        g=copy.deepcopy(self.g)
        g["edges"]=[e for e in g["edges"] if not (e["from"]=="cherub_1" and e["type"]=="has_face" and e["to"].endswith("eagle"))]
        self.assertEqual(self.codes(g)["FACES"],"BLOCKER")
    def test_extra_central_wheel(self):
        g=copy.deepcopy(self.g)
        g["nodes"].append({"id":"wheel_central","type":"wheel_within_wheel","source":"ez1","eyes_on_rim":True})
        self.assertEqual(self.codes(g)["CARDINALITY"],"BLOCKER")
    def test_wrong_wheel_pair(self):
        g=copy.deepcopy(self.g)
        for e in g["edges"]:
            if e["from"]=="cherub_1" and e["type"]=="beside":
                e["to"]="wheel_2"
        self.assertEqual(self.codes(g)["WHEEL_PAIR"],"BLOCKER")
    def test_duplicate_relation(self):
        g=copy.deepcopy(self.g)
        g["edges"].append(copy.deepcopy(g["edges"][0]))
        self.assertEqual(self.codes(g)["DUPLICATE_EDGE"],"BLOCKER")
    def test_false_canonical_promotion(self):
        g=copy.deepcopy(self.g)
        g["status"]="CANON_VERIFIED"
        self.assertEqual(self.codes(g)["UNREVIEWED_PROMOTION"],"BLOCKER")
    def test_unattested_source(self):
        g=copy.deepcopy(self.g)
        g["nodes"][0]["source"]="phantom"
        self.assertEqual(self.codes(g)["UNKNOWN_SOURCE"],"BLOCKER")
if __name__ == "__main__":
    unittest.main()
