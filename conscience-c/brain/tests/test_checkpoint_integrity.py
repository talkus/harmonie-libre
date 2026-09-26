"""Regression tests for locally anchored checkpoint verification, not signatures."""
import copy
import json
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain.core import ConscienceCBrain, _stable_hash


class CheckpointIntegrityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.brain = ConscienceCBrain.load_or_bootstrap(Path(self.tmp.name))
        self.brain.imagine("before", ["a"], ["b"])
        self.receipt = self.brain.save_checkpoint_receipt("recorded")
        self.brain.imagine("after", ["c"], ["d"])

    def test_receipt_recomputed_hash_cannot_change_recorded_content(self):
        forged = copy.deepcopy(self.receipt)
        forged["checkpoint"]["telos"] = "forged"
        forged["checkpoint_hash"] = _stable_hash(forged["checkpoint"])
        self.assertFalse(self.brain.verify_checkpoint_receipt(forged))

    def test_receipt_must_have_been_recorded_not_just_reference_a_boundary(self):
        forged = copy.deepcopy(self.receipt)
        forged["receipt_id"] = "CP9999"
        self.assertFalse(self.brain.verify_checkpoint_receipt(forged))

    def test_genesis_is_not_a_substitute_for_a_recorded_receipt(self):
        forged = copy.deepcopy(self.receipt)
        forged["ledger_boundary"] = "GENESIS"
        forged["checkpoint"]["ledger_head"] = "GENESIS"
        forged["checkpoint_hash"] = _stable_hash(forged["checkpoint"])
        self.assertFalse(self.brain.verify_checkpoint_receipt(forged))

    def test_manifest_recomputed_hash_must_still_match_current_projection(self):
        forged = self.brain.checkpoint_manifest()
        forged["checkpoint"]["telos"] = "forged"
        forged["checkpoint_hash"] = _stable_hash(forged["checkpoint"])
        self.assertFalse(self.brain.verify_checkpoint_manifest(forged))

    def test_report_cannot_omit_all_events_from_a_nonempty_interval(self):
        report = self.brain.transition_report(0)
        report["events"] = []
        self.assertFalse(self.brain.verify_transition_report(report))

    def test_report_cannot_omit_first_event_and_keep_remaining_chain(self):
        report = self.brain.transition_report(0)
        report["events"].pop(0)
        self.assertFalse(self.brain.verify_transition_report(report))

    def test_report_event_content_must_match_ledger_not_only_neighbor_hashes(self):
        report = self.brain.transition_report(0)
        report["events"][0]["event_type"] = "FORGED_TYPE"
        self.assertFalse(self.brain.verify_transition_report(report))

    def test_receipt_cannot_verify_against_an_altered_unchecked_ledger(self):
        rows = self.brain.ledger.read()
        rows[0]["payload"]["tampered"] = True
        self.brain.ledger.path.write_text(
            "\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n",
            encoding="utf-8",
        )
        self.assertFalse(self.brain.verify_checkpoint_receipt(self.receipt))

    def test_recorded_receipt_remains_valid_after_restart_and_later_events(self):
        resumed = ConscienceCBrain.load_or_bootstrap(self.brain.root)
        resumed.imagine("later", [], [])
        self.assertTrue(resumed.verify_checkpoint_receipt(self.receipt))
        self.assertTrue(resumed.verify_checkpoint_receipt(resumed.checkpoint_receipts()[0]))

    def test_returned_and_original_stored_receipt_formats_are_accepted(self):
        self.assertTrue(self.brain.verify_checkpoint_receipt(self.receipt))
        self.assertTrue(self.brain.verify_checkpoint_receipt(self.brain.checkpoint_receipts()[0]))

    def test_receipt_metadata_and_unknown_fields_cannot_be_forged(self):
        for key, value in {
            "label": "renamed", "state": "C(t_999)",
            "receipt_event_hash": "0" * 64, "post_receipt_state": "C(t_999)",
            "unrecorded_authorization": True,
        }.items():
            with self.subTest(field=key):
                receipt = copy.deepcopy(self.receipt)
                receipt[key] = value
                self.assertFalse(self.brain.verify_checkpoint_receipt(receipt))

    def test_missing_receipt_fields_are_rejected(self):
        for key in ("state", "label", "receipt_id", "checkpoint", "ledger_boundary"):
            with self.subTest(field=key):
                receipt = copy.deepcopy(self.receipt)
                del receipt[key]
                self.assertFalse(self.brain.verify_checkpoint_receipt(receipt))

    def test_edited_continuity_hash_cannot_be_self_certified(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["continuity_structure_hash"] = "0" * 64
        receipt["checkpoint"]["continuity_structure_hash"] = "0" * 64
        receipt["checkpoint_hash"] = _stable_hash(receipt["checkpoint"])
        self.assertFalse(self.brain.verify_checkpoint_receipt(receipt))

    def test_forged_receipt_is_refused_by_resume_and_replay(self):
        receipt = copy.deepcopy(self.receipt)
        receipt["checkpoint"]["telos"] = "forged"
        receipt["checkpoint_hash"] = _stable_hash(receipt["checkpoint"])
        for method in (self.brain.resume_from_receipt, self.brain.replay_plan_from_receipt):
            with self.subTest(method=method.__name__), self.assertRaises(ValueError):
                method(receipt)

    def test_valid_replay_remains_a_plan_without_rollback(self):
        before = copy.deepcopy(self.brain.state)
        plan = self.brain.replay_plan_from_receipt(self.receipt)
        self.assertFalse(plan["automatic_replay_allowed"])
        self.assertEqual(plan["replay_status"], "plan_only_no_state_mutation")
        self.assertEqual(plan["events_to_replay"][0]["event_type"], "CHECKPOINT_RECEIPT")
        self.assertEqual(self.brain.state, before)

    def test_current_manifest_is_valid_but_becomes_stale(self):
        manifest = self.brain.checkpoint_manifest()
        self.assertTrue(self.brain.verify_checkpoint_manifest(manifest))
        self.brain.imagine("new", [], [])
        self.assertFalse(self.brain.verify_checkpoint_manifest(manifest))
        self.assertTrue(self.brain.verify_checkpoint_receipt(self.receipt))

    def test_manifest_metadata_is_checked(self):
        for key in ("ledger_head", "continuity_structure_hash", "semantics"):
            with self.subTest(field=key):
                manifest = self.brain.checkpoint_manifest()
                manifest[key] = "forged"
                self.assertFalse(self.brain.verify_checkpoint_manifest(manifest))

    def test_report_must_cover_every_event_in_the_declared_interval(self):
        original = self.brain.transition_report(0)
        for index in range(len(original["events"])):
            with self.subTest(omitted=index):
                report = copy.deepcopy(original)
                del report["events"][index]
                self.assertFalse(self.brain.verify_transition_report(report))

    def test_report_checks_metadata_not_only_hash_links(self):
        for key, value in {"n": 99, "origin": "FAKE", "event_hash": "0" * 64}.items():
            with self.subTest(field=key):
                report = self.brain.transition_report(0)
                report["events"][0][key] = value
                self.assertFalse(self.brain.verify_transition_report(report))

    def test_report_checks_declared_range_and_destination(self):
        for key, value in {"from_n": 1, "to_n": 999, "ledger_head": "0" * 64}.items():
            with self.subTest(field=key):
                report = self.brain.transition_report(0)
                report[key] = value
                self.assertFalse(self.brain.verify_transition_report(report))

    def test_empty_report_is_valid_only_for_an_empty_declared_interval(self):
        report = self.brain.transition_report(self.brain.state["n"])
        self.assertEqual(report["events"], [])
        self.assertTrue(self.brain.verify_transition_report(report))
        report["ledger_head"] = "forged"
        self.assertFalse(self.brain.verify_transition_report(report))

    def test_range_validation_rejects_negative_future_boolean_and_noninteger(self):
        for value in (-1, self.brain.state["n"] + 1, True, 1.0, None, "1"):
            with self.subTest(index=value), self.assertRaises(ValueError):
                self.brain.transition_report(value)

    def test_verifiers_reject_non_object_input_without_mutating(self):
        before = copy.deepcopy(self.brain.state)
        for method in (self.brain.verify_checkpoint_receipt,
                       self.brain.verify_checkpoint_manifest,
                       self.brain.verify_transition_report):
            for value in (None, [], 7, "text", {}):
                with self.subTest(method=method.__name__, value=value):
                    self.assertFalse(method(value))
        self.assertEqual(self.brain.state, before)

    def test_verifiers_refuse_malformed_journal_without_repairing_it(self):
        manifest = self.brain.checkpoint_manifest()
        report = self.brain.transition_report(0)
        original = self.brain.ledger.path.read_bytes()
        for malformed in (b"not json\n", b"[]\n", b"{\"payload\": {}}\n"):
            with self.subTest(malformed=malformed):
                self.brain.ledger.path.write_bytes(malformed)
                self.assertFalse(self.brain.verify_checkpoint_receipt(self.receipt))
                self.assertFalse(self.brain.verify_checkpoint_manifest(manifest))
                self.assertFalse(self.brain.verify_transition_report(report))
                self.assertEqual(self.brain.ledger.path.read_bytes(), malformed)
        self.brain.ledger.path.write_bytes(original)

    def test_missing_journal_is_rejected_not_recreated(self):
        manifest = self.brain.checkpoint_manifest()
        report = self.brain.transition_report(0)
        self.brain.ledger.path.unlink()
        self.assertFalse(self.brain.verify_checkpoint_receipt(self.receipt))
        self.assertFalse(self.brain.verify_checkpoint_manifest(manifest))
        self.assertFalse(self.brain.verify_transition_report(report))
        self.assertFalse(self.brain.ledger.path.exists())

    def test_successful_reads_do_not_change_state_or_files(self):
        before = copy.deepcopy(self.brain.state)
        ledger_before = self.brain.ledger.path.read_bytes()
        snapshot_before = self.brain.state_path.read_bytes()
        self.brain.verify_checkpoint_receipt(self.receipt)
        self.brain.verify_checkpoint_manifest(self.brain.checkpoint_manifest())
        self.brain.verify_transition_report(self.brain.transition_report(0))
        self.brain.resume_from_receipt(self.receipt)
        self.brain.replay_plan_from_receipt(self.receipt)
        self.assertEqual(self.brain.state, before)
        self.assertEqual(self.brain.ledger.path.read_bytes(), ledger_before)
        self.assertEqual(self.brain.state_path.read_bytes(), snapshot_before)

    def test_current_projection_requires_matching_snapshot_head(self):
        self.brain.state["last_event_hash"] = "wrong"
        with self.assertRaises(ValueError):
            self.brain.checkpoint_manifest()
        with self.assertRaises(ValueError):
            self.brain.transition_report(0)

    def test_current_projection_requires_matching_snapshot_count(self):
        self.brain.state["n"] += 1
        with self.assertRaises(ValueError):
            self.brain.current_checkpoint()

    def test_ledger_verify_preserves_none_on_success_contract(self):
        self.assertIsNone(self.brain.ledger.verify())
        self.assertEqual(self.brain.ledger.read_verified(), self.brain.ledger.read())

    def test_receipt_return_is_detached_from_recorded_data(self):
        self.receipt["checkpoint"]["loop"][0] = "changed copy"
        stored = self.brain.checkpoint_receipts()[0]
        self.assertEqual(stored["checkpoint"]["loop"][0], "Humilité")
        self.assertTrue(self.brain.verify_checkpoint_receipt(stored))


if __name__ == "__main__":
    unittest.main(verbosity=2)
