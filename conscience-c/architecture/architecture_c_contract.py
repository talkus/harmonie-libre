"""Checks the proposed Architecture C document contract, not a deployed service.

This reference checks declared structure, references and transition guards.
It does not establish semantic truth, durable storage or continuous operation.
"""
import argparse
import json
from pathlib import Path


BLOCKS = ("purpose", "scope", "work", "review", "evidence", "continuity")
STATES = {"non_execute", "en_cours", "attente", "bloque", "valide", "annule"}


def _validate_well_shaped(model):
    errors = []

    def check(condition, message):
        if not condition:
            errors.append(message)

    contract = model.get("operational_contract", {})
    goals = contract.get("goals", [])
    nodes = contract.get("nodes", [])
    goal_ids = {g.get("id") for g in goals}
    node_ids = {n.get("id") for n in nodes}
    check(bool(goals) and sum(g.get("parent") is None for g in goals) == 1,
          "Goal hierarchy requires one root")
    check({n.get("scope", {}).get("view") for n in nodes} == {"micro", "meso", "macro", "meta"}
          and len(nodes) == 4, "Reference requires one instance of each view")
    check(len(goal_ids) == len(goals), "Duplicate goal identifiers")
    check(len(node_ids) == len(nodes), "Duplicate node identifiers")
    goal_by_id = {g.get("id"): g for g in goals}
    for goal in goals:
        parent = goal.get("parent")
        check(parent is None or parent in goal_ids, "Unknown parent goal: " + str(parent))
        if parent is not None:
            check(bool(goal.get("serves_because")), "Missing semantic justification")
        visited = {goal.get("id")}
        while parent in goal_by_id:
            if parent in visited:
                check(False, "Cycle in goal hierarchy")
                break
            visited.add(parent)
            parent = goal_by_id[parent].get("parent")

    registry = contract.get("registry", {})
    registries = {name: set(registry.get(name, [])) for name in
                  ("source_refs", "proof_refs", "objection_refs", "unknown_refs", "criteria_refs")}
    budgets = {b["id"]: b for b in contract.get("budgets", [])}
    budget_used = {key: 0 for key in budgets}
    execution_keys = set()
    node_by_id = {n.get("id"): n for n in nodes}
    for node in nodes:
        label = str(node.get("id"))
        check(all(isinstance(node.get(block), dict) for block in BLOCKS),
              label + ": missing common contract block")
        if not all(isinstance(node.get(block), dict) for block in BLOCKS):
            continue
        purpose, scope, work, review, evidence, continuity = (node[b] for b in BLOCKS)
        check(bool(purpose.get("goal_refs")) and set(purpose.get("goal_refs", [])) <= goal_ids,
              label + ": unknown or missing goal")
        check(bool(purpose.get("serves_because")), label + ": missing purpose justification")
        check(scope.get("view") in {"micro", "meso", "macro", "meta"}, label + ": unknown view")
        check(bool(scope.get("boundary")) and bool(scope.get("observer")), label + ": missing scope")
        check(bool(work.get("output_contract")), label + ": missing expected output")
        check(bool(review.get("criteria_version")), label + ": missing criteria version")
        for field, block in (("source_refs", evidence), ("proof_refs", evidence),
                             ("objection_refs", review), ("unknown_refs", review),
                             ("criteria_refs", review)):
            check(field in block and isinstance(block[field], list), label + ": missing " + field)
            check(set(block.get(field, [])) <= registries[field], label + ": unresolved " + field)
        check(isinstance(evidence.get("losses"), list), label + ": losses must be declared")
        state = continuity.get("state")
        check(state in STATES, label + ": unknown state")
        check(bool(continuity.get("checkpoint_ref")), label + ": missing resume reference")
        check(bool(continuity.get("next_step")), label + ": missing next step")
        if state == "valide":
            check(bool(evidence.get("proof_refs")), label + ": completion requires evidence")
        budget_id = continuity.get("budget_ref")
        attempts = continuity.get("attempts_used", -1)
        check(budget_id in budgets, label + ": unknown shared budget")
        check(isinstance(attempts, int) and not isinstance(attempts, bool) and attempts >= 0,
              label + ": invalid attempt count")
        if budget_id in budgets and isinstance(attempts, int) and attempts >= 0:
            budget_used[budget_id] += attempts
        if work.get("external_effect"):
            key = work.get("execution_key")
            check(bool(key) and key not in execution_keys, label + ": duplicate or missing effect key")
            execution_keys.add(key)
            if continuity.get("effect_result") == "unknown":
                check(continuity.get("next_action") != "retry", label + ": reconcile before retry")
        if evidence.get("claim") == "fonctionnement_continu_observe":
            check(evidence.get("proof_kind") == "runtime_observation" and
                  bool(evidence.get("observed_interval")) and
                  bool(evidence.get("proof_refs")) and
                  "PROOF-SIMULATED" not in evidence.get("proof_refs", []),
                  label + ": continuous-operation claim lacks observation")
        if scope.get("view") == "meta":
            check(bool(scope.get("reviews")) and set(scope.get("reviews", [])) <= node_ids,
                  label + ": missing reflexive targets")
    for budget_id, used in budget_used.items():
        check(used <= budgets[budget_id]["max_attempts"], "Shared retry budget exceeded: " + budget_id)

    for transfer in contract.get("transfers", []):
        source = node_by_id.get(transfer.get("from"))
        target = node_by_id.get(transfer.get("to"))
        check(source is not None and target is not None, "Transfer has unknown endpoint")
        check(bool(transfer.get("serves_because")), "Transfer lacks semantic justification")
        if source is None or target is None:
            continue
        for block, field in (("purpose", "goal_refs"), ("review", "objection_refs"),
                             ("review", "unknown_refs"), ("evidence", "source_refs")):
            missing = set(source.get(block, {}).get(field, [])) - set(target.get(block, {}).get(field, []))
            check(not missing, "Transfer dropped " + field + ": " + str(sorted(missing)))
        check(source.get("review", {}).get("criteria_version") == target.get("review", {}).get("criteria_version")
              or bool(transfer.get("criteria_migration")), "Undeclared criteria migration")
    return errors



def _shape_errors(model):
    """Reject malformed declared data before graph/set operations."""
    errors = []
    def require(condition, label):
        if not condition:
            errors.append(label)
    def text(value):
        return isinstance(value, str) and bool(value.strip())
    def refs(value):
        return isinstance(value, list) and all(text(x) for x in value) and len(set(value)) == len(value)
    def integer(value):
        return isinstance(value, int) and not isinstance(value, bool)
    if not isinstance(model, dict) or not isinstance(model.get("operational_contract"), dict):
        return ["Expected an object with operational_contract"]
    c = model["operational_contract"]
    require(c.get("common_blocks") == list(BLOCKS), "Common contract blocks differ")
    for collection in ("goals", "nodes", "budgets", "transfers"):
        require(isinstance(c.get(collection), list)
                and all(isinstance(row, dict) for row in c.get(collection, [])),
                collection + " must be a list of objects")
    registry = c.get("registry")
    require(isinstance(registry, dict), "Registry must be an object")
    if errors:
        return errors
    for key in ("source_refs", "proof_refs", "objection_refs", "unknown_refs", "criteria_refs"):
        require(refs(registry.get(key)), "Invalid registry " + key)
    for g in c["goals"]:
        require(text(g.get("id")) and (g.get("parent") is None or text(g["parent"])),
                "Invalid goal identifiers")
        require(text(g.get("text")) and text(g.get("serves_because")), "Invalid goal meaning")
    for b in c["budgets"]:
        require(text(b.get("id")), "Invalid budget identifier")
        require(integer(b.get("max_attempts")) and b["max_attempts"] > 0,
                "Budget attempts must be a positive integer")
        require(integer(b.get("timeout_seconds_per_attempt")) and b["timeout_seconds_per_attempt"] > 0,
                "Budget timeout must be a positive integer")
    budget_ids = [b.get("id") for b in c["budgets"]]
    require(all(text(x) for x in budget_ids)
            and len(set(x for x in budget_ids if isinstance(x, str))) == len(budget_ids),
            "Duplicate or malformed budget identifiers")
    for n in c["nodes"]:
        label = n.get("id") if text(n.get("id")) else "node"
        require(text(n.get("id")), "Invalid node identifier")
        require(all(isinstance(n.get(b), dict) for b in BLOCKS), label + ": missing common contract block")
        if not all(isinstance(n.get(b), dict) for b in BLOCKS):
            continue
        p, s, w, r, e, t = (n[b] for b in BLOCKS)
        require(refs(p.get("goal_refs")) and bool(p.get("goal_refs")), label + ": invalid goal refs")
        require(text(p.get("serves_because")), label + ": missing purpose justification")
        require(text(s.get("view")) and text(s.get("boundary")) and text(s.get("observer")),
                label + ": invalid scope")
        require(refs(s.get("reviews")), label + ": invalid review targets")
        require(refs(w.get("input_refs")) and text(w.get("output_contract")), label + ": invalid work")
        require(isinstance(w.get("external_effect"), bool), label + ": external_effect must be boolean")
        require(text(w.get("execution_key")), label + ": invalid execution key")
        require(text(r.get("criteria_version")), label + ": invalid criteria version")
        for key, block in (("criteria_refs", r), ("objection_refs", r), ("unknown_refs", r),
                           ("source_refs", e), ("proof_refs", e)):
            require(refs(block.get(key)), label + ": invalid " + key)
        require(isinstance(e.get("losses"), list)
                and all(text(x) for x in e.get("losses", [])), label + ": invalid declared losses")
        require(text(e.get("claim")) and text(e.get("proof_kind")), label + ": invalid evidence declaration")
        # This validator has no service observations. It cannot certify runtime.
        require(e.get("claim") != "fonctionnement_continu_observe",
                label + ": document contract cannot certify observed continuous operation")
        for key in ("state", "checkpoint_ref", "checkpoint_kind", "budget_ref",
                    "effect_result", "next_action", "next_step"):
            require(text(t.get(key)), label + ": invalid " + key)
        require(isinstance(t.get("durable_checkpoint_verified"), bool),
                label + ": durable checkpoint flag must be boolean")
        require(integer(t.get("attempts_used")) and t["attempts_used"] >= 0,
                label + ": invalid attempt count")
    for tr in c["transfers"]:
        require(all(text(tr.get(k)) for k in ("from", "to", "kind", "serves_because")),
                "Invalid transfer contract")
        if "criteria_migration" in tr:
            require(text(tr["criteria_migration"]), "Invalid criteria migration")
    return errors


def validate(model):
    errors = _shape_errors(model)
    if errors:
        return errors
    errors = _validate_well_shaped(model)
    c = model["operational_contract"]
    known_sources = set(c["registry"]["source_refs"])
    for n in c["nodes"]:
        if not set(n["work"]["input_refs"]) <= known_sources:
            errors.append(n["id"] + ": unresolved input source")
        if n["scope"]["view"] == "meta" and n["id"] in n["scope"]["reviews"]:
            errors.append(n["id"] + ": meta review needs situated targets other than itself")
        if n["continuity"]["state"] == "valide" and (
            n["evidence"]["proof_kind"] in {"none", "simulation"}
            or "PROOF-SIMULATED" in n["evidence"]["proof_refs"]
        ):
            errors.append(n["id"] + ": completion cannot rely on simulated evidence")
        if n["continuity"]["durable_checkpoint_verified"]:
            errors.append(n["id"] + ": document validator cannot attest durable checkpoint storage")
    return errors


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    args = parser.parse_args(argv)
    try:
        model = json.loads(args.model.read_text(encoding="utf-8"))
        errors = validate(model)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors = ["Cannot read JSON model: " + str(exc)]
    print(json.dumps({
        "valid": not errors, "errors": errors,
        "coverage": "document_contract_only",
        "evidence_verified": False, "execution_authority": False,
        "continuous_operation_observed": False
    }, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())

