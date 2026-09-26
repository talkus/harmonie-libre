"""Integration checks for review recording, deliberately not truth certification."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind
from conscience_c_brain.models import CausalOrigin


class ReviewAdmissionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.b = ConscienceCBrain.load_or_bootstrap(self.root)
        self.b.save_checkpoint_receipt("before evidence")
        self.receipt = self.b.checkpoint_receipts()[0]
        self.b.ingest_evidence(Evidence("E1", "claim", EvidenceKind.ATTESTED_SOURCE,
                                       source_ref="source:old"))
        self.item = self.b.revalidation_queue_from_receipt(self.receipt)["items"][0]
        self.review = {"source_ref": "source:new", "result": "supported"}

    def record(self, review=None):
        return self.b.record_revalidation_review(
            self.item, self.review if review is None else review, "operator:declared")

    def unchanged_on_failure(self, item, review, provenance="operator:declared"):
        state = copy.deepcopy(self.b.state)
        journal = self.b.ledger.path.read_bytes()
        snapshot = self.b.state_path.read_bytes()
        with self.assertRaises((ValueError, OSError)):
            self.b.record_revalidation_review(item, review, provenance)
        self.assertEqual(self.b.state, state)
        self.assertEqual(self.b.ledger.path.read_bytes(), journal)
        self.assertEqual(self.b.state_path.read_bytes(), snapshot)

    def test_canonical_api_records_but_does_not_verify(self):
        before = self.b.state["n"]
        out = self.record()
        self.assertEqual(out["status"], "recorded_not_verified")
        self.assertEqual(out["verification_status"], "not_performed")
        self.assertFalse(out["automatic_replay_allowed"])
        self.assertEqual(self.b.state["n"], before + 1)
        payload = self.b.ledger.read()[-1]["payload"]
        self.assertEqual(payload["status"], "recorded_not_verified")
        self.assertEqual(payload["recording_version"], 2)
        self.assertEqual(payload["historical_event_hash"], self.item["event_hash"])
        self.assertEqual(out["review_event_hash"], self.b.ledger.head())

    def test_legacy_resolved_means_recorded_only(self):
        out = self.b.validate_revalidation_item(self.item, self.review, "operator:declared")
        self.assertEqual(out["status"], "resolved")
        self.assertEqual(out["legacy_status_semantics"], "submission_recorded_only")
        self.assertEqual(out["recording_status"], "recorded_not_verified")
        self.assertEqual(out["verification_status"], "not_performed")
        self.assertEqual(self.b.ledger.read()[-1]["payload"]["status"], "recorded_not_verified")

    def test_declared_contradiction_does_not_modify_evidence_or_hypotheses(self):
        evidence = copy.deepcopy(self.b.state["E"])
        hypotheses = copy.deepcopy(self.b.state["hypotheses"])
        self.record({"source_ref": "source:new", "result": "contradicted"})
        self.assertEqual(self.b.state["E"], evidence)
        self.assertEqual(self.b.state["hypotheses"], hypotheses)

    def test_declared_date_does_not_claim_freshness(self):
        out = self.record({**self.review, "observed_at": "2020-01-01T00:00:00Z"})
        self.assertIn("evidence_freshness", out["checks_not_performed"])
        self.assertIn("source_retrieval", out["checks_not_performed"])
        self.assertIn("reviewer_independence", out["checks_not_performed"])
        self.assertNotIn("evidence_truth", out["checks_performed"])

    def test_item_cannot_inject_verdict_or_authority_fields(self):
        for name in ("verified", "reviewer_authenticated", "automatic_replay_allowed"):
            with self.subTest(name=name):
                self.unchanged_on_failure({**self.item, name: True}, self.review)

    def test_report_cannot_inject_verdict_or_authority_fields(self):
        for name in ("verified", "independent", "automatic_replay_allowed"):
            with self.subTest(name=name):
                self.unchanged_on_failure(self.item, {**self.review, name: True})

    def test_non_object_inputs_fail_without_write(self):
        for value in (None, [], True, "text", 1):
            with self.subTest(value=value):
                self.unchanged_on_failure(value, self.review)
                self.unchanged_on_failure(self.item, value)

    def test_all_item_fields_are_required(self):
        for field in ("event_hash", "event_type", "replay_class", "status"):
            item = copy.deepcopy(self.item)
            del item[field]
            with self.subTest(field=field):
                self.unchanged_on_failure(item, self.review)

    def test_report_values_must_be_nonblank_strings(self):
        for field in ("source_ref", "result", "notes", "observed_at"):
            for value in (None, True, 3, {}, [], "", " \t"):
                with self.subTest(field=field, value=value):
                    self.unchanged_on_failure(self.item, {**self.review, field: value})

    def test_non_pending_task_is_rejected(self):
        self.unchanged_on_failure({**self.item, "status": "resolved"}, self.review)

    def test_real_canon_task_is_not_auto_compared(self):
        self.b._transition("REPAIR_DRIFT", {"drifts": [], "provenance": "fixture:legacy"},
                           CausalOrigin.MIXED)
        row = self.b.ledger.read()[-1]
        item = {"event_hash": row["event_hash"], "event_type": row["event_type"],
                "status": "pending", "replay_class": "requires_current_canon_check"}
        self.unchanged_on_failure(item, self.review)

    def test_unknown_recorded_event_is_not_reviewable_by_substitution(self):
        self.b._transition("UNKNOWN_FUTURE_EVENT", {}, CausalOrigin.SELF)
        row = self.b.ledger.read()[-1]
        item = {"event_hash": row["event_hash"], "event_type": row["event_type"],
                "status": "pending", "replay_class": "requires_external_reverification"}
        self.unchanged_on_failure(item, self.review)

    def test_history_tracks_successive_reports_without_overwriting(self):
        first = self.record()
        second = self.record({"source_ref": "source:next", "result": "contradicted"})
        history = self.b.revalidation_history(self.item["event_hash"])
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["fresh_evidence"]["result"], "supported")
        self.assertEqual(second["supersedes_revalidation_event_hash"], first["review_event_hash"])
        self.assertTrue(all(h["verification_status"] == "not_performed" for h in history))

    def test_input_and_output_objects_are_detached(self):
        before = copy.deepcopy(self.item)
        out = self.record()
        self.assertEqual(self.item, before)
        self.review["result"] = "caller edited"
        out["fresh_evidence"]["result"] = "return value edited"
        out["checks_performed"].append("invented")
        history = self.b.revalidation_history(self.item["event_hash"])
        self.assertEqual(history[0]["fresh_evidence"]["result"], "supported")
        history[0]["fresh_evidence"]["result"] = "history copy edited"
        self.assertEqual(self.b.current_revalidation_view(self.item["event_hash"])
                         ["fresh_evidence"]["result"], "supported")

    def test_queue_remains_pending_and_review_does_not_authorize_replay(self):
        self.record()
        plan = self.b.replay_plan_from_receipt(self.receipt)
        self.assertFalse(plan["automatic_replay_allowed"])
        self.assertEqual(plan["events_to_replay"][-1]["replay_class"], "documentary_only")
        queue = self.b.revalidation_queue_from_receipt(self.receipt)
        self.assertEqual(queue["pending_count"], 1)
        self.assertEqual(queue["items"][0]["status"], "pending")

    def test_recorded_report_survives_restart(self):
        self.record()
        journal = self.b.ledger.path.read_bytes()
        resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(resumed.ledger.path.read_bytes(), journal)
        self.assertEqual(resumed.revalidation_history()[0]["verification_status"], "not_performed")

    def test_recovery_after_append_does_not_reexecute_review(self):
        def fail(stage):
            if stage == "after_append":
                raise OSError("simulated interruption")
        with patch.object(self.b._store, "_stage", side_effect=fail), self.assertRaises(OSError):
            self.record()
        with patch.object(ConscienceCBrain, "record_revalidation_review", side_effect=AssertionError("no replay")):
            resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        history = resumed.revalidation_history(self.item["event_hash"])
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["verification_status"], "not_performed")
        self.assertEqual(resumed.audit(), [])

    def test_legacy_reports_stay_unchanged_and_are_not_certified(self):
        payload = {"historical_event_hash": self.item["event_hash"],
                   "outcome": "revalidated_with_fresh_evidence", "provenance": "legacy:claim",
                   "fresh_evidence": {"source_ref": "legacy:source", "result": "supported"}}
        row = self.b._transition("REVALIDATE_HISTORICAL_EVENT", payload, CausalOrigin.MIXED)
        journal = self.b.ledger.path.read_bytes()
        history = self.b.revalidation_history(self.item["event_hash"])
        self.assertEqual(history[0]["outcome"], "revalidated_with_fresh_evidence")
        self.assertEqual(history[0]["recording_status"], "legacy_declaration_not_verified")
        self.assertEqual(history[0]["verification_status"], "not_performed")
        self.assertEqual(self.b.ledger.path.read_bytes(), journal)
        out = self.record()
        self.assertEqual(out["supersedes_revalidation_event_hash"], row["event_hash"])
        self.assertTrue(self.b.ledger.path.read_bytes().startswith(journal))

    def test_unlinked_legacy_report_is_not_hidden_or_treated_as_valid(self):
        self.b._transition("REVALIDATE_HISTORICAL_EVENT",
                           {"historical_event_hash": "0" * 64, "outcome": "revalidated"},
                           CausalOrigin.MIXED)
        report = self.b.revalidation_history()[0]
        self.assertFalse(report["historical_event_found"])
        self.assertEqual(report["verification_status"], "not_performed")

    def test_corrupted_journal_is_not_used_for_admission_or_history(self):
        rows = self.b.ledger.read()
        rows[0]["payload"]["tampered"] = True
        self.b.ledger.path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
        self.unchanged_on_failure(self.item, self.review)
        with self.assertRaises(ValueError):
            self.b.revalidation_history()

    def test_missing_journal_is_not_recreated(self):
        self.b.ledger.path.unlink()
        before = self.b.state_path.read_bytes()
        with self.assertRaises((ValueError, OSError)):
            self.record()
        self.assertFalse(self.b.ledger.path.exists())
        self.assertEqual(self.b.state_path.read_bytes(), before)

    def test_stale_instance_cannot_append_a_review(self):
        stale = ConscienceCBrain.load_or_bootstrap(self.root)
        self.b.imagine("newer state", [], [])
        journal = self.b.ledger.path.read_bytes()
        with self.assertRaises(ValueError):
            stale.record_revalidation_review(self.item, self.review, "operator:stale")
        self.assertEqual(self.b.ledger.path.read_bytes(), journal)

    def test_history_read_does_not_change_state_or_files(self):
        self.record()
        state = copy.deepcopy(self.b.state)
        journal = self.b.ledger.path.read_bytes()
        snapshot = self.b.state_path.read_bytes()
        self.b.revalidation_history()
        self.b.current_revalidation_view(self.item["event_hash"])
        self.assertEqual(self.b.state, state)
        self.assertEqual(self.b.ledger.path.read_bytes(), journal)
        self.assertEqual(self.b.state_path.read_bytes(), snapshot)


if __name__ == "__main__":
    unittest.main()
