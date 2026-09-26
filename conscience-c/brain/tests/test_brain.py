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

    def test_resume_tn_no_reset(self):
        b = self.make()
        b.imagine("futur", ["A"], ["B"])
        root = b.root
        before = b.state["n"]
        b2 = ConscienceCBrain.load_or_bootstrap(root)
        self.assertEqual(b2.state["n"], before)
        self.assertNotEqual(b2.state["state_label"], "C(t_0)")

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

    def test_provenance_types_are_not_collapsed(self):
        b = self.make()
        b.ingest_evidence(Evidence("E1", "primary", EvidenceKind.ATTESTED_SOURCE))
        b.ingest_evidence(Evidence("E2", "derived", EvidenceKind.CONSOLIDATED_DERIVATION))
        b.ingest_evidence(Evidence("E3", "analytic", EvidenceKind.ANALYTICAL_RECONSTRUCTION))
        kinds = {x["kind"] for x in b.state["E"]["evidence"].values()}
        self.assertEqual(kinds, {"source_attestee","derivation_consolidee","reconstruction_analytique"})

    def test_extended_statuses_remain_distinct(self):
        b = self.make()
        b.ingest_evidence(Evidence("E4", "insufficient", EvidenceKind.INDETERMINATE))
        b.ingest_evidence(Evidence("E5", "old refuted claim", EvidenceKind.HISTORICAL_REFUTED))
        self.assertEqual(b.state["E"]["evidence"]["E4"]["kind"], "indetermine")
        self.assertEqual(b.state["E"]["evidence"]["E5"]["kind"], "historique_refute")

    def test_falsifiable_hypothesis_can_be_rejected(self):
        b = self.make()
        b.add_hypothesis(Hypothesis("H1", "X est vrai", .8, ["preuve contraire de X"]))
        b.ingest_evidence(Evidence("E1", "X est faux", EvidenceKind.ATTESTED_SOURCE, contradicts=["H1"], confidence=.95))
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
