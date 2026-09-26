"""Negative cases for historical review admission; no external truth oracle."""
import copy
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind


class RevalidationRegressions(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.b = ConscienceCBrain.load_or_bootstrap(Path(self.tmp.name))
        self.b.save_checkpoint_receipt("review anchor")
        self.receipt = self.b.checkpoint_receipts()[0]
        self.b.ingest_evidence(Evidence(
            "E1", "historical claim", EvidenceKind.ATTESTED_SOURCE,
            source_ref="source:old"))
        self.item = self.b.revalidation_queue_from_receipt(self.receipt)["items"][0]
        self.review = {"source_ref": "source:review", "result": "supported"}

    def rejected_without_write(self, item, review, provenance="operator:review"):
        before_state = copy.deepcopy(self.b.state)
        before_journal = self.b.ledger.path.read_bytes()
        before_snapshot = self.b.state_path.read_bytes()
        with self.assertRaises(ValueError):
            self.b.validate_revalidation_item(item, review, provenance)
        self.assertEqual(self.b.state, before_state)
        self.assertEqual(self.b.ledger.path.read_bytes(), before_journal)
        self.assertEqual(self.b.state_path.read_bytes(), before_snapshot)

    def test_unknown_event_hash_cannot_receive_review(self):
        item = copy.deepcopy(self.item)
        item["event_hash"] = "0" * 64
        self.rejected_without_write(item, self.review)

    def test_event_type_must_match_recorded_event(self):
        item = copy.deepcopy(self.item)
        item["event_type"] = "UPDATE_OTHER"
        self.rejected_without_write(item, self.review)

    def test_replay_class_cannot_be_substituted_by_caller(self):
        item = copy.deepcopy(self.item)
        item["replay_class"] = "requires_current_canon_check"
        self.rejected_without_write(item, None)

    def test_documentary_event_cannot_masquerade_as_external_evidence(self):
        self.b.imagine("not observed", ["hypothesis"], ["possible"])
        row = self.b.ledger.read()[-1]
        item = {"status": "pending", "event_hash": row["event_hash"],
                "event_type": row["event_type"],
                "replay_class": "requires_external_reverification"}
        self.rejected_without_write(item, self.review)

    def test_bootstrap_cannot_masquerade_as_external_evidence(self):
        row = self.b.ledger.read()[0]
        item = {"status": "pending", "event_hash": row["event_hash"],
                "event_type": row["event_type"],
                "replay_class": "requires_external_reverification"}
        self.rejected_without_write(item, self.review)

    def test_blank_source_reference_is_not_a_justification(self):
        self.rejected_without_write(self.item, {"source_ref": "   ", "result": "supported"})

    def test_blank_provenance_is_not_an_operator_identity(self):
        self.rejected_without_write(self.item, self.review, "   ")

    def test_source_without_reported_result_is_not_a_review(self):
        self.rejected_without_write(self.item, {"source_ref": "source:review"})

    def test_recording_a_contradiction_does_not_certify_the_claim(self):
        result = self.b.validate_revalidation_item(
            self.item, {"source_ref": "source:new", "result": "contradicted"},
            "operator:review")
        self.assertEqual(result.get("outcome"), "review_recorded_not_verified")
        self.assertEqual(result.get("verification_status"), "not_performed")
        self.assertFalse(result.get("automatic_replay_allowed", True))
        self.assertEqual(self.b.state["E"]["evidence"]["E1"]["content"], "historical claim")


if __name__ == "__main__":
    unittest.main()
