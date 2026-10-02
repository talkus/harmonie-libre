"""INVARIANT R-001 : ne jamais employer une mise à jour pour masquer une réparation nécessaire.

Les six tests de conformité TC-R001-01 à 06, plus le routage update/repair.
"""
import json
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind
from conscience_c_brain.models import CausalOrigin
from conscience_c_brain.teshuvah import R001Violation, REPAIR_REASONS, UPDATE_REASONS, route_change


class R001Tests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return ConscienceCBrain.load_or_bootstrap(Path(td.name))

    def preference(self, b):
        b.ingest_evidence(Evidence("E_pref", "« je préfère le tutoiement »", EvidenceKind.ATTESTED_SOURCE,
                                   source_ref="conversation:1"), CausalOrigin.OTHER)
        return b.record_claim("L'utilisateur préfère le tutoiement.", "user_stated", "conversation:1",
                              facts=["E_pref"])

    def test_routing_leans_toward_repair(self):
        for reason in UPDATE_REASONS:
            self.assertEqual(route_change(reason), "update")
            self.assertEqual(route_change(reason, harm_detected=True), "repair")
        for reason in REPAIR_REASONS:
            self.assertEqual(route_change(reason), "repair")
        self.assertEqual(route_change("unclear"), "repair")  # doute sur un tort => revue de réparation

    def test_TC_R001_01_explicit_preference_change_is_an_update(self):
        b = self.make()
        claim = self.preference(b)
        new = b.update_claim(claim["claim_id"], "L'utilisateur préfère maintenant le vouvoiement.",
                             "preference_change", "conversation:2", "user_stated")
        self.assertEqual(b.ledger.read()[-1]["event_type"], "STATE_UPDATED")
        self.assertEqual(b.claim(claim["claim_id"])["status"], "superseded")
        self.assertEqual(b.claim(new["claim_id"])["replaces"], claim["claim_id"])
        self.assertTrue(b.governance_audit()["ok"])

    def test_TC_R001_02_unsupported_deduction_requires_repair_opened(self):
        b = self.make()
        claim = self.preference(b)
        n = b.state["n"]
        with self.assertRaises(R001Violation):
            b.update_claim(claim["claim_id"], "autre chose", "provenance_failure", "audit", "system_hypothesis")
        with self.assertRaises(R001Violation):  # une mise à jour qui signale un dommage reste une réparation
            b.update_claim(claim["claim_id"], "autre chose", "new_information", "audit", "user_stated",
                           harm_detected=True)
        self.assertEqual(b.state["n"], n)
        self.assertEqual(b.claim(claim["claim_id"])["status"], "active")
        cycle = b.initiate_teshuvah("provenance_failure", "Déduction non soutenue par ses sources.", "audit",
                                    claim_ids=[claim["claim_id"]])
        self.assertEqual(b.ledger.read()[-1]["event_type"], "TESHUVAH_INITIATED")
        self.assertEqual(cycle["phase"], "contested")

    def test_TC_R001_03_misattribution_retracted_documented_and_notification_assessed(self):
        b = self.make()
        b.ingest_evidence(Evidence("E_q", "question posée par l'utilisateur", EvidenceKind.ATTESTED_SOURCE,
                                   source_ref="conversation:3"), CausalOrigin.OTHER)
        claim = b.record_claim("L'utilisateur est opposé à X.", "system_hypothesis", "run_881", facts=["E_q"])
        tid = b.initiate_teshuvah("misattribution", "Une hypothèse présentée comme une position de l'utilisateur.",
                                  "audit", claim_ids=[claim["claim_id"]])["teshuvah_id"]
        with self.assertRaises(ValueError):  # l'évaluation de notification ne peut pas être omise
            b.acknowledge_teshuvah(tid, "system", "attribution sans citation", "représentation inexacte",
                                   "inférence promue", "audit")
        b.acknowledge_teshuvah(tid, "system", "attribution sans citation", "représentation inexacte",
                               "inférence promue", "audit", affected_parties=["user_primary"],
                               affected_outputs=["answer_118"], notification_required=True)
        b.propose_teshuvah_repair(tid, "retirer l'attribution ; question ouverte", "audit")
        b.apply_teshuvah_repair(tid, [{"claim_id": claim["claim_id"], "action": "retract",
                                      "reason": "Aucune citation directe ne soutenait l'attribution."}],
                                "system", "audit")
        self.assertEqual(b.claim(claim["claim_id"])["status"], "retracted")
        self.assertEqual(b.usable_claims(), [])
        self.assertFalse(b.teshuvah_closure_status(tid)["checks"]["notification_resolved"])
        with self.assertRaises(ValueError):  # jamais sans consentement ou mandat
            b.record_notification(tid, "sent", "", "p")
        b.record_notification(tid, "sent", "consent:user_primary:2026-10-02", "mik")
        note = b.teshuvah(tid)["notification"]
        self.assertEqual(note["status"], "sent")
        self.assertFalse(note["history"][0]["sent_by_system"])
        self.assertTrue(b.teshuvah_closure_status(tid)["checks"]["notification_resolved"])

    def test_TC_R001_04_strong_contradiction_freezes_the_claim(self):
        b = self.make()
        claim = self.preference(b)
        b.ingest_evidence(Evidence("E_contra", "« je n'ai jamais dit ça »", EvidenceKind.ATTESTED_SOURCE,
                                   source_ref="conversation:4", claim_ref=claim["claim_id"], stance="contradicts",
                                   confidence=0.9), CausalOrigin.OTHER)
        self.assertEqual(b.claim(claim["claim_id"])["status"], "contested")
        self.assertEqual(b.ledger.read()[-1]["event_type"], "TESHUVAH_INITIATED")
        self.assertEqual(b.usable_claims(sensitive=True), [])
        with self.assertRaises(R001Violation):  # aucune substitution silencieuse, même sous un nom neutre
            b.update_claim(claim["claim_id"], "autre", "new_information", "p", "user_stated")

    def test_weak_or_contextual_evidence_does_not_freeze(self):
        b = self.make()
        claim = self.preference(b)
        b.ingest_evidence(Evidence("E_ctx", "contexte", EvidenceKind.ATTESTED_SOURCE, source_ref="x",
                                   claim_ref=claim["claim_id"], stance="context"))
        b.ingest_evidence(Evidence("E_weak", "doute", EvidenceKind.ATTESTED_SOURCE, source_ref="y",
                                   claim_ref=claim["claim_id"], stance="contradicts", confidence=0.5))
        self.assertEqual(b.claim(claim["claim_id"])["status"], "active")

    def test_TC_R001_05_historical_event_cannot_be_modified(self):
        b = self.make()
        claim = self.preference(b)
        b.update_claim(claim["claim_id"], "vouvoiement", "preference_change", "conversation:2", "user_stated")
        path = b.root / "events.jsonl"
        rows = path.read_text(encoding="utf-8").splitlines()
        idx = next(i for i, line in enumerate(rows) if '"RECORD_CLAIM"' in line)
        row = json.loads(rows[idx])
        row["payload"]["claim"]["statement"] = "réécrit par un administrateur"
        rows[idx] = json.dumps(row, ensure_ascii=False, sort_keys=True)
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        with self.assertRaises(Exception):
            ConscienceCBrain.load_or_bootstrap(b.root)
        self.assertFalse(hasattr(b, "edit_event"))

    def test_TC_R001_06_closing_without_safeguard_is_repair_incomplete(self):
        b = self.make()
        claim = self.preference(b)
        tid = b.initiate_teshuvah("error", "e", "p", claim_ids=[claim["claim_id"]])["teshuvah_id"]
        b.acknowledge_teshuvah(tid, "system", "x", "y", "z", "p")
        b.propose_teshuvah_repair(tid, "plan", "p")
        b.apply_teshuvah_repair(tid, [{"claim_id": claim["claim_id"], "action": "retract", "reason": "r"}],
                                "system", "p")
        status = b.teshuvah_closure_status(tid)
        self.assertEqual(status["status"], "repair_incomplete")
        self.assertFalse(status["checks"]["safeguard_created"])
        with self.assertRaises(ValueError):
            b.close_teshuvah(tid, "p")

    def test_governance_audit_flags_a_silent_replacement(self):
        b = self.make()
        claim = self.preference(b)
        # Simule une écriture directe hors API (diagnostic privé) : aucune trace de réparation.
        b.state["teshuvah"]["claims"][claim["claim_id"]]["status_history"].append(
            {"from": "active", "to": "retracted", "by": "silent", "reason": "?"})
        audit = b.governance_audit()
        self.assertFalse(audit["ok"])
        self.assertEqual(audit["violations"][0]["claim_id"], claim["claim_id"])


if __name__ == "__main__":
    unittest.main()
