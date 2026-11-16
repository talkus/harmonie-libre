"""Contrat de cinematique Merkabah, CANDIDAT (Ez 1 seulement).

Controle mathematique de trajectoires echantillonnees, pas validation biblique
ni demonstration des formes reelles. Aucune geometrie physique canonisee.
"""
from __future__ import annotations

import math

COMMANDS = {
    "stop": (0, 0, 0),
    "east": (1, 0, 0), "west": (-1, 0, 0),
    "north": (0, 1, 0), "south": (0, -1, 0),
    "up": (0, 0, 1), "down": (0, 0, -1),
}
TOL = 1e-8


def _delta(end, start):
    return tuple(float(a) - float(b) for a, b in zip(end, start))


def _same(a, b):
    return len(a) == len(b) and all(math.isfinite(float(x)) and math.isfinite(float(y))
                                      and abs(float(x) - float(y)) < TOL for x, y in zip(a, b))


def graph_pairs(graph):
    """Rend les quatre associations documentees, ou lève ValueError."""
    errors = []
    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    edges = graph.get("edges", [])
    beings = {k for k, n in nodes.items() if n.get("type") == "living_being"}
    wheels = {k for k, n in nodes.items() if n.get("type") == "wheel_within_wheel"}
    if len(beings) != 4 or len(wheels) != 4:
        errors.append("COUNT_4_BEINGS_4_WHEELS")
    pairs = {}
    for being in sorted(beings):
        beside = [e["to"] for e in edges if e.get("from") == being and e.get("type") == "beside"]
        if len(beside) != 1 or beside[0] not in wheels:
            errors.append("ADJACENCY:" + being)
            continue
        wheel = beside[0]
        pairs[being] = wheel
        if len([e for e in edges if e.get("from") == wheel
                and e.get("to") == being and e.get("type") == "moves_with"]) != 1:
            errors.append("MOTION_RELATION:" + being)
        if len([e for e in edges if e.get("from") == being
                and e.get("to") == "ruach" and e.get("type") == "directed_by"]) != 1:
            errors.append("RUACH_RELATION:" + being)
    if len(set(pairs.values())) != 4:
        errors.append("NOT_ONE_TO_ONE")
    if errors:
        raise ValueError(";".join(errors))
    return pairs


def validate_track(graph, track):
    """Retourne des codes d'erreur; les positions sont des proxys arbitraires.

    Chaque frame: {t, command, poses: {id: {p: [x,y,z], yaw: nombre}}}.
    L'instruction externe commande la direction; les roues suivent les etres.
    """
    errors = []
    try:
        pairs = graph_pairs(graph)
    except (ValueError, KeyError, TypeError) as exc:
        return ["INVALID_GRAPH:" + str(exc)]
    if track.get("scene") != "Ezekiel_1":
        return ["SCENE_NOT_MODELED:Ez10_requires_separate_provenance"]
    if track.get("command_origin") != "EXTERNAL_PROXY":
        errors.append("COMMAND_ORIGIN_UNDOCUMENTED")
    frames = track.get("frames", [])
    if len(frames) < 2:
        return errors + ["TOO_FEW_FRAMES"]
    allowed = set(pairs) | set(pairs.values())
    start = frames[0].get("poses", {})
    for idx, frame in enumerate(frames):
        poses = frame.get("poses", {})
        if set(poses) != allowed:
            errors.append(f"OBJECT_SET:{idx}")
            continue
        for item, pose in poses.items():
            p = pose.get("p", ())
            yaw = pose.get("yaw")
            if len(p) != 3 or yaw is None or not _same(p, p) or not math.isfinite(float(yaw)):
                errors.append(f"BAD_POSE:{idx}:{item}")
                continue
            if item in start and not _same([yaw], [start[item].get("yaw", float("nan"))]):
                errors.append(f"TURNED:{idx}:{item}")
        for being, wheel in pairs.items():
            if not _same(_delta(poses[wheel]["p"], poses[being]["p"]),
                         _delta(start[wheel]["p"], start[being]["p"])):
                errors.append(f"WHEEL_LOST_ADJACENCY:{idx}:{wheel}")
        if idx == 0:
            continue
        prev = frames[idx - 1]
        if frame.get("t", -1) <= prev.get("t", -1):
            errors.append(f"TIME_NOT_INCREASING:{idx}")
        command = frame.get("command")
        if command not in COMMANDS:
            errors.append(f"UNKNOWN_COMMAND:{idx}")
            continue
        last = prev.get("poses", {})
        if set(last) != allowed:
            errors.append(f"PREVIOUS_FRAME_INVALID:{idx}")
            continue
        reference = _delta(poses[sorted(pairs)[0]]["p"], last[sorted(pairs)[0]]["p"])
        for item in sorted(allowed):
            if not _same(_delta(poses[item]["p"], last[item]["p"]), reference):
                errors.append(f"UNSYNCED:{idx}:{item}")
        direction = COMMANDS[command]
        forward = sum(reference[j] * direction[j] for j in range(3))
        cross = tuple(reference[j] - forward * direction[j] for j in range(3))
        if (command == "stop" and not _same(reference, (0, 0, 0))) or (
            command != "stop" and (forward <= TOL or not _same(cross, (0, 0, 0)))
        ):
            errors.append(f"COMMAND_MISMATCH:{idx}:{command}")
    return errors


def example_track(graph, commands=("east", "north", "up", "stop", "west")):
    """Exemple de calcul artificiel (non observation du texte ni de la vision)."""
    pairs = graph_pairs(graph)
    poses = {}
    for i, (being, wheel) in enumerate(sorted(pairs.items())):
        x = -3.0 if i % 2 == 0 else 3.0
        y = -3.0 if i // 2 == 0 else 3.0
        poses[being] = {"p": [x, y, 1.0], "yaw": 0.0}
        poses[wheel] = {"p": [x + 1.0, y, 1.0], "yaw": 0.0}
    frames = [{"t": 0, "command": "stop", "poses": {k: {"p": v["p"][:], "yaw": v["yaw"]} for k, v in poses.items()}}]
    for t, cmd in enumerate(commands, 1):
        direction = COMMANDS[cmd]
        for pose in poses.values():
            pose["p"] = [pose["p"][j] + direction[j] for j in range(3)]
        frames.append({"t": t, "command": cmd, "poses": {k: {"p": v["p"][:], "yaw": v["yaw"]} for k, v in poses.items()}})
    return {"scene": "Ezekiel_1", "command_origin": "EXTERNAL_PROXY", "frames": frames}