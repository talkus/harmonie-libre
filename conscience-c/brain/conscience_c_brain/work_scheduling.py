"""One declared scheduling policy across scales; no execution authority.

Pure calculations over a validated immutable plan and recorded scheduler state.
Goal priority is an operator declaration, never inferred from prose or a scale.
"""
from __future__ import annotations

import copy
from datetime import datetime

from .checkpoint_integrity import equal_json


SCHEDULED_WORK_VERSION = "CC-WORK-2"
SCHEDULING_VERSION = "CC-SCHEDULE-1"


def initial_scheduler(spec):
    return {"dispatches": 0, "waits": {u["id"]: 0 for u in spec["units"]}}


def goal_paths(unit, goals):
    paths = []
    for gid in unit["purpose"]["goal_refs"]:
        path = []
        while gid is not None:
            path.append(gid)
            gid = goals[gid]["parent"]
        paths.append(list(reversed(path)))
    return paths


def scheduling_view(spec, runtime, scheduler, eligible, revision_unavailable):
    by_id = {u["id"]: u for u in spec["units"]}
    goals = {g["id"]: g for g in spec["goals"]}
    paths = {uid: goal_paths(u, goals) for uid, u in by_id.items()}
    declared = {uid: min(tuple(goals[g]["priority"] for g in path) for path in paths[uid])
                for uid in by_id}
    effective = dict(declared)
    sources = {uid: [uid] for uid in by_id}
    dependency_order, visited = [], set()
    def visit(uid):
        if uid not in visited:
            visited.add(uid)
            for dep in by_id[uid]["work"]["depends_on"]:
                visit(dep)
            dependency_order.append(uid)
    for uid in by_id:
        visit(uid)
    unavailable = set(revision_unavailable)
    # A stale, blocked or obsolete dependency makes its consumers unsuitable
    # sources of priority. The objection remains visible in the work view.
    for uid in dependency_order:
        if set(by_id[uid]["work"]["depends_on"]) & unavailable:
            unavailable.add(uid)
    if spec["scheduling"]["inherit_priorities"]:
        # Consumers precede their dependencies here, so priority and its
        # original purpose travel transitively in one graph traversal.
        for consumer in reversed(dependency_order):
            if consumer in unavailable or runtime[consumer]["state"] not in {"queued", "waiting"}:
                continue
            for target in by_id[consumer]["work"]["depends_on"]:
                if runtime[target]["state"] not in {"queued", "waiting"}:
                    continue
                if effective[consumer] < effective[target]:
                    effective[target], sources[target] = effective[consumer], list(sources[consumer])
                elif effective[consumer] == effective[target]:
                    sources[target] = list(dict.fromkeys(sources[target] + sources[consumer]))
    ready = set(eligible)
    threshold = spec["scheduling"]["fair_after"]
    details = {uid: {
        "policy_version": SCHEDULING_VERSION,
        "goal_paths": paths[uid], "declared_priority": list(declared[uid]),
        "effective_priority": list(effective[uid]),
        "priority_from": [source for source in by_id if source in sources[uid]],
        "waiting_dispatches": scheduler["waits"][uid],
        "fairness_due": uid in ready and scheduler["waits"][uid] >= threshold,
    } for uid in by_id}
    indices = {uid: i for i, uid in enumerate(by_id)}
    def order(uid):
        aged = details[uid]["fairness_due"]
        return (0 if aged else 1, -scheduler["waits"][uid] if aged else 0,
                effective[uid], indices[uid])
    return sorted(eligible, key=order), details


def advance_scheduler(spec, runtime, scheduler, receipt):
    """Recalculate the recorded choice and counters, not supplied after-state."""
    fields = {"version", "eligible", "revision_unavailable", "selected", "reason",
              "decision_at", "ledger_boundary", "criteria_version"}
    if not isinstance(receipt, dict) or set(receipt) != fields or receipt["version"] != SCHEDULING_VERSION:
        raise ValueError("invalid scheduling receipt")
    ids = set(runtime)
    for key in ("eligible", "revision_unavailable"):
        value = receipt[key]
        if (not isinstance(value, list) or any(type(uid) is not str or uid not in ids for uid in value)
                or len(value) != len(set(value))):
            raise ValueError("invalid scheduling references")
    eligible = receipt["eligible"]
    try:
        decision_at = datetime.fromisoformat(receipt["decision_at"].replace("Z", "+00:00"))
        if decision_at.tzinfo is None:
            raise ValueError("scheduling decision requires a timezone")
    except (TypeError, AttributeError) as exc:
        raise ValueError("invalid scheduling decision time") from exc
    by_id = {u["id"]: u for u in spec["units"]}
    if (not eligible or set(eligible) & set(receipt["revision_unavailable"])
            or any(runtime[uid]["state"] not in {"queued", "waiting"} for uid in eligible)):
        raise ValueError("scheduling receipt requires available reads")
    for uid in eligible:
        if (any(runtime[dep]["state"] != "completed" for dep in by_id[uid]["work"]["depends_on"])
                or by_id[uid]["review"]["criteria_version"] != receipt["criteria_version"]
                or (runtime[uid]["ready_at"] and
                    datetime.fromisoformat(runtime[uid]["ready_at"]) > decision_at)):
            raise ValueError("recorded eligible read violates dependency, criteria or delay")
    if (scheduler["dispatches"] != sum(u["attempts"] for u in runtime.values())
            or scheduler["dispatches"] >= spec["budget"]["max_attempts"]
            or sum(u["state"] == "running" for u in runtime.values()) >= spec["budget"]["max_inflight"]):
        raise ValueError("scheduling receipt exceeds shared limits")
    order, details = scheduling_view(spec, runtime, scheduler, eligible, receipt["revision_unavailable"])
    selected = order[0]
    reason = "aged_eligible" if details[selected]["fairness_due"] else "effective_priority"
    if not equal_json([selected, reason], [receipt["selected"], receipt["reason"]]):
        raise ValueError("recorded selection differs from declared scheduling policy")
    return {"dispatches": scheduler["dispatches"] + 1,
            "waits": {uid: scheduler["waits"][uid] + 1 if uid in eligible and uid != selected else 0
                      for uid in runtime}}


def scheduling_transition(spec, runtime, scheduler, receipt):
    from ._state_model import _stable_hash
    return {"before_digest": _stable_hash(scheduler), "receipt": copy.deepcopy(receipt),
            "after": advance_scheduler(spec, runtime, scheduler, receipt)}
