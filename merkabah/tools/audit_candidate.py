"""Audit de graphe Merkabah (lecture seule). Blocages structurels vs lacunes de preuves."""
from __future__ import annotations
import argparse
import json
from pathlib import Path

DEFAULT = Path(__file__).resolve().parents[1] / "schema" / "merkabah_candidate_v0.1.json"
FACES = {"human", "lion", "ox", "eagle"}

def audit(data: dict) -> list[dict]:
    findings = []
    def report(level, code, message):
        findings.append({"level": level, "code": code, "message": message})
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])
    ids = [n.get("id") for n in nodes]
    index = {n.get("id"): n for n in nodes}
    sources = {s.get("id") for s in data.get("sources", [])}
    if len(ids) != len(set(ids)):
        report("BLOCKER", "DUPLICATE_ID", "Identifiants de noeud répétés")
    if any(e.get("from") not in index or e.get("to") not in index for e in edges):
        report("BLOCKER", "DANGLING_EDGE", "Relation vers un noeud absent")
    keys = [(e.get("from"), e.get("to"), e.get("type")) for e in edges]
    if len(keys) != len(set(keys)):
        report("BLOCKER", "DUPLICATE_EDGE", "Relation typée répétée")
    if any(n.get("source") not in sources for n in nodes) or any(e.get("source") not in sources for e in edges):
        report("BLOCKER", "UNKNOWN_SOURCE", "Source absente du registre")
    if data.get("status") != "PROPOSED_NOT_VALIDATED":
        report("BLOCKER", "UNREVIEWED_PROMOTION", "Statut promu sans contre-validation")
    beings = {n["id"] for n in nodes if n.get("type") == "living_being"}
    wheels = {n["id"] for n in nodes if n.get("type") == "wheel_within_wheel"}
    if beings != {f"cherub_{i}" for i in range(1,5)} or wheels != {f"wheel_{i}" for i in range(1,5)}:
        report("BLOCKER", "CARDINALITY", "Quatre êtres et quatre roues distincts requis")
    def related(src, kind):
        return [e.get("to") for e in edges if e.get("from") == src and e.get("type") == kind]
    for i in range(1,5):
        b, w = f"cherub_{i}", f"wheel_{i}"
        faces = related(b, "has_face")
        if len(faces) != 4 or len(set(faces)) != 4 or {index.get(f,{}).get("form") for f in faces} != FACES:
            report("BLOCKER", "FACES", f"{b}: quatre visages distincts absents")
        wings = related(b, "has_wing")
        if len(wings) != 4 or len(set(wings)) != 4 or any(index.get(x,{}).get("type") != "wing" for x in wings):
            report("BLOCKER", "WINGS", f"{b}: quatre ailes distinctes absentes")
        if related(b,"beside") != [w] or related(w,"moves_with") != [b]:
            report("BLOCKER", "WHEEL_PAIR", f"{b}: lien roue/être incohérent")
        if not index.get(w,{}).get("eyes_on_rim"):
            report("BLOCKER", "WHEEL_EYES", f"{w}: yeux non attestés")
    if any(not n.get("verse") for n in nodes) or any(not e.get("verse") for e in edges):
        report("GAP", "VERSE_PROVENANCE", "Verset précis manquant sur certaines assertions")
    if any(not n.get("scenes") for n in nodes) or any(not e.get("scenes") for e in edges):
        report("GAP", "SCENE_SCOPE", "Scènes Ézéchiel 1 et 10 non attribuées par assertion")
    if not data.get("scene_variants"):
        report("GAP", "EZ10_VARIANTS", "Éz 1:10 (boeuf) vs Éz 10:14 (chérubin) non différenciés")
    if not data.get("geometry_evidence"):
        report("GAP", "GEOMETRY_EVIDENCE", "Vues 3D et orientations non contre-vérifiées")
    if not data.get("movement_evidence"):
        report("GAP", "MOVEMENT_EVIDENCE", "Synchronisation sans retournement non contre-vérifiée")
    return findings

def main():
    p = argparse.ArgumentParser()
    p.add_argument("path", nargs="?", type=Path, default=DEFAULT)
    p.add_argument("--strict", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    graph = json.loads(args.path.read_text(encoding="utf-8"))
    findings = audit(graph)
    blockers = sum(f["level"] == "BLOCKER" for f in findings)
    gaps = sum(f["level"] == "GAP" for f in findings)
    report = {"nodes":len(graph.get("nodes",[])), "edges":len(graph.get("edges",[])),
              "blockers": blockers, "evidence_gaps":gaps,
              "status":"BLOCKED" if blockers else ("INCOMPLETE" if gaps else "CANDIDATE_CHECKS_PASSED"),
              "findings":findings}
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Merkabah {report['nodes']} noeuds, {report['edges']} relations : {report['status']}")
        for f in findings:
            print(f"{f['level']} {f['code']}: {f['message']}")
    return 1 if blockers else (2 if args.strict and gaps else 0)

if __name__ == "__main__":
    raise SystemExit(main())
