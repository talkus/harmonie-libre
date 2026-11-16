"""Validate a candidate graph without claiming historical or visual verification."""
import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path

SCENES = {"ez1", "ez10"}
FACE_FORMS = {"ez1": {"human", "lion", "ox", "eagle"},
              "ez10": {"cherub", "human", "lion", "eagle"}}
STATUSES = {"TEXTUEL", "DEDUIT", "INTERPRETATION", "INCONNU"}


def validate(graph):
    """Return human-readable errors; all graph comparisons are scene-local."""
    errors = []
    if graph.get("status") != "PROPOSED_NOT_VALIDATED":
        errors.append("candidate status must remain PROPOSED_NOT_VALIDATED")
    scenes = graph.get("scenes", [])
    if len(scenes) != 2 or set(scenes) != SCENES:
        errors.append("exactly the two distinct scenes ez1 and ez10 are required")
    sources = graph.get("sources", {})
    nodes, edges = graph.get("nodes", []), graph.get("edges", [])
    node_ids = [n.get("id") for n in nodes]
    if not all(isinstance(i, str) and i for i in node_ids) or len(set(node_ids)) != len(node_ids):
        errors.append("node ids must be nonempty and unique")
    index = {n.get("id"): n for n in nodes}
    outgoing, incoming, seen = defaultdict(list), defaultdict(list), set()

    def check_refs(obj, label):
        scene = obj.get("scene")
        refs = obj.get("references", [])
        if scene not in SCENES:
            errors.append(f"{label}: unknown scene")
        if obj.get("status") not in STATUSES:
            errors.append(f"{label}: unknown status")
        if not isinstance(refs, list) or not refs:
            errors.append(f"{label}: references required")
            return
        for ref in refs:
            source, verse = ref.get("source"), ref.get("verse")
            if source not in sources or not isinstance(verse, str) or not verse.strip():
                errors.append(f"{label}: invalid reference")
            elif scene in SCENES and (not source.endswith("_" + scene.upper()) or not verse.startswith("1:" if scene == "ez1" else "10:")):
                errors.append(f"{label}: reference belongs to another scene")

    for node in nodes:
        check_refs(node, f"node {node.get('id')}")
    for edge in edges:
        label = f"edge {edge.get('from')} -> {edge.get('to')}"
        check_refs(edge, label)
        source, target, kind, scene = edge.get("from"), edge.get("to"), edge.get("type"), edge.get("scene")
        key = (source, target, kind, scene)
        if key in seen:
            errors.append(f"{label}: duplicate relation {kind}")
        seen.add(key)
        if source not in index or target not in index:
            errors.append(f"{label}: missing endpoint")
            continue
        if index[source].get("scene") != scene or index[target].get("scene") != scene:
            errors.append(f"{label}: cross-scene relation")
        outgoing[(source, kind)].append(target)
        incoming[(target, kind)].append(source)

    for scene in sorted(SCENES):
        subset = [n for n in nodes if n.get("scene") == scene]
        by_type = defaultdict(list)
        for n in subset:
            by_type[n.get("type")].append(n)
        for kind, count in (("living_being", 4), ("wheel", 4), ("face", 16), ("wing", 16), ("expanse", 1), ("throne", 1)):
            if len(by_type[kind]) != count:
                errors.append(f"{scene}: expected {count} {kind}, got {len(by_type[kind])}")
        for being in by_type["living_being"]:
            ident = being["id"]
            faces, wings = outgoing[(ident, "has_face")], outgoing[(ident, "has_wing")]
            wheels = outgoing[(ident, "beside")]
            forms = [index[x].get("form") for x in faces if x in index and index[x].get("type") == "face"]
            if len(faces) != 4 or set(forms) != FACE_FORMS[scene]:
                errors.append(f"{ident}: four distinct scene-appropriate faces required")
            if len(wings) != 4 or any(index[x].get("type") != "wing" for x in wings if x in index):
                errors.append(f"{ident}: four wings required")
            if len(wheels) != 1 or any(index[x].get("type") != "wheel" for x in wheels if x in index):
                errors.append(f"{ident}: exactly one associated wheel required")
            for wheel in wheels:
                if outgoing[(wheel, "moves_with")] != [ident]:
                    errors.append(f"{ident}: wheel movement association missing or ambiguous")
            for name in faces:
                if len(incoming[(name, "has_face")]) != 1:
                    errors.append(f"{name}: face must have exactly one owner")
            for name in wings:
                if len(incoming[(name, "has_wing")]) != 1:
                    errors.append(f"{name}: wing must have exactly one owner")
        for wheel in by_type["wheel"]:
            if len(incoming[(wheel["id"], "beside")]) != 1:
                errors.append(f"{wheel['id']}: wheel must have exactly one owner")
            if wheel.get("wheel_inside_wheel") is not True:
                errors.append(f"{wheel['id']}: wheel within wheel not represented")
            rr = wheel.get("rim_reference", {})
            if (rr.get("source") not in sources or not rr.get("verse")
                    or not rr.get("source", "").endswith("_" + scene.upper())
                    or not rr.get("verse", "").startswith("1:" if scene == "ez1" else "10:")):
                errors.append(f"{wheel['id']}: rim translation reference required")
        if len(by_type["expanse"]) == len(by_type["throne"]) == 1:
            if outgoing[(by_type["throne"][0]["id"], "above")] != [by_type["expanse"][0]["id"]]:
                errors.append(f"{scene}: throne/expanse relation missing")
    return errors


def to_networkx(graph):
    """Optional MultiDiGraph: retains parallel typed edges and all provenance."""
    import networkx as nx
    result = nx.MultiDiGraph()
    for node in graph["nodes"]:
        result.add_node(node["id"], **{k: v for k, v in node.items() if k != "id"})
    for edge in graph["edges"]:
        result.add_edge(edge["from"], edge["to"], **{k: v for k, v in edge.items() if k not in {"from", "to"}})
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("graph", nargs="?", type=Path, default=Path(__file__).parent / "schema" / "merkabah_candidate_v0.3.json")
    args = parser.parse_args()
    try:
        graph = json.loads(args.graph.read_text(encoding="utf-8"))
        errors = validate(graph)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(f"ERREUR DE LECTURE: {exc}")
        return 2
    if errors:
        print("\n".join("ECHEC: " + error for error in errors))
        return 1
    print("OK: cohérence structurelle du candidat uniquement; scènes et interprétations non validées.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
