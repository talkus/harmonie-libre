"""Tests du candidat Merkabah v0.2. Aucune validation exégétique ou 3D implicite."""
import json
import pathlib
import unittest
from collections import Counter

try:
    import networkx as nx
except ImportError:
    nx = None

ROOT = pathlib.Path(__file__).resolve().parents[1]
FILE = ROOT / "schema" / "merkabah_candidate_v0.2.json"

def read_graph():
    return json.loads(FILE.read_text(encoding="utf-8"))

def defects(graph):
    """Diagnostics bloquants vérifiables, indépendants du moteur 3D."""
    errors = []
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    ids = [n.get("id") for n in nodes]
    lookup = {n.get("id"): n for n in nodes}
    if len(ids) != len(set(ids)):
        errors.append("duplicate_node_id")
    for e in edges:
        if e.get("from") not in lookup or e.get("to") not in lookup:
            errors.append("dangling_edge")
        if not (e.get("source") and e.get("scene") and e.get("verse_ref")):
            errors.append("edge_missing_provenance")
    if len({(e.get("from"), e.get("to"), e.get("type")) for e in edges}) != len(edges):
        errors.append("duplicate_typed_edge")
    if any(not all(n.get(k) for k in ("id", "type", "source", "scene", "verse_ref", "status")) for n in nodes):
        errors.append("node_missing_provenance")
    if Counter(n.get("type") for n in nodes)["living_being"] != 4:
        errors.append("incorrect_being_count")
    if Counter(n.get("type") for n in nodes)["wheel_within_wheel"] != 4:
        errors.append("incorrect_wheel_count")
    for i in range(1, 5):
        ch = f"cherub_{i}"
        wh = f"wheel_{i}"
        related = lambda kind: [e["to"] for e in edges if e.get("from") == ch and e.get("type") == kind]
        wheel_to = [e["to"] for e in edges if e.get("from") == wh and e.get("type") == "moves_with"]
        if related("beside") != [wh] or wheel_to != [ch]:
            errors.append("wheel_pairing")
        faces = related("has_face")
        if len(faces) != 4 or {lookup.get(f, {}).get("form") for f in faces} != {"human", "lion", "ox", "eagle"}:
            errors.append("face_cardinality")
        if len(related("has_wing")) != 4:
            errors.append("wing_cardinality")
    observations = graph.get("observations", [])
    if not any(o.get("scene") == "Ezekiel_1" for o in observations) or not any(o.get("scene") == "Ezekiel_10" for o in observations):
        errors.append("scene_observation_missing")
    if not any(c.get("id") == "FACE_OX_VS_CHERUB" and c.get("status") == "UNRESOLVED" for c in graph.get("unresolved", [])):
        errors.append("face_conflict_silenced")
    if any(not o.get("verse_ref") or not o.get("status") for o in observations):
        errors.append("observation_provenance_missing")
    if graph.get("status") != "PROPOSED_NOT_VALIDATED":
        errors.append("premature_validation")
    return errors

class TestMerkabahV02(unittest.TestCase):
    def setUp(self):
        self.data = read_graph()

    def test_candidate_structural_contract(self):
        self.assertEqual([], defects(self.data))

    def test_candidate_not_legacy_rewrite(self):
        original = json.loads((ROOT / "schema" / "merkabah_candidate_v0.1.json").read_text(encoding="utf-8"))
        self.assertEqual([n["id"] for n in original["nodes"]], [n["id"] for n in self.data["nodes"]])
        self.assertEqual([(e["from"], e["to"], e["type"]) for e in original["edges"]],
                         [(e["from"], e["to"], e["type"]) for e in self.data["edges"]])
        self.assertEqual(self.data["lineage"]["mode"], "DERIVED_NEW_CANDIDATE_NO_HISTORY_REWRITE")

    def test_chapter_ten_is_observations_not_anatomical_overwrite(self):
        ten = [o for o in self.data["observations"] if o["scene"] == "Ezekiel_10"]
        self.assertGreaterEqual(len(ten), 6)
        self.assertTrue(all(o["status"] == "TEXTUAL" for o in ten))
        self.assertEqual({n["scene"] for n in self.data["nodes"]}, {"Ezekiel_1"})

    def test_mutant_duplicate_face_link_rejected(self):
        bad = read_graph()
        bad["edges"].append(dict(bad["edges"][4]))
        self.assertIn("duplicate_typed_edge", defects(bad))

    def test_mutant_missing_wheel_rejected(self):
        bad = read_graph()
        bad["edges"] = [e for e in bad["edges"] if not (e["from"] == "cherub_1" and e["type"] == "beside")]
        self.assertIn("wheel_pairing", defects(bad))

    def test_mutant_silent_face_harmonization_rejected(self):
        bad = read_graph()
        bad["unresolved"] = []
        self.assertIn("face_conflict_silenced", defects(bad))

    @unittest.skipIf(nx is None, "NetworkX non installé — contrôle de graphe non exécuté")
    def test_networkx_multidigraph_integrity(self):
        g = nx.MultiDiGraph()
        for n in self.data["nodes"]:
            g.add_node(n["id"], **{k:v for k,v in n.items() if k != "id"})
        for e in self.data["edges"]:
            g.add_edge(e["from"], e["to"], key=e["type"], **{k:v for k,v in e.items() if k not in ("from","to","type")})
        self.assertEqual(g.number_of_nodes(), 45)
        self.assertEqual(g.number_of_edges(), 50)
        self.assertEqual(len(list(nx.isolates(g))), 1)  # Kebar: context, non-causal link

if __name__ == "__main__":
    unittest.main()
