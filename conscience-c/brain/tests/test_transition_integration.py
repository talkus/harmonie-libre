"""The existing brain API must use the coordinated commit boundary."""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from conscience_c_brain import ConscienceCBrain
from conscience_c_brain.transition_store import RecoveryRequired


class TransitionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)

    def fail_after(self, stage):
        def fail(name):
            if name == stage:
                raise OSError("simulated failure: " + stage)
        return patch.object(self.brain._store, "_stage", side_effect=fail)

    def test_failed_prepare_discards_only_uncommitted_model_changes(self):
        before = copy.deepcopy(self.brain.state)
        with self.fail_after("after_prepare"), self.assertRaises(OSError):
            self.brain.imagine("uncommitted", ["x"], ["y"])
        self.assertEqual(self.brain.state, before)
        with self.assertRaises(RecoveryRequired):
            self.brain.imagine("must reload", [], [])
        resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(resumed.state, before)
        self.assertEqual(resumed._store.last_recovery, "aborted_before_append")
        resumed.imagine("new attempt", [], [])
        self.assertEqual(resumed.state["n"], 1)
        self.assertEqual(resumed.state["imaginations"][0]["title"], "new attempt")

    def test_recovery_restores_repair_data_without_reexecuting_action(self):
        with self.fail_after("after_append"), self.assertRaises(OSError):
            self.brain.record_repair("O1", "issue", "declared action", "source:fixture")
        with patch.object(ConscienceCBrain, "record_repair", side_effect=AssertionError("must not rerun")):
            resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(resumed.state["n"], 1)
        self.assertEqual(len(resumed.state["R"]["repairs"]), 1)
        self.assertEqual(resumed.state["R"]["repairs"][0]["status"], "pending_verification")
        self.assertEqual([r["event_type"] for r in resumed.ledger.read()], ["BOOTSTRAP_T0", "RECORD_REPAIR"])

    def test_recovered_checkpoint_receipt_remains_bound_to_original_boundary(self):
        self.brain.imagine("before receipt", [], [])
        original = self.brain.state["state_label"]
        with self.fail_after("after_append"), self.assertRaises(OSError):
            self.brain.save_checkpoint_receipt("interrupted capture")
        resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        receipts = resumed.checkpoint_receipts()
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts[0]["state"], original)
        self.assertTrue(resumed.verify_checkpoint_receipt(receipts[0]))
        self.assertEqual(resumed.state["n"], 2)

    def test_read_after_failed_commit_cannot_claim_stale_snapshot_is_current(self):
        with self.fail_after("after_append"), self.assertRaises(OSError):
            self.brain.imagine("committed event", [], [])
        with self.assertRaises(ValueError):
            self.brain.current_checkpoint()
        resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertTrue(resumed.verify_checkpoint_manifest(resumed.checkpoint_manifest()))

    def test_missing_journal_is_not_created_by_brain_constructor(self):
        self.brain.ledger.path.unlink()
        with self.assertRaises(RecoveryRequired):
            ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertFalse(self.brain.ledger.path.exists())

    def test_unexplained_snapshot_ledger_mismatch_is_not_auto_recovered(self):
        old = self.brain.state_path.read_bytes()
        self.brain.imagine("advanced", [], [])
        self.brain.state_path.write_bytes(old)
        journal = self.brain.ledger.path.read_bytes()
        with self.assertRaises(RecoveryRequired):
            ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.brain.state_path.read_bytes(), old)
        self.assertEqual(self.brain.ledger.path.read_bytes(), journal)

    def test_several_commits_and_restart_preserve_sequence(self):
        for n in range(5):
            self.brain.imagine("iteration " + str(n), [], [])
        resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(resumed.state, self.brain.state)
        self.assertEqual(resumed.state["n"], 5)
        self.assertEqual(resumed.audit(), [])
        self.assertTrue(resumed.verify_transition_report(resumed.transition_report(0)))

    def test_actual_process_exit_and_public_restart(self):
        import os
        import subprocess
        import sys
        script = '''
import os, sys
from pathlib import Path
from conscience_c_brain import ConscienceCBrain
b=ConscienceCBrain.load_or_bootstrap(Path(sys.argv[1]))
b._store._stage=lambda stage: os._exit(74) if stage=="after_append" else None
b.imagine("abrupt exit", [], [])
'''
        proc = subprocess.run([sys.executable, "-c", script, str(self.root)],
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
            capture_output=True, timeout=10)
        self.assertEqual(proc.returncode, 74, proc.stderr.decode())
        resumed = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(resumed.state["n"], 1)
        self.assertEqual(resumed.state["imaginations"][0]["title"], "abrupt exit")
        self.assertEqual(len(resumed.ledger.read()), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
