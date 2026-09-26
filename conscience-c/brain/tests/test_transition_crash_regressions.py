"""Same public API expectations before/after the persistence refactor.

Only the fault-injection adapter depends on the internal storage implementation.
On the pre-fix commit: crash recovery and stale-writer tests must fail.
"""
import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from conscience_c_brain import ConscienceCBrain


class CrashRegressions(unittest.TestCase):
    def test_restart_completes_recorded_event_after_snapshot_failure(self):
        with tempfile.TemporaryDirectory() as root:
            brain = ConscienceCBrain.load_or_bootstrap(Path(root))
            def fail(stage):
                if stage == "after_append":
                    raise OSError("simulated interrupted snapshot write")
            if hasattr(brain, "_store"):
                injected = patch.object(brain._store, "_stage", side_effect=fail)
            else:
                injected = patch.object(brain, "_save", side_effect=OSError("snapshot interrupted"))
            with injected, self.assertRaises(OSError):
                brain.imagine("recorded before crash", ["a"], ["b"])
            journal = (Path(root) / "events.jsonl").read_bytes()
            resumed = ConscienceCBrain.load_or_bootstrap(Path(root))
            self.assertEqual(resumed.state["n"], 1)
            self.assertEqual(resumed.state["imaginations"][0]["title"], "recorded before crash")
            self.assertEqual((Path(root) / "events.jsonl").read_bytes(), journal)
            self.assertEqual(len(resumed.ledger.read()), 2)

    def test_interrupted_initialization_does_not_need_a_second_genesis(self):
        with tempfile.TemporaryDirectory() as root:
            if hasattr(ConscienceCBrain(Path(root)), "_store"):
                from conscience_c_brain.transition_store import TransitionStore
                def fail(stage):
                    if stage == "after_append":
                        raise OSError("bootstrap snapshot interrupted")
                injected = patch.object(TransitionStore, "_stage", side_effect=fail)
            else:
                injected = patch.object(ConscienceCBrain, "_save", side_effect=OSError("bootstrap snapshot interrupted"))
            with injected, self.assertRaises(OSError):
                ConscienceCBrain.load_or_bootstrap(Path(root))
            resumed = ConscienceCBrain.load_or_bootstrap(Path(root))
            self.assertEqual(resumed.state["n"], 0)
            self.assertEqual(len(resumed.ledger.read()), 1)
            self.assertEqual(resumed.ledger.read()[0]["event_type"], "BOOTSTRAP_T0")

    def test_stale_instance_cannot_overwrite_newer_state(self):
        with tempfile.TemporaryDirectory() as root:
            first = ConscienceCBrain.load_or_bootstrap(Path(root))
            stale = ConscienceCBrain.load_or_bootstrap(Path(root))
            before_stale = copy.deepcopy(stale.state)
            first.imagine("first writer", ["a"], ["b"])
            journal = (Path(root) / "events.jsonl").read_bytes()
            snapshot = (Path(root) / "state.json").read_bytes()
            with self.assertRaises(ValueError):
                stale.imagine("stale writer", ["c"], ["d"])
            self.assertEqual(stale.state, before_stale)
            self.assertEqual((Path(root) / "events.jsonl").read_bytes(), journal)
            self.assertEqual((Path(root) / "state.json").read_bytes(), snapshot)


if __name__ == "__main__":
    unittest.main(verbosity=2)
