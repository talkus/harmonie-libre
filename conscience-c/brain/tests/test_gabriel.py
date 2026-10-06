"""Gabriel's public contract, exercised against real persisted brain instances."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind
from conscience_c_brain.models import CausalOrigin
from conscience_c_brain.multiscale_coherence import (
    Scale, EvidenceStatus, CoherenceStatus, validate_scale_receipt,
)


class GabrielTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.brain = ConscienceCBrain.load_or_bootstrap(Path(self.tmp.name))
        self.cid = self.brain.record_claim(
            "La réponse est étayée dans ce contexte.", "system_hypothesis", "fixture",
            confidence=0.95,
        )["claim_id"]

    def evidence(self, eid, stance="supports", **kw):
        values = dict(claim_ref=self.cid, scope="local", subject_ref="subject:1",
                      stance=stance, confidence=0.5, source_ref="source:" + eid)
        values.update(kw)
        kind = values.pop("kind", EvidenceKind.ATTESTED_SOURCE)
        self.brain.ingest_evidence(Evidence(eid, "observation " + eid, kind, **values), CausalOrigin.OTHER)

    def examine(self, **kw):
        args = dict(scope_ref="local", observer_ref="observer:1", subject_ref="subject:1")
        args.update(kw)
        return self.brain.gabriel_examine(self.cid, **args)

    def record(self, **kw):
        args = dict(scope_ref="local", observer_ref="observer:1", subject_ref="subject:1",
                    provenance="test:request")
        args.update(kw)
        return self.brain.record_gabriel_examination(self.cid, **args)

    def open(self, ref):
        return self.brain.open_gabriel_repair(ref, requested_by="operator", provenance="test:decision")

    def test_missing_evidence_stays_unknown_without_any_mutation(self):
        state = copy.deepcopy(self.brain.state)
        files = {p.name: p.read_bytes() for p in self.brain.root.iterdir() if p.is_file()}
        report = self.examine()
        self.assertEqual(report["verdict"], "INDETERMINATE")
        self.assertTrue(report["unknowns"])
        self.assertFalse(report["execution_authority"])
        self.assertEqual(self.brain.state, state)
        self.assertEqual(files, {p.name: p.read_bytes() for p in self.brain.root.iterdir() if p.is_file()})

    def test_explicit_support_allows_bounded_hold_not_truth_certification(self):
        self.evidence("E1")
        report = self.examine()
        self.assertEqual(report["verdict"], "HOLD")
        self.assertEqual(report["scope_ref"], "local")
        self.assertEqual(report["support_refs"], ["E1"])
        self.assertFalse(report["independent_validation"])
        self.assertTrue(report["stop_condition"])
        self.assertIn("new_relevant_evidence", report["revision_triggers"])

    def test_contradiction_is_review_not_automatic_repair(self):
        self.evidence("E1")
        self.evidence("E2", "contradicts")
        report = self.examine()
        self.assertEqual(report["verdict"], "REVIEW_REQUIRED")
        self.assertEqual(report["contradiction_refs"], ["E2"])
        self.assertEqual(self.brain.claim(self.cid)["status"], "active")
        self.assertEqual(self.brain.teshuvah_cycles(), [])

    def test_wrong_context_and_expired_evidence_cannot_trigger_review(self):
        self.evidence("E1")
        self.evidence("E2", "contradicts", scope="elsewhere")
        self.evidence("E3", "contradicts", subject_ref="someone:else")
        self.evidence("E4", "contradicts", expires_at="2026-01-01T00:00:00Z")
        report = self.examine(at_time="2026-10-06T09:00:00+00:00")
        self.assertEqual(report["verdict"], "HOLD")
        self.assertEqual(len(report["excluded_evidence"]), 3)
        self.assertEqual(report["contradiction_refs"], [])

    def test_context_only_or_unscoped_or_analytical_data_do_not_certify_support(self):
        for change in ({"stance": "context"}, {"scope": None},
                       {"kind": EvidenceKind.ANALYTICAL_RECONSTRUCTION}):
            with self.subTest(change=change):
                eid = "E" + str(len(self.brain.state["E"]["evidence"]))
                self.evidence(eid, **change)
                self.assertEqual(self.examine()["verdict"], "INDETERMINATE")

    def test_unassessed_contradiction_remains_visible_even_with_support(self):
        self.evidence("E1")
        self.evidence("E2", "contradicts", scope=None)
        report = self.examine()
        self.assertEqual(report["verdict"], "INDETERMINATE")
        self.assertTrue(report["unknowns"])

    def test_invalid_dates_remain_invalid_not_absence_of_alert(self):
        self.evidence("E1", valid_at="not-a-date")
        report = self.examine()
        self.assertEqual(report["evidence_status"], "INVALID_DATA")
        self.assertEqual(report["verdict"], "INDETERMINATE")

    def test_timezone_offsets_are_compared_as_instants(self):
        self.evidence("E1", valid_at="2026-10-06T10:00:00+02:00")
        self.assertEqual(self.examine(at_time="2026-10-06T08:30:00Z")["verdict"], "HOLD")

    def test_report_persists_and_unchanged_inputs_stop_without_more_events(self):
        self.evidence("E1")
        report = self.record()
        head = self.brain.ledger.head()
        again = self.record()
        self.assertEqual(again["report_ref"], report["report_ref"])
        self.assertEqual(self.brain.ledger.head(), head)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.brain.root)
        self.assertEqual(self.brain.gabriel_report(report["report_ref"])["report"], report["report"])
        self.assertEqual(self.brain.classify_replay_event(self.brain.ledger.read_verified()[-1]), "documentary_only")

    def test_new_evidence_reopens_examination(self):
        first = self.record()
        self.evidence("E1")
        second = self.record()
        self.assertNotEqual(first["report_ref"], second["report_ref"])
        self.assertEqual(second["report"]["verdict"], "HOLD")
        self.assertEqual(second["report"]["reexamines"], first["report_ref"])

    def test_explicit_repair_is_single_claim_and_retry_does_not_duplicate(self):
        other = self.brain.record_claim("Autre affirmation", "user_stated", "fixture")["claim_id"]
        self.evidence("E1", "contradicts")
        report = self.record()
        cycle = self.open(report["report_ref"])
        self.assertEqual(cycle["origin"]["claim_ids"], [self.cid])
        self.assertIn(report["report_ref"], cycle["origin"]["drift_events"])
        self.assertEqual(self.brain.claim(other)["status"], "active")
        head = self.brain.ledger.head()
        self.assertEqual(self.open(report["report_ref"])["teshuvah_id"], cycle["teshuvah_id"])
        self.assertEqual(self.brain.ledger.head(), head)

    def test_stale_report_cannot_open_repair(self):
        self.evidence("E1", "contradicts")
        report = self.record()
        self.evidence("E2")
        head = self.brain.ledger.head()
        with self.assertRaisesRegex(ValueError, "stale"):
            self.open(report["report_ref"])
        self.assertEqual(self.brain.ledger.head(), head)

    def test_hold_or_unknown_cannot_open_repair(self):
        unknown = self.record()
        with self.assertRaises(ValueError):
            self.open(unknown["report_ref"])
        self.evidence("E1")
        held = self.record()
        with self.assertRaises(ValueError):
            self.open(held["report_ref"])

    def test_contestation_blocks_application_and_survives_reexamination(self):
        self.evidence("E1", "contradicts")
        report = self.record()
        objection = self.brain.contest_gabriel(report["report_ref"], reason="Mauvais contexte",
                                            actor="other", provenance="test:objection")
        with self.assertRaisesRegex(ValueError, "contest"):
            self.open(report["report_ref"])
        self.evidence("E2")
        revised = self.record()
        self.assertIn(objection["event_hash"], revised["contestation_refs"])
        with self.assertRaisesRegex(ValueError, "contest"):
            self.open(revised["report_ref"])

    def test_false_diagnosis_can_be_corrected_without_erasing_it(self):
        self.evidence("E1", "contradicts", scope="elsewhere")
        wrong_context = self.record(scope_ref="elsewhere")
        self.brain.contest_gabriel(wrong_context["report_ref"], reason="Portée mal choisie",
                                  actor="other", provenance="test:objection")
        before = self.brain.ledger.read_verified()
        correction = self.brain.correct_gabriel(wrong_context["report_ref"], reason="Portée rectifiée",
            evidence_refs=["E1"], actor="reviewer", provenance="test:correction")
        self.assertEqual(self.brain.ledger.read_verified()[:len(before)], before)
        self.assertEqual(self.brain.gabriel_report(wrong_context["report_ref"])["status"], "corrected")
        self.assertFalse(correction["independent_validation"])
        with self.assertRaises(ValueError):
            self.open(wrong_context["report_ref"])
        self.evidence("E2")
        revised = self.record(reexamines=wrong_context["report_ref"], revision_reason="Retour à la portée locale")
        self.assertEqual(revised["report"]["verdict"], "HOLD")
        self.assertEqual(self.brain.claim(self.cid)["status"], "active")

    def test_unknown_report_or_correction_evidence_is_rejected_without_writing(self):
        report = self.record()
        head = self.brain.ledger.head()
        with self.assertRaises(ValueError):
            self.brain.gabriel_report("invented")
        with self.assertRaises(ValueError):
            self.brain.correct_gabriel(report["report_ref"], reason="x", evidence_refs=["missing"],
                                       actor="reviewer", provenance="p")
        self.assertEqual(head, self.brain.ledger.head())

    def test_same_contract_preserves_unknown_at_each_scale(self):
        for scale in Scale:
            with self.subTest(scale=scale):
                report = self.record(scale=scale)
                receipt = self.brain.gabriel_scale_receipt(report["report_ref"])
                checked = validate_scale_receipt(receipt)
                self.assertEqual(receipt.scale, scale)
                self.assertEqual(checked.issues, ())
                self.assertEqual(checked.status, CoherenceStatus.INDETERMINATE)
                self.assertEqual(checked.evidence_status, EvidenceStatus.INSUFFICIENT_DATA)
                self.assertFalse(checked.execution_authority)

    def test_objection_is_carried_into_multiscale_receipt(self):
        self.evidence("E1")
        report = self.record(scale=Scale.META)
        self.brain.contest_gabriel(report["report_ref"], reason="Critère incomplet",
                                  actor="other", provenance="p")
        checked = validate_scale_receipt(self.brain.gabriel_scale_receipt(report["report_ref"]))
        self.assertEqual(checked.status, CoherenceStatus.CONTESTED)
        self.assertEqual(checked.issues, ())

    def test_broken_history_refuses_examination(self):
        with (self.brain.root / "events.jsonl").open("a") as out:
            out.write('{"forged": true}\n')
        with self.assertRaises(ValueError):
            self.examine()

    def test_end_to_end_repair_preserves_history_and_resumes(self):
        self.evidence("E1", "contradicts")
        report = self.record()
        before = self.brain.ledger.read_verified()
        cycle = self.open(report["report_ref"])
        tid = cycle["teshuvah_id"]
        self.brain.acknowledge_teshuvah(tid, "operator", "Affirmation trop large", "Portée trompeuse",
                                      "Généralisation", "test:ack")
        self.brain.propose_teshuvah_repair(tid, "Retirer uniquement cette affirmation", "test:plan")
        self.brain.apply_teshuvah_repair(tid, [{"claim_id": self.cid, "action": "retract",
                                               "reason": "Preuve contradictoire"}], "operator", "test:apply")
        reloaded = ConscienceCBrain.load_or_bootstrap(self.brain.root)
        self.assertEqual(reloaded.ledger.read_verified()[:len(before)], before)
        self.assertEqual(reloaded.claim(self.cid)["status"], "retracted")
        self.assertEqual(reloaded.teshuvah(tid)["phase"], "repair_applied")
        self.assertEqual(reloaded.gabriel_report(report["report_ref"])["repair_refs"], [tid])
        self.assertTrue(reloaded.governance_audit()["ok"])

    def test_changing_observer_or_scale_cannot_launder_an_objection(self):
        self.evidence("E1", "contradicts")
        first = self.record()
        objection = self.brain.contest_gabriel(first["report_ref"], reason="Portée contestée",
                                              actor="other", provenance="p")
        for change in ({"observer_ref": "observer:2"}, {"scale": Scale.META}):
            with self.subTest(change=change):
                report = self.record(revision_reason="Nouvelle lecture", **change)
                self.assertIn(objection["event_hash"], report["contestation_refs"])
                with self.assertRaisesRegex(ValueError, "contest"):
                    self.open(report["report_ref"])

    def test_cannot_fork_from_an_older_report_to_omit_later_objections(self):
        first = self.record()
        self.evidence("E1")
        second = self.record()
        self.brain.contest_gabriel(second["report_ref"], reason="Appui contesté", actor="other", provenance="p")
        head = self.brain.ledger.head()
        with self.assertRaisesRegex(ValueError, "latest"):
            self.record(reexamines=first["report_ref"], revision_reason="Retour arbitraire")
        self.assertEqual(self.brain.ledger.head(), head)

    def test_corrected_report_cannot_be_reactivated_by_identical_repetition(self):
        self.evidence("E1", "contradicts")
        first = self.record()
        self.brain.correct_gabriel(first["report_ref"], reason="Diagnostic incomplet", evidence_refs=["E1"],
                                   actor="reviewer", provenance="p")
        head = self.brain.ledger.head()
        again = self.record()
        self.assertEqual(again["status"], "corrected")
        self.assertEqual(self.brain.ledger.head(), head)

    def test_correction_identifies_already_started_repair_effects(self):
        self.evidence("E1", "contradicts")
        report = self.record()
        cycle = self.open(report["report_ref"])
        correction = self.brain.correct_gabriel(report["report_ref"], reason="Diagnostic à reprendre",
            evidence_refs=["E1"], actor="reviewer", provenance="p")
        self.assertEqual(correction["repair_refs_requiring_review"], [cycle["teshuvah_id"]])
        self.assertEqual(self.brain.claim(self.cid)["status"], "contested")
        with self.assertRaises(ValueError):
            self.open(report["report_ref"])

    def test_same_scope_new_observer_requires_a_reason_for_context_change(self):
        self.record()
        with self.assertRaises(ValueError):
            self.record(observer_ref="another")

    def test_empty_validity_metadata_is_invalid_data(self):
        self.evidence("E1", valid_at="")
        self.assertEqual(self.examine()["evidence_status"], "INVALID_DATA")

    def test_correction_of_new_report_does_not_resolve_objection_to_ancestor(self):
        self.evidence("E1", "contradicts")
        first = self.record()
        objection = self.brain.contest_gabriel(first["report_ref"], reason="Critère contesté", actor="other", provenance="p")
        self.evidence("E2")
        second = self.record()
        self.brain.correct_gabriel(second["report_ref"], reason="Cette version est incomplète",
                                   evidence_refs=["E2"], actor="reviewer", provenance="p")
        self.assertIn(objection["event_hash"], self.brain.gabriel_report(second["report_ref"])["contestation_refs"])

    def test_receipt_retains_the_claim_contradiction(self):
        self.evidence("E1")
        self.evidence("E2", "contradicts")
        report = self.record()
        checked = validate_scale_receipt(self.brain.gabriel_scale_receipt(report["report_ref"]))
        self.assertEqual(checked.status, CoherenceStatus.CONTESTED)
        self.assertEqual(checked.issues, ())

    def test_receipt_marks_a_report_stale_when_inputs_changed(self):
        self.evidence("E1")
        report = self.record()
        self.evidence("E2", "contradicts")
        checked = validate_scale_receipt(self.brain.gabriel_scale_receipt(report["report_ref"]))
        self.assertTrue(checked.has_unknown)

    def cli(self, *args):
        return subprocess.run([sys.executable, "-B", "-m", "conscience_c_brain.cli",
                               "--root", str(self.brain.root), *args],
                              text=True, capture_output=True)

    def test_command_line_examination_record_contest_and_correction(self):
        self.evidence("E1")
        head = self.brain.ledger.head()
        args = ("gabriel-examine", self.cid, "--scope", "local", "--observer", "observer:1",
                "--subject", "subject:1")
        examined = self.cli(*args)
        self.assertEqual(examined.returncode, 0, examined.stderr)
        self.assertEqual(json.loads(examined.stdout)["verdict"], "HOLD")
        self.assertEqual(self.brain.ledger.head(), head)
        recorded = self.cli(*args, "--record", "--provenance", "test:cli")
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        ref = json.loads(recorded.stdout)["report_ref"]
        disputed = self.cli("gabriel-contest", ref, "--reason", "Critère incomplet",
                            "--actor", "other", "--provenance", "test:cli")
        self.assertEqual(disputed.returncode, 0, disputed.stderr)
        shown = self.cli("gabriel-report", ref)
        self.assertEqual(json.loads(shown.stdout)["status"], "contested")
        corrected = self.cli("gabriel-correct", ref, "--reason", "Reconnaissance de la limite",
                             "--evidence-ref", "E1", "--actor", "reviewer", "--provenance", "test:cli")
        self.assertEqual(corrected.returncode, 0, corrected.stderr)
        shown = self.cli("gabriel-report", ref)
        self.assertEqual(json.loads(shown.stdout)["status"], "corrected")

    def test_command_line_repair_is_explicit_and_does_not_apply_replacement(self):
        self.evidence("E1", "contradicts")
        report = self.record()
        opened = self.cli("gabriel-open-repair", report["report_ref"], "--actor", "operator",
                          "--provenance", "test:cli")
        self.assertEqual(opened.returncode, 0, opened.stderr)
        self.assertEqual(json.loads(opened.stdout)["phase"], "contested")
        resumed = ConscienceCBrain.load_or_bootstrap(self.brain.root)
        self.assertIsNone(resumed.claim(self.cid)["replaced_by"])

    def test_command_line_does_not_bootstrap_a_missing_memory(self):
        missing = self.brain.root / "absent"
        result = subprocess.run([sys.executable, "-B", "-m", "conscience_c_brain.cli",
            "--root", str(missing), "gabriel-examine", self.cid, "--scope", "local", "--observer", "o"],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("existing memory", result.stderr)
        self.assertFalse(missing.exists())

    def test_updated_claim_can_be_examined_from_its_real_creation_trace(self):
        updated = self.brain.update_claim(self.cid, "Nouveau contexte", "context_shift", "p", "user_stated")
        report = self.brain.gabriel_examine(updated["claim_id"], scope_ref="local", observer_ref="o")
        self.assertIn(updated["event_hash"], report["trace_refs"])

    def test_repaired_replacement_can_be_examined(self):
        cycle = self.brain.initiate_teshuvah("error", "Trop général", "p", claim_ids=[self.cid])
        tid = cycle["teshuvah_id"]
        self.brain.acknowledge_teshuvah(tid, "operator", "Trop large", "Confusion", "Généralisation", "p")
        self.brain.propose_teshuvah_repair(tid, "Reformuler", "p")
        repaired = self.brain.apply_teshuvah_repair(tid, [{"claim_id": self.cid, "action": "supersede",
            "reason": "Préciser", "replacement": {"statement": "Hypothèse limitée", "provenance_kind":
            "system_hypothesis", "provenance": "p"}}], "operator", "p")
        new_id = self.brain.claim(self.cid)["replaced_by"]
        report = self.brain.gabriel_examine(new_id, scope_ref="local", observer_ref="o")
        self.assertIn(repaired["event_hash"], report["trace_refs"])

    def test_support_derived_from_refuted_evidence_keeps_its_unknown(self):
        self.evidence("E0", kind=EvidenceKind.HISTORICAL_REFUTED, claim_ref=None)
        self.evidence("E1", kind=EvidenceKind.CONSOLIDATED_DERIVATION, derived_from=["E0"])
        report = self.examine()
        self.assertEqual(report["verdict"], "INDETERMINATE")
        self.assertIn(self.brain._ingest_row("E0")["event_hash"], report["trace_refs"])

    def test_refuted_fact_requires_bounded_review(self):
        self.evidence("E0", kind=EvidenceKind.HISTORICAL_REFUTED, claim_ref=None)
        claim = self.brain.record_claim("Basé sur E0", "system_hypothesis", "p", facts=["E0"])
        report = self.brain.gabriel_examine(claim["claim_id"], scope_ref="local", observer_ref="o")
        self.assertEqual(report["verdict"], "REVIEW_REQUIRED")
        self.assertEqual(report["findings"][0]["code"], "refuted_basis")

    def test_invalid_or_uncommitted_inputs_do_not_mutate_memory(self):
        head = self.brain.ledger.head()
        for change in ({"scope_ref": " "}, {"observer_ref": ""}, {"scale": "unknown"},
                       {"at_time": "2026-10-06"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.examine(**change)
        self.brain.state["teshuvah"]["claims"][self.cid]["statement"] = "edited without event"
        with self.assertRaisesRegex(ValueError, "uncommitted"):
            self.examine()
        self.assertEqual(self.brain.ledger.head(), head)


if __name__ == "__main__":
    unittest.main()
