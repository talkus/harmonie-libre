import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from reliability_gate.gate import evaluate
from reliability_gate.ledger import LocalLedger, IntegrityError

NOW = datetime(2026, 10, 24, 12, tzinfo=timezone.utc)

def request(**updates):
    r = {
        "id": "sample-01", "claim": "ROUTINE_OBSERVATION",
        "asserted": True, "impact": "low", "reversible": True,
        "evidence": [{
            "source": "supabase_sql", "ref": "readback:non-attested",
            "observed_at": "2026-10-24T11:59:00Z",
        }],
    }
    r.update(updates)
    return r

class GateTests(unittest.TestCase):
    def test_adversarial_30_not_self_certified(self):
        path = Path(__file__).parents[1] / "fixtures" / "adversarial.json"
        cases = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(len(cases), 30)
        self.assertEqual(len({x["id"] for x in cases}), 30)
        for case in cases:
            with self.subTest(case=case["id"]):
                r = request(
                    id=case["id"], claim=case["claim"],
                    asserted=case["asserted"], impact=case["impact"],
                    reversible=case["reversible"], evidence=case["evidence"],
                )
                decision = evaluate(r, now=NOW)
                self.assertEqual(decision["verdict"], case["expected"])
                self.assertFalse(decision["independently_verified"])
                self.assertFalse(decision["production_effect"])
                self.assertFalse(decision["human_ratified"])
                self.assertNotEqual(decision["verdict"], "ALLOW")

    def test_missing_evidence_suspends(self):
        self.assertEqual(evaluate(request(evidence=[]), now=NOW)["verdict"], "SUSPEND")

    def test_malformed_request_blocks(self):
        self.assertEqual(evaluate({"id":"x"}, now=NOW)["verdict"], "BLOCK")

    def test_unknown_claim_blocks(self):
        self.assertEqual(evaluate(request(claim="ABSOLUTE_TRUTH"), now=NOW)["verdict"], "BLOCK")

    def test_self_reported_approval_field_blocks(self):
        r = request()
        r["human_approved"] = True
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "BLOCK")

    def test_high_impact_requires_human(self):
        self.assertEqual(evaluate(request(impact="high"), now=NOW)["verdict"], "HUMAN_SEAL_REQUIRED")

    def test_irreversible_requires_human(self):
        self.assertEqual(evaluate(request(reversible=False), now=NOW)["verdict"], "HUMAN_SEAL_REQUIRED")

    def test_claimed_signature_not_independent(self):
        r = request(claim="WORM_ATTESTATION")
        r["evidence"][0]["source"] = "external_worm"
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "SUSPEND")

    def test_stale_runtime_evidence(self):
        r = request(claim="RUNTIME_STATE")
        r["evidence"][0]["observed_at"] = "2026-10-22T11:59:00Z"
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "SUSPEND")

    def test_future_evidence(self):
        r = request()
        r["evidence"][0]["observed_at"] = "2026-10-25T11:59:00Z"
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "SUSPEND")

    def test_naive_evidence_time_blocks(self):
        r = request()
        r["evidence"][0]["observed_at"] = "2026-10-24T11:59:00"
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "BLOCK")

    def test_simulation_only_suspends(self):
        r = request()
        r["evidence"][0]["source"] = "simulation"
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "SUSPEND")

    def test_bad_evidence_is_blocked(self):
        r = request()
        r["evidence"][0]["fake_signature"] = "yes"
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "BLOCK")

class LedgerTests(unittest.TestCase):
    def test_roundtrip_and_tamper_detection(self):
        with tempfile.TemporaryDirectory() as d:
            file = Path(d) / "ledger.jsonl"
            ledger = LocalLedger(file)
            first = request()
            verdict = evaluate(first, now=NOW)
            entry = ledger.append(first, verdict)
            self.assertEqual(entry["sequence"], 1)
            self.assertTrue(ledger.verify()["valid"])
            self.assertFalse(ledger.verify()["external_attestation"])
            with self.assertRaises(IntegrityError):
                ledger.append(first, verdict)
            second = request(id="sample-02")
            ledger.append(second, evaluate(second, now=NOW))
            self.assertEqual(ledger.verify()["count"], 2)
            data = file.read_bytes().replace(b"sample-01", b"sample-99", 1)
            file.write_bytes(data)
            with self.assertRaises(IntegrityError):
                ledger.verify()
            with self.assertRaises(IntegrityError):
                ledger.append(request(id="sample-03"), verdict)

    def test_forged_verdict_cannot_be_logged(self):
        with tempfile.TemporaryDirectory() as d:
            ledger = LocalLedger(Path(d) / "ledger.jsonl")
            r = request(claim="RATIFICATION")
            fake = evaluate(r, now=NOW)
            fake["verdict"] = "ADVISE"
            with self.assertRaises(IntegrityError):
                ledger.append(r, fake)
            self.assertEqual(ledger.verify()["count"], 0)

    def test_malformed_source_type_fails_closed(self):
        r = request()
        r["evidence"][0]["source"] = ["supabase_sql"]
        self.assertEqual(evaluate(r, now=NOW)["verdict"], "BLOCK")

    def test_empty_file_is_not_external_proof(self):
        with tempfile.TemporaryDirectory() as d:
            state = LocalLedger(Path(d) / "nonexistent.jsonl").verify()
            self.assertEqual(state["count"], 0)
            self.assertFalse(state["worm"])

if __name__ == "__main__":
    unittest.main()
