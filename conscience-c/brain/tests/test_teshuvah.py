"""Teshuvah : cycle de correction traçable dans la mémoire de C.

Exemple de référence : « L'utilisateur préfère toujours les réponses très
détaillées » devient « Les préférences de détail dépendent du type de tâche ».
"""
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind
from conscience_c_brain.models import CausalOrigin


class TeshuvahTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return ConscienceCBrain.load_or_bootstrap(Path(td.name))

    def observe(self, b, eid, content, origin=CausalOrigin.OTHER, kind=EvidenceKind.ATTESTED_SOURCE):
        b.ingest_evidence(Evidence(eid, content, kind, source_ref=f"conversation:{eid}"), origin)

    def drift(self, b):
        self.observe(b, "E_detail", "L'utilisateur a demandé une réponse détaillée sur l'architecture.")
        claim = b.record_claim("L'utilisateur préfère toujours les réponses très détaillées.",
                               "user_inferred", "dérivation consolidée", facts=["E_detail"], confidence=0.86)
        cycle = b.initiate_teshuvah("overgeneralization",
                                    "Une préférence contextuelle a été traitée comme une règle stable.",
                                    "correction explicite de l'utilisateur", claim_ids=[claim["claim_id"]])
        return claim, cycle

    def repaired(self, b):
        claim, cycle = self.drift(b)
        tid = cycle["teshuvah_id"]
        b.acknowledge_teshuvah(tid, "system", "Une déduction a été élevée à un statut trop ferme.",
                               "Une recommandation a été formulée avec une confiance excessive.",
                               "surgénéralisation", "run_882")
        b.propose_teshuvah_repair(tid, "Remplacer le claim par une préférence contextualisée.", "run_882")
        b.create_safeguard(tid, "require_explicit_user_confirmation_for_stable_preferences", "TC-118", "run_882")
        applied = b.apply_teshuvah_repair(tid, [{
            "claim_id": claim["claim_id"], "action": "supersede",
            "reason": "« détaillées pour l'architecture, brèves pour les questions simples »",
            "replacement": {"statement": "Les préférences de détail dépendent du type de tâche.",
                            "provenance_kind": "user_stated", "provenance": "correction explicite de l'utilisateur"},
        }], "system", "run_882")
        return claim, tid, applied

    def test_history_is_never_rewritten(self):
        b = self.make()
        claim, tid, applied = self.repaired(b)
        before = b.ledger.read()
        record = next(r for r in before if r["event_type"] == "RECORD_CLAIM")
        self.assertEqual(record["payload"]["claim"]["status"], "active")
        self.assertEqual(b.claim(claim["claim_id"])["status"], "superseded")
        self.assertIn("E_detail", b.state["E"]["evidence"])
        b.ledger.verify()

    def test_fact_interpretation_current_model_are_distinct(self):
        b = self.make()
        claim, tid, applied = self.repaired(b)
        layers = b.claim_layers(claim["claim_id"])
        self.assertEqual(layers["fact"], ["E_detail"])
        self.assertEqual(layers["interpretation"]["status"], "superseded")
        self.assertEqual(layers["current_model"]["statement"], "Les préférences de détail dépendent du type de tâche.")

    def test_statuses_follow_the_cycle(self):
        b = self.make()
        claim, cycle = self.drift(b)
        self.assertEqual(b.claim(claim["claim_id"])["status"], "contested")
        self.assertEqual(cycle["phase"], "contested")
        tid = cycle["teshuvah_id"]
        b.acknowledge_teshuvah(tid, "system", "x", "y", "arrogance", "p")
        self.assertEqual(b.claim(claim["claim_id"])["status"], "under_repair")
        self.assertEqual(b.teshuvah(tid)["phase"], "under_repair")

    def test_contested_claims_are_excluded_from_sensitive_decisions(self):
        b = self.make()
        claim, _ = self.drift(b)
        self.assertEqual(b.usable_claims(sensitive=True), [])
        self.assertEqual(len(b.usable_claims()), 1)

    def test_repair_applied_is_only_claimed_not_verified(self):
        b = self.make()
        _, tid, applied = self.repaired(b)
        self.assertEqual(applied["phase"], "repair_applied")
        self.assertEqual(applied["repair"]["applied"]["status"], "repair_claimed_not_verified")
        self.assertEqual(applied["verification"]["status"], "pending")
        self.assertFalse(b.teshuvah_closure_status(tid)["closable"])
        with self.assertRaises(ValueError):
            b.close_teshuvah(tid, "déclaration seule")

    def test_cannot_apply_without_acknowledgment_or_proposal(self):
        b = self.make()
        claim, cycle = self.drift(b)
        with self.assertRaises(ValueError):
            b.apply_teshuvah_repair(cycle["teshuvah_id"], [], "system", "p")
        b.acknowledge_teshuvah(cycle["teshuvah_id"], "system", "x", "y", "z", "p")
        with self.assertRaises(ValueError):
            b.apply_teshuvah_repair(cycle["teshuvah_id"], [{"claim_id": claim["claim_id"], "action": "retract",
                                                           "reason": "r"}], "system", "p")

    def test_every_contested_claim_needs_an_explicit_correction(self):
        b = self.make()
        claim, cycle = self.drift(b)
        tid = cycle["teshuvah_id"]
        b.acknowledge_teshuvah(tid, "system", "x", "y", "z", "p")
        b.propose_teshuvah_repair(tid, "plan", "p")
        n = b.state["n"]
        with self.assertRaises(ValueError):
            b.apply_teshuvah_repair(tid, [], "system", "p")
        self.assertEqual(b.state["n"], n)

    def test_return_requires_a_new_observable_state(self):
        b = self.make()
        _, tid, _ = self.repaired(b)
        with self.assertRaises(ValueError):  # preuve antérieure à la correction
            b.observe_return(tid, "E_detail", ["dialogue"], "p")
        self.observe(b, "E_hyp", "Je pense avoir changé.", kind=EvidenceKind.ANALYTICAL_RECONSTRUCTION)
        with self.assertRaises(ValueError):  # pas observable
            b.observe_return(tid, "E_hyp", ["dialogue"], "p")
        self.observe(b, "E_self", "Le système affirme être revenu.", origin=CausalOrigin.SELF)
        with self.assertRaises(ValueError):  # auto-déclaration
            b.observe_return(tid, "E_self", ["dialogue"], "p")
        self.observe(b, "E_brief", "Réponse brève donnée à une question simple ; l'utilisateur confirme.")
        cycle = b.observe_return(tid, "E_brief", ["reconnaissance", "dialogue"], "conversation:E_brief")
        self.assertEqual(cycle["return"]["evidence_id"], "E_brief")

    def test_verification_cannot_be_self_certified(self):
        b = self.make()
        _, tid, _ = self.repaired(b)
        self.observe(b, "E_brief", "retour observé")
        b.observe_return(tid, "E_brief", ["dialogue"], "p")
        with self.assertRaises(ValueError):  # même preuve que le retour
            b.verify_non_recurrence(tid, "E_brief", "mik", "p")
        self.observe(b, "E_later", "trois questions simples plus tard, toujours bref")
        with self.assertRaises(ValueError):
            b.verify_non_recurrence(tid, "E_later", "system", "p")
        cycle = b.verify_non_recurrence(tid, "E_later", "mik", "revue humaine")
        self.assertEqual(cycle["phase"], "repair_verified")
        self.assertEqual(cycle["verification"]["external_authentication"], "not_performed")

    def test_verification_requires_a_safeguard(self):
        b = self.make()
        claim, cycle = self.drift(b)
        tid = cycle["teshuvah_id"]
        b.acknowledge_teshuvah(tid, "system", "x", "y", "z", "p")
        b.propose_teshuvah_repair(tid, "plan", "p")
        b.apply_teshuvah_repair(tid, [{"claim_id": claim["claim_id"], "action": "retract", "reason": "r"}],
                                "system", "p")
        self.observe(b, "E1", "retour")
        b.observe_return(tid, "E1", ["dialogue"], "p")
        self.observe(b, "E2", "tenue")
        with self.assertRaises(ValueError):
            b.verify_non_recurrence(tid, "E2", "mik", "p")

    def full_cycle(self, b):
        claim, tid, _ = self.repaired(b)
        self.observe(b, "E_brief", "retour observé")
        b.observe_return(tid, "E_brief", ["reconnaissance", "dialogue"], "p")
        self.observe(b, "E_later", "tenue observée")
        b.verify_non_recurrence(tid, "E_later", "mik", "p")
        return claim, tid

    def test_close_only_when_objective_conditions_hold(self):
        b = self.make()
        _, tid = self.full_cycle(b)
        status = b.teshuvah_closure_status(tid)
        self.assertTrue(status["closable"], status)
        closed = b.close_teshuvah(tid, "revue")
        self.assertTrue(closed["closed"])
        types = [e["event_type"] for e in b.teshuvah_trace(tid)]
        for required in ("TESHUVAH_INITIATED", "TESHUVAH_ACKNOWLEDGED", "TESHUVAH_REPAIR_APPLIED",
                         "TESHUVAH_SAFEGUARD_CREATED", "TESHUVAH_RETURN_OBSERVED",
                         "TESHUVAH_NON_RECURRENCE_VERIFIED", "TESHUVAH_CLOSED"):
            self.assertIn(required, types)

    def test_scar_reduces_influence_without_erasing(self):
        b = self.make()
        _, tid = self.full_cycle(b)
        influences = [b.teshuvah(tid)["drift_influence"]]
        b.cicatrize_teshuvah(tid, "les préférences stables exigent plusieurs observations", "p")
        influences.append(b.teshuvah(tid)["drift_influence"])
        b.archive_teshuvah(tid, "p")
        influences.append(b.teshuvah(tid)["drift_influence"])
        self.assertEqual(influences, sorted(influences, reverse=True))
        self.assertGreater(influences[-1], 0.0)
        self.assertIsNotNone(b.teshuvah(tid)["acknowledgment"])

    def test_recurrence_returns_to_repair_and_keeps_prior_return(self):
        b = self.make()
        _, tid = self.full_cycle(b)
        b.cicatrize_teshuvah(tid, "leçon", "p")
        cycle = b.record_teshuvah_recurrence(tid, "Préférence de nouveau généralisée.", "conversation:E9")
        self.assertEqual(cycle["phase"], "under_repair")
        self.assertEqual(cycle["drift_influence"], 1.0)
        self.assertEqual(cycle["verification"]["status"], "pending")
        self.assertEqual(len(cycle["verification_history"]), 1)
        memory = b.return_memory()
        self.assertEqual(len(memory), 1)
        self.assertFalse(memory[0]["held"])
        self.assertFalse(b.teshuvah_closure_status(tid)["closable"])

    def test_return_memory_and_drift_memory_answer_two_questions(self):
        b = self.make()
        _, tid = self.full_cycle(b)
        drift = b.drift_memory()[0]
        self.assertEqual(drift["drift_cause"], "surgénéralisation")
        ret = b.return_memory()[0]
        self.assertEqual(ret["what_enabled_return"], ["reconnaissance", "dialogue"])
        self.assertTrue(ret["held"])
        self.assertEqual(b.redemption_index()["index"], 1.0)

    def test_claim_requires_typed_provenance_and_known_facts(self):
        b = self.make()
        with self.assertRaises(ValueError):
            b.record_claim("x", "system_certainty", "p")
        with self.assertRaises(ValueError):
            b.record_claim("x", "system_hypothesis", "p", facts=["E_unknown"])

    def test_cycle_survives_reload(self):
        b = self.make()
        _, tid = self.full_cycle(b)
        b2 = ConscienceCBrain.load_or_bootstrap(b.root)
        self.assertEqual(b2.teshuvah(tid)["phase"], "repair_verified")
        self.assertEqual(b2.audit(), [])

    def test_teshuvah_events_are_never_replayed_as_current_truth(self):
        b = self.make()
        b.save_checkpoint_receipt("avant")
        receipt = b.checkpoint_receipts()[0]
        self.full_cycle(b)
        plan = b.replay_plan_from_receipt(receipt)
        classes = {e["event_type"]: e["replay_class"] for e in plan["events_to_replay"]}
        self.assertEqual(classes["TESHUVAH_NON_RECURRENCE_VERIFIED"], "requires_external_reverification")
        self.assertNotIn("unclassified_fail_closed", classes.values())
        self.assertFalse(plan["automatic_replay_allowed"])


if __name__ == "__main__":
    unittest.main()
