"""Private subprocess entry point: one read-only examination, JSON result."""
from __future__ import annotations

import json
from pathlib import Path
import sys

from .core import ConscienceCBrain
from .checkpoint_integrity import verified_history


def examine_reserved_read(brain, plan_id, unit_id, attempt_id):
    plan = brain._work_plans().get(plan_id)
    if plan is None or unit_id not in plan["units"]:
        raise ValueError("unknown reserved work")
    current = plan["units"][unit_id]
    if current["state"] != "running" or current["attempt_id"] != attempt_id:
        raise ValueError("attempt is not current")
    unit = next(u for u in plan["spec"]["units"] if u["id"] == unit_id)
    report = brain.gabriel_examine(
        unit["work"]["claim_id"], scope_ref=unit["scope"]["boundary"],
        observer_ref=unit["scope"]["observer"], scale=unit["scope"]["view"],
        subject_ref=unit["work"]["subject_ref"])
    # Preserve prior diagnostic objections; a new scale must not erase them.
    reports = [r for r in verified_history(brain)
               if r["event_type"] == "GABRIEL_EXAMINED"
               and r["payload"]["report"]["claim_id"] == unit["work"]["claim_id"]]
    report["objection_refs"] = []
    if reports:
        prior = brain.gabriel_report(reports[-1]["event_hash"])
        report["objection_refs"] = prior["contestation_refs"]
    return {"attempt_id": attempt_id, "basis_digest": brain._work_plan_bases(plan)[unit_id],
            "report": report, "execution_authority": False,
            "result_kind": "bounded_local_diagnostic"}


def main():
    root, plan_id, unit_id, attempt_id = sys.argv[1:]
    root = Path(root)
    if not (root / "state.json").is_file() or not (root / "events.jsonl").is_file():
        raise ValueError("worker requires an existing memory; no bootstrap")
    brain = ConscienceCBrain.load_or_bootstrap(root)
    print(json.dumps(examine_reserved_read(brain, plan_id, unit_id, attempt_id),
                     ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
