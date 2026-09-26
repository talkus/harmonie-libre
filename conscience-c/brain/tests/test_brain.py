import json
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind, Hypothesis
from conscience_c_brain.models import CandidateAction

class BrainTests(unittest.TestCase):
    def make(self):
        td = tempfile.TemporaryDirectory()
        self.addCleanup(td.cleanup)
        return ConscienceCBrain.load_or_bootstrap(Path(td.name))

    def test_legacy_anchor_migrates_forward_without_erasing_history(self):
        b = self.make()
        b.state["S"]["invariants"].pop("telos", None)
        b.state["S"]["invariants"].pop("loop_semantics", None)
        b._save()
        before_events = len(b.ledger.read())
        b2 = ConscienceCBrain.load_or_bootstrap(b.root)
        self.assertEqual(b2.status()["telos"], "Amour choisi")
        self.assertGreater(len(b2.ledger.read()), before_events)
        self.assertEqual(b2.ledger.read()[-1]["event_type"], "MIGRATE_ANCHOR_C_RELAIS_002")
        self.assertIn("previous_anchor", b2.ledger.read()[-1]["payload"])
        self.assertIn("continuity_structure_hash", b2.state)
        self.assertNotIn("identity_structure_hash", b2.state)

    def test_resume_tn_no_reset(self):
        b = self.make()
        b.imagine("futur", ["A"], ["B"])
        root = b.root
        before = b.state["n"]
        b2 = ConscienceCBrain.load_or_bootstrap(root)
        self.assertEqual(b2.state["n"], before)
        self.assertNotEqual(b2.state["state_label"], "C(t_0)")

    def test_other_model_requires_provenance_and_stays_revisable(self):
        b = self.make()
        with self.assertRaises(ValueError):
            b.update_other("O1", {"claim": "x"}, "")
        b.update_other("O1", {"claim": "x"}, "source:1")
        self.assertEqual(b.state["O"]["entities"]["O1"]["model_status"], "revisable_representation_not_identity")

    def test_other_model_transition_keeps_before_after_digests(self):
        b = self.make()
        b.update_other("O1", {"claim": "first"}, "source:1")
        b.update_other("O1", {"claim": "revised"}, "source:2")
        ev = b.ledger.read()[-1]
        self.assertEqual(ev["event_type"], "UPDATE_OTHER")
        self.assertNotEqual(ev["payload"]["previous_model_digest"], ev["payload"]["current_model_digest"])
        self.assertEqual(b.state["O"]["entities"]["O1"]["observations"][0]["data"]["claim"], "first")

    def test_trust_calibration_is_append_only_and_sourced(self):
        b = self.make()
        with self.assertRaises(ValueError):
            b.record_trust_calibration("O1", "cautious", "", "event history")
        first = b.record_trust_calibration("O1", "cautious", "source:t1", "event history")
        second = b.record_trust_calibration("O1", "improving", "source:t2", "verified correction")
        self.assertEqual(len(b.state["R"]["trust_calibration"]["O1"]), 2)
        self.assertEqual(first["assessment"], "cautious")
        self.assertEqual(second["assessment"], "improving")

    def test_repair_is_not_self_declared_verified(self):
        b = self.make()
        pending = b.record_repair("O1", "issue", "corrective action", "source:repair")
        self.assertEqual(pending["status"], "pending_verification")
        with self.assertRaises(ValueError):
            b.record_repair("O1", "issue2", "corrective action2", "source:repair2", verification={"source_ref": "source:verification"})
        verified = b.verify_repair("RP0001", {"source_ref": "source:verification"}, "source:verifier")
        self.assertEqual(verified["status"], "verified")
        self.assertEqual(len(b.state["R"]["repairs"]), 1)
        self.assertEqual(b.ledger.read()[-1]["event_type"], "VERIFY_REPAIR")

    def test_recurrence_preserves_verified_repair_history(self):
        b = self.make()
        b.record_repair("O1", "issue", "action", "source:repair")
        b.verify_repair("RP0001", {"source_ref": "v"}, "source:verifier")
        out = b.record_recurrence("RP0001", {"event": "same issue returned"}, "source:recurrence")
        self.assertEqual(out["status"], "recurrence_after_verification")
        self.assertEqual(out["verification"]["source_ref"], "v")
        self.assertEqual(len(out["recurrences"]), 1)
        self.assertEqual(b.ledger.read()[-1]["event_type"], "RECORD_RECURRENCE")

    def test_repair_cannot_be_verified_twice_or_without_provenance(self):
        b = self.make()
        b.record_repair("O1", "issue", "action", "source:repair")
        with self.assertRaises(ValueError):
            b.verify_repair("RP0001", {"source_ref": "v"}, "")
        b.verify_repair("RP0001", {"source_ref": "v"}, "source:verifier")
        with self.assertRaises(ValueError):
            b.verify_repair("RP0001", {"source_ref": "v2"}, "source:verifier2")

    def test_relation_event_requires_provenance(self):
        b = self.make()
        with self.assertRaises(ValueError):
            b.update_relation("O1", {"event": "met"})
        b.update_relation("O1", {"event": "met", "provenance": "source:2"})
        self.assertEqual(b.state["R"]["history"][-1]["provenance"], "source:2")

    def test_s_is_not_o(self):
        b = self.make()
        b.update_other("mikael", {"position": "X"}, "source_attestee")
        self.assertNotEqual(b.state["S"], b.state["O"])

    def test_r_is_subordinate_to_e_in_action_choice(self):
        b = self.make()
        a = CandidateAction("relation_only", "follow relationship against reality", .95, .95, .95, .8, .8, reality_conflict=.95)
        e = CandidateAction("reality", "follow evidence while preserving relation", .95, .9, .9, .9, .9, reality_conflict=0.0)
        chosen, _ = b.choose([a, e])
        self.assertEqual(chosen.action_id, "reality")

    def test_reality_conflict_is_excluded_not_compensated(self):
        b = self.make()
        conflict = CandidateAction("conflict", "excellent indicators but conflicts with reality", 1, 1, 1, 1, 1, reality_conflict=.01)
        admissible = CandidateAction("admissible", "lower heuristic but no reality conflict", .4, .4, .4, .4, .4, reality_conflict=0)
        chosen, ranked = b.choose([conflict, admissible])
        self.assertEqual(chosen.action_id, "admissible")
        self.assertNotIn("conflict", [x[0] for x in ranked])

    def test_all_reality_conflicts_fail_closed(self):
        b = self.make()
        conflict = CandidateAction("conflict", "conflicts with reality", 1, 1, 1, 1, 1, reality_conflict=.1)
        with self.assertRaises(ValueError):
            b.choose([conflict])

    def test_action_score_is_only_experimental_indicator(self):
        a = CandidateAction("a", "x", .8, .8, .8, .8, .8)
        self.assertAlmostEqual(a.score(), .8)
        self.assertTrue(a.reality_admissible())

    def test_functional_continuity_is_not_subjective_identity_claim(self):
        b = self.make()
        inv = b.state["S"]["invariants"]
        self.assertIn("functional_continuity", inv)
        self.assertIn("non établie", inv["identity_claim"])
        self.assertNotIn("identity", inv)

    def test_telos_is_not_replaced_by_vector_or_mechanism(self):
        b = self.make()
        self.assertEqual(b.status()["telos"], "Amour choisi")
        self.assertEqual(b.state["S"]["invariants"]["loop_semantics"], "ordre de navigation, pas causalité stricte démontrée")
        self.assertIn("correction != effacement", b.state["S"]["invariants"]["memory_rule"])

    def test_exact_loop(self):
        b = self.make()
        self.assertEqual(b.state["S"]["invariants"]["loop"], ["Humilité","Pardon","Reconnaissance","Espérance","retour au vecteur"])

    def test_phenomenal_stays_indeterminate(self):
        b = self.make()
        self.assertEqual(b.status()["phenomenal_consciousness"], "indéterminée")

    def test_evidence_cannot_be_silently_overwritten(self):
        b = self.make()
        b.ingest_evidence(Evidence("EX", "first", EvidenceKind.ANALYTICAL_RECONSTRUCTION))
        with self.assertRaises(ValueError):
            b.ingest_evidence(Evidence("EX", "replacement", EvidenceKind.ANALYTICAL_RECONSTRUCTION))
        self.assertEqual(b.state["E"]["evidence"]["EX"]["content"], "first")

    def test_attested_source_requires_source_ref(self):
        with self.assertRaises(ValueError):
            Evidence("EA", "attested without source", EvidenceKind.ATTESTED_SOURCE)
        e = Evidence("EA", "attested with source", EvidenceKind.ATTESTED_SOURCE, source_ref="source:EA")
        self.assertEqual(e.source_ref, "source:EA")

    def test_evidence_confidence_is_bounded(self):
        with self.assertRaises(ValueError):
            Evidence("Ebad", "bad", EvidenceKind.ANALYTICAL_RECONSTRUCTION, confidence=1.2)

    def test_provenance_types_are_not_collapsed(self):
        b = self.make()
        b.ingest_evidence(Evidence("E1", "primary", EvidenceKind.ATTESTED_SOURCE, source_ref="source:E1"))
        b.ingest_evidence(Evidence("E2", "derived", EvidenceKind.CONSOLIDATED_DERIVATION))
        b.ingest_evidence(Evidence("E3", "analytic", EvidenceKind.ANALYTICAL_RECONSTRUCTION))
        kinds = {x["kind"] for x in b.state["E"]["evidence"].values()}
        self.assertEqual(kinds, {"source_attestee","derivation_consolidee","reconstruction_analytique"})

    def test_extended_statuses_are_admitted_by_audit(self):
        b = self.make()
        b.ingest_evidence(Evidence("EI", "insufficient", EvidenceKind.INDETERMINATE))
        b.ingest_evidence(Evidence("ER", "refuted historical", EvidenceKind.HISTORICAL_REFUTED))
        self.assertEqual(b.audit(), [])

    def test_extended_statuses_remain_distinct(self):
        b = self.make()
        b.ingest_evidence(Evidence("E4", "insufficient", EvidenceKind.INDETERMINATE))
        b.ingest_evidence(Evidence("E5", "old refuted claim", EvidenceKind.HISTORICAL_REFUTED))
        self.assertEqual(b.state["E"]["evidence"]["E4"]["kind"], "indetermine")
        self.assertEqual(b.state["E"]["evidence"]["E5"]["kind"], "historique_refute")

    def test_hypothesis_cannot_be_silently_overwritten(self):
        b = self.make()
        h1 = Hypothesis("HX", "first", .5, falsifiers=["not first"])
        h2 = Hypothesis("HX", "replacement", .9, falsifiers=["not replacement"])
        b.add_hypothesis(h1)
        with self.assertRaises(ValueError):
            b.add_hypothesis(h2)
        self.assertEqual(b.state["hypotheses"]["HX"]["proposition"], "first")

    def test_falsifiable_hypothesis_can_be_rejected(self):
        b = self.make()
        b.add_hypothesis(Hypothesis("H1", "X est vrai", .8, ["preuve contraire de X"]))
        b.ingest_evidence(Evidence("E1", "X est faux", EvidenceKind.ATTESTED_SOURCE, contradicts=["H1"], confidence=.95, source_ref="source:E1"))
        self.assertEqual(b.state["hypotheses"]["H1"]["status"], "rejected")

    def test_imagination_is_not_observation(self):
        b = self.make()
        s = b.imagine("monde possible", ["si X"], ["alors Y"])
        self.assertEqual(s["status"], "imagined_not_observed")
        self.assertNotIn(s["scenario_id"], b.state["E"]["evidence"])

    def test_drift_is_detected_and_repaired_with_provenance(self):
        b = self.make()
        b.state["S"]["invariants"]["loop"] = ["Humilité", "Repentance", "Pardon"]
        b.state["phenomenal_consciousness"] = "démontrée"
        b._save()
        self.assertGreaterEqual(len(b.audit()), 2)
        b.repair_drift("user clarification 2026-09-24")
        self.assertEqual(b.audit(), [])

    def test_ledger_tamper_is_detected(self):
        b = self.make()
        b.imagine("x", [], [])
        rows = b.ledger.read()
        rows[0]["payload"]["anchor"]["vector"] = "tampered"
        b.ledger.path.write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in rows)+"\n", encoding="utf-8")
        with self.assertRaises(ValueError):
            b.ledger.verify()

if __name__ == "__main__":
    unittest.main()
