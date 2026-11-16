"""Join current scholarship to the already-pinned Merkabah candidate, read-only.

The 102/115 source graph is never modified. Interpretation is metadata, not
biblical new nodes, edges, coordinates or proven geometry.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0,str(Path(__file__).resolve().parent))
from merkabah_qualitative_overlay import load_pinned, construct_overlay

RESEARCH = Path(__file__).resolve().parent / "recherche_ezechiel_2026.json"
ALLOWED = {"SCHOLARLY_HYPOTHESIS", "TRANSLATION_VARIANT", "LITERARY_INTERPRETATION"}
STATUS = "PROPOSED_NOT_VALIDATED"

def build_researched_model(graph, research):
    before = json.dumps(graph, ensure_ascii=False, sort_keys=True)
    if research.get("status") != STATUS or research.get("kind") != "LITERATURE_OVERLAY_NOT_CANON":
        raise ValueError("Non-canonical research status required")
    if research.get("source_graph",{}).get("blob_sha") != "fb2c508c164e72185368eca012160cf5240630b7":
        raise ValueError("Research bound to wrong source graph")
    if graph.get("status") != STATUS or (len(graph["nodes"]),len(graph["edges"])) != (102,115):
        raise ValueError("Wrong unvalidated graph or graph count")
    entries = research.get("findings",[])
    if not entries or len({e["id"] for e in entries}) != len(entries):
        raise ValueError("Missing or duplicate research IDs")
    out = construct_overlay(graph)
    out["evidence_as_of"] = research["researched_as_of"]
    out["research_status"] = research["status"]
    out["research_sources"] = copy.deepcopy(research["sources"])
    out["discourse_interpretations"] = []
    for node in out["nodes"].values():
        node["research_annotations"]=[]
    for entry in entries:
        fid, level = entry["id"], entry["level"]
        if level not in ALLOWED or entry.get("assertion_mode") in (None, "FACT_CERTIFIED"):
            raise ValueError("Research must be qualified")
        if not entry.get("source_ids") or not entry.get("limits") or not entry.get("rendering_implication"):
            raise ValueError("Research provenance, limits and rendering needed")
        if not all(src in research["sources"] for src in entry["source_ids"]):
            raise ValueError("Research source missing")
        ids=entry["target_node_ids"]
        if len(ids)!=len(set(ids)):
            raise ValueError("Duplicate mapped node")
        if level=="TRANSLATION_VARIANT" and (len(entry["source_ids"])<2 or len(entry.get("rendering_profiles",[]))<2):
            raise ValueError("Translation conflict must preserve distinct sources and visual alternatives")
        if not ids:
            if level != "LITERARY_INTERPRETATION":
                raise ValueError("Non-literary findings must be grounded to nodes")
            out["discourse_interpretations"].append(fid)
        for node_id in ids:
            if node_id not in out["nodes"]:
                raise ValueError(f"Nonexistent graph node in research {fid}: {node_id}")
            if not (node_id.startswith("ez1_") or node_id.startswith("ez10_")):
                raise ValueError("Unknown scene node")
            # Adds annotations to an existing output node, NEVER to the source graph.
            out["nodes"][node_id]["research_annotations"].append({
                "finding_id":fid,
                "level":level,
                "source_ids":copy.deepcopy(entry["source_ids"]),
                "limits":copy.deepcopy(entry["limits"]),
                "rendering_implication":entry["rendering_implication"],
                "rendering_profiles":copy.deepcopy(entry.get("rendering_profiles",[])),
                "assertion_mode":entry["assertion_mode"]
            })
    if json.dumps(graph,ensure_ascii=False,sort_keys=True)!=before:
        raise AssertionError("BUG: research modified source graph")
    if len(out["nodes"])!=102 or out["edge_count_untouched"]!=115:
        raise AssertionError("BUG: model ontology was altered")
    out["research_finding_count"]=len(entries)
    out["graph_digest_unchanged"]=hashlib.sha256(before.encode("utf-8")).hexdigest()
    return out

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("pinned_graph")
    parser.add_argument("--out",type=Path)
    args=parser.parse_args()
    graph=load_pinned(args.pinned_graph)
    research=json.loads(RESEARCH.read_text(encoding="utf-8"))
    view=build_researched_model(graph,research)
    if args.out:
        args.out.write_text(json.dumps(view,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    print(f"Merkabah research overlay PASS: {len(view['nodes'])} nodes, 115 original relations, "
          f"{view['research_finding_count']} qualified findings, "
          f"{len(view['discourse_interpretations'])} discourse-level readings")

if __name__=="__main__":
    main()
