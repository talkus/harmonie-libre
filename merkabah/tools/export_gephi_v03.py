"""Export candidat Merkabah v0.3 vers Gephi GEXF; aucune validation biblique."""
import json
from pathlib import Path
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "schema" / "merkabah_candidate_v0.3.json"
OUTPUT = ROOT / "exports" / "merkabah_v03.gexf"

def build_graph(data):
    graph = nx.MultiDiGraph(project="MERKABAH", epistemic_status="PROPOSED_NOT_VALIDATED")
    for n in data["nodes"]:
        attrs = {"kind": n["type"], "source_ref": n["source"], "epistemic_status": n["status"]}
        if "form" in n:
            attrs["form"] = n["form"]
        graph.add_node(n["id"], **attrs)
    for i, e in enumerate(data["edges"]):
        if e["from"] not in graph or e["to"] not in graph:
            raise ValueError("Unresolved edge endpoint")
        graph.add_edge(e["from"], e["to"], key=str(i),
                       relation=e["type"], source_ref=e["source"],
                       epistemic_status=e.get("status", "UNSPECIFIED"))
    if graph.number_of_nodes() != len(data["nodes"]) or graph.number_of_edges() != len(data["edges"]):
        raise ValueError("Graph cardinality mismatch")
    # Projection simple pour Brandes: la centralité ne prouve ni la valeur ni la vérité d'un élément.
    projected = nx.DiGraph()
    projected.add_nodes_from(graph.nodes)
    projected.add_edges_from((u,v) for u,v in graph.edges())
    scores = nx.betweenness_centrality(projected, normalized=True)
    for node, score in scores.items():
        graph.nodes[node]["betweenness_brandes_projected"] = float(score)
    return graph

def main():
    data = json.loads(SOURCE.read_text(encoding="utf-8"))
    if data["status"] != "PROPOSED_NOT_VALIDATED":
        raise ValueError("Unexpected canonical status")
    graph = build_graph(data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    nx.write_gexf(graph, OUTPUT)
    print(f"Wrote {OUTPUT}: {graph.number_of_nodes()} nodes, {graph.number_of_edges()} edges, non-validated candidate")

if __name__ == "__main__":
    main()
