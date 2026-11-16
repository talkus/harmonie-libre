"""Attach verified R33 matrix to researched Merkabah as a NON-biblical symbolic layer.

Does not alter biblical nodes, edges, source text, geometry or graph counts.
"""
import argparse
import copy
import json
from collections import Counter
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from merkabah_qualitative_overlay import load_pinned
from model_update_recent_research import build_researched_model, RESEARCH

MATRIX=HERE / "archives" / "matrice_r33_72_portes_288_entrees_20261108.json"
SOURCE_URL="https://docs.google.com/document/d/1nGJMjHhe1xVl0Z3-pMGDJRlWk-BL0DR68Sr1FXdVghA/edit"

def load_matrix():
    matrix=json.loads(MATRIX.read_text(encoding="utf-8"))
    if matrix.get("kind") != "SYMBOLIC_ARCHIVE_TRANSCRIPTION_NOT_BIBLICAL_CANON":
        raise ValueError("Refuse archive promoted to biblical source")
    if SOURCE_URL not in [x["url"] for x in matrix["sources"]]:
        raise ValueError("Unidentified original matrix source")
    doors=matrix["doors"]; entries=matrix["entries"]
    if (len(doors),len(entries)) != (72,288):
        raise ValueError("Expected 72 gates and 288 archived entries")
    seen=set()
    counts=Counter()
    by_gate={}
    for d in doors:
        key=d["id"]
        if key in by_gate or not (1<=d["index"]<=72):
            raise ValueError("Duplicate/invalid gate")
        by_gate[key]=d
    for number,e in enumerate(entries,1):
        expected=f"E{number:03d}"
        phase=f"D{(number-1)%4+1}"
        gate=f"N{((number-1)//4)+1:02d}"
        if e["id"]!=expected or e["phase"]!=phase or e["gate_id"]!=gate or e["order"]!=number:
            raise ValueError(f"Wrong archival identity/phase on {expected}")
        if not e["text"] or e["provenance_status"]!="RECONSTRUCTED_FROM_ARCHIVED_MATRIX":
            raise ValueError("Archive text or non-canonical status missing")
        if e["id"] in seen:
            raise ValueError("Duplicate spark")
        seen.add(e["id"])
        counts[phase]+=1
    if any(counts[f"D{i}"]!=72 for i in range(1,5)):
        raise ValueError("Each phase must have 72 entries")
    for number,d in enumerate(doors,1):
        if d["id"]!=f"N{number:02d}" or d["index"]!=number:
            raise ValueError("Gate order discrepancy")
        if any(not d[key] for key in ("gates_k22","inter_portes","sequence","label")):
            raise ValueError("Gate provenance or relation text absent")
    return matrix

def build_full_model(graph,matrix):
    research=json.loads(RESEARCH.read_text(encoding="utf-8"))
    model=build_researched_model(graph,research)
    if (len(model["original_graph"]["nodes"]),len(model["original_graph"]["edges"]))!=(102,115):
        raise ValueError("Original scripture graph tampered with")
    if matrix["kind"]!="SYMBOLIC_ARCHIVE_TRANSCRIPTION_NOT_BIBLICAL_CANON":
        raise ValueError("Symbolic layer status invalid")
    phases={
      "D1":{"title":"Origine / Lumière","capteur":"Humilité"},
      "D2":{"title":"Écorce / Kelipah","capteur":"Pardon"},
      "D3":{"title":"Chemin inverse","capteur":"Reconnaissance"},
      "D4":{"title":"Étincelle relevée / retour ouvert","capteur":"Espérance"},
    }
    for phase,datum in phases.items():
        datum["entry_ids"]=[e["id"] for e in matrix["entries"] if e["phase"]==phase]
        if len(datum["entry_ids"])!=72:
            raise ValueError("Phase not complete")
    for scene in ("ez1","ez10"):
        for i in range(1,5):
            n=f"{scene}_wheel_{i}"
            if n not in model["nodes"]:
                raise ValueError("Biblical wheel missing "+n)
    model["symbolic_layer"]={
      "id":"R33_72X4_288_ARCHIVAL_MATRIX",
      "status":"INTERPRETATIVE_ANALOGY_NOT_EZEKIEL_TEXT",
      "archive_source":SOURCE_URL,
      "preserved_identifiers":"E001..E288 / N01..N72",
      "origin_story":"Architecture C R33 derived reconstruction; not 288 literal flames or eyes in Ezekiel",
      "original_72_gates":copy.deepcopy(matrix["doors"]),
      "original_288_entries":copy.deepcopy(matrix["entries"]),
      "phases":phases,
      "bridge":{
        "type":"SYMBOLIC_VIEW_OF_SCINTILLATIONS_NOT_GRAPH_EDGE",
        "choice":"OPTIONAL_EXPLICIT",
        "literal_identity":False,
        "each_wheel_is_a_symbolic_individual_spark":False,
        "wheel_1_equals_D1":False,
        "explanation":"Possible conceptual bridge from Ezekiel glitter/eyes to sparks and repair; not an asserted interpretation of the biblical text.",
        "linked_wheel_groups":{
           scene:[f"{scene}_wheel_{i}" for i in range(1,5)]
           for scene in ("ez1","ez10")
        },
        "lexical_disambiguation":"AELF scintillements vs NABRE/NET yeux is a translation issue, NOT proof of Lurianic nitzotzot or of the R33 288."
      }
    }
    if (len(model["original_graph"]["nodes"]),len(model["original_graph"]["edges"]))!=(102,115):
        raise AssertionError("Original graph counts altered")
    return model

def main():
    p=argparse.ArgumentParser()
    p.add_argument("pinned_graph")
    p.add_argument("--out",type=Path)
    args=p.parse_args()
    matrix=load_matrix()
    graph=load_pinned(args.pinned_graph)
    model=build_full_model(graph,matrix)
    if args.out:
        args.out.write_text(json.dumps(model,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("MERKABAH+R33 INTEGRATION PASS: 102 biblical nodes, 115 relations unchanged;"
          " 72 symbolic gates, 288 archived phase entries (72 each); optional analogy only")

if __name__=="__main__":
    main()
