"""Meaningful work remains reachable despite failures and process recovery."""
import copy
from datetime import datetime, timedelta
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from conscience_c_brain import ConscienceCBrain
from conscience_c_brain.checkpoint_integrity import verified_history
from test_work_coordination import plan_for


class WorkSchedulingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        cid = self.brain.record_claim("Fixture locale", "system_hypothesis", "fixture")["claim_id"]
        self.spec = plan_for(cid)
        self.spec["version"] = "CC-WORK-2"
        self.spec["scheduling"] = {"version": "CC-SCHEDULE-1", "fair_after": 3,
                                   "inherit_priorities": True}
        self.spec["budget"].update(max_attempts=16, retry_delay_seconds=0)
        for unit in self.spec["units"]:
            unit["work"]["depends_on"] = []
            unit["purpose"]["goal_refs"] = ["TRANSMIT"]
        self.spec["units"][0]["purpose"]["goal_refs"] = ["EXAMINE"]

    def register(self):
        return self.brain.record_work_plan(self.spec, provenance="fixture:scheduling")

    def unit(self, uid):
        return next(u for u in self.brain.work_view("P1")["units"] if u["id"] == uid)

    def fail_next(self):
        uid, attempt, _ = self.brain._work_start_next("P1")
        self.brain._work_finish("P1", uid, attempt, error="fixture:read failed")
        return uid

    def test_ready_work_at_all_scales_survives_repeated_priority_failure(self):
        self.register()
        selected = [self.fail_next() for _ in range(6)]
        self.assertEqual(selected, ["micro", "micro", "micro", "meso", "macro", "meta"])
        for uid in ("meso", "macro", "meta"):
            self.assertGreater(self.unit(uid)["continuity"]["attempts"], 0)
        self.assertEqual(self.brain.work_view("P1")["shared_attempts_used"], 6)
        self.assertFalse(self.brain.work_view("P1")["continuous_service_observed"])

    def test_priority_reaches_transitive_dependency_with_a_traceable_purpose(self):
        # A low-ranked micro read is needed by an urgent meta read. Independent
        # medium-ranked work must not mask that critical dependency.
        units = self.spec["units"]
        self.spec["goals"].append({"id": "MEDIUM", "parent": "ROOT", "text": "Autre lecture",
            "serves_because": "Tâche indépendante", "priority": 3})
        units[0]["purpose"]["goal_refs"] = ["TRANSMIT"]
        units[1]["work"]["depends_on"] = ["micro"]
        units[2]["purpose"]["goal_refs"] = ["MEDIUM"]
        units[3]["purpose"]["goal_refs"] = ["EXAMINE"]
        units[3]["work"]["depends_on"] = ["meso"]
        self.register()
        schedule = self.unit("micro")["continuity"]["scheduling"]
        self.assertEqual(schedule["declared_priority"], [0, 5])
        self.assertEqual(schedule["effective_priority"], [0, 1])
        self.assertEqual(schedule["priority_from"], ["meta"])
        self.assertEqual(schedule["goal_paths"], [["ROOT", "TRANSMIT"]])
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "micro")
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "meso")
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "meta")

    def test_reflexive_review_is_not_an_execution_dependency(self):
        self.spec["units"][0]["purpose"]["goal_refs"] = ["TRANSMIT"]
        self.spec["units"][2]["purpose"]["goal_refs"] = ["EXAMINE"]
        self.spec["units"][3]["purpose"]["goal_refs"] = ["ROOT"]
        self.register()
        self.assertEqual(self.unit("micro")["continuity"]["scheduling"]["effective_priority"], [0, 5])
        self.assertEqual(self.brain.work_view("P1")["ready"][0], "meta")

    def test_inheritance_can_be_explicitly_disabled(self):
        self.spec["scheduling"]["inherit_priorities"] = False
        self.spec["units"][0]["purpose"]["goal_refs"] = ["TRANSMIT"]
        self.spec["units"][3]["work"]["depends_on"] = ["micro"]
        self.spec["units"][3]["purpose"]["goal_refs"] = ["EXAMINE"]
        self.register()
        self.assertEqual(self.unit("micro")["continuity"]["scheduling"]["effective_priority"], [0, 5])
        self.assertEqual(self.unit("micro")["continuity"]["scheduling"]["priority_from"], ["micro"])

    def test_polling_neither_ages_work_nor_writes_history(self):
        self.register()
        before = self.brain.ledger.path.read_bytes()
        for _ in range(8):
            view = self.brain.work_view("P1")
            self.assertEqual(view["scheduling"]["dispatches"], 0)
            self.assertEqual(self.unit("meta")["continuity"]["scheduling"]["waiting_dispatches"], 0)
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_wait_counters_and_choice_resume_without_reset_after_process_exit(self):
        self.register()
        self.assertEqual(self.fail_next(), "micro")
        self.assertEqual(self.fail_next(), "micro")
        script = """
import os,sys
from pathlib import Path
from conscience_c_brain import ConscienceCBrain
b=ConscienceCBrain.load_or_bootstrap(Path(sys.argv[1]))
b._store._stage=lambda stage: os._exit(74) if stage=='after_append' else None
b.work_run_next('P1')
"""
        proc = subprocess.run([sys.executable, "-c", script, str(self.root)],
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
            capture_output=True, timeout=15)
        self.assertEqual(proc.returncode, 74, proc.stderr.decode())
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.unit("meta")["continuity"]["scheduling"]["waiting_dispatches"], 3)
        deadline = datetime.fromisoformat(self.unit("micro")["continuity"]["deadline"])
        with patch("conscience_c_brain.work_coordination._clock", return_value=deadline + timedelta(seconds=1)):
            self.brain.work_recover_expired("P1")
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "meso")
        self.assertEqual(self.brain.work_view("P1")["scheduling"]["dispatches"], 4)
        self.assertEqual(self.brain.audit(), [])

    def test_uncommitted_reservation_does_not_age_other_scales(self):
        self.register()
        def fail(stage):
            if stage == "after_prepare":
                raise OSError("fixture:failed write")
        with patch.object(self.brain._store, "_stage", side_effect=fail), self.assertRaises(OSError):
            self.brain._work_start_next("P1")
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.brain.work_view("P1")["scheduling"]["dispatches"], 0)
        self.assertEqual(self.unit("meta")["continuity"]["scheduling"]["waiting_dispatches"], 0)

    def test_delay_and_dependencies_remain_binding_for_aged_work(self):
        self.spec["scheduling"]["fair_after"] = 1
        self.spec["budget"]["retry_delay_seconds"] = 3600
        self.spec["units"][3]["work"]["depends_on"] = ["meso"]
        self.register()
        self.assertEqual(self.fail_next(), "micro")
        self.assertEqual(self.unit("micro")["continuity"]["readiness"], "retry_delay")
        self.assertEqual(self.unit("meta")["continuity"]["readiness"], "dependency_pending")
        self.assertEqual(self.brain.work_view("P1")["ready"], ["meso", "macro"])

    def test_shared_budget_and_capacity_cannot_be_bypassed_by_fairness(self):
        self.spec["scheduling"]["fair_after"] = 1
        self.spec["budget"]["max_attempts"] = 2
        self.register()
        uid, attempt, _ = self.brain._work_start_next("P1")
        self.assertFalse(self.brain.work_run_next("P1")["started"])
        self.brain._work_finish("P1", uid, attempt, error="fixture")
        self.assertEqual(self.fail_next(), "meso")
        before = self.brain.ledger.path.read_bytes()
        self.assertFalse(self.brain.work_run_next("P1")["started"])
        self.assertEqual(self.brain.work_view("P1")["scheduling"]["dispatches"], 2)
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_old_contract_order_and_existing_snapshot_are_preserved(self):
        self.spec["version"] = "CC-WORK-1"
        self.spec.pop("scheduling")
        self.register()
        original = copy.deepcopy(self.brain.state["S"]["invariants"])
        selected = [self.fail_next() for _ in range(4)]
        self.assertEqual(selected, ["micro"] * 4)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.brain.work_view("P1")["version"], "CC-WORK-1")
        self.assertNotIn("scheduler", self.brain.state["work_coordination"]["P1"])
        self.assertEqual(self.brain.state["S"]["invariants"], original)

    def test_scheduling_parameters_cannot_be_changed_or_mistyped(self):
        before = self.brain.ledger.path.read_bytes()
        for value in (True, 0, 129, "3"):
            bad = copy.deepcopy(self.spec)
            bad["scheduling"]["fair_after"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.brain.record_work_plan(bad, provenance="fixture")
        bad = copy.deepcopy(self.spec)
        bad["scheduling"]["inherit_priorities"] = 1
        with self.assertRaises(ValueError):
            self.brain.record_work_plan(bad, provenance="fixture")
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)
        self.register()
        self.spec["scheduling"]["fair_after"] = 2
        with self.assertRaisesRegex(ValueError, "immutable"):
            self.register()

    def test_forged_aging_cannot_become_a_valid_checkpoint(self):
        self.register()
        self.brain.state["work_coordination"]["P1"]["scheduler"]["waits"]["meta"] = 999
        with self.assertRaises(ValueError):
            self.brain.work_view("P1")
        self.brain._save()
        with self.assertRaises(ValueError):
            ConscienceCBrain.load_or_bootstrap(self.root)

    def test_objections_and_located_unknowns_survive_fair_scheduling(self):
        self.register()
        prior = self.brain.record_gabriel_examination(self.spec["units"][0]["work"]["claim_id"],
            scope_ref="local", observer_ref="fixture", provenance="fixture")
        objection = self.brain.contest_gabriel(prior["report_ref"], reason="source absente",
                                              actor="fixture:other", provenance="fixture")
        for _ in range(3):
            self.assertEqual(self.fail_next(), "micro")
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "meso")
        view = self.unit("meso")
        self.assertIn(objection["event_hash"], view["review"]["objection_refs"])
        self.assertTrue(view["review"]["unknown_details"])
        self.assertEqual(view["evidence"]["result"]["report"]["verdict"], "INDETERMINATE")
        self.assertFalse(view["evidence"]["result"]["execution_authority"])

    def test_choice_receipt_is_recorded_with_reservation_and_rejects_inconsistent_age(self):
        self.register()
        self.fail_next()
        rows = verified_history(self.brain)
        record = next(r for r in rows if r["event_type"] == "WORK_PROGRESS_RECORDED"
                      and r["payload"]["unit"]["state"] == "running")
        receipt = record["payload"]["scheduling"]
        self.assertEqual(receipt["receipt"]["selected"], "micro")
        self.assertEqual(receipt["receipt"]["reason"], "effective_priority")
        self.assertEqual(receipt["after"]["waits"]["meta"], 1)
        from conscience_c_brain.work_coordination import _projection
        changed = copy.deepcopy(rows)
        index = next(i for i, row in enumerate(changed) if row["event_hash"] == record["event_hash"])
        changed[index]["payload"]["scheduling"]["after"]["waits"]["meta"] = 900
        with self.assertRaises(ValueError):
            _projection(changed)

    def test_read_view_verifies_history_once_instead_of_once_per_unit(self):
        self.register()
        self.brain.record_gabriel_examination(self.spec["units"][0]["work"]["claim_id"],
            scope_ref="local", observer_ref="fixture", provenance="fixture")
        self.brain.work_run_next("P1")
        with patch.object(self.brain.ledger, "read_verified", wraps=self.brain.ledger.read_verified) as read:
            self.brain.work_view("P1")
            self.assertEqual(read.call_count, 1)
        # A shared read must still reject a changed snapshot / ledger boundary.
        self.brain.state["last_event_hash"] = "wrong"
        with self.assertRaises(ValueError):
            self.brain.work_view("P1")

    def test_new_criteria_block_execution_without_invalidating_recorded_choices(self):
        self.register()
        self.fail_next()
        before = self.brain.ledger.path.read_bytes()
        with patch("conscience_c_brain.work_coordination.GABRIEL_CRITERIA_VERSION", "2.0.0"):
            self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
            self.assertFalse(self.brain.work_run_next("P1")["started"])
            self.assertEqual(self.unit("meta")["continuity"]["readiness"], "criteria_revision_required")
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_unusable_dependency_excludes_the_consumers_priority(self):
        units = self.spec["units"]
        units[0]["purpose"]["goal_refs"] = ["TRANSMIT"]
        units[3]["purpose"]["goal_refs"] = ["EXAMINE"]
        units[3]["work"]["depends_on"] = ["micro", "meso"]
        meso_claim = self.brain.record_claim("Autre proposition", "system_hypothesis", "fixture")["claim_id"]
        units[1]["work"]["claim_id"] = meso_claim
        self.spec["units"] = [units[1], units[0], units[2], units[3]]
        self.register()
        # Complete meso, then change its claim context so that its result is
        # historical. The pending meta now needs revision, not priority help.
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "meso")
        self.assertEqual(self.unit("micro")["continuity"]["scheduling"]["effective_priority"], [0, 1])
        from conscience_c_brain import Evidence, EvidenceKind, CausalOrigin
        self.brain.ingest_evidence(Evidence("E-change", "Nouvelle trace de test", EvidenceKind.ATTESTED_SOURCE,
            source_ref="fixture:changed", claim_ref=meso_claim, scope="local", stance="supports"), CausalOrigin.OTHER)
        self.assertEqual(self.unit("meso")["continuity"]["readiness"], "completed_result_historical")
        self.assertEqual(self.unit("micro")["continuity"]["scheduling"]["effective_priority"], [0, 5])

    def dependent_claims(self):
        self.spec["budget"].update(max_attempts=10)
        previous = []
        for index, unit in enumerate(self.spec["units"]):
            unit["work"]["depends_on"] = previous
            if index:
                unit["work"]["claim_id"] = self.brain.record_claim(
                    "Proposition distincte " + str(index), "system_hypothesis", "fixture")["claim_id"]
            previous = [unit["id"]]
        self.register()
        return self.spec["units"][0]["work"]["claim_id"]

    def change_micro(self, cid):
        from conscience_c_brain import Evidence, EvidenceKind, CausalOrigin
        self.brain.ingest_evidence(Evidence("E-micro-change", "Trace de test ajoutée", EvidenceKind.ATTESTED_SOURCE,
            source_ref="fixture:micro-change", claim_ref=cid, scope="local", stance="supports"), CausalOrigin.OTHER)

    def assert_syntheses_become_historical(self):
        cid = self.dependent_claims()
        for _ in range(4):
            self.brain.work_run_next("P1")
        self.assertTrue(all(u["evidence"]["result_current"] for u in self.brain.work_view("P1")["units"]))
        self.change_micro(cid)
        before = self.brain.ledger.path.read_bytes()
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        for unit in self.brain.work_view("P1")["units"]:
            self.assertFalse(unit["evidence"]["result_current"])
            self.assertEqual(unit["continuity"]["readiness"], "completed_result_historical")
            self.assertIsNotNone(unit["evidence"]["result"])
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_changed_micro_evidence_makes_completed_syntheses_historical_transitively(self):
        self.assert_syntheses_become_historical()

    def test_legacy_syntheses_keep_history_and_encoding_but_expose_stale_dependencies(self):
        self.spec["version"] = "CC-WORK-1"
        self.spec.pop("scheduling")
        self.assert_syntheses_become_historical()

    def test_dependency_change_during_read_cannot_publish_a_current_v2_result(self):
        cid = self.dependent_claims()
        self.brain.work_run_next("P1")
        uid, attempt, _ = self.brain._work_start_next("P1")
        self.assertEqual(uid, "meso")
        from conscience_c_brain.work_runner import examine_reserved_read
        result = examine_reserved_read(self.brain, "P1", uid, attempt)
        self.change_micro(cid)
        self.brain._work_finish("P1", uid, attempt, result=result)
        self.assertEqual(self.unit("meso")["continuity"]["state"], "waiting")
        self.assertIn("inputs_changed", self.unit("meso")["continuity"]["error"])
        self.assertEqual(self.unit("meso")["continuity"]["readiness"], "dependency_requires_revision")
        self.assertIsNone(self.unit("meso")["evidence"]["result"])


if __name__ == "__main__":
    unittest.main()
