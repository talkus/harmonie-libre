import json
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain
from conscience_c_brain.greffier import (
    EVENT, MODEL_ID, build_dossier, main, tenir_greffe, unknown_citations, verify_chain,
)
from conscience_c_brain.ledger import AppendOnlyLedger


class FakeBedrock:
    def __init__(self, text):
        self.text = text
        self.calls = []

    def converse(self, **kwargs):
        self.calls.append(kwargs)
        return {
            "output": {"message": {"role": "assistant", "content": [{"text": self.text}]}},
            "usage": {"inputTokens": 27, "outputTokens": 3},
            "stopReason": "end_turn",
        }


class GreffierTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        b = ConscienceCBrain.load_or_bootstrap(Path(td.name))
        b.imagine("passage", ["a"], ["b"])
        return b

    def test_acte_is_recorded_beside_the_history_never_inside_it(self):
        b = self.make()
        before = (b.root / "events.jsonl").read_text(encoding="utf-8")
        fake = FakeBedrock("#1 ouvre l'histoire. #2 est une imagination.")
        row = tenir_greffe(b.root, fake)
        self.assertEqual((b.root / "events.jsonl").read_text(encoding="utf-8"), before)
        self.assertEqual(row["event_type"], EVENT)
        self.assertEqual(row["payload"]["ledger_head"], b.ledger.head())
        self.assertFalse(row["payload"]["certifie"])
        self.assertEqual(row["payload"]["statut"], "reconstruction_analytique")
        self.assertEqual(fake.calls[0]["modelId"], MODEL_ID)
        AppendOnlyLedger(b.root / "greffe.jsonl", create=False).verify()

    def test_broken_history_stops_the_greffier_before_any_model_call(self):
        b = self.make()
        path = b.root / "events.jsonl"
        rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["timestamp"] = "falsifié"
        path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        fake = FakeBedrock("rien")
        with self.assertRaises(ValueError):
            tenir_greffe(b.root, fake)
        self.assertEqual(fake.calls, [])
        self.assertFalse((b.root / "greffe.jsonl").exists())

    def test_invented_citations_are_named_not_removed(self):
        b = self.make()
        acte = "#1 existe ; #99 n'existe pas."
        row = tenir_greffe(b.root, FakeBedrock(acte))
        self.assertEqual(row["payload"]["citations_inconnues"], [99])
        self.assertEqual(row["payload"]["acte"], acte)

    def test_dossier_carries_raw_events_with_their_hashes(self):
        b = self.make()
        rows = verify_chain(b.root)
        dossier = build_dossier(rows, since_seq=2)
        self.assertEqual(dossier["seq_range"][0], 2)
        self.assertEqual(dossier["events"][0]["event_hash"], rows[1]["event_hash"])
        self.assertEqual(unknown_citations("#1", dossier), [1])

    def test_successive_actes_chain_to_each_other(self):
        b = self.make()
        first = tenir_greffe(b.root, FakeBedrock("#1"))
        second = tenir_greffe(b.root, FakeBedrock("#2"))
        self.assertEqual(second["prev_hash"], first["event_hash"])

    def test_dry_run_and_missing_ledger(self):
        b = self.make()
        self.assertEqual(main(["--root", str(b.root), "--dry-run"]), 0)
        with tempfile.TemporaryDirectory() as empty:
            self.assertEqual(main(["--root", empty, "--dry-run"]), 2)


if __name__ == "__main__":
    unittest.main()
