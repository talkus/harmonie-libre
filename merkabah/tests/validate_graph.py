"""Merkabah candidate graph topology checker (standard library only).
This checks internal consistency, NOT biblical fidelity.
Usage: python merkabah/tests/validate_graph.py merkabah/schema/merkabah_candidate_v0.1.json
"""
import json
import sys

FACES = {"human", "lion", "ox", "eagle"}
STATUSES = {"TEXTUAL", "DEDUCED", "INTERPRETATION", "UNKNOWN"}

def validate(graph):
    errors = []
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    ids = [node.get("id") for node in nodes]
    if len(ids) != len(set(ids)):
        errors.append("duplicate node ID")
    by_id = {node.get("id"): node for node in nodes}
    sources = {s.get("id") for s in graph.get("sources", [])}
    for node in nodes:
        if node.get("source") not in sources:
            errors.append(f"unknown node source: {node.get('id')}")
        if node.get("status") not in STATUSES:
            errors.append(f"unknown status: {node.get('id')}")
    for edge in edges:
        if edge.get("from") not in by_id or edge.get("to") not in by_id:
            errors.append("dangling edge")
        if edge.get("source") not in sources:
            errors.append("unknown edge source")
    cherubs = [n["id"] for n in nodes if n.get("type") == "living_being"]
    wheels = [n["id"] for n in nodes if n.get("type") == "wheel_within_wheel"]
    if len(cherubs) != 4:
        errors.append("expected four living beings")
    if len(wheels) != 4:
        errors.append("expected four wheels")
    def targets(source, relation):
        return [e["to"] for e in edges if e.get("from") == source and e.get("type") == relation]
    associated = []
    for cherub in cherubs:
        faces = targets(cherub, "has_face")
        wings = targets(cherub, "has_wing")
        adjacent = targets(cherub, "beside")
        if len(faces) != 4 or {by_id.get(f, {}).get("form") for f in faces} != FACES:
            errors.append(f"{cherub}: four distinct faces required")
        if len(wings) != 4 or any(by_id.get(w, {}).get("type") != "wing" for w in wings):
            errors.append(f"{cherub}: four wings required")
        if len(adjacent) != 1 or adjacent[0] not in wheels:
            errors.append(f"{cherub}: exactly one adjacent wheel required")
        associated.extend(adjacent)
    if len(set(associated)) != 4:
        errors.append("wheel associations must be one-to-one")
    for cherub in cherubs:
        for wheel in targets(cherub, "beside"):
            if cherub not in targets(wheel, "moves_with"):
                errors.append(f"{cherub}: wheel movement not coupled")
    return errors

if __name__ == "__main__":
    with open(sys.argv[1], encoding="utf-8") as stream:
        graph = json.load(stream)
    problems = validate(graph)
    print(json.dumps({
        "result": "PASS" if not problems else "FAIL",
        "nodes": len(graph.get("nodes", [])),
        "edges": len(graph.get("edges", [])),
        "errors": problems
    }, indent=2))
    sys.exit(bool(problems))
