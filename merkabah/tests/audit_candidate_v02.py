#!/usr/bin/env python3
"""Audit structurel du graphe Merkabah candidat v0.2, sans dépendance externe.

Exécution : python3 merkabah/tests/audit_candidate_v02.py
Ne valide ni l'exégèse, ni une géométrie, ni une animation.
"""
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GRAPH = ROOT / "schema" / "merkabah_candidate_v0.2.json"
SCHEMA = ROOT / "schema" / "merkabah.schema.json"


def audit(graph, schema):
    errors = []
    notes = []
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    ids = [n.get("id") for n in nodes]
    if len(set(ids)) != len(ids):
        errors.append("Identifiants de noeuds dupliqués")
    by_id = {n.get("id"): n for n in nodes}
    for index, edge in enumerate(edges):
        if edge.get("from") not in by_id or edge.get("to") not in by_id:
            errors.append(f"Arête {index}: référence absente")
    for i in range(1, 5):
        cherub = f"cherub_{i}"
        faces = [e for e in edges if e.get("from") == cherub and e.get("type") == "has_face"]
        wings = [e for e in edges if e.get("from") == cherub and e.get("type") == "has_wing"]
        if cherub not in by_id or len(faces) != 4 or len(wings) != 4:
            errors.append(f"{cherub}: attendu 1 être, 4 faces, 4 ailes")
        wheel = f"wheel_{i}"
        if wheel not in by_id or not by_id.get(wheel, {}).get("eyes_on_rim"):
            errors.append(f"{wheel}: roue absente ou yeux non représentés")
        for src, dst, relation in [(cherub, wheel, "beside"), (wheel, cherub, "moves_with"),
                                   (cherub, "ruach", "directed_by")]:
            if not any(e.get("from") == src and e.get("to") == dst and e.get("type") == relation for e in edges):
                errors.append(f"Relation manquante : {src} --{relation}--> {dst}")
        for suffix in ("legs", "feet", "hands"):
            if f"{cherub}_{suffix}" not in by_id:
                errors.append(f"{cherub}: {suffix} absent")
    allowed = {"TEXTUAL", "DERIVED", "UNCERTAIN", "INTERPRETATION", "UNKNOWN"}
    for node in nodes:
        if node.get("status") not in allowed:
            errors.append(f"Statut inconnu : {node.get('id')}")
    required = set(schema.get("required", []))
    if not required.issubset(graph):
        errors.append(f"Incompatibilité schéma : champs racine absents {sorted(required - set(graph))}")
    if schema.get("properties", {}).get("status", {}).get("const") != graph.get("status"):
        errors.append("Incompatibilité schéma : valeur du statut racine")
    if nodes and "kind" in schema["properties"]["nodes"]["items"].get("required", []) and "kind" not in nodes[0]:
        errors.append("Incompatibilité schéma : kind/scene/epistemic_status/sources vs type/source/status")
    if edges and "relation" in schema["properties"]["edges"]["items"].get("required", []) and "relation" not in edges[0]:
        errors.append("Incompatibilité schéma : relation vs type")
    if "face_discrepancy_ez10_14" in by_id:
        notes.append("Divergence Ézéchiel 1:10 / 10:14 présente mais non résolue")
    notes.append("Les contrôles structurels ne prouvent aucune fidélité biblique ou géométrique")
    return errors, notes, len(nodes), len(edges)


if __name__ == "__main__":
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    errors, notes, n_nodes, n_edges = audit(graph, schema)
    print(f"Merkabah candidat {graph.get('version')}: {n_nodes} noeuds, {n_edges} relations")
    for msg in errors:
        print("FAIL:", msg)
    for msg in notes:
        print("NOTE:", msg)
    print("VERDICT:", "FAIL — contrat de données non conforme" if errors else "PASS structurel limité")
    raise SystemExit(1 if errors else 0)
