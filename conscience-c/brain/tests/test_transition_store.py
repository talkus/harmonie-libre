"""Crash/restart and negative-path tests of the persistence protocol."""
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from conscience_c_brain.ledger import AppendOnlyLedger, _hash
from conscience_c_brain.transition_store import (
    TransitionStore, RecoveryRequired, StaleWriter, snapshot_bytes, digest,
)


STAMP = "2026-09-26T00:00:00+00:00"


def bootstrap(store):
    return store.commit({"n": 0, "state_label": "C(t_0)", "last_event_hash": "GENESIS",
                         "value": "initial"}, "BOOTSTRAP_T0", STAMP, {"anchor": "fixture"}, None, "GENESIS")


def next_commit(store, state, token):
    candidate = copy.deepcopy(state)
    candidate.update(n=1, state_label="C(t_1)", value="updated")
    return store.commit(candidate, "FIXTURE_UPDATE", STAMP, {"n": 1, "value": "updated"},
                        token, state["last_event_hash"])


class Interrupted(Exception):
    pass


class TransitionStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.store = TransitionStore(self.root)
        self.state, self.token, self.genesis = bootstrap(self.store)
        self.original_snapshot = self.store.state_path.read_bytes()
        self.original_journal = self.store.journal_path.read_bytes()

    def interrupt(self, stage, bootstrap_mode=False):
        def fail(name):
            if name == stage:
                raise Interrupted(name)
        with patch.object(self.store, "_stage", side_effect=fail):
            with self.assertRaises(Interrupted):
                next_commit(self.store, self.state, self.token)

    def mutate_intent(self, mutate, rehash=False):
        intent = json.loads(self.store.pending_path.read_bytes())
        mutate(intent)
        if rehash:
            intent["intent_hash"] = _hash({k: v for k, v in intent.items() if k != "intent_hash"})
        self.store.pending_path.write_bytes(snapshot_bytes(intent))

    def assert_unchanged_on_refusal(self):
        before = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        with self.assertRaises(RecoveryRequired):
            TransitionStore(self.root).load()
        after = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        self.assertEqual(before, after)

    def test_success_adds_exactly_one_event_and_committed_receipt(self):
        state, token, event = next_commit(self.store, self.state, self.token)
        self.assertEqual(state["n"], 1)
        self.assertEqual(state["last_event_hash"], event["event_hash"])
        self.assertEqual(token, digest(self.store.state_path.read_bytes()))
        self.assertEqual(len(AppendOnlyLedger(self.store.journal_path).read_verified()), 2)
        self.assertFalse(self.store.pending_path.exists())
        self.assertEqual(len(list(self.store.receipts_path.glob("*.committed.json"))), 2)

    def test_no_prepare_means_no_change(self):
        self.interrupt("before_prepare")
        self.assertEqual(self.store.state_path.read_bytes(), self.original_snapshot)
        self.assertEqual(self.store.journal_path.read_bytes(), self.original_journal)
        self.assertFalse(self.store.pending_path.exists())

    def test_prepare_without_append_aborts_and_retains_intent(self):
        self.interrupt("after_prepare")
        restarted = TransitionStore(self.root)
        loaded, _ = restarted.load()
        self.assertEqual(loaded, self.state)
        self.assertEqual(restarted.last_recovery, "aborted_before_append")
        self.assertEqual(self.store.state_path.read_bytes(), self.original_snapshot)
        self.assertEqual(self.store.journal_path.read_bytes(), self.original_journal)
        aborted = list(self.store.receipts_path.glob("*.aborted.json"))
        self.assertEqual(len(aborted), 1)
        self.assertIn("uncommitted_intent", json.loads(aborted[0].read_bytes()))

    def test_append_without_snapshot_completes_exact_prepared_state(self):
        self.interrupt("after_append")
        prepared = json.loads(self.store.pending_path.read_bytes())
        journal = self.store.journal_path.read_bytes()
        self.assertEqual(self.store.state_path.read_bytes(), self.original_snapshot)
        restarted = TransitionStore(self.root)
        loaded, _ = restarted.load()
        self.assertEqual(loaded, prepared["after_snapshot"])
        self.assertEqual(restarted.last_recovery, "completed_interrupted_commit")
        self.assertEqual(self.store.journal_path.read_bytes(), journal)
        self.assertEqual(len(AppendOnlyLedger(self.store.journal_path).read_verified()), 2)

    def test_snapshot_without_cleanup_is_finalized_once(self):
        self.interrupt("after_snapshot")
        before = self.store.state_path.read_bytes(), self.store.journal_path.read_bytes()
        loaded, _ = TransitionStore(self.root).load()
        self.assertEqual(loaded["n"], 1)
        TransitionStore(self.root).load()
        self.assertEqual(before, (self.store.state_path.read_bytes(), self.store.journal_path.read_bytes()))
        self.assertFalse(self.store.pending_path.exists())

    def test_cleanup_retry_after_receipt_is_idempotent(self):
        self.interrupt("after_receipt")
        paths = list(self.store.receipts_path.glob("*.committed.json"))
        self.assertEqual(len(paths), 2)
        TransitionStore(self.root).load()
        self.assertEqual(len(list(self.store.receipts_path.glob("*.committed.json"))), 2)
        self.assertFalse(self.store.pending_path.exists())

    def test_second_process_recovery_uses_actual_abrupt_exit(self):
        package_root = str(Path(__file__).resolve().parents[1])
        program = '''
import os, sys
from conscience_c_brain.transition_store import TransitionStore
s=TransitionStore(sys.argv[1])
state, token=s.load()
state.update(n=1, state_label="C(t_1)", value="crash-child")
s._stage=lambda stage: os._exit(73) if stage=="after_append" else None
s.commit(state, "FIXTURE_UPDATE", "2026-09-26T00:00:00Z", {"n":1}, token, state["last_event_hash"])
'''
        env = {**os.environ, "PYTHONPATH": package_root}
        proc = subprocess.run([sys.executable, "-c", program, str(self.root)], env=env,
                              capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 73, proc.stderr.decode())
        loaded, _ = TransitionStore(self.root).load()
        self.assertEqual(loaded["value"], "crash-child")
        self.assertEqual(loaded["n"], 1)

    def test_stale_writer_rejected_before_preparation(self):
        next_commit(self.store, self.state, self.token)
        journal = self.store.journal_path.read_bytes()
        with self.assertRaises(StaleWriter):
            next_commit(TransitionStore(self.root), self.state, self.token)
        self.assertEqual(journal, self.store.journal_path.read_bytes())
        self.assertFalse(self.store.pending_path.exists())

    def test_cooperating_writer_lock_prevents_overlapping_commit(self):
        second = TransitionStore(self.root)
        with self.store._locked():
            with self.assertRaises(StaleWriter):
                next_commit(second, self.state, self.token)
        self.assertEqual(self.store.journal_path.read_bytes(), self.original_journal)

    def test_pending_blocks_new_writes_until_reload(self):
        self.interrupt("after_prepare")
        with self.assertRaises(RecoveryRequired):
            next_commit(self.store, self.state, self.token)

    def test_torn_append_requires_recovery_without_truncation(self):
        self.interrupt("after_prepare")
        with self.store.journal_path.open("ab") as stream:
            stream.write(b'{"seq":2,')
        self.assert_unchanged_on_refusal()

    def test_valid_json_without_final_newline_is_not_silently_completed(self):
        self.interrupt("after_append")
        self.store.journal_path.write_bytes(self.store.journal_path.read_bytes().rstrip(b"\n"))
        self.assert_unchanged_on_refusal()

    def test_corrupted_pending_hash_is_rejected(self):
        self.interrupt("after_append")
        self.mutate_intent(lambda i: i["after_snapshot"].update(value="forged"))
        self.assert_unchanged_on_refusal()

    def test_unknown_pending_version_is_rejected(self):
        self.interrupt("after_append")
        self.mutate_intent(lambda i: i.update(format="FUTURE"), rehash=True)
        self.assert_unchanged_on_refusal()

    def test_rehashed_intent_with_unknown_ledger_event_is_rejected(self):
        self.interrupt("after_append")
        def forge(i):
            i["event"]["payload"]["value"] = "forged"
            i["event"]["event_hash"] = _hash({k:v for k,v in i["event"].items() if k != "event_hash"})
            i["after_snapshot"]["last_event_hash"] = i["event"]["event_hash"]
            i["after_snapshot_hash"] = digest(snapshot_bytes(i["after_snapshot"]))
        self.mutate_intent(forge, rehash=True)
        self.assert_unchanged_on_refusal()

    def test_snapshot_ahead_without_append_is_refused(self):
        self.interrupt("after_prepare")
        intent = json.loads(self.store.pending_path.read_bytes())
        self.store.state_path.write_bytes(snapshot_bytes(intent["after_snapshot"]))
        self.assert_unchanged_on_refusal()

    def test_unrelated_snapshot_is_not_overwritten(self):
        self.interrupt("after_append")
        data = json.loads(self.original_snapshot)
        data["value"] = "unexplained"
        self.store.state_path.write_bytes(snapshot_bytes(data))
        self.assert_unchanged_on_refusal()

    def test_missing_snapshot_without_intent_is_not_bootstrap(self):
        self.store.state_path.unlink()
        self.assert_unchanged_on_refusal()

    def test_missing_journal_without_intent_is_not_recreated(self):
        self.store.journal_path.unlink()
        self.assert_unchanged_on_refusal()
        self.assertFalse(self.store.journal_path.exists())

    def test_erased_files_with_committed_receipts_do_not_recreate_t0(self):
        self.store.journal_path.unlink()
        self.store.state_path.unlink()
        self.assert_unchanged_on_refusal()

    def test_journal_ahead_without_intent_requires_explicit_recovery(self):
        self.interrupt("after_append")
        self.store.pending_path.unlink()
        self.assert_unchanged_on_refusal()

    def test_invalid_proposed_index_rejected_without_pending(self):
        candidate = copy.deepcopy(self.state)
        candidate.update(n=2, state_label="C(t_2)")
        with self.assertRaises(RecoveryRequired):
            self.store.commit(candidate, "FIXTURE_UPDATE", STAMP, {"n":1}, self.token, self.state["last_event_hash"])
        self.assertFalse(self.store.pending_path.exists())

    def test_nonfinite_snapshot_is_not_written(self):
        candidate = copy.deepcopy(self.state)
        candidate.update(n=1, state_label="C(t_1)", value=float("nan"))
        with self.assertRaises(ValueError):
            self.store.commit(candidate, "FIXTURE_UPDATE", STAMP, {"n":1}, self.token, self.state["last_event_hash"])
        self.assertFalse(self.store.pending_path.exists())
        self.assertEqual(self.store.journal_path.read_bytes(), self.original_journal)

    def test_snapshot_replace_failure_leaves_complete_old_snapshot(self):
        from conscience_c_brain import transition_store as module
        replace = os.replace
        def failing_replace(src, dst):
            if Path(dst) == self.store.state_path:
                raise OSError("simulated disk failure")
            return replace(src, dst)
        with patch.object(module.os, "replace", side_effect=failing_replace):
            with self.assertRaises(OSError):
                next_commit(self.store, self.state, self.token)
        self.assertEqual(self.store.state_path.read_bytes(), self.original_snapshot)
        self.assertEqual(TransitionStore(self.root).load()[0]["n"], 1)

    def test_interrupted_bootstrap_resumes_without_second_genesis(self):
        for stage in ("after_prepare", "after_append", "after_snapshot", "after_receipt"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory() as root:
                store = TransitionStore(root)
                def fail(name):
                    if name == stage:
                        raise Interrupted(name)
                with patch.object(store, "_stage", side_effect=fail), self.assertRaises(Interrupted):
                    bootstrap(store)
                restarted = TransitionStore(root)
                loaded = restarted.load()
                if stage == "after_prepare":
                    self.assertIsNone(loaded)
                    bootstrap(restarted)
                else:
                    self.assertEqual(loaded[0]["n"], 0)
                self.assertEqual(len(AppendOnlyLedger(restarted.journal_path).read_verified()), 1)

    def test_successful_new_commit_preserves_legacy_journal_prefix(self):
        # Remove only the new top-level tx metadata from a standalone legacy fixture.
        row = copy.deepcopy(self.genesis)
        row.pop("transaction_id")
        row["event_hash"] = _hash({k:v for k,v in row.items() if k != "event_hash"})
        state = copy.deepcopy(self.state)
        state["last_event_hash"] = row["event_hash"]
        with tempfile.TemporaryDirectory() as root:
            s = TransitionStore(root)
            s.journal_path.write_bytes(json.dumps(row).encode() + b"\n")
            s.state_path.write_bytes(snapshot_bytes(state))
            prefix = s.journal_path.read_bytes()
            old, token = s.load()
            next_commit(s, old, token)
            self.assertTrue(s.journal_path.read_bytes().startswith(prefix))
            self.assertEqual(s.load()[0]["n"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
