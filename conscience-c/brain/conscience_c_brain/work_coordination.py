"""Local, recoverable coordination of bounded Gabriel examinations.

Six common blocks at every scale; declared goal priorities, explicit dependencies
and one shared attempt budget. No external action, repair or background daemon.
Journal hashes establish local consistency, not authentication or ethical truth.
"""
from __future__ import annotations

import copy
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import subprocess
import sys
import uuid

from ._state_model import _stable_hash
from .checkpoint_integrity import equal_json, verified_history
from .gabriel import GABRIEL_CRITERIA_VERSION
from .examination_grid import examination_profile
from .models import CausalOrigin
from .multiscale_coherence import Scale
from .work_scheduling import (
    SCHEDULED_WORK_VERSION, SCHEDULING_VERSION, initial_scheduler,
    scheduling_view, scheduling_transition,
)


WORK_VERSION = "CC-WORK-1"
BLOCKS = ("purpose", "scope", "work", "review", "evidence", "continuity")
_REGISTER = "WORK_PLAN_RECORDED"
_PROGRESS = "WORK_PROGRESS_RECORDED"
_STATES = {"queued", "running", "waiting", "completed", "blocked"}
_ROOT = "work_coordination"


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(field + " must be a nonblank string")
    return value


def _refs(value, field):
    if not isinstance(value, list) or len(value) > 256:
        raise ValueError(field + " must be a bounded list")
    for item in value:
        _text(item, field)
    if len(set(value)) != len(value):
        raise ValueError(field + " contains duplicate references")
    return value


def _integer(value, field, low, high):
    if type(value) is not int or not low <= value <= high:
        raise ValueError(f"{field} must be an integer from {low} to {high}")


def _fields(value, names, field):
    if not isinstance(value, dict) or set(value) != set(names):
        raise ValueError(field + " has invalid fields")


def _clock():
    return datetime.now(timezone.utc)


def _instant(value):
    result = datetime.fromisoformat(_text(value, "datetime").replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("datetime requires a timezone")
    return result.astimezone(timezone.utc)


def validate_work_plan(spec, *, require_current_criteria=True):
    """Validate shape, meaning links and both DAGs before any state mutation."""
    scheduled = isinstance(spec, dict) and spec.get("version") == SCHEDULED_WORK_VERSION
    fields = ("plan_id", "version", "goals", "units", "budget")
    _fields(spec, (*fields, "scheduling") if scheduled else fields, "plan")
    _text(spec["plan_id"], "plan_id")
    _text(spec["version"], "version")
    if spec["version"] not in {WORK_VERSION, SCHEDULED_WORK_VERSION}:
        raise ValueError("unsupported work contract version")
    if scheduled:
        policy = spec["scheduling"]
        _fields(policy, ("version", "fair_after", "inherit_priorities"), "scheduling")
        if policy["version"] != SCHEDULING_VERSION:
            raise ValueError("unsupported scheduling policy version")
        _integer(policy["fair_after"], "scheduling.fair_after", 1, 128)
        if type(policy["inherit_priorities"]) is not bool:
            raise ValueError("scheduling.inherit_priorities must be a boolean")
    for name in ("goals", "units"):
        if not isinstance(spec[name], list) or not 1 <= len(spec[name]) <= 128:
            raise ValueError(name + " requires 1 to 128 entries")
    goals = {}
    for goal in spec["goals"]:
        _fields(goal, ("id", "parent", "text", "serves_because", "priority"), "goal")
        for name in ("id", "text", "serves_because"):
            _text(goal[name], "goal." + name)
        if goal["parent"] is not None:
            _text(goal["parent"], "goal.parent")
        _integer(goal["priority"], "goal.priority", 0, 999)
        if goal["id"] in goals:
            raise ValueError("duplicate goal identifier")
        goals[goal["id"]] = goal
    if sum(g["parent"] is None for g in goals.values()) != 1:
        raise ValueError("goal hierarchy requires one root")
    for gid in goals:
        seen = set()
        current = gid
        while current is not None:
            if current in seen or current not in goals:
                raise ValueError("cyclic or unresolved goal hierarchy")
            seen.add(current)
            current = goals[current]["parent"]
    budget = spec["budget"]
    _fields(budget, ("max_attempts", "timeout_seconds", "max_inflight", "retry_delay_seconds"), "budget")
    for key, low, high in (("max_attempts", 1, 1024), ("timeout_seconds", 1, 300),
                           ("max_inflight", 1, 32), ("retry_delay_seconds", 0, 3600)):
        _integer(budget[key], "budget." + key, low, high)
    units = {}
    for unit in spec["units"]:
        _fields(unit, ("id", *BLOCKS), "unit")
        _text(unit["id"], "unit.id")
        if unit["id"] in units:
            raise ValueError("duplicate unit identifier")
        units[unit["id"]] = unit
        _fields(unit["purpose"], ("goal_refs", "serves_because"), "purpose")
        refs = _refs(unit["purpose"]["goal_refs"], "goal_refs")
        if not refs or not set(refs) <= set(goals):
            raise ValueError("unit requires known purpose references")
        _text(unit["purpose"]["serves_because"], "purpose.serves_because")
        _fields(unit["scope"], ("view", "boundary", "observer", "reviews"), "scope")
        Scale(unit["scope"]["view"])
        for key in ("boundary", "observer"):
            _text(unit["scope"][key], "scope." + key)
        _refs(unit["scope"]["reviews"], "scope.reviews")
        _fields(unit["work"], ("kind", "claim_id", "depends_on", "input_refs",
                              "output_contract", "subject_ref"), "work")
        # Fixed read-only operation; names never select arbitrary methods/shells.
        if unit["work"]["kind"] != "gabriel_examine":
            raise ValueError("only bounded, read-only Gabriel examinations are supported")
        for key in ("claim_id", "output_contract"):
            _text(unit["work"][key], "work." + key)
        if unit["work"]["subject_ref"] is not None:
            _text(unit["work"]["subject_ref"], "work.subject_ref")
        for key in ("depends_on", "input_refs"):
            _refs(unit["work"][key], "work." + key)
        _fields(unit["review"], ("criteria_version", "objection_refs", "unknown_refs"), "review")
        _text(unit["review"]["criteria_version"], "review.criteria_version")
        if require_current_criteria and unit["review"]["criteria_version"] != GABRIEL_CRITERIA_VERSION:
            raise ValueError("criteria version must match the installed Gabriel")
        for key in ("objection_refs", "unknown_refs"):
            _refs(unit["review"][key], "review." + key)
        _fields(unit["evidence"], ("source_refs",), "evidence")
        _refs(unit["evidence"]["source_refs"], "evidence.source_refs")
        if not set(unit["work"]["input_refs"]) <= set(unit["evidence"]["source_refs"]):
            raise ValueError("input source references cannot disappear")
        _fields(unit["continuity"], ("next_step",), "continuity")
        _text(unit["continuity"]["next_step"], "continuity.next_step")
    for uid, unit in units.items():
        refs = unit["scope"]["reviews"]
        if not set(refs) <= set(units) or uid in refs:
            raise ValueError("invalid reflexive review targets")
        if unit["scope"]["view"] == "meta" and not refs:
            raise ValueError("meta view requires situated review targets")
        visited, stack = set(), [uid]
        while stack:
            current = stack.pop()
            if current not in units:
                raise ValueError("unresolved work dependency")
            for dep in units[current]["work"]["depends_on"]:
                if dep == uid:
                    raise ValueError("cyclic work dependencies")
                if dep not in visited:
                    visited.add(dep)
                    stack.append(dep)
    return copy.deepcopy(spec)


def _initial(spec):
    plan = {"spec": copy.deepcopy(spec), "units": {
        u["id"]: {"state": "queued", "attempts": 0, "attempt_id": None,
                  "deadline": None, "ready_at": None, "error": None,
                  "basis_digest": None, "result": None}
        for u in spec["units"]}}
    if spec["version"] == SCHEDULED_WORK_VERSION:
        plan["scheduler"] = initial_scheduler(spec)
    return plan


def _projection(rows):
    """Rebuild coordinator state from its own recorded events, not caller edits."""
    plans = {}
    for row in rows:
        kind, payload = row["event_type"], row["payload"]
        if kind == _REGISTER:
            # Historical declarations remain readable after a criteria upgrade.
            spec = validate_work_plan(payload["spec"], require_current_criteria=False)
            if spec["plan_id"] in plans:
                raise ValueError("duplicate recorded plan")
            plans[spec["plan_id"]] = _initial(spec)
        elif kind == _PROGRESS:
            plan = plans.get(payload["plan_id"])
            uid = payload["unit_id"]
            if plan is None or uid not in plan["units"]:
                raise ValueError("work progress has no recorded unit")
            old = plan["units"][uid]
            new = payload["unit"]
            if (_stable_hash(old) != payload["before_digest"] or
                    not isinstance(new, dict) or set(new) != set(old) or
                    new["state"] not in _STATES or type(new["attempts"]) is not int or
                    new["attempts"] < old["attempts"]):
                raise ValueError("invalid recorded work progress")
            if plan["spec"]["version"] == SCHEDULED_WORK_VERSION:
                reserved = new["state"] == "running" and new["attempts"] == old["attempts"] + 1
                if reserved:
                    recorded = payload.get("scheduling", {})
                    if not isinstance(recorded, dict) or not isinstance(recorded.get("receipt"), dict):
                        raise ValueError("missing scheduling receipt")
                    receipt = recorded.get("receipt", {})
                    _instant(receipt.get("decision_at"))
                    if receipt.get("ledger_boundary") != row["prev_hash"] or receipt.get("selected") != uid:
                        raise ValueError("scheduling receipt is not bound to this reservation")
                    expected = scheduling_transition(plan["spec"], plan["units"], plan["scheduler"], receipt)
                    if not equal_json(recorded, expected):
                        raise ValueError("scheduling state differs from recorded choice")
                    plan["scheduler"] = expected["after"]
                elif "scheduling" in payload or new["attempts"] != old["attempts"] or new["state"] == "running":
                    raise ValueError("invalid scheduling transition")
            plan["units"][uid] = copy.deepcopy(new)
    return plans


def _priority(unit, goals):
    paths = []
    for gid in unit["purpose"]["goal_refs"]:
        route = []
        while gid is not None:
            route.append(goals[gid]["priority"])
            gid = goals[gid]["parent"]
        paths.append(tuple(reversed(route)))
    return min(paths)


def _execute_worker(root, plan_id, unit_id, attempt_id, timeout):
    # No shell, no network operation, no supplied executable or Python source.
    env = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[1])}
    process = subprocess.run(
        [sys.executable, "-m", "conscience_c_brain.work_runner", str(root),
         plan_id, unit_id, attempt_id], capture_output=True, text=True,
        encoding="utf-8", timeout=timeout, env=env, check=False)
    if process.returncode:
        raise ValueError("bounded worker failed: " + process.stderr[-600:])
    import json
    return json.loads(process.stdout)


def _result_matches(result, unit, current, attempt, rows):
    if (not isinstance(result, dict) or result.get("attempt_id") != attempt
            or result.get("basis_digest") != current["basis_digest"]
            or result.get("execution_authority") is not False
            or result.get("result_kind") != "bounded_local_diagnostic"
            or not isinstance(result.get("report"), dict)):
        return False
    report = result["report"]
    expected = {"claim_id": unit["work"]["claim_id"],
                "scope_ref": unit["scope"]["boundary"],
                "observer_ref": unit["scope"]["observer"],
                "scale": unit["scope"]["view"],
                "subject_ref": unit["work"]["subject_ref"],
                "criteria_version": unit["review"]["criteria_version"],
                "execution_authority": False, "independent_validation": False}
    if any(not equal_json(report.get(k), v) for k, v in expected.items()):
        return False
    if report.get("verdict") not in {"HOLD", "REVIEW_REQUIRED", "INDETERMINATE", "NOT_APPLICABLE"}:
        return False
    if report.get("evidence_status") not in {"TRIGGERED", "NOT_TRIGGERED", "INSUFFICIENT_DATA", "INVALID_DATA"}:
        return False
    try:
        for key in ("trace_refs", "unknowns", "objection_refs", "support_refs", "contradiction_refs"):
            _refs(report.get(key), "report." + key)
        _text(report.get("input_digest"), "report.input_digest")
        _instant(report.get("observed_at"))
    except (ValueError, TypeError):
        return False
    recorded = {r["event_hash"] for r in rows}
    return (bool(report["trace_refs"]) and set(report["trace_refs"]) <= recorded
            and report.get("ledger_boundary") in recorded)


def _situated_unknowns(plan_id, unit, current, result_current):
    """Keep equal reason text distinct across different objects and contexts."""
    report = (current["result"] or {}).get("report", {})
    context = {
        "plan_id": plan_id, "origin_unit_id": unit["id"],
        "claim_id": unit["work"]["claim_id"], "scale": unit["scope"]["view"],
        "scope_ref": unit["scope"]["boundary"], "observer_ref": unit["scope"]["observer"],
        "subject_ref": unit["work"]["subject_ref"], "basis_digest": current["basis_digest"],
    }
    return [{**context, "reason": reason,
             "unknown_id": "UNKNOWN:" + _stable_hash({**context, "reason": reason}),
             "trace_refs": list(report.get("trace_refs", [])),
             "result_current": result_current}
            for reason in report.get("unknowns", [])]


class WorkCoordinationMixin:
    def classify_replay_event(self, row):
        if row.get("event_type") in {_REGISTER, _PROGRESS}:
            return "documentary_only"
        return super().classify_replay_event(row)

    def _work_plans(self, *, history=None):
        # Internal callers may share one freshly verified read frame. It is
        # never cached across calls or after a transition.
        rows = verified_history(self) if history is None else history
        plans = _projection(rows)
        stored = self.state.get(_ROOT, {})
        if (not equal_json(plans, stored) or
                not equal_json(stored, self._last_committed_state.get(_ROOT, {}))):
            raise ValueError("work state differs from recorded history")
        return plans

    def audit(self):
        drifts = super().audit()
        try:
            self._work_plans()
        except (ValueError, KeyError, TypeError) as exc:
            drifts.append({"field": _ROOT, "expected": "recorded local work history",
                           "observed": str(exc)})
        return drifts

    def record_work_plan(self, spec, *, provenance):
        spec = validate_work_plan(spec)
        _text(provenance, "provenance")
        plans = self._work_plans()
        pid = spec["plan_id"]
        if pid in plans:
            if not equal_json(plans[pid]["spec"], spec):
                raise ValueError("plan is immutable; record a new version with a new plan_id")
            return self.work_view(pid)
        for unit in spec["units"]:
            if unit["work"]["claim_id"] not in self.state.get("teshuvah", {}).get("claims", {}):
                raise ValueError("work requires an existing claim")
        plans[pid] = _initial(spec)
        self.state[_ROOT] = plans
        self._transition(_REGISTER, {"spec": spec, "provenance": provenance,
            "execution_authority": False}, CausalOrigin.MIXED)
        return self.work_view(pid)

    def _work_change(self, pid, uid, update, reason, *, schedule_receipt=None):
        plans = self._work_plans()
        old = plans[pid]["units"][uid]
        new = {**copy.deepcopy(old), **copy.deepcopy(update)}
        scheduling = {}
        if schedule_receipt is not None:
            scheduling["scheduling"] = scheduling_transition(
                plans[pid]["spec"], plans[pid]["units"], plans[pid]["scheduler"], schedule_receipt)
            plans[pid]["scheduler"] = scheduling["scheduling"]["after"]
        plans[pid]["units"][uid] = new
        self.state[_ROOT] = plans
        return self._transition(_PROGRESS, {"plan_id": pid, "unit_id": uid,
            "before_digest": _stable_hash(old), "unit": new, "reason": reason,
            "execution_authority": False, **scheduling}, CausalOrigin.SELF)

    def _work_basis_contexts(self, claim_ids, *, history, at_time):
        """Share input searches within one fresh frame, never across calls."""
        claims = self.state.get("teshuvah", {}).get("claims", {})
        all_evidence = self.state["E"]["evidence"]
        # Keep the original distinction: facts select existing entries;
        # absent ancestors remain explicit missing inputs during traversal.
        related = {cid: {eid for eid in (claims.get(cid) or {}).get("facts", [])
                         if eid in all_evidence} for cid in claim_ids}
        for eid, item in all_evidence.items():
            cid = item.get("claim_ref")
            if cid in related:
                related[cid].add(eid)
        reports = {row["event_hash"]: row["payload"]["report"]["claim_id"]
                   for row in history if row["event_type"] == "GABRIEL_EXAMINED"
                   and row["payload"]["report"]["claim_id"] in related}
        diagnostics = {cid: [] for cid in related}
        for row in history:
            cid = reports.get(row["event_hash"])
            if cid is None and row["event_type"] in {"GABRIEL_CONTESTED", "GABRIEL_CORRECTED"}:
                cid = reports.get(row["payload"]["report_ref"])
            if cid is not None:
                diagnostics[cid].append(row["event_hash"])
        temporal, contexts = {}, {}
        for cid, refs in related.items():
            stack = list(refs)
            while stack:
                eid = stack.pop()
                for ancestor in all_evidence.get(eid, {}).get("derived_from", []):
                    if ancestor not in refs:
                        refs.add(ancestor)
                        stack.append(ancestor)
            evidence = {eid: all_evidence.get(eid) for eid in sorted(refs)}
            for eid, item in evidence.items():
                if eid not in temporal:
                    temporal[eid] = self._work_evidence_time(item, at_time)
            contexts[cid] = {"claim": claims.get(cid), "evidence": evidence,
                             "temporal": {eid: temporal[eid] for eid in evidence},
                             "diagnostic_refs": diagnostics[cid]}
        return contexts

    @staticmethod
    def _work_evidence_time(item, now):
        if item is None:
            return "missing"
        try:
            start = _instant(item["valid_at"]) if item.get("valid_at") else None
            end = _instant(item["expires_at"]) if item.get("expires_at") else None
            return "future" if start and now < start else "expired" if end and now > end else "current"
        except (ValueError, TypeError):
            return "invalid"

    @staticmethod
    def _work_context_digest(unit, context):
        # Unit boundaries remain distinct; preserve both historical encodings.
        return _stable_hash({**context, "work": unit["work"], "scope": unit["scope"],
                             "criteria": GABRIEL_CRITERIA_VERSION})

    def _work_basis(self, unit, *, history=None, at_time=None):
        """Check relevant evidence/ancestors and temporal boundaries only."""
        rows = verified_history(self) if history is None else history
        now = _clock() if at_time is None else at_time
        cid = unit["work"]["claim_id"]
        context = self._work_basis_contexts([cid], history=rows, at_time=now)[cid]
        return self._work_context_digest(unit, context)

    def _work_plan_bases(self, plan, *, history=None, at_time=None, unit_ids=None):
        """One fresh frame; optionally examine only selected dependency closures."""
        rows = verified_history(self) if history is None else history
        now = _clock() if at_time is None else at_time
        by_id = {u["id"]: u for u in plan["spec"]["units"]}
        requested = list(by_id) if unit_ids is None else list(unit_ids)
        required, stack = set(), list(requested)
        while stack:
            uid = stack.pop()
            if uid not in required:
                required.add(uid)
                if plan["spec"]["version"] == SCHEDULED_WORK_VERSION:
                    stack.extend(by_id[uid]["work"]["depends_on"])
        contexts = self._work_basis_contexts(
            {by_id[uid]["work"]["claim_id"] for uid in required}, history=rows, at_time=now)
        own = {uid: self._work_context_digest(u, contexts[u["work"]["claim_id"]])
               for uid, u in by_id.items() if uid in required}
        if plan["spec"]["version"] == WORK_VERSION:
            return {uid: own[uid] for uid in requested}
        runtime, bases = plan["units"], {}
        def resolve(uid):
            if uid not in bases:
                dependencies = {dep: {"current_basis": resolve(dep),
                    "recorded_basis": runtime[dep]["basis_digest"],
                    "result_digest": _stable_hash(runtime[dep]["result"]),
                    "state": runtime[dep]["state"]}
                    for dep in by_id[uid]["work"]["depends_on"]}
                bases[uid] = _stable_hash({"own_basis": own[uid], "dependencies": dependencies})
            return bases[uid]
        return {uid: resolve(uid) for uid in requested}

    def work_view(self, plan_id):
        rows = verified_history(self)
        plans = self._work_plans(history=rows)
        if plan_id not in plans:
            raise ValueError("unknown plan_id")
        plan = plans[plan_id]
        spec, runtime = plan["spec"], plan["units"]
        by_id = {u["id"]: u for u in spec["units"]}
        goals = {g["id"]: g for g in spec["goals"]}
        now = _clock()
        total = sum(x["attempts"] for x in runtime.values())
        active = sum(x["state"] == "running" for x in runtime.values())
        bases = self._work_plan_bases(plan, history=rows, at_time=now)
        freshness = {}
        def result_current(uid):
            if uid not in freshness:
                freshness[uid] = (runtime[uid]["result"] is not None
                    and runtime[uid]["basis_digest"] == bases[uid]
                    and all(runtime[dep]["state"] == "completed" and result_current(dep)
                            for dep in by_id[uid]["work"]["depends_on"]))
            return freshness[uid]
        for uid in by_id:
            result_current(uid)
        unknowns = {u["id"]: _situated_unknowns(
            plan_id, u, runtime[u["id"]], freshness[u["id"]]) for u in spec["units"]}
        latest = {}
        for row in rows:
            if row["event_type"] == "GABRIEL_EXAMINED":
                latest[row["payload"]["report"]["claim_id"]] = row["event_hash"]
        current_objections = {cid: self._gabriel_report_from_history(latest[cid], rows)["contestation_refs"]
                              for cid in {u["work"]["claim_id"] for u in spec["units"]}
                              if cid in latest}
        ready, units = [], []
        for unit in spec["units"]:
            uid = unit["id"]
            current = runtime[uid]
            deps = unit["work"]["depends_on"]
            if current["state"] == "completed" and not freshness[uid]:
                reason = "completed_result_historical"
            elif current["state"] in {"completed", "blocked", "running"}:
                reason = current["state"]
            elif unit["review"]["criteria_version"] != GABRIEL_CRITERIA_VERSION:
                reason = "criteria_revision_required"
            elif total >= spec["budget"]["max_attempts"]:
                reason = "shared_budget_exhausted"
            elif any(runtime[d]["state"] == "blocked" for d in deps):
                reason = "dependency_blocked"
            elif any(runtime[d]["state"] != "completed" for d in deps):
                reason = "dependency_pending"
            elif any(not freshness[d] for d in deps):
                reason = "dependency_requires_revision"
            elif current["ready_at"] and _instant(current["ready_at"]) > now:
                reason = "retry_delay"
            elif active >= spec["budget"]["max_inflight"]:
                reason = "capacity_full"
            else:
                reason = "ready"
                ready.append(uid)
            ancestors, stack = set(), [uid]
            # Both work dependencies and explicit reflexive targets retain refs.
            while stack:
                target = stack.pop()
                if target in ancestors:
                    continue
                ancestors.add(target)
                stack.extend(by_id[target]["work"]["depends_on"])
                stack.extend(by_id[target]["scope"]["reviews"])
            view = copy.deepcopy(unit)
            for block, key in (("purpose", "goal_refs"), ("review", "objection_refs"),
                               ("review", "unknown_refs"), ("evidence", "source_refs")):
                refs = set()
                for target in ancestors:
                    refs.update(by_id[target][block][key])
                    result = runtime[target]["result"] or {}
                    if block == "review":
                        refs.update(result.get("report", {}).get(
                            "unknowns" if key == "unknown_refs" else "objection_refs", []))
                        if key == "objection_refs":
                            refs.update(current_objections.get(by_id[target]["work"]["claim_id"], []))
                    if block == "evidence":
                        refs.update(result.get("report", {}).get("trace_refs", []))
                view[block][key] = sorted(refs)
            details = {d["unknown_id"]: d for target in ancestors for d in unknowns[target]}
            view["review"]["unknown_details"] = [details[key] for key in sorted(details)]
            # Keep legacy reason strings, but use located identifiers for identity.
            view["review"]["unknown_refs"] = sorted(set(view["review"]["unknown_refs"]) | set(details))
            view["review"]["examination_profile"] = examination_profile(unit["scope"]["view"])
            view["evidence"]["result"] = copy.deepcopy(current["result"])
            view["evidence"]["result_current"] = freshness[uid]
            view["continuity"].update(copy.deepcopy(current))
            view["continuity"].update(
                readiness=reason, checkpoint=self.state["state_label"],
                shared_attempts_used=total, budget=copy.deepcopy(spec["budget"]))
            units.append(view)
        extra = {}
        if spec["version"] == SCHEDULED_WORK_VERSION:
            unavailable = [u["id"] for u in units if u["continuity"]["readiness"] in {
                "blocked", "completed_result_historical", "criteria_revision_required",
                "dependency_blocked", "dependency_requires_revision"}]
            eligible = list(ready)
            ready, details = scheduling_view(spec, runtime, plan["scheduler"], eligible, unavailable)
            for unit in units:
                unit["continuity"]["scheduling"] = details[unit["id"]]
            extra["scheduling"] = {**copy.deepcopy(spec["scheduling"]),
                "dispatches": plan["scheduler"]["dispatches"],
                "eligible": eligible, "revision_unavailable": unavailable,
                "decision_at": now.isoformat()}
        else:
            ready.sort(key=lambda uid: (_priority(by_id[uid], goals), list(by_id).index(uid)))
        return {"version": spec["version"], "plan_id": plan_id,
                "goals": copy.deepcopy(spec["goals"]), "units": units,
                "ready": ready, "shared_attempts_used": total, "inflight": active,
                "checkpoint": self.state["state_label"], "ledger_head": rows[-1]["event_hash"],
                "execution_authority": False, "independent_validation": False,
                "continuous_service_observed": False, **extra}

    def work_recover_expired(self, plan_id):
        """Requeue only expired pure reads, never an external side effect."""
        plan = self._work_plans().get(plan_id)
        if plan is None:
            raise ValueError("unknown plan_id")
        now = _clock()
        recovered = []
        for uid, current in plan["units"].items():
            if current["state"] == "running" and _instant(current["deadline"]) <= now:
                self._work_change(plan_id, uid, {"state": "waiting",
                    "ready_at": ((now + timedelta(seconds=plan["spec"]["budget"]["retry_delay_seconds"])).isoformat()
                                 if plan["spec"]["budget"]["retry_delay_seconds"] else None),
                    "deadline": None, "error": "interrupted_or_expired_read"},
                    "expired bounded read; original attempt remains counted")
                recovered.append(uid)
        return {"recovered": recovered, "view": self.work_view(plan_id)}

    def _work_start_next(self, plan_id):
        """Reserve capacity and a shared attempt durably before starting work."""
        view = self.work_view(plan_id)
        if not view["ready"]:
            return None
        pid, uid = plan_id, view["ready"][0]
        plan = self._work_plans()[pid]
        timeout = plan["spec"]["budget"]["timeout_seconds"]
        attempt = uuid.uuid4().hex
        schedule_receipt = None
        if plan["spec"]["version"] == SCHEDULED_WORK_VERSION:
            chosen = next(u for u in view["units"] if u["id"] == uid)["continuity"]["scheduling"]
            schedule_receipt = {"version": SCHEDULING_VERSION,
                "criteria_version": GABRIEL_CRITERIA_VERSION,
                "eligible": view["scheduling"]["eligible"],
                "revision_unavailable": view["scheduling"]["revision_unavailable"],
                "selected": uid, "reason": "aged_eligible" if chosen["fairness_due"] else "effective_priority",
                "decision_at": view["scheduling"]["decision_at"], "ledger_boundary": view["ledger_head"]}
        self._work_change(pid, uid, {"state": "running",
            "attempts": plan["units"][uid]["attempts"] + 1, "attempt_id": attempt,
            "deadline": (_clock() + timedelta(seconds=timeout)).isoformat(),
            "ready_at": None, "error": None,
            "basis_digest": self._work_plan_bases(plan, unit_ids=[uid])[uid]},
            "bounded local examination reserved", schedule_receipt=schedule_receipt)
        return uid, attempt, timeout

    def _work_finish(self, pid, uid, attempt, result=None, error=None):
        plan = self._work_plans()[pid]
        current = plan["units"][uid]
        if current["state"] != "running" or current["attempt_id"] != attempt:
            raise ValueError("attempt is no longer current")
        unit = next(u for u in plan["spec"]["units"] if u["id"] == uid)
        if error is None:
            if not _result_matches(result, unit, current, attempt, verified_history(self)):
                error = "worker_output_invalid"
            elif self._work_plan_bases(plan, unit_ids=[uid])[uid] != current["basis_digest"]:
                error = "inputs_changed; new bounded examination required"
            elif _clock() > _instant(current["deadline"]):
                error = "read_deadline_exceeded"
        if error is not None:
            update = {"state": "waiting", "error": _text(error, "error")[:800],
                "deadline": None, "result": None,
                "ready_at": ((_clock() + timedelta(
                    seconds=plan["spec"]["budget"]["retry_delay_seconds"])).isoformat()
                    if plan["spec"]["budget"]["retry_delay_seconds"] else None)}
        else:
            update = {"state": "completed", "deadline": None, "ready_at": None,
                      "error": None, "result": copy.deepcopy(result)}
        self._work_change(pid, uid, update,
            "bounded read failed" if error else "bounded diagnostic completed; not truth or repair certification")
        return self.work_view(pid)

    def work_run_next(self, plan_id):
        """One pure read per invocation. Timeout kills its worker, not a service."""
        started = self._work_start_next(plan_id)
        if started is None:
            return {"started": False, "outcome": "not_started", "view": self.work_view(plan_id)}
        uid, attempt, timeout = started
        try:
            result = _execute_worker(self.root, plan_id, uid, attempt, timeout)
        except (OSError, ValueError, subprocess.TimeoutExpired) as exc:
            return {"started": True, "outcome": "waiting", "unit_id": uid,
                    "view": self._work_finish(plan_id, uid, attempt, error=str(exc))}
        view = self._work_finish(plan_id, uid, attempt, result=result)
        outcome = next(u["continuity"]["state"] for u in view["units"] if u["id"] == uid)
        return {"started": True, "outcome": outcome, "unit_id": uid, "view": view}

