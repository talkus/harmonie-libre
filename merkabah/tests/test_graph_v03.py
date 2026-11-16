"""Regression and counterexamples for the two-scene candidate."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

PROJECT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT))
from validate_graph_v03 import validate, to_networkx  # noqa: E402

GRAPH = PROJECT / "schema" / "merkabah_candidate_v0.3.json"
SCHEMA = PROJECT / "schema" / "merkabah_v03.schema.json"


class GraphTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = json.loads(GRAPH.read_text(encoding="utf-8"))

    def candidate(self):
        return copy.deepcopy(self.original)

    def rejected(self, graph, expected):
        errors = validate(graph)
        self.assertTrue(any(expected in e for e in errors), f"expected {expected!r}, got {errors!r}")

    def test_candidate_is_structurally_consistent(self):
        self.assertEqual(validate(self.original), [])

    def test_two_face_descriptions_remain_distinct(self):
        forms = lambda scene: {n.get("form") for n in self.original["nodes"] if n["scene"] == scene and n["type"] == "face"}
        self.assertEqual(forms("ez1"), {"human", "lion", "ox", "eagle"})
        self.assertEqual(forms("ez10"), {"cherub", "human", "lion", "eagle"})

    def test_schema_on_candidate(self):
        try:
            import jsonschema
        except ImportError:
            self.skipTest("jsonschema not installed")
        schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
        jsonschema.Draft202012Validator.check_schema(schema)
        jsonschema.validate(self.original, schema, format_checker=jsonschema.FormatChecker())

    def test_missing_face_is_rejected(self):
        g = self.candidate()
        g["edges"] = [e for e in g["edges"] if not (e["from"] == "ez1_being_1" and e["to"] == "ez1_being_1_face_ox")]
        self.rejected(g, "four distinct scene-appropriate faces required")

    def test_duplicate_face_is_rejected(self):
        g = self.candidate()
        e = next(e for e in g["edges"] if e["from"] == "ez1_being_1" and e["type"] == "has_face")
        g["edges"].append(copy.deepcopy(e))
        self.rejected(g, "duplicate relation")

    def test_missing_wing_is_rejected(self):
        g = self.candidate()
        g["nodes"] = [n for n in g["nodes"] if n["id"] != "ez10_being_4_wing_1"]
        self.rejected(g, "missing endpoint")

    def test_shared_wheel_is_rejected(self):
        g = self.candidate()
        e = next(e for e in g["edges"] if e["from"] == "ez1_being_2" and e["type"] == "beside")
        e["to"] = "ez1_wheel_1"
        self.rejected(g, "wheel must have exactly one owner")

    def test_unsynchronised_wheel_relation_is_rejected(self):
        g = self.candidate()
        g["edges"] = [e for e in g["edges"] if not (e["from"] == "ez10_wheel_3" and e["type"] == "moves_with")]
        self.rejected(g, "wheel movement association missing")

    def test_cross_scene_relation_is_rejected(self):
        g = self.candidate()
        e = next(e for e in g["edges"] if e["from"] == "ez1_being_1" and e["type"] == "beside")
        e["to"] = "ez10_wheel_1"
        self.rejected(g, "cross-scene relation")

    def test_wrong_scene_reference_is_rejected(self):
        g = self.candidate()
        g["nodes"][0]["references"][0]["verse"] = "10:1"
        self.rejected(g, "reference belongs to another scene")

    def test_missing_source_is_rejected(self):
        g = self.candidate()
        g["nodes"][0]["references"][0]["source"] = "made_up"
        self.rejected(g, "invalid reference")

    def test_cannot_promote_candidate(self):
        g = self.candidate()
        g["status"] = "VALIDATED"
        self.rejected(g, "candidate status must remain")

    def test_networkx_preserves_all_relations_when_available(self):
        if importlib.util.find_spec("networkx") is None:
            self.skipTest("networkx not installed; adapter not verified")
        g = to_networkx(self.original)
        self.assertTrue(g.is_multigraph())
        self.assertEqual(g.number_of_nodes(), len(self.original["nodes"]))
        self.assertEqual(g.number_of_edges(), len(self.original["edges"]))
        self.assertEqual(g.nodes["ez1_being_1_face_ox"]["references"][0]["verse"], "1:10")


if __name__ == "__main__":
    unittest.main()
