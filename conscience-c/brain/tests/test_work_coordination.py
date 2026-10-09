"""Public coordinator against actual persisted memories and bounded processes."""
import copy
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from conscience_c_brain import (
    ConscienceCBrain, Evidence, EvidenceKind, CausalOrigin, validate_work_plan,
)
from conscience_c_brain.gabriel import GABRIEL_CRITERIA_VERSION
from conscience_c_brain.work_coordination import BLOCKS, WORK_VERSION, _execute_worker
from conscience_c_brain.work_runner import examine_reserved_read
from conscience_c_brain.transition_store import RecoveryRequired


def plan_for(cid):
    goals = [
        {"id": "ROOT", "parent": None, "text": "Reprendre un examen traçable",
         "serves_because": "Respecter le réel et les limites", "priority": 0},
        {"id": "EXAMINE", "parent": "ROOT", "text": "Clarifier avec des traces",
         "serves_because": "Un diagnostic précède une décision", "priority": 1},
        {"id": "TRANSMIT", "parent": "ROOT", "text": "Relier les lectures",
         "serves_because": "Garder les inconnues visibles", "priority": 5},
    ]
    units = []
    previous = []
    for scale in ("micro", "meso", "macro", "meta"):
        units.append({
            "id": scale,
            "purpose": {"goal_refs": ["EXAMINE"], "serves_because": "Situer le diagnostic"},
            "scope": {"view": scale, "boundary": "local", "observer": "fixture:reader",
                      "reviews": ["micro", "meso", "macro"] if scale == "meta" else []},
            "work": {"kind": "gabriel_examine", "claim_id": cid,
                     "depends_on": previous, "input_refs": ["fixture:source"],
                     "output_contract": "Un diagnostic borné, pas une réparation",
                     "subject_ref": None},
            "review": {"criteria_version": GABRIEL_CRITERIA_VERSION,
                       "objection_refs": ["OBJECTION-1"], "unknown_refs": ["UNKNOWN-1"]},
            "evidence": {"source_refs": ["fixture:source"]},
            "continuity": {"next_step": "Lire le diagnostic et décider de la suite"},
        })
        previous = [scale]
    return {"plan_id": "P1", "version": WORK_VERSION, "goals": goals, "units": units,
            "budget": {"max_attempts": 8, "timeout_seconds": 10,
                       "max_inflight": 1, "retry_delay_seconds": 0}}


class WorkCoordinationTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.cid = self.brain.record_claim(
            "Proposition de test", "system_hypothesis", "fixture:claim")["claim_id"]
        self.spec = plan_for(self.cid)

    def register(self):
        return self.brain.record_work_plan(self.spec, provenance="fixture:request")

    def single(self):
        self.spec["units"] = self.spec["units"][:1]

    def state(self, uid="micro", brain=None):
        b = brain or self.brain
        return next(u["continuity"] for u in b.work_view("P1")["units"] if u["id"] == uid)

    def evidence(self, eid="E1"):
        self.brain.ingest_evidence(Evidence(
            eid, "observation de test", EvidenceKind.ATTESTED_SOURCE,
            source_ref="fixture:" + eid, claim_ref=self.cid, scope="local",
            stance="supports"), CausalOrigin.OTHER)

    def expire(self):
        deadline = datetime.fromisoformat(self.state()["deadline"]) + timedelta(seconds=1)
        with patch("conscience_c_brain.work_coordination._clock", return_value=deadline):
            return self.brain.work_recover_expired("P1")

    def test_four_scales_execute_with_same_blocks_and_resume_after_each_step(self):
        example = Path(__file__).resolve().parents[1] / "examples" / "work-plan-gabriel.json"
        self.spec = json.loads(example.read_text(encoding="utf-8"))
        self.spec["plan_id"] = "P1"
        for unit in self.spec["units"]:
            unit["work"]["claim_id"] = self.cid
        self.evidence()
        original = copy.deepcopy(self.brain.state["S"]["invariants"])
        self.register()
        for uid in ("micro", "meso", "macro", "meta"):
            outcome = self.brain.work_run_next("P1")
            self.assertEqual(outcome["unit_id"], uid)
            self.assertEqual(outcome["outcome"], "completed")
            self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
            self.assertEqual(self.state(uid)["state"], "completed")
        view = self.brain.work_view("P1")
        self.assertEqual(view["shared_attempts_used"], 4)
        for unit in view["units"]:
            self.assertTrue(set(BLOCKS) <= set(unit))
            self.assertEqual(unit["evidence"]["result"]["report"]["verdict"], "HOLD")
        self.assertEqual(self.brain.state["S"]["invariants"], original)
        self.assertFalse(view["continuous_service_observed"])
        self.assertFalse(view["execution_authority"])
        self.assertEqual(self.brain.audit(), [])

    def test_duplicate_plan_is_idempotent_and_spec_cannot_be_overwritten(self):
        self.register()
        before = self.brain.ledger.path.read_bytes()
        self.register()
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)
        self.spec["budget"]["max_attempts"] += 1
        with self.assertRaises(ValueError):
            self.register()
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_completed_read_does_not_repeat_or_claim_repair(self):
        self.single()
        self.register()
        out = self.brain.work_run_next("P1")
        self.assertEqual(out["outcome"], "completed")
        self.assertEqual(out["view"]["units"][0]["evidence"]["result"]["report"]["verdict"], "INDETERMINATE")
        before = self.brain.ledger.path.read_bytes()
        self.assertFalse(self.brain.work_run_next("P1")["started"])
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)
        self.assertEqual(self.brain.claim(self.cid)["status"], "active")
        self.assertEqual(self.brain.teshuvah_cycles(), [])

    def test_priorities_follow_goal_hierarchy_after_dependencies(self):
        self.spec["units"][0]["purpose"]["goal_refs"] = ["TRANSMIT"]
        self.spec["units"][2]["work"]["depends_on"] = []
        self.register()
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "macro")
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "meta")
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "micro")

    def test_dependency_and_reflexive_views_retain_sources_and_unknowns(self):
        for unit in self.spec["units"][1:]:
            unit["work"]["input_refs"] = []
            unit["review"].update(objection_refs=[], unknown_refs=[])
            unit["evidence"]["source_refs"] = []
        self.register()
        self.brain.work_run_next("P1")
        macro = self.brain.work_view("P1")["units"][2]
        meta = self.brain.work_view("P1")["units"][3]
        for view in (macro, meta):
            self.assertIn("UNKNOWN-1", view["review"]["unknown_refs"])
            self.assertIn("no_explicit_applicable_support", view["review"]["unknown_refs"])
            self.assertIn("OBJECTION-1", view["review"]["objection_refs"])
            self.assertIn("fixture:source", view["evidence"]["source_refs"])
            self.assertTrue(view["evidence"]["source_refs"])

    def test_prior_gabriel_objection_survives_new_scale(self):
        prior = self.brain.record_gabriel_examination(
            self.cid, scope_ref="local", observer_ref="fixture:reader",
            provenance="fixture:diagnostic")
        objection = self.brain.contest_gabriel(
            prior["report_ref"], reason="source à vérifier", actor="fixture:other",
            provenance="fixture:objection")
        self.register()
        self.brain.work_run_next("P1")
        meta = self.brain.work_view("P1")["units"][3]
        self.assertIn(objection["event_hash"], meta["review"]["objection_refs"])

    def test_shared_attempt_budget_does_not_multiply_by_scale(self):
        self.spec["budget"]["max_attempts"] = 2
        self.register()
        self.brain.work_run_next("P1")
        self.brain.work_run_next("P1")
        before = self.brain.ledger.path.read_bytes()
        out = self.brain.work_run_next("P1")
        self.assertFalse(out["started"])
        self.assertEqual(out["view"]["shared_attempts_used"], 2)
        self.assertEqual(self.state("macro")["readiness"], "shared_budget_exhausted")
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_capacity_is_reserved_before_any_worker_starts(self):
        for unit in self.spec["units"]:
            unit["work"]["depends_on"] = []
        self.register()
        self.brain._work_start_next("P1")
        with patch("conscience_c_brain.work_coordination._execute_worker") as worker:
            self.assertFalse(self.brain.work_run_next("P1")["started"])
            worker.assert_not_called()
        self.assertEqual(self.state("meso")["readiness"], "capacity_full")
        self.assertEqual(self.brain.work_view("P1")["shared_attempts_used"], 1)

    def test_waiting_task_does_not_block_independent_work(self):
        self.spec["units"][2]["work"]["depends_on"] = []
        self.spec["budget"]["retry_delay_seconds"] = 60
        self.register()
        with patch("conscience_c_brain.work_coordination._execute_worker",
                   side_effect=subprocess.TimeoutExpired("fixture", 10)):
            self.assertEqual(self.brain.work_run_next("P1")["outcome"], "waiting")
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "macro")
        self.assertEqual(self.state()["readiness"], "retry_delay")

    def test_timeout_is_bounded_in_an_actual_subprocess(self):
        self.single()
        self.spec["budget"].update(timeout_seconds=1, max_attempts=1)
        self.register()
        def slow(root, pid, uid, attempt, timeout):
            subprocess.run([sys.executable, "-c", "import time; time.sleep(30)"],
                           timeout=timeout, capture_output=True)
        start = time.monotonic()
        with patch("conscience_c_brain.work_coordination._execute_worker", side_effect=slow):
            result = self.brain.work_run_next("P1")
        self.assertLess(time.monotonic() - start, 5)
        self.assertEqual(result["outcome"], "waiting")
        self.assertFalse(self.brain.work_run_next("P1")["started"])
        self.assertEqual(self.state()["attempts"], 1)

    def test_expired_read_resumes_without_resetting_consumed_budget(self):
        self.single()
        self.register()
        self.brain._work_start_next("P1")
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.brain.work_recover_expired("P1")["recovered"], [])
        self.assertEqual(self.expire()["recovered"], ["micro"])
        self.assertEqual(self.state()["attempts"], 1)
        self.assertEqual(self.brain.work_run_next("P1")["outcome"], "completed")
        self.assertEqual(self.state()["attempts"], 2)

    def test_older_attempt_cannot_finish_a_replacement_attempt(self):
        self.single()
        self.register()
        uid, old, timeout = self.brain._work_start_next("P1")
        self.expire()
        self.brain._work_start_next("P1")
        before = self.brain.ledger.path.read_bytes()
        with self.assertRaises(ValueError):
            self.brain._work_finish("P1", uid, old, error="old result")
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_changed_inputs_cannot_be_presented_as_current_completion(self):
        self.single()
        self.register()
        uid, attempt, _ = self.brain._work_start_next("P1")
        result = examine_reserved_read(self.brain, "P1", uid, attempt)
        self.evidence()
        self.brain._work_finish("P1", uid, attempt, result=result)
        self.assertEqual(self.state()["state"], "waiting")
        self.assertIn("inputs_changed", self.state()["error"])

    def test_existing_results_become_historical_when_evidence_changes(self):
        self.register()
        self.brain.work_run_next("P1")
        self.evidence()
        view = self.brain.work_view("P1")
        self.assertFalse(view["units"][0]["evidence"]["result_current"])
        self.assertEqual(self.state("meso")["readiness"], "dependency_requires_revision")
        self.assertEqual(self.state()["state"], "completed")

    def test_unrelated_evidence_does_not_stall_ready_work(self):
        self.register()
        self.brain.work_run_next("P1")
        self.brain.ingest_evidence(Evidence(
            "UNRELATED", "autre contexte", EvidenceKind.ATTESTED_SOURCE,
            source_ref="fixture:unrelated", claim_ref="another-claim"),
            CausalOrigin.OTHER)
        self.assertTrue(self.brain.work_view("P1")["units"][0]["evidence"]["result_current"])
        self.assertEqual(self.brain.work_run_next("P1")["unit_id"], "meso")

    def test_expired_evidence_invalidates_currentness_without_rewriting_history(self):
        expires = datetime.now(timezone.utc) + timedelta(minutes=5)
        self.brain.ingest_evidence(Evidence(
            "E1", "observation temporaire", EvidenceKind.ATTESTED_SOURCE,
            source_ref="fixture:E1", claim_ref=self.cid, scope="local",
            stance="supports", expires_at=expires.isoformat()), CausalOrigin.OTHER)
        self.register()
        self.brain.work_run_next("P1")
        before = self.brain.ledger.path.read_bytes()
        with patch("conscience_c_brain.work_coordination._clock",
                   return_value=expires + timedelta(seconds=1)):
            self.assertFalse(self.brain.work_view("P1")["units"][0]["evidence"]["result_current"])
            self.assertEqual(self.state("meso")["readiness"], "dependency_requires_revision")
        self.assertEqual(before, self.brain.ledger.path.read_bytes())

    def test_new_objection_is_visible_even_when_result_becomes_historical(self):
        prior = self.brain.record_gabriel_examination(
            self.cid, scope_ref="local", observer_ref="fixture:reader", provenance="fixture")
        self.register()
        self.brain.work_run_next("P1")
        objection = self.brain.contest_gabriel(
            prior["report_ref"], reason="nouvelle objection", actor="fixture:other", provenance="fixture")
        meta = self.brain.work_view("P1")["units"][3]
        self.assertIn(objection["event_hash"], meta["review"]["objection_refs"])
        self.assertEqual(self.state("meso")["readiness"], "dependency_requires_revision")

    def test_criteria_upgrade_preserves_history_and_stops_new_dispatch(self):
        self.register()
        with patch("conscience_c_brain.work_coordination.GABRIEL_CRITERIA_VERSION", "2.0"):
            loaded = ConscienceCBrain.load_or_bootstrap(self.root)
            self.assertEqual(loaded.audit(), [])
            self.assertEqual(self.state(brain=loaded)["readiness"], "criteria_revision_required")
            self.assertFalse(loaded.work_run_next("P1")["started"])

    def test_forged_worker_output_does_not_complete_work(self):
        self.single()
        self.register()
        uid, attempt, _ = self.brain._work_start_next("P1")
        result = examine_reserved_read(self.brain, "P1", uid, attempt)
        result["report"]["scope_ref"] = "elsewhere"
        self.brain._work_finish("P1", uid, attempt, result=result)
        self.assertEqual(self.state()["state"], "waiting")
        self.assertEqual(self.state()["error"], "worker_output_invalid")
        self.assertIsNone(self.brain.work_view("P1")["units"][0]["evidence"]["result"])

    def test_uncommitted_or_privately_saved_work_edits_are_not_attested(self):
        self.register()
        self.brain.state["work_coordination"]["P1"]["units"]["micro"]["state"] = "completed"
        with self.assertRaises(ValueError):
            self.brain.work_view("P1")
        self.brain._save()
        with self.assertRaises(ValueError):
            ConscienceCBrain.load_or_bootstrap(self.root)

    def test_stale_reader_cannot_reserve_another_attempt(self):
        self.register()
        stale = ConscienceCBrain.load_or_bootstrap(self.root)
        self.brain._work_start_next("P1")
        before = self.brain.ledger.path.read_bytes()
        with self.assertRaises(ValueError):
            stale.work_run_next("P1")
        self.assertEqual(self.brain.ledger.path.read_bytes(), before)

    def test_failed_prepare_does_not_consume_an_uncommitted_attempt(self):
        self.single()
        self.register()
        def fail(stage):
            if stage == "after_prepare":
                raise OSError("fixture:power loss")
        with patch.object(self.brain._store, "_stage", side_effect=fail):
            with self.assertRaises(OSError):
                self.brain.work_run_next("P1")
        with self.assertRaises(RecoveryRequired):
            self.brain._transition("anything", {}, CausalOrigin.SELF)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.state()["attempts"], 0)
        self.assertEqual(self.brain.work_run_next("P1")["outcome"], "completed")

    def test_result_committed_before_crash_is_recovered_without_reexecution(self):
        self.single()
        self.register()
        uid, attempt, timeout = self.brain._work_start_next("P1")
        result = _execute_worker(self.root, "P1", uid, attempt, timeout)
        def fail(stage):
            if stage == "after_append":
                raise OSError("fixture:power loss")
        with patch.object(self.brain._store, "_stage", side_effect=fail):
            with self.assertRaises(OSError):
                self.brain._work_finish("P1", uid, attempt, result=result)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        with patch("conscience_c_brain.work_coordination._execute_worker") as worker:
            self.assertFalse(self.brain.work_run_next("P1")["started"])
            worker.assert_not_called()
        self.assertEqual(self.state()["state"], "completed")
        self.assertEqual(self.state()["attempts"], 1)
        self.assertEqual(self.brain.audit(), [])

    def test_actual_process_exit_after_reservation_is_recoverable(self):
        self.single()
        self.register()
        script = """
import os, sys
from pathlib import Path
from conscience_c_brain import ConscienceCBrain
b=ConscienceCBrain.load_or_bootstrap(Path(sys.argv[1]))
b._store._stage=lambda stage: os._exit(74) if stage=='after_append' else None
b.work_run_next('P1')
"""
        process = subprocess.run([sys.executable, "-c", script, str(self.root)],
            env={**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])},
            capture_output=True, timeout=10)
        self.assertEqual(process.returncode, 74, process.stderr.decode())
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.state()["state"], "running")
        self.expire()
        self.assertEqual(self.brain.work_run_next("P1")["outcome"], "completed")
        self.assertEqual(self.state()["attempts"], 2)
        self.assertEqual(self.brain.state["n"], len(self.brain.ledger.read_verified()) - 1)

    def test_invalid_contracts_never_mutate_memory(self):
        originals = {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()}
        cases = [
            (("budget", "max_attempts"), True),
            (("units", 0, "work", "kind"), "deploy"),
            (("units", 0, "work", "depends_on"), ["meta"]),
            (("goals", 0, "parent"), "EXAMINE"),
            (("units", 3, "scope", "reviews"), []),
            (("units", 0, "purpose", "serves_because"), ""),
            (("units", 0, "purpose", "goal_refs"), [["not-hashable"]]),
            (("units", 0, "work", "claim_id"), "missing"),
            (("units", 0, "review", "criteria_version"), "old"),
        ]
        for path, value in cases:
            spec = copy.deepcopy(self.spec)
            target = spec
            for key in path[:-1]:
                target = target[key]
            target[path[-1]] = value
            with self.subTest(path=path), self.assertRaises(ValueError):
                self.brain.record_work_plan(spec, provenance="fixture")
        self.assertEqual(originals, {p.name: p.read_bytes() for p in self.root.iterdir() if p.is_file()})

    def test_cli_uses_existing_memory_and_runs_one_unit(self):
        self.single()
        specfile = self.root / "plan.json"
        specfile.write_text(json.dumps(self.spec), encoding="utf-8")
        base = [sys.executable, "-m", "conscience_c_brain.cli", "--root", str(self.root)]
        for command in (["work-register", str(specfile), "--provenance", "fixture"],
                        ["work-view", "P1"], ["work-next", "P1"]):
            proc = subprocess.run(base + command, capture_output=True, text=True, timeout=15)
            self.assertEqual(proc.returncode, 0, proc.stderr)
            json.loads(proc.stdout)
        self.brain = ConscienceCBrain.load_or_bootstrap(self.root)
        self.assertEqual(self.state()["state"], "completed")

    def test_cli_refuses_to_bootstrap_a_workflow_memory(self):
        missing = self.root / "missing"
        process = subprocess.run(
            [sys.executable, "-m", "conscience_c_brain.cli", "--root", str(missing), "work-view", "P1"],
            capture_output=True, text=True, timeout=10)
        self.assertNotEqual(process.returncode, 0)
        self.assertFalse(missing.exists())


if __name__ == "__main__":
    unittest.main()
