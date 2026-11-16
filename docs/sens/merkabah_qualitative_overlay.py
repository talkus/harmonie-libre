"""Read-only qualitative overlay for Merkabah experimental v0.3 (102/115).

Does NOT rewrite graph, create nodes, infer geometry, or certify Ezekiel.
Input must be exact pinned Git blob extracted with:
 git fetch --depth=1 origin merkabah/experimental-v03-two-scenes
 git show FETCH_HEAD:merkabah/schema/merkabah_candidate_v0.3.json > reference.json
"""
import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

SOURCE_BLOB = "fb2c508c164e72185368eca012160cf5240630b7"
SOURCE_REF = "merkabah/experimental-v03-two-scenes"
BIBLICAL_ENTITIES = {"living_being", "wheel", "spirit", "face", "wing",
                     "hands_presence", "legs_and_feet", "expanse", "throne",
                     "location", "person", "coals"}
MOVEMENT = {
    "living_being": ("GROUP_TRANSLATION_RISE_STOP", ["translate", "rise", "stop"]),
    "wheel": ("PAIRED_TRANSLATION_RISE_STOP", ["translate_with_being", "rise_with_being", "stop_with_being"]),
    "spirit": ("COORDINATES_NOT_A_RIGID_BODY", []),
    "face": ("INHERITS_PARENT_TRANSFORM_ONLY", []),
    "wing": ("INHERITS_PARENT_TRANSFORM_ONLY", []),
    "hands_presence": ("INHERITS_PARENT_TRANSFORM_ONLY", []),
    "legs_and_feet": ("INHERITS_PARENT_TRANSFORM_ONLY", []),
}
# Everything else remains explicitly unmodeled, not physically prohibited.

def git_blob_sha(data):
    return hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()

def load_pinned(path):
    raw = Path(path).read_bytes()
    if git_blob_sha(raw) != SOURCE_BLOB:
        raise ValueError("Source blob differs: refuse silent v0.3 replacement")
    graph = json.loads(raw)
    if (len(graph["nodes"]), len(graph["edges"])) != (102, 115):
        raise ValueError("Wrong cardinality for pinned two-scene graph")
    if set(graph["scenes"]) != {"ez1", "ez10"}:
        raise ValueError("Two biblical scenes must remain separate")
    return graph

def construct_overlay(graph):
    nodes = graph["nodes"]
    source_ids = set(graph["sources"])
    index = {n["id"]: n for n in nodes}
    if len(index) != len(nodes):
        raise ValueError("Duplicate node identifiers")
    counts = Counter((n["scene"], n["type"]) for n in nodes)
    for scene in ("ez1", "ez10"):
        if counts[(scene, "wheel")] != 4 or counts[(scene, "living_being")] != 4:
            raise ValueError("Exactly four wheels and beings PER scene")
    for e in graph["edges"]:
        if e["from"] not in index or e["to"] not in index:
            raise ValueError("Broken edge")
        if e["status"] not in {"TEXTUEL", "DEDUIT", "INTERPRETATION", "INCONNU"}:
            raise ValueError("Unknown edge provenance")
    overlay = {}
    for n in nodes:
        typ, scene = n["type"], n["scene"]
        if typ not in BIBLICAL_ENTITIES:
            raise ValueError("Unexpected type: " + typ)
        refs = n.get("references", [])
        if not refs or not all(r.get("source") in source_ids and r.get("verse") for r in refs):
            raise ValueError("Untraceable node: " + n["id"])
        kind, permitted = MOVEMENT.get(typ, ("NOT_SPECIFIED", []))
        warnings = ["Individual numbering, dimensions and positioning are model choices."]
        strength = "TEXTUAL_DESCRIPTION_NOT_GEOMETRIC_CERTAINTY" if n["status"] == "TEXTUEL" else "PROVISIONAL"
        if typ == "wheel":
            if n.get("wheel_inside_wheel") is not True:
                raise ValueError("Wheel-in-wheel attribute missing")
            warnings.append("Wheel-within-wheel is an attribute, not another wheel node.")
        if typ == "wheel" and scene == "ez1":
            strength = "TRANSLATION_DEPENDENT"
            warnings.append("Ez 1:18: NABRE eyes / AELF scintillements; preserve translation provenance.")
        if typ == "face":
            warnings.append("Ez 1:10 ox / Ez 10:14 cherub discrepancy is not silently harmonized.")
        if typ == "living_being":
            warnings.append("Ez1 living beings are named cherubim only in Ez10; numbering is not historical.")
        if typ in {"wheel", "living_being"}:
            warnings.append("Allowed motion here is a simulation constraint derived from shared motion, not an independent physical law.")
        overlay[n["id"]] = {
            "scene": scene, "type": typ,
            "evidence_strength": strength,
            "source_status": n["status"],
            "references": refs,
            "limitations": warnings,
            "motion": {
                "model_contract": kind,
                "allowed_in_candidate": permitted,
                "rotation_of_body": "NOT_REQUIRED" if typ == "living_being" else "UNSPECIFIED",
                "independent_motion": "NOT_MODELED" if typ in {"face", "wing", "hands_presence", "legs_and_feet"} else "UNDETERMINED",
                "ruach_zero": "PAUSE_SIMULATION" if typ in {"wheel", "living_being"} else "NOT_APPLICABLE",
            }
        }
    return {
        "status": "PROPOSED_NOT_VALIDATED", "source_blob_sha": SOURCE_BLOB,
        "graph_version": graph["version"], "node_count": len(overlay),
        "edge_count_untouched": len(graph["edges"]),
        "text_vs_simulation": "TEXT_SOURCE_DISTINCT_FROM_MOTION_CONTRACT",
        "nodes": overlay
    }

def main():
    p = argparse.ArgumentParser()
    p.add_argument("pinned_graph")
    p.add_argument("--out", type=Path)
    a = p.parse_args()
    result = construct_overlay(load_pinned(a.pinned_graph))
    dumped = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
    if a.out:
        a.out.write_text(dumped, encoding="utf-8")
        print("overlay exported:", a.out)
    else:
        print("verified", result["node_count"], "nodes,",
              result["edge_count_untouched"], "unchanged relationships",
              "across two scenes; no scene rendering")

if __name__ == "__main__":
    main()
