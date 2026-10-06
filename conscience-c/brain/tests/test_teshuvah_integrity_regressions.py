"""Public-API regressions for evidence admission and recurring repairs."""
import copy
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind


class TeshuvahIntegrityRegressions(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.brain = ConscienceCBrain.load_or_bootstrap(Path(directory.name))
        self.brain.ingest_evidence(Evidence("E1", "observed", EvidenceKind.ATTESTED_SOURCE,
                                            source_ref="fixture:observation"))

    def claim(self, statement="initial"):
        return self.brain.record_claim(statement, "system_hypothesis", "fixture", facts=["E1"])["claim_id"]

    def proposed(self, claims):
        b = self.brain
        tid = b.initiate_teshuvah("error", "correction needed", "fixture", claim_ids=claims)["teshuvah_id"]
        b.acknowledge_teshuvah(tid, "actor", "error", "impact", "cause", "fixture")
        b.propose_teshuvah_repair(tid, "replace the interpretation", "fixture")
        return tid

    def correction(self, claim_id, **replacement):
        return {"claim_id": claim_id, "action": "supersede", "reason": "correction",
                "replacement": {"statement": "corrected", "provenance_kind": "system_hypothesis",
                                "provenance": "fixture", **replacement}}

    def apply(self, tid, corrections, **kwargs):
        return self.brain.apply_teshuvah_repair(tid, corrections, "actor", "fixture", **kwargs)

    def assert_rejected_without_mutation(self, tid, corrections):
        b = self.brain
        before = copy.deepcopy(b.state)
        history = (b.root / "events.jsonl").read_bytes()
        with self.assertRaises(ValueError):
            self.apply(tid, corrections)
        self.assertEqual(b.state, before)
        self.assertEqual((b.root / "events.jsonl").read_bytes(), history)

    def test_all_replacement_facts_are_validated_before_any_mutation(self):
        first, second = self.claim(), self.claim("second")
        tid = self.proposed([first, second])
        self.assert_rejected_without_mutation(tid, [self.correction(first),
            self.correction(second, facts=["MISSING-EVIDENCE"])])

    def test_replacement_confidence_must_be_a_finite_probability(self):
        for confidence in (-0.1, 2.0, float("nan"), float("inf"), True, "high"):
            with self.subTest(confidence=confidence):
                cid = self.claim(); tid = self.proposed([cid])
                self.assert_rejected_without_mutation(tid, [self.correction(cid, confidence=confidence)])

    def test_duplicate_corrections_do_not_create_orphan_active_claims(self):
        cid = self.claim(); tid = self.proposed([cid])
        self.assert_rejected_without_mutation(tid, [self.correction(cid), self.correction(cid)])

    def test_replacement_may_cite_an_existing_ledger_event(self):
        cid = self.claim(); tid = self.proposed([cid]); head = self.brain.ledger.head()
        self.apply(tid, [self.correction(cid, facts=[head], confidence=0.0)])
        self.assertEqual(self.brain.usable_claims(sensitive=True)[0]["facts"], [head])

    def test_recurrence_freezes_the_current_successor_and_repairs_its_lineage(self):
        b = self.brain; original = self.claim(); tid = self.proposed([original])
        self.apply(tid, [self.correction(original)])
        successor = b.claim(original)["replaced_by"]
        historical_origin = b.teshuvah(tid)["origin"]
        history = b.ledger.read_verified()
        b.record_teshuvah_recurrence(tid, "same error again", "fixture")
        self.assertEqual(b.usable_claims(sensitive=True), [])
        self.assertEqual(b.claim(original)["status"], "superseded")
        self.assertEqual(b.claim(successor)["status"], "under_repair")
        b = self.brain = ConscienceCBrain.load_or_bootstrap(b.root)
        b.propose_teshuvah_repair(tid, "repair the current interpretation", "fixture")
        self.assert_rejected_without_mutation(tid, [self.correction(original)])
        self.apply(tid, [self.correction(successor)])
        current = b.usable_claims(sensitive=True)
        self.assertEqual(len(current), 1)
        self.assertEqual(current[0]["replaces"], successor)
        self.assertEqual(b.claim(original)["replaced_by"], successor)
        self.assertEqual(b.teshuvah(tid)["origin"], historical_origin)
        self.assertEqual(b.ledger.read_verified()[:len(history)], history)

    def test_recurrence_follows_subsequent_updates_and_keeps_unrelated_claims(self):
        b = self.brain; original = self.claim(); tid = self.proposed([original])
        self.apply(tid, [self.correction(original)])
        successor = b.claim(original)["replaced_by"]
        updated = b.update_claim(successor, "new context", "context_shift", "fixture", "system_hypothesis")
        unrelated = self.claim("unrelated")
        b.record_teshuvah_recurrence(tid, "recurrence", "fixture")
        self.assertEqual([c["claim_id"] for c in b.usable_claims(sensitive=True)], [unrelated])
        self.assertEqual(b.claim(updated["claim_id"])["status"], "under_repair")

    def test_spark_can_be_raised_into_a_successor_after_recurrence(self):
        b = self.brain; original = self.claim(); tid = self.proposed([original])
        named = b.name_sparks(tid, [{"claim_id": original, "content": "retained fact", "facts": ["E1"]}], "fixture")
        sid = next(iter(named["sparks"]))
        correction = self.correction(original); correction["raised_sparks"] = [sid]
        self.apply(tid, [correction])
        successor = b.claim(original)["replaced_by"]
        b.record_teshuvah_recurrence(tid, "recurrence", "fixture")
        b.propose_teshuvah_repair(tid, "repair again", "fixture")
        correction = self.correction(successor); correction["raised_sparks"] = [sid]
        result = self.apply(tid, [correction])
        self.assertEqual(result["sparks"][sid]["status"], "raised")
        self.assertEqual(result["sparks"][sid]["claim_id"], original)
        self.assertEqual(len(b.usable_claims(sensitive=True)), 1)

    def test_recurrence_does_not_reactivate_a_retracted_claim(self):
        b = self.brain; original = self.claim(); tid = self.proposed([original])
        self.apply(tid, [{"claim_id": original, "action": "retract", "reason": "unsupported"}])
        b.record_teshuvah_recurrence(tid, "event recurred", "fixture")
        self.assertEqual(b.claim(original)["status"], "retracted")
        self.assertEqual(b.usable_claims(sensitive=True), [])
        b.propose_teshuvah_repair(tid, "repair the recurrence without inventing a claim", "fixture")
        self.apply(tid, [])
        self.assertEqual(b.usable_claims(sensitive=True), [])
