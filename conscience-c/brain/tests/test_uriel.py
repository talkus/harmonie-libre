"""A situated reading must preserve doubt and history without acting on C."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from conscience_c_brain import ConscienceCBrain, Evidence, EvidenceKind, CausalOrigin
from conscience_c_brain.multiscale_coherence import Scale


class UrielTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.cid = self.brain.record_claim("Texte privé de l'affirmation", "system_hypothesis", "fixture")["claim_id"]

    def evidence(self, eid, stance="supports", **kw):
        values = dict(claim_ref=self.cid, scope="local", stance=stance,
                      source_ref="origin:shared", confidence=0.5)
        values.update(kw)
        kind = values.pop("kind", EvidenceKind.ATTESTED_SOURCE)
        self.brain.ingest_evidence(Evidence(eid, "Contenu privé de la preuve", kind,
                                            **values), CausalOrigin.OTHER)

    def report(self, **kw):
        args = dict(scope_ref="local", observer_ref="examiner:1", provenance="fixture")
        args.update(kw)
        return self.brain.record_gabriel_examination(self.cid, **args)["report_ref"]

    def read(self, refs, **kw):
        args = dict(observer_ref="reader:1", scope_ref="selection:local")
        args.update(kw)
        return self.brain.uriel_read(refs, **args)

    def files(self):
        return {str(p.relative_to(self.root)): p.read_bytes()
                for p in self.root.rglob("*") if p.is_file()}

    def test_reading_does_not_change_state_or_any_persisted_file(self):
        ref = self.report()
        state, files = copy.deepcopy(self.brain.state), self.files()
        self.read([ref])
        self.assertEqual((self.brain.state, self.files()), (state, files))

    def test_unknown_is_preserved_at_all_four_projection_scales(self):
        view = self.read([self.report()])
        self.assertEqual({r["scale"] for r in view["receipts"]}, {s.value for s in Scale})
        for receipt in view["receipts"]:
            with self.subTest(scale=receipt["scale"], unit=receipt["receipt_id"]):
                self.assertTrue(receipt["unknowns"])
                self.assertEqual(receipt["observer_ref"], "reader:1")
                self.assertEqual(receipt["scope_ref"], "selection:local")
                self.assertEqual(receipt["property_ref"], "uriel:situated_trace_projection")
                self.assertTrue(receipt["revision_triggers"])
        self.assertTrue(view["validation"]["has_unknown"])
        self.assertEqual(view["validation"]["issues"], [])
        self.assertFalse(view["validation"]["execution_authority"])
        self.assertFalse(view["validation"]["independent_validation"])

    def test_reader_coordinates_do_not_replace_the_source_coordinates(self):
        ref = self.report(scale=Scale.MACRO)
        source = self.read([ref])["sources"][0]
        self.assertEqual((source["report_ref"], source["scale"], source["observer_ref"], source["scope_ref"]),
                         (ref, "macro", "examiner:1", "local"))

    def test_reading_is_reproducible_and_input_order_does_not_create_progress(self):
        a = self.report()
        self.cid = self.brain.record_claim("Autre", "user_stated", "fixture")["claim_id"]
        b = self.report()
        self.assertEqual(self.read([a, b]), self.read([b, a]))

    def test_mirrors_keep_one_source_origin_without_becoming_independent_witnesses(self):
        self.evidence("E1")
        a = self.report()
        b = self.report(observer_ref="examiner:2", revision_reason="Autre perspective")
        view = self.read([a, b])
        for receipt in view["receipts"]:
            self.assertEqual(receipt["origin_refs"].count("origin:shared"), 1)
            self.assertEqual(receipt["external_witness_refs"], [])
        self.assertFalse(view["independent_validation"])

    def test_default_projection_exposes_references_but_not_private_contents(self):
        self.evidence("E1")
        view = self.read([self.report()])
        encoded = json.dumps(view, ensure_ascii=False)
        self.assertNotIn("Texte privé", encoded)
        self.assertNotIn("Contenu privé", encoded)
        self.assertTrue(view["declared_losses"])
        self.assertEqual(view["sources"][0]["evidence"][0]["kind"], "source_attestee")

    def test_every_bridge_preserves_the_child_contract_and_has_no_authority(self):
        ref = self.report()
        self.brain.contest_gabriel(ref, reason="Portée contestée", actor="other", provenance="fixture")
        view = self.read([ref])
        receipts = {r["receipt_hash"]: r for r in view["receipts"]}
        for bridge in view["bridges"]:
            child, parent = (receipts[bridge[k]] for k in ("child_receipt_hash", "parent_receipt_hash"))
            self.assertEqual(bridge["preserved_origin_refs"], child["origin_refs"])
            self.assertEqual(bridge["carried_unknown_ids"], [x["unknown_id"] for x in child["unknowns"]])
            self.assertEqual(bridge["carried_contestation_ids"], [x["contestation_id"] for x in child["contestations"]])
            self.assertEqual(bridge["carried_evidence_status"], child["evidence_status"])
            self.assertTrue(set(child["origin_refs"]) <= set(parent["origin_refs"]))
            self.assertFalse(bridge["authority_transfer"])
        self.assertTrue(view["validation"]["has_contestation"])
        self.assertTrue(view["validation"]["has_unknown"])
        self.assertTrue(all(not r["issues"] for r in view["validation"]["bridge_reports"]))
        self.assertEqual(view["validation"]["issues"], [])

    def test_selected_hold_does_not_hide_objections_to_another_perspective(self):
        self.evidence("E1")
        a = self.report()
        b = self.report(observer_ref="examiner:2", scale=Scale.META, revision_reason="Autre lecture")
        objection = self.brain.contest_gabriel(b, reason="Désaccord", actor="other", provenance="fixture")
        view = self.read([a])
        self.assertIn(objection["event_hash"], view["sources"][0]["contestation_refs"])
        self.assertIn(b, view["coverage"]["omitted_same_claim_report_refs"])
        self.assertTrue(view["validation"]["has_contestation"])

    def test_selection_gap_is_attached_to_its_own_claim(self):
        a = self.report()
        omitted = self.report(observer_ref="examiner:2", revision_reason="Autre perspective")
        first_claim = self.cid
        self.cid = self.brain.record_claim("Autre", "system_hypothesis", "fixture")["claim_id"]
        b = self.report()
        view = self.read([a, b])
        sources = {s["claim_id"]: s for s in view["sources"]}
        self.assertEqual(sources[first_claim]["omitted_same_claim_report_refs"], [omitted])
        self.assertEqual(sources[self.cid]["omitted_same_claim_report_refs"], [])
        leaf = next(r for r in view["receipts"] if r["receipt_id"] == "uriel:micro:" + b)
        self.assertNotIn("same_claim_reports_outside_selection", [u["question"] for u in leaf["unknowns"]])

    def test_different_local_evidence_states_remain_visible_without_a_total_score(self):
        self.evidence("E1", valid_at="invalid")
        a = self.report()
        self.cid = self.brain.record_claim("Autre", "system_hypothesis", "fixture")["claim_id"]
        b = self.report()
        view = self.read([a, b])
        self.assertEqual({s["evidence_status"] for s in view["sources"]}, {"INVALID_DATA", "INSUFFICIENT_DATA"})
        self.assertTrue(view["validation"]["has_unknown"])
        self.assertNotIn("score", view)
        self.assertTrue(any(r["issues"] for r in view["validation"]["scale_reports"]))

    def test_new_evidence_marks_a_historical_report_stale_without_rewriting_it(self):
        self.evidence("E1")
        ref = self.report()
        before = self.brain.gabriel_report(ref)["report"]
        self.evidence("E2", "contradicts", source_ref="origin:new")
        view = self.read([ref])
        source = view["sources"][0]
        self.assertTrue(source["stale"])
        self.assertEqual(source["verdict"], "HOLD")
        self.assertEqual(before, self.brain.gabriel_report(ref)["report"])
        self.assertIn("stale_report_requires_reexamination", source["unknowns"])
        self.assertEqual(source["current_examination"]["contradiction_refs"], ["E2"])
        self.assertEqual(source["current_examination"]["verdict"], "REVIEW_REQUIRED")
        self.assertEqual([e["evidence_id"] for e in source["evidence"]], ["E1"])
        for receipt in view["receipts"]:
            self.assertIn("origin:new", receipt["origin_refs"])
            self.assertTrue(set(source["current_examination"]["trace_refs"]) <= set(receipt["trace_refs"]))
        self.assertTrue(view["validation"]["has_contestation"])

    def test_clear_supported_map_does_not_close_its_own_limits(self):
        self.evidence("E1")
        view = self.read([self.report()])
        self.assertEqual(view["sources"][0]["verdict"], "HOLD")
        for receipt in view["receipts"]:
            self.assertTrue(receipt["unknowns"])
            self.assertIn("reader_context_changed", receipt["revision_triggers"])
            self.assertIn("projection_criteria_changed", receipt["revision_triggers"])
        self.assertEqual(view["validation"]["status"], "INDETERMINATE")
        self.assertFalse(view["coverage"]["complete_flow_observation"])
        earlier = copy.deepcopy(view)
        other = self.read([view["sources"][0]["report_ref"]], observer_ref="reader:2")
        self.assertNotEqual(view["projection_state_ref"], other["projection_state_ref"])
        self.assertEqual(view, earlier)

    def test_current_invalid_data_remains_visible_beside_a_historical_hold(self):
        self.evidence("E1")
        ref = self.report()
        self.evidence("E2", valid_at="invalid")
        view = self.read([ref])
        source = view["sources"][0]
        self.assertEqual(source["verdict"], "HOLD")
        self.assertEqual(source["evidence_status"], "NOT_TRIGGERED")
        self.assertEqual(source["current_evidence_status"], "INVALID_DATA")
        self.assertTrue(any(r["issues"] for r in view["validation"]["scale_reports"]))

    def test_derived_evidence_does_not_hide_the_source_ancestry(self):
        self.evidence("E1", source_ref="source:original", claim_ref=None)
        self.evidence("E2", kind=EvidenceKind.CONSOLIDATED_DERIVATION, source_ref="source:derivation",
                      derived_from=["E1"])
        view = self.read([self.report()])
        for receipt in view["receipts"]:
            self.assertIn("source:original", receipt["origin_refs"])
            self.assertIn("source:derivation", receipt["origin_refs"])
        derived = next(e for e in view["sources"][0]["evidence"] if e["evidence_id"] == "E2")
        self.assertTrue(all(e["trace_ref"] in view["sources"][0]["trace_refs"] for e in derived["lineage"]))

    def test_local_grouping_preserves_observers_and_distinct_subjects(self):
        refs = [self.report(subject_ref="subject:1"),
                self.report(subject_ref="subject:1", observer_ref="examiner:2", revision_reason="Autre lecteur"),
                self.report(subject_ref="subject:2", revision_reason="Autre sujet")]
        view = self.read(refs)
        self.assertEqual(len([r for r in view["receipts"] if r["scale"] == "micro"]), 3)
        self.assertEqual(len([r for r in view["receipts"] if r["scale"] == "meso"]), 2)
        self.assertEqual({s["observer_ref"] for s in view["sources"]}, {"examiner:1", "examiner:2"})
        self.assertEqual(view["validation"]["issues"], [])

    def test_unrelated_transition_changes_boundary_without_claiming_new_relevant_state(self):
        ref = self.report()
        before = self.read([ref])
        self.brain.imagine("Sans rapport", [], [])
        after = self.read([ref])
        self.assertNotEqual(before["reading_ref"], after["reading_ref"])
        self.assertEqual(before["projection_state_ref"], after["projection_state_ref"])
        self.assertEqual(before["receipts"], after["receipts"])

    def test_every_projected_objection_retains_its_original_source_target(self):
        ref = self.report()
        objection = self.brain.contest_gabriel(ref, reason="Limite", actor="other", provenance="fixture")
        view = self.read([ref])
        self.assertEqual(view["source_contestation_targets"][objection["event_hash"]], ref)
        for receipt in view["receipts"]:
            for projected in receipt["contestations"]:
                self.assertIn(ref, projected["target_assertion_ref"])

    def test_time_dependent_applicability_revises_the_reading_but_not_the_past(self):
        self.evidence("E1", expires_at="2030-01-01T00:00:00Z")
        ref = self.report(at_time="2026-10-06T00:00:00Z")
        before = self.read([ref], at_time="2026-10-06T00:00:00Z")
        after = self.read([ref], at_time="2031-01-01T00:00:00Z")
        self.assertFalse(before["sources"][0]["stale"])
        self.assertTrue(after["sources"][0]["stale"])
        self.assertNotEqual(before["reading_ref"], after["reading_ref"])

    def test_correction_keeps_the_objection_history_visible(self):
        self.evidence("E1")
        ref = self.report()
        objection = self.brain.contest_gabriel(ref, reason="Limite", actor="other", provenance="fixture")
        correction = self.brain.correct_gabriel(ref, reason="Limite reconnue", evidence_refs=["E1"],
                                                actor="reader", provenance="fixture")
        source = self.read([ref])["sources"][0]
        self.assertEqual(source["status"], "corrected")
        self.assertIn(objection["event_hash"], source["contestation_history_refs"])
        self.assertIn(correction["event_hash"], source["correction_refs"])
        self.assertEqual(source["contestation_refs"], [])
        self.assertFalse(source["independent_validation"])

    def test_applied_repair_is_not_displayed_as_independently_verified(self):
        self.evidence("E1", "contradicts")
        ref = self.report()
        tid = self.brain.open_gabriel_repair(ref, requested_by="operator", provenance="fixture")["teshuvah_id"]
        self.brain.acknowledge_teshuvah(tid, "operator", "Erreur", "Confusion", "Généralisation", "fixture")
        self.brain.propose_teshuvah_repair(tid, "Retirer", "fixture")
        self.brain.apply_teshuvah_repair(tid, [{"claim_id": self.cid, "action": "retract", "reason": "Erreur"}],
                                        "operator", "fixture")
        repair = self.read([ref])["sources"][0]["repairs"][0]
        self.assertEqual(repair["phase"], "repair_applied")
        self.assertFalse(repair["independent_validation"])
        self.assertTrue(repair["trace_refs"])

    def test_modifying_a_returned_map_cannot_modify_the_source_or_objections(self):
        ref = self.report()
        before = self.read([ref])
        changed = self.read([ref])
        changed["sources"][0]["unknowns"].clear()
        changed["receipts"].clear()
        self.assertEqual(before, self.read([ref]))

    def test_invalid_requests_are_refused_without_writes(self):
        ref = self.report()
        files = self.files()
        for refs, kw in [(ref, {}), ([], {}), ([ref, ref], {}), (["unknown"], {}),
                         ([ref], {"observer_ref": " "}), ([ref], {"scope_ref": ""}),
                         ([ref], {"at_time": "2026-10-06"})]:
            with self.subTest(refs=refs, kw=kw), self.assertRaises(ValueError):
                self.read(refs, **kw)
        self.assertEqual(files, self.files())

    def test_uncommitted_edits_cannot_be_projected_as_recorded_reality(self):
        ref = self.report()
        self.brain.state["teshuvah"]["claims"][self.cid]["statement"] = "unstaged"
        with self.assertRaisesRegex(ValueError, "uncommitted"):
            self.read([ref])

    def test_damaged_journal_is_refused_before_any_projection(self):
        ref = self.report()
        with (self.root / "events.jsonl").open("a") as out:
            out.write('{"forged":true}\n')
        with self.assertRaises(ValueError):
            self.read([ref])

    def test_a_changed_boundary_during_reading_is_refused(self):
        ref = self.report()
        original = self.brain.gabriel_report
        def changed(ref):
            value = original(ref)
            self.brain.imagine("Concurrent update", [], [])
            return value
        with patch.object(self.brain, "gabriel_report", side_effect=changed):
            with self.assertRaisesRegex(ValueError, "boundary|snapshot"):
                self.read([ref])

    def test_read_only_reload_resumes_without_changing_the_history(self):
        ref = self.report()
        before, files = self.read([ref]), self.files()
        resumed = ConscienceCBrain.load_read_only(self.root)
        self.assertEqual(before, resumed.uriel_read([ref], observer_ref="reader:1", scope_ref="selection:local"))
        self.assertEqual(files, self.files())

    def test_read_only_loader_refuses_missing_or_pending_memory_without_recovery(self):
        missing = self.root / "missing"
        with self.assertRaises(ValueError):
            ConscienceCBrain.load_read_only(missing)
        self.assertFalse(missing.exists())
        (self.root / "transition.pending.json").write_text("{}")
        files = self.files()
        with self.assertRaises(ValueError):
            ConscienceCBrain.load_read_only(self.root)
        self.assertEqual(files, self.files())

    def test_cli_reading_is_real_and_does_not_bootstrap_or_record(self):
        ref = self.report()
        files = self.files()
        args = [sys.executable, "-B", "-m", "conscience_c_brain.cli", "--root", str(self.root),
                "uriel-read", ref, "--observer", "reader:1", "--scope", "selection:local"]
        result = subprocess.run(args, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout), self.read([ref]))
        self.assertEqual(files, self.files())
        args[args.index(str(self.root))] = str(self.root / "missing")
        result = subprocess.run(args, text=True, capture_output=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse((self.root / "missing").exists())
