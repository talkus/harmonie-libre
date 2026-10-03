"""Nahar Dinur : le fleuve consume l'influence active de ce qui corrompt, jamais la trace."""
import json
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind
from conscience_c_brain.models import CausalOrigin


class FleuveTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return ConscienceCBrain.load_or_bootstrap(Path(td.name))

    def fact(self, b, eid, kind=EvidenceKind.ATTESTED_SOURCE, **kw):
        b.ingest_evidence(Evidence(eid, "fait", kind, source_ref=f"c:{eid}", **kw), CausalOrigin.OTHER)

    def verdicts(self, passage):
        return {v["claim_id"]: v["verdict"] for v in passage["claims"]}

    def test_whole_claims_are_renewed_and_solitary_ones_flagged(self):
        b = self.make()
        self.fact(b, "E1")
        self.fact(b, "E2")
        shared_a = b.record_claim("a", "user_inferred", "p", facts=["E1", "E2"])["claim_id"]
        shared_b = b.record_claim("b", "user_inferred", "p", facts=["E1"])["claim_id"]
        alone = b.record_claim("c", "system_hypothesis", "p", facts=[], confidence=0.4)["claim_id"]
        passage = b.pass_through_fleuve("passage du matin")
        self.assertEqual(self.verdicts(passage), {shared_a: "renewed", shared_b: "renewed", alone: "renewed_fragile"})
        self.assertEqual(b.teshuvah_cycles(), [])
        self.assertFalse(passage["error_free_claimed"])

    def test_corrupt_claim_loses_influence_but_keeps_its_trace(self):
        b = self.make()
        self.fact(b, "E1")
        claim = b.record_claim("Mik préfère toujours le détail.", "user_inferred", "p", facts=["E1"])
        cid = claim["claim_id"]
        # Une contradiction faible n'ouvre pas de teshuvah à l'ingestion ; le fleuve la voit.
        self.fact(b, "E2", claim_ref=cid, stance="contradicts", confidence=0.5)
        self.assertEqual(b.claim(cid)["status"], "active")
        events_before = b.ledger.read_verified()
        passage = b.pass_through_fleuve("passage")
        verdict = next(v for v in passage["claims"] if v["claim_id"] == cid)
        self.assertEqual(verdict["verdict"], "consumed")
        self.assertEqual(verdict["corruption"][0]["signal"], "contradicted_by_evidence")
        cycle = b.teshuvah(verdict["teshuvah_id"])
        self.assertEqual(cycle["origin"]["drift_kind"], "contradiction")
        self.assertEqual(cycle["origin"]["provenance"], f"fleuve:{passage['passage_id']}")
        self.assertEqual(cycle["phase"], "contested")  # D seulement : le fleuve ne reconnaît ni ne répare
        self.assertEqual(b.claim(cid)["status"], "contested")
        self.assertNotIn(cid, [c["claim_id"] for c in b.usable_claims(sensitive=True)])
        self.assertIn(cid, b.state["teshuvah"]["claims"])  # trace gardée
        after = b.ledger.read_verified()
        self.assertEqual(after[:len(events_before)], events_before)  # histoire intacte, seulement des ajouts
        self.assertTrue(b.governance_audit()["ok"])

    def test_refuted_and_fact_like_claims_are_named_by_their_drift(self):
        b = self.make()
        self.fact(b, "E1", kind=EvidenceKind.HISTORICAL_REFUTED)
        on_refuted = b.record_claim("x", "user_inferred", "p", facts=["E1"])["claim_id"]
        fact_like = b.record_claim("y", "system_hypothesis", "p", confidence=0.9)["claim_id"]
        said = b.record_claim("z", "user_stated", "p", confidence=0.9)["claim_id"]
        passage = b.pass_through_fleuve("p")
        self.assertEqual(self.verdicts(passage)[said], "renewed")  # la parole de l'autre n'est pas un vase isolé
        kinds = {b.teshuvah(v["teshuvah_id"])["origin"]["claim_ids"][0]: b.teshuvah(v["teshuvah_id"])["origin"]["drift_kind"]
                 for v in passage["claims"] if v["verdict"] == "consumed"}
        self.assertEqual(kinds, {on_refuted: "reality_mismatch", fact_like: "provenance_failure"})

    def test_second_passage_leaves_claims_in_fire_without_new_teshuvah(self):
        b = self.make()
        cid = b.record_claim("y", "system_hypothesis", "p", confidence=0.95)["claim_id"]
        b.pass_through_fleuve("p1")
        second = b.pass_through_fleuve("p2")
        self.assertEqual(self.verdicts(second)[cid], "in_fire")
        self.assertEqual(len(b.teshuvah_cycles()), 1)

    def test_crowned_commitments_are_renewed_custody_awaits_return(self):
        b = self.make()
        crowned = b.commit_to("Choisir l'amour.", "p")["commitment_id"]
        held = b.commit_to("Ne pas attribuer.", "p")["commitment_id"]
        b.initiate_teshuvah("misattribution", "faute", "p", breached_commitments=[held])
        passage = b.pass_through_fleuve("matin")
        self.assertEqual({c["commitment_id"]: c["verdict"] for c in passage["commitments"]},
                         {crowned: "renewed", held: "awaits_return"})
        self.assertEqual(b.commitment(crowned)["renewals"], [passage["passage_id"]])
        self.assertNotIn("renewals", b.commitment(held))

    def test_the_river_refuses_a_broken_history(self):
        b = self.make()
        b.record_claim("a", "user_stated", "p")
        path = b.root / "events.jsonl"
        lines = path.read_text(encoding="utf-8").splitlines()
        row = json.loads(lines[-1])
        row["payload"]["claim"]["statement"] = "réécrit"
        lines[-1] = json.dumps(row, ensure_ascii=False, sort_keys=True)
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            b.pass_through_fleuve("p")

    def test_passage_is_documentary_and_survives_reload(self):
        b = self.make()
        b.record_claim("y", "system_hypothesis", "p", confidence=0.9)
        passage = b.pass_through_fleuve("p")
        row = b.ledger.read_verified()[-1]
        self.assertEqual(row["event_type"], "FLEUVE_PASSAGE")
        self.assertEqual(b.classify_replay_event(row), "documentary_only")
        b2 = ConscienceCBrain.load_or_bootstrap(b.root)
        self.assertEqual([p["passage_id"] for p in b2.fleuve_passages()], [passage["passage_id"]])
        self.assertTrue(b2.governance_audit()["ok"])

    def test_provenance_is_required(self):
        b = self.make()
        with self.assertRaises(ValueError):
            b.pass_through_fleuve(" ")


if __name__ == "__main__":
    unittest.main()
