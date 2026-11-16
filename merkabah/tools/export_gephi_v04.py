"""Export Merkabah v0.4 as an auditable Gephi GEXF candidate (NetworkX).

Structural coherence only; no biblical, geometric, or theological attestation.
GEXF 1.2draft is NetworkX's supported format; it is NOT GEXF 1.3.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "schema" / "merkabah_candidate_v0.4.json"
DESTINATION = ROOT / "exports" / "merkabah_v04_candidate.gexf"
ALLOWED = {"TEXTUAL", "DERIVED", "UNCERTAIN", "INTERPRETATION", "UNKNOWN"}


def validate_source(data: dict) -> None:
    if data.get("project") != "MERKABAH" or data.get("version") != "0.4.0-candidate":
        raise ValueError("Expected Merkabah candidate v0.4 only")
    if data.get("status") != "PROPOSED_NOT_VALIDATED":
        raise ValueError("Cannot silently promote candidate status")
    for key in ("nodes", "edges", "sources"):
        if not isinstance(data.get(key), list):
            raise ValueError("Missing or invalid " + key)
    ids = [n["id"] for n in data["nodes"]]
    if len(ids) != len(set(ids)) or len(ids) != 61:
        raise ValueError("Unexpected count or duplicate node identifiers")
    if len(data["edges"]) != 76:
        raise ValueError("Unexpected edge count")
    sources = [s["id"] for s in data["sources"]]
    if len(sources) != 10 or len(set(sources)) != 10:
        raise ValueError("Incorrect source inventory")
    for node in data["nodes"]:
        if node.get("source") not in sources or node.get("status") not in ALLOWED:
            raise ValueError("Undeclared source or epistemic status at node " + node["id"])
    for edge in data["edges"]:
        if not {edge.get("from"), edge.get("to")} <= set(ids):
            raise ValueError("Unresolved edge endpoint")
        if edge.get("source") not in sources:
            raise ValueError("Undeclared edge source")
        if "status" in edge and edge["status"] not in ALLOWED:
            raise ValueError("Invalid edge status")
    uncertain = [n for n in data["nodes"] if n["id"] == "face_discrepancy_ez10_14"]
    if len(uncertain) != 1 or uncertain[0]["status"] != "UNCERTAIN":
        raise ValueError("Missing open textual discrepancy")
    comp = uncertain[0].get("verse_comparison", {})
    if comp.get("Ezekiel_1") != ["human", "lion", "ox", "eagle"]:
        raise ValueError("Ezekiel 1:10 face inventory changed")
    if comp.get("Ezekiel_10") != ["cherub", "human", "lion", "eagle"]:
        raise ValueError("Ezekiel 10:14 face inventory changed")


def _attribute(value):
    if isinstance(value, (list, dict)):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    if value is None:
        return "UNSPECIFIED"
    return value


def build_graph(data: dict) -> nx.MultiDiGraph:
    validate_source(data)
    graph = nx.MultiDiGraph(
        project=data["project"], version=data["version"],
        epistemic_status=data["status"],
        analysis_note="Centralities are descriptive; they establish no truth or authority."
    )
    for node in data["nodes"]:
        attrs = {"kind": node["type"], "source_ref": node["source"],
                 "epistemic_status": node["status"]}
        attrs.update({k: _attribute(v) for k, v in node.items()
                      if k not in {"id", "type", "source", "status"}})
        graph.add_node(node["id"], **attrs)
    for idx, edge in enumerate(data["edges"]):
        graph.add_edge(edge["from"], edge["to"], key=str(idx),
                       relation=edge["type"], source_ref=edge["source"],
                       epistemic_status=edge.get("status", "UNSPECIFIED"),
                       source_edge_index=idx)
    simple = nx.DiGraph()
    simple.add_nodes_from(graph.nodes())
    simple.add_edges_from((u, v) for u, v in graph.edges())
    centrality = nx.betweenness_centrality(simple, weight=None, normalized=True)
    for node_id, value in centrality.items():
        graph.nodes[node_id]["betweenness_brandes_directed_projection"] = float(value)
        graph.nodes[node_id]["projected_in_degree"] = int(simple.in_degree(node_id))
        graph.nodes[node_id]["projected_out_degree"] = int(simple.out_degree(node_id))
    return graph


def export(data: dict, destination: Path) -> nx.MultiDiGraph:
    graph = build_graph(data)
    destination.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(graph, destination, version="1.2draft")
    loaded = nx.read_gexf(destination)
    if loaded.number_of_nodes() != 61 or loaded.number_of_edges() != 76:
        destination.unlink(missing_ok=True)
        raise ValueError("GEXF roundtrip lost nodes or edges")
    if loaded.nodes["face_discrepancy_ez10_14"]["epistemic_status"] != "UNCERTAIN":
        destination.unlink(missing_ok=True)
        raise ValueError("GEXF roundtrip lost the textual discrepancy")
    return graph


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--output", type=Path, default=DESTINATION)
    args = parser.parse_args()
    data = json.loads(args.source.read_text(encoding="utf-8"))
    graph = export(data, args.output)
    print(json.dumps({"status": "PROPOSED_NOT_VALIDATED", "version": data["version"],
                      "format": "GEXF 1.2draft", "nodes": graph.number_of_nodes(),
                      "edges": graph.number_of_edges(), "output": str(args.output)},
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
