"""Distinct missing knowledge must retain its source through aggregation."""
import copy
import json
from pathlib import Path
import tempfile
import unittest

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind, CausalOrigin


class SituatedUnknownTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.claims = [self.brain.record_claim(text, "system_hypothesis", "fixture:unknowns")["claim_id"]
                       for text in ("Premier objet", "Deuxième objet")]
        path = Path(__file__).resolve().parents[1] / "examples" / "work-plan-gabriel.json"
        self.spec = json.loads(path.read_text(encoding="utf-8"))
        first = self.spec["units"][0]
        first["id"] = "micro-a"
        first["work"]["claim_id"] = self.claims[0]
        first["review"]["unknown_refs"] = []
        second = copy.deepcopy(first)
        second["id"] = "micro-b"
        second["work"]["claim_id"] = self.claims[1]
        meta = self.spec["units"][-1]
        meta["work"]["claim_id"] = self.claims[0]
        meta["work"]["depends_on"] = ["micro-a", "micro-b"]
        meta["scope"]["reviews"] = ["micro-a", "micro-b"]
        self.spec["units"] = [first, second, meta]
        self.pid = self.spec["plan_id"]
        self.brain.record_work_plan(self.spec, provenance="fixture:unknowns")
        self.brain.work_run_next(self.pid)
        self.brain.work_run_next(self.pid)

    def details(self, brain=None):
        view = (brain or self.brain).work_view(self.pid)
        return view["units"][-1]["review"]["unknown_details"]

    def test_same_reason_on_two_claims_is_not_one_unknown(self):
        details = [d for d in self.details() if d["reason"] == "no_explicit_applicable_support"]
        self.assertEqual({d["claim_id"] for d in details}, set(self.claims))
        self.assertEqual({d["origin_unit_id"] for d in details}, {"micro-a", "micro-b"})
        self.assertEqual(len({d["unknown_id"] for d in details}), 2)
        self.assertTrue(all(d["scope_ref"] == "local" and d["trace_refs"] for d in details))
        refs = self.brain.work_view(self.pid)["units"][-1]["review"]["unknown_refs"]
        self.assertTrue({d["unknown_id"] for d in details} <= set(refs))

    def test_unknown_identity_survives_reload_and_repeated_views_without_writes(self):
        first = self.details()
        before = self.brain.ledger.path.read_bytes()
        loaded = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.details(loaded), first)
        self.assertEqual(self.details(), first)
        self.assertEqual(before, self.brain.ledger.path.read_bytes())

    def test_historical_unknown_is_retained_without_contaminating_other_claim(self):
        ids = {d["unknown_id"] for d in self.details()}
        self.brain.ingest_evidence(Evidence(
            "E1", "appui de test", EvidenceKind.ATTESTED_SOURCE,
            source_ref="fixture:evidence", claim_ref=self.claims[0], scope="local", stance="supports"),
            CausalOrigin.OTHER)
        details = self.details()
        self.assertEqual({d["unknown_id"] for d in details}, ids)
        current = {d["claim_id"]: d["result_current"] for d in details}
        self.assertFalse(current[self.claims[0]])
        self.assertTrue(current[self.claims[1]])
        self.assertEqual(ConscienceCBrain.load_or_bootstrap(self.root).audit(), [])


if __name__ == "__main__":
    unittest.main()
