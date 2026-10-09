"""Preserve recorded bases while bounding repeated cross-scale evidence reads."""
import copy
from datetime import datetime, timedelta, timezone
import unittest

from conscience_c_brain.work_coordination import WorkCoordinationMixin, _initial
from conscience_c_brain.work_scheduling import SCHEDULED_WORK_VERSION
from test_work_coordination import plan_for


def basis_fixture(version="CC-WORK-1"):
    brain = WorkCoordinationMixin()
    brain.state = {
        "teshuvah": {"claims": {
            "CLAIM-A": {"facts": ["fact", "missing"], "proposition": "A"},
            "CLAIM-B": {"facts": [], "proposition": "B"},
        }},
        "E": {"evidence": {
            "fact": {"derived_from": ["origin"], "content": "trace"},
            "origin": {"derived_from": ["fact"], "expires_at": "2026-10-08T00:00:00Z"},
            "linked": {"claim_ref": "CLAIM-A", "valid_at": "invalid-date"},
            "b-evidence": {"claim_ref": "CLAIM-B", "valid_at": "2026-10-10T00:00:00Z"},
            "unrelated": {"claim_ref": "CLAIM-C", "content": "not an input"},
        }},
    }
    rows = [
        {"event_hash": "report-a1", "event_type": "GABRIEL_EXAMINED",
         "payload": {"report": {"claim_id": "CLAIM-A"}}},
        {"event_hash": "report-b", "event_type": "GABRIEL_EXAMINED",
         "payload": {"report": {"claim_id": "CLAIM-B"}}},
        {"event_hash": "objection-a", "event_type": "GABRIEL_CONTESTED",
         "payload": {"report_ref": "report-a1"}},
        {"event_hash": "correction-b", "event_type": "GABRIEL_CORRECTED",
         "payload": {"report_ref": "report-b"}},
        {"event_hash": "report-a2", "event_type": "GABRIEL_EXAMINED",
         "payload": {"report": {"claim_id": "CLAIM-A"}}},
        {"event_hash": "unrelated-report", "event_type": "GABRIEL_EXAMINED",
         "payload": {"report": {"claim_id": "CLAIM-C"}}},
    ]
    spec = plan_for("CLAIM-A")
    spec["units"][2]["work"]["claim_id"] = "CLAIM-B"
    spec["version"] = version
    if version == SCHEDULED_WORK_VERSION:
        spec["scheduling"] = {"version": "CC-SCHEDULE-1", "fair_after": 3,
                              "inherit_priorities": True}
    return brain, _initial(spec), rows, datetime(2026, 10, 9, tzinfo=timezone.utc)


class CountingEvidence(dict):
    scans = 0

    def items(self):
        self.scans += 1
        return super().items()


class CountingHistory(list):
    scans = 0

    def __iter__(self):
        self.scans += 1
        return super().__iter__()


class WorkEvidenceTests(unittest.TestCase):
    # Captured before the optimization from main at 1461cd31022f, with
    # ancestors, unresolved fact refs, temporal limits and historical objections.
    def test_legacy_recorded_bases_keep_their_exact_encoding(self):
        brain, plan, rows, now = basis_fixture()
        self.assertEqual(brain._work_plan_bases(plan, history=rows, at_time=now), {
            "micro": "7fe2c7b577d66893bc5042f852d34ad64942e55479e9ceedec0d118dcd07341a",
            "meso": "975dd01a79bc698127f1011027918dcb5d6d9b690be06772f05797fa00d3b91c",
            "macro": "0b97a914ae65f38f6d2a5aee4680d9e95677d2b882f771f2e4f4e8c5a5307e7c",
            "meta": "ef7f249e9b61dc0902eacd5bc7af0580f5bedd005cdad609aebace443857e2aa",
        })

    def test_scheduled_bases_keep_their_exact_dependency_encoding(self):
        brain, plan, rows, now = basis_fixture(SCHEDULED_WORK_VERSION)
        self.assertEqual(brain._work_plan_bases(plan, history=rows, at_time=now), {
            "micro": "1c2626467cdb7fabe23f8b0f01a8caf151919485d5c95f931f8675050d695fa0",
            "meso": "7ce9a4a3d0f868e32e4f35fa6e6a92c65064cd523abdad07c31dfe62c2ba137d",
            "macro": "cb3b0e00cb928bcf7f53d7ae35846411013c26060597feaa583204b32ac2e464",
            "meta": "41de7e37ed420ddf1cabb100b9dcb5ed600403944589b33a2416fc257da109ed",
        })

    def test_many_scale_views_do_not_rescan_all_evidence_and_history_per_unit(self):
        brain, plan, rows, now = basis_fixture()
        template = plan["spec"]["units"][0]
        plan["spec"]["units"] = []
        for index in range(128):
            unit = copy.deepcopy(template)
            unit["id"] = "view-" + str(index)
            unit["scope"]["view"] = ("micro", "meso", "macro", "meta")[index % 4]
            if unit["scope"]["view"] == "meta":
                unit["scope"]["reviews"] = ["view-0"]
            plan["spec"]["units"].append(unit)
        plan = _initial(plan["spec"])
        evidence = CountingEvidence(brain.state["E"]["evidence"])
        brain.state["E"]["evidence"] = evidence
        history = CountingHistory(rows)
        bases = brain._work_plan_bases(plan, history=history, at_time=now)
        self.assertEqual(len(bases), 128)
        self.assertLessEqual(evidence.scans, 1)
        self.assertLessEqual(history.scans, 2)

    def test_selected_reads_keep_transitive_dependencies_and_skip_unrelated_claims(self):
        for version in ("CC-WORK-1", SCHEDULED_WORK_VERSION):
            with self.subTest(version=version):
                brain, plan, rows, now = basis_fixture(version)
                full = brain._work_plan_bases(plan, history=rows, at_time=now)
                self.assertEqual(brain._work_plan_bases(
                    plan, history=rows, at_time=now, unit_ids=["meta"]), {"meta": full["meta"]})
                # The micro read does not need CLAIM-B's evidence context.
                # A consulted bad temporal trace must never be silently masked.
                brain.state["E"]["evidence"]["b-evidence"]["expires_at"] = "invalid-date"
                micro = brain._work_plan_bases(plan, history=rows, at_time=now, unit_ids=["micro"])
                self.assertEqual(micro, {"micro": full["micro"]})
                if version == SCHEDULED_WORK_VERSION:
                    self.assertNotEqual(brain._work_plan_bases(
                        plan, history=rows, at_time=now, unit_ids=["meta"])["meta"], full["meta"])

    def test_shared_context_is_rebuilt_after_evidence_objections_or_time_change(self):
        brain, plan, rows, now = basis_fixture(SCHEDULED_WORK_VERSION)
        before = brain._work_plan_bases(plan, history=rows, at_time=now)
        later = brain._work_plan_bases(plan, history=rows, at_time=now + timedelta(days=2))
        self.assertEqual(later["micro"], before["micro"])
        self.assertNotEqual(later["macro"], before["macro"])
        self.assertNotEqual(later["meta"], before["meta"])
        brain.state["E"]["evidence"]["fact"]["content"] = "new trace"
        changed = brain._work_plan_bases(plan, history=rows, at_time=now)
        self.assertTrue(all(changed[uid] != before[uid] for uid in before))
        rows.append({"event_hash": "new-objection", "event_type": "GABRIEL_CONTESTED",
                     "payload": {"report_ref": "report-a2"}})
        contested = brain._work_plan_bases(plan, history=rows, at_time=now)
        self.assertTrue(all(contested[uid] != changed[uid] for uid in before))


if __name__ == "__main__":
    unittest.main()
