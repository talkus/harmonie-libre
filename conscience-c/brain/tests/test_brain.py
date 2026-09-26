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

    def test_transition_report_verification_detects_chain_tamper(self):
        b = self.make()
        start = b.state["n"]
        b.imagine("one", ["a"], ["b"])
        b.imagine("two", ["c"], ["d"])
        report = b.transition_report(start)
        self.assertTrue(b.verify_transition_report(report))
        report["events"][1]["prev_hash"] = "tampered"
        self.assertFalse(b.verify_transition_report(report))

    def test_resume_from_receipt_never_rolls_current_state_backward(self):
        b = self.make()
        b.imagine("before receipt", ["a"], ["b"])
        receipt = b.save_checkpoint_receipt("anchor")
        captured = receipt["state"]
        b.imagine("after receipt", ["c"], ["d"])
        current_before = b.state["state_label"]
        plan = b.resume_from_receipt(b.checkpoint_receipts()[0])
        self.assertEqual(plan["captured_state"], captured)
        self.assertEqual(plan["current_state"], current_before)
        self.assertTrue(plan["requires_forward_replay"])
        self.assertEqual(b.state["state_label"], current_before)

    def test_invalid_receipt_cannot_be_resume_anchor(self):
        b = self.make()
        b.imagine("x", ["a"], ["b"])
        b.save_checkpoint_receipt("anchor")
        receipt = b.checkpoint_receipts()[0]
        receipt["checkpoint"]["telos"] = "tampered"
        with self.assertRaises(ValueError):
            b.resume_from_receipt(receipt)

    def test_explicit_checkpoint_receipt_preserves_full_historical_projection(self):
        b = self.make()
        b.imagine("one", ["a"], ["b"])
        captured_state = b.state["state_label"]
        receipt = b.save_checkpoint_receipt("milestone")
        self.assertEqual(receipt["state"], captured_state)
        self.assertNotEqual(receipt["post_receipt_state"], captured_state)
        self.assertEqual(receipt["checkpoint"]["telos"], "Amour choisi")
        self.assertEqual(receipt["ledger_boundary"], receipt["checkpoint"]["ledger_head"])
        self.assertTrue(receipt["receipt_event_hash"])
        stored = b.checkpoint_receipts()[0]
        self.assertEqual(stored["checkpoint_hash"], receipt["checkpoint_hash"])
        self.assertTrue(b.verify_checkpoint_receipt(stored))
        b.imagine("later", ["c"], ["d"])
        historical = b.checkpoint_receipts()[0]
        self.assertEqual(historical["checkpoint"]["state"], captured_state)
        self.assertTrue(b.verify_checkpoint_receipt(historical))
        historical["checkpoint"]["telos"] = "tampered"
        self.assertFalse(b.verify_checkpoint_receipt(historical))

    def test_historical_checkpoint_boundary_is_not_invented_snapshot(self):
        b = self.make()
        b.imagine("one", ["a"], ["b"])
        b.imagine("two", ["c"], ["d"])
        old = b.checkpoint_at(1)
        self.assertEqual(old["state"], "C(t_1)")
        self.assertEqual(old["reconstruction_status"], "documentary_boundary_not_full_snapshot")
        self.assertNotIn("telos", old)
        self.assertEqual(old["event_hash"], b.ledger.read()[1]["event_hash"])

    def test_checkpoint_at_current_returns_current_projection(self):
        b = self.make()
        b.imagine("one", ["a"], ["b"])
        self.assertEqual(b.checkpoint_at(b.state["n"]), b.current_checkpoint())
        with self.assertRaises(ValueError):
            b.checkpoint_at(b.state["n"] + 1)

    def test_transition_report_connects_checkpoint_to_history(self):
        b = self.make()
        start = b.state["n"]
        b.imagine("one", ["a"], ["b"])
        b.imagine("two", ["c"], ["d"])
        report = b.transition_report(start)
        self.assertEqual(report["from_n"], start)
        self.assertEqual(report["to_n"], b.state["n"])
        self.assertEqual([e["event_type"] for e in report["events"]], ["IMAGINE_COUNTERFACTUAL", "IMAGINE_COUNTERFACTUAL"])
        self.assertEqual(report["ledger_head"], b.ledger.head())
        self.assertEqual(report["checkpoint_hash"], b.checkpoint_manifest()["checkpoint_hash"])

    def test_checkpoint_manifest_is_verifiable_and_tamper_evident(self):
        b = self.make()
        manifest = b.checkpoint_manifest()
        self.assertTrue(b.verify_checkpoint_manifest(manifest))
        manifest["checkpoint"]["telos"] = "tampered"
        self.assertFalse(b.verify_checkpoint_manifest(manifest))

    def test_old_checkpoint_manifest_stops_matching_new_ledger_head(self):
        b = self.make()
        old = b.checkpoint_manifest()
        b.imagine("future", ["a"], ["b"])
        self.assertFalse(b.verify_checkpoint_manifest(old))
        self.assertTrue(b.verify_checkpoint_manifest(b.checkpoint_manifest()))

    def test_checkpoint_is_current_projection_not_history_replacement(self):
        b = self.make()
        b.add_hypothesis(Hypothesis("Hopen", "open", .5, falsifiers=["not open"]))
        b.add_hypothesis(Hypothesis("Hreject", "reject me", .8, falsifiers=["not reject"]))
        b.ingest_evidence(Evidence("Ereject", "contrary", EvidenceKind.ATTESTED_SOURCE, contradicts=["Hreject"], confidence=1.0, source_ref="source:Ereject"))
        b.record_repair("O1", "issue", "action", "source:repair")
        cp = b.current_checkpoint()
        self.assertEqual(cp["ledger_head"], b.ledger.head())
        self.assertEqual([h["hypothesis_id"] for h in cp["open_hypotheses"]], ["Hopen"])
        self.assertEqual(cp["active_repairs"][0]["repair_id"], "RP0001")
        self.assertGreater(len(b.ledger.read()), 0)
        cp["loop"][0] = "tampered"
        self.assertEqual(b.current_checkpoint()["loop"][0], "Humilité")

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

    def test_current_other_model_is_projection_not_history(self):
        b = self.make()
        b.update_other("O1", {"claim": "first"}, "source:o1")
        b.update_other("O1", {"claim": "revised"}, "source:o2")
        current = b.current_other_model("O1")
        history = b.other_observation_history("O1")
        self.assertEqual(current["model"]["claim"], "revised")
        self.assertEqual([x["data"]["claim"] for x in history], ["first", "revised"])
        current["model"]["claim"] = "tampered copy"
        self.assertEqual(b.current_other_model("O1")["model"]["claim"], "revised")

    def test_active_repairs_are_projection_of_full_repair_history(self):
        b = self.make()
        b.record_repair("O1", "old", "action", "source:r1")
        b.verify_repair("RP0001", {"source_ref": "v1"}, "source:v1")
        b.scar_repair("RP0001", "lesson", "source:l1")
        b.archive_scar("RP0001", "source:a1")
        b.record_repair("O1", "current", "action2", "source:r2")
        self.assertEqual(len(b.repair_history("O1")), 2)
        active = b.active_repairs("O1")
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0]["repair_id"], "RP0002")
        self.assertEqual(b.repair_history("O1")[0]["status"], "archived")

    def test_current_trust_view_does_not_erase_history(self):
        b = self.make()
        self.assertIsNone(b.current_trust_calibration("O1"))
        b.record_trust_calibration("O1", "cautious", "source:t1", "event history")
        b.record_trust_calibration("O1", "improving", "source:t2", "verified correction")
        current = b.current_trust_calibration("O1")
        history = b.trust_calibration_history("O1")
        self.assertEqual(current["assessment"], "improving")
        self.assertEqual([x["assessment"] for x in history], ["cautious", "improving"])
        current["assessment"] = "tampered copy"
        self.assertEqual(b.current_trust_calibration("O1")["assessment"], "improving")

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

    def test_only_verified_repair_can_be_scarred_and_lesson_is_preserved(self):
        b = self.make()
        b.record_repair("O1", "issue", "action", "source:repair")
        with self.assertRaises(ValueError):
            b.scar_repair("RP0001", "lesson", "source:lesson")
        b.verify_repair("RP0001", {"source_ref": "v"}, "source:verifier")
        out = b.scar_repair("RP0001", "remember the failure mode without letting it dominate current evaluation", "source:lesson")
        self.assertEqual(out["status"], "scarred")
        self.assertEqual(out["current_influence"], .25)
        self.assertIn("failure mode", out["lesson"])
        self.assertEqual(b.ledger.read()[-1]["event_type"], "SCAR_REPAIR")

    def test_archive_is_zero_current_influence_not_deletion(self):
        b = self.make()
        b.record_repair("O1", "issue", "action", "source:repair")
        b.verify_repair("RP0001", {"source_ref": "v"}, "source:verifier")
        b.scar_repair("RP0001", "lesson", "source:lesson")
        out = b.archive_scar("RP0001", "source:archive")
        self.assertEqual(out["status"], "archived")
        self.assertEqual(out["current_influence"], 0.0)
        self.assertEqual(out["lesson"], "lesson")
        self.assertEqual(out["verification"]["source_ref"], "v")
        self.assertEqual(b.ledger.read()[-1]["event_type"], "ARCHIVE_SCAR")

    def test_recurrence_reactivates_archived_scar_without_deletion(self):
        b = self.make()
        b.record_repair("O1", "issue", "action", "source:repair")
        b.verify_repair("RP0001", {"source_ref": "v"}, "source:verifier")
        b.scar_repair("RP0001", "lesson", "source:lesson")
        b.archive_scar("RP0001", "source:archive")
        out = b.record_recurrence("RP0001", {"event": "returned"}, "source:recurrence")
        self.assertEqual(out["status"], "recurrence_after_verification")
        self.assertEqual(out["current_influence"], 1.0)
        self.assertEqual(out["lesson"], "lesson")

    def test_scar_influence_is_bounded(self):
        b = self.make()
        b.record_repair("O1", "issue", "action", "source:repair")
        b.verify_repair("RP0001", {"source_ref": "v"}, "source:verifier")
        with self.assertRaises(ValueError):
            b.scar_repair("RP0001", "lesson", "source:lesson", current_influence=-.1)

    def test_recurrence_can_reactivate_a_scar_without_erasing_it(self):
        b = self.make()
        b.record_repair("O1", "issue", "action", "source:repair")
        b.verify_repair("RP0001", {"source_ref": "v"}, "source:verifier")
        b.scar_repair("RP0001", "lesson", "source:lesson")
        out = b.record_recurrence("RP0001", {"event": "issue returned"}, "source:recurrence")
        self.assertEqual(out["status"], "recurrence_after_verification")
        self.assertEqual(out["lesson"], "lesson")
        self.assertEqual(out["current_influence"], 1.0)
        self.assertEqual(out["verification"]["source_ref"], "v")

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
