"""Reproducible incident fixture. No sensor, network, service or human seal.

The numerical checks and optional-extra Ed25519 operations really run locally.
All scenario evidence remains an analytical reconstruction in the brain.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import tempfile

from .core import ConscienceCBrain
from .examination_grid import EXAMINATION_GRID_VERSION, examination_profile
from .models import CausalOrigin, Evidence, EvidenceKind
from .work_coordination import WORK_VERSION
from .gabriel import GABRIEL_CRITERIA_VERSION


PROPOSAL = "ASSISTANT_PROPOSAL_REVISABLE"


def _bytes(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def _sha(value):
    return hashlib.sha256(_bytes(value)).hexdigest()


def sign_fixture_packet(payload):
    # Fresh throwaway key, never written. This is not RFC8785 or the registry protocol.
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    key = Ed25519PrivateKey.generate()
    public = key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)
    return {"protocol": "CC-SIM-SIGNED-1", "canonicalization": "python-json-sorted-utf8",
            "payload": copy.deepcopy(payload), "payload_sha256": _sha(payload),
            "public_key_hex": public.hex(), "signature_hex": key.sign(_bytes(payload)).hex()}


def verify_fixture_packet(packet):
    from cryptography.exceptions import InvalidSignature
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    try:
        if (packet["protocol"] != "CC-SIM-SIGNED-1" or
                packet["canonicalization"] != "python-json-sorted-utf8" or
                packet["payload_sha256"] != _sha(packet["payload"])):
            return False
        key = Ed25519PublicKey.from_public_bytes(bytes.fromhex(packet["public_key_hex"]))
        key.verify(bytes.fromhex(packet["signature_hex"]), _bytes(packet["payload"]))
        return True
    except (InvalidSignature, ValueError, TypeError, KeyError):
        return False


def binary_floats(values):
    return bool(values) and all(type(v) is float and math.isfinite(v) and v in {-1.0, 1.0}
                                for v in values)


def participation_rank(matrix):
    """PR of eigenvalues of W W^T: tr(G)^2 / tr(G^2), not a universal quality score."""
    if (not matrix or not matrix[0] or any(len(row) != len(matrix[0]) for row in matrix)
            or any(type(v) not in (int, float) or not math.isfinite(v) for row in matrix for v in row)):
        raise ValueError("finite rectangular numeric matrix required")
    scale = max(abs(v) for row in matrix for v in row)
    if not scale:
        raise ValueError("nonzero finite spectrum required")
    normalized = [[v / scale for v in row] for row in matrix]
    gram = [[sum(a * b for a, b in zip(left, right)) for right in normalized] for left in normalized]
    trace = sum(gram[i][i] for i in range(len(gram)))
    square_trace = sum(v * v for row in gram for v in row)
    if not square_trace or not math.isfinite(square_trace) or not math.isfinite(trace):
        raise ValueError("nonzero finite spectrum required")
    return trace * trace / square_trace


def fixture_merkle_root(records):
    """CC-SIM-MERKLE-1, domain separated, duplicate last on odd levels; not RFC9162."""
    if not records:
        raise ValueError("nonempty fixture required")
    level = [hashlib.sha256(b"\x00" + _bytes(row)).digest() for row in records]
    while len(level) > 1:
        if len(level) % 2:
            level.append(level[-1])
        level = [hashlib.sha256(b"\x01" + level[i] + level[i + 1]).digest()
                 for i in range(0, len(level), 2)]
    # Commit the count, so padding cannot confuse three leaves with four.
    return hashlib.sha256(b"\x02" + len(records).to_bytes(8, "big") + level[0]).hexdigest()


def compare_fixture_replicas(local, remote):
    if local["checkpoint"] != remote["checkpoint"]:
        return "UNKNOWN"
    return "PASS" if fixture_merkle_root(local["records"]) == fixture_merkle_root(remote["records"]) else "FAIL"


def _plan(claims, sources):
    order = ("micro", "micro-independent", "meso", "macro", "meta")
    dependencies = {"micro": [], "micro-independent": [], "meso": ["micro"],
                    "macro": ["meso"], "meta": ["macro"]}
    units = []
    for uid in order:
        scale = "micro" if uid == "micro-independent" else uid
        units.append({"id": uid,
            "purpose": {"goal_refs": ["EXAMINER"], "serves_because": "Transmettre le constat et ses limites"},
            "scope": {"view": scale, "boundary": "simulation:" + uid,
                      "observer": "simulation:lecteur", "reviews": list(order[:-1]) if uid == "meta" else []},
            "work": {"kind": "gabriel_examine", "claim_id": claims[uid],
                     "depends_on": dependencies[uid], "input_refs": [sources[uid]],
                     "output_contract": "Diagnostic de scénario, aucune autorité réelle", "subject_ref": None},
            "review": {"criteria_version": GABRIEL_CRITERIA_VERSION,
                       "objection_refs": [], "unknown_refs": ["UNKNOWN:terrain:" + uid]},
            "evidence": {"source_refs": [sources[uid]]},
            "continuity": {"next_step": "Examiner les limites avant une décision séparée"}})
    return {"plan_id": "signal-muet-simulation-v1", "version": WORK_VERSION,
            "goals": [{"id": "EXAMINER", "parent": None, "text": "Examiner sans confondre simulation et terrain",
                       "serves_because": "Préserver R≺E et la révisabilité", "priority": 0}],
            "units": units, "budget": {"max_attempts": 8, "timeout_seconds": 10,
                                       "max_inflight": 1, "retry_delay_seconds": 0}}


def run_simulation(root):
    root = Path(root)
    if root.exists() and any(root.iterdir()):
        raise ValueError("simulation requires an empty isolated directory; existing memory refused")
    brain = ConscienceCBrain.load_or_bootstrap(root)
    anchor = copy.deepcopy(brain.state["S"]["invariants"])
    sensor, output = [-1.0, 1.0, -1.0, 1.0], [1.0, 1.0, 1.0, 1.0]
    typed = binary_floats(output)
    frozen = len(set(output)) == 1 and len(set(sensor)) > 1
    packet = sign_fixture_packet({"packet_id": "fixture:packet-1", "outputs": output})
    signed = verify_fixture_packet(packet)
    queue = [{"id": "bad-channel", "wait_cycles": 4}, {"id": "healthy-channel", "wait_cycles": 0}]
    # Fixture policy only, not the deployed coordinator's scheduling policy.
    triage = sorted(queue, key=lambda q: (q["wait_cycles"] < 3, -q["wait_cycles"]))
    quarantine = [q["id"] for q in triage if q["id"] == "bad-channel"]
    baseline, drifted = [[1.0, 0.0], [0.0, 1.0]], [[1.0, 1.0], [1.0, 1.0]]
    local = {"checkpoint": "fixture:replica-v1", "records": [{"W": drifted}, {"outputs": output}]}
    remote = {"checkpoint": "fixture:replica-v1", "records": [{"W": baseline}, {"outputs": output}]}
    older = {**remote, "checkpoint": "fixture:replica-v0"}
    artifacts = {
        "micro": {"sensor": sensor, "output": output, "type_valid": typed, "frozen_alert": frozen,
                  "accepted_as_empirical": not frozen, "raw_trace_retained": True},
        "micro-independent": {"channel": "healthy-channel", "isolated_from": quarantine},
        "meso": {"packet": packet, "signature_valid": signed, "authorized_key_identity": "UNKNOWN",
                 "queue": queue, "fixture_triage_order": [q["id"] for q in triage],
                 "quarantined_channels": quarantine, "nonconvergence_established": False},
        "macro": {"baseline_rank_pr": participation_rank(baseline),
                  "drifted_rank_pr": participation_rank(drifted), "fixture_min_rank_pr": 1.5,
                  "local_merkle_root": fixture_merkle_root(local["records"]),
                  "remote_merkle_root": fixture_merkle_root(remote["records"]),
                  "same_checkpoint_comparison": compare_fixture_replicas(local, remote),
                  "different_checkpoint_comparison": compare_fixture_replicas(local, older)},
        "meta": {"proposal_status": PROPOSAL, "proposal": "Séparer contrôle de type et ancrage empirique ; comparer des répliques au même checkpoint",
                 "beta_candidate": None, "beta_cause_established": False,
                 "automatic_remediation": False, "human_seal": False, "canonical_version": None,
                 "retention_after_candidate_restore": "UNKNOWN"},
    }
    claims, sources = {}, {}
    for uid, artifact in artifacts.items():
        claims[uid] = brain.record_claim("Le contrat de " + uid + " est satisfait sur le terrain",
                                         "system_hypothesis", "simulation:signal-muet")["claim_id"]
        sources[uid] = "simulation:artifact:sha256:" + _sha(artifact)
        brain.ingest_evidence(Evidence("SIM-" + uid, _bytes(artifact).decode("utf-8"),
            EvidenceKind.ANALYTICAL_RECONSTRUCTION, source_ref=sources[uid],
            claim_ref=claims[uid], scope="simulation:" + uid, stance="context"), CausalOrigin.SELF)
    meta_diagnostic = brain.record_gabriel_examination(claims["meta"], scope_ref="simulation:meta",
        observer_ref="simulation:lecteur", scale="meta", provenance="simulation:meta-question")
    objection = brain.contest_gabriel(meta_diagnostic["report_ref"],
        reason="Pourquoi un contrôle de type suffirait-il à établir l'ancrage empirique ?",
        actor="simulation:critique", provenance="simulation:objection-au-critere")
    initial_rows = brain.ledger.read_verified()
    spec = _plan(claims, sources)
    brain.record_work_plan(spec, provenance="simulation:incident")
    executed = []
    while len(executed) < len(spec["units"]):
        result = brain.work_run_next(spec["plan_id"])
        if not result["started"] or result["outcome"] != "completed":
            raise RuntimeError("simulation examination failed: " + str(result.get("outcome")))
        executed.append(result["unit_id"])
        brain = ConscienceCBrain.load_or_bootstrap(root)
    view = brain.work_view(spec["plan_id"])
    units = {u["id"]: u for u in view["units"]}
    rows = brain.ledger.read_verified()
    history_preserved = rows[:len(initial_rows)] == initial_rows and brain.audit() == []
    if not history_preserved or brain.state["S"]["invariants"] != anchor:
        raise RuntimeError("fixture history or anchor changed")
    artifact_integrity = _sha(json.loads(brain.state["E"]["evidence"]["SIM-micro"]["content"])) == _sha(artifacts["micro"])
    unknown_origins = {d["origin_unit_id"] for d in units["meta"]["review"]["unknown_details"]}
    objection_preserved = objection["event_hash"] in units["meta"]["review"]["objection_refs"]
    criteria = {
        "micro": {"MIC-TYPE": "PASS" if typed else "FAIL", "MIC-TRACE": "PASS" if artifact_integrity else "FAIL", "MIC-ANCHOR": "UNKNOWN", "MIC-UNKNOWN": "PASS" if unknown_origins == set(artifacts) else "FAIL"},
        "meso": {"MES-ENVELOPE": "UNKNOWN" if signed else "FAIL", "MES-DELIVERY": "FAIL" if queue[0]["wait_cycles"] > 3 else "PASS", "MES-FAIRNESS": "PASS" if triage[0]["wait_cycles"] >= 3 else "FAIL", "MES-PERMISSION": "UNKNOWN"},
        "macro": {"MAC-HISTORY": "PASS" if history_preserved else "FAIL", "MAC-REPLICA": compare_fixture_replicas(local, remote),
                  "MAC-RETENTION": "FAIL" if participation_rank(drifted) < 1.5 else "PASS", "MAC-REVOCATION": "UNKNOWN"},
        "meta": {"MET-OBJECTION": "PASS" if objection_preserved else "FAIL", "MET-REVISION": "UNKNOWN", "MET-VETO": "UNKNOWN", "MET-GENERATIVITY": "UNKNOWN"},
    }
    stages = []
    for scale in ("micro", "meso", "macro", "meta"):
        unit = units[scale]
        stages.append({"object": scale + ":signal-muet", "scope_k": {"scale": scale, "boundary": "simulation:" + scale,
            "observer": "simulation:lecteur", "criteria_version": EXAMINATION_GRID_VERSION},
            "support_sha256": {"artifact_sha256": _sha(artifacts[scale]), "trace_refs": unit["evidence"]["source_refs"]},
            "dependencies": unit["work"]["depends_on"],
            "omissions_pi": {"declared_refs": unit["review"]["unknown_refs"], "situated": unit["review"]["unknown_details"]},
            "correction": {"status": PROPOSAL, "external_effect_applied": False,
                           "next_step": unit["continuity"]["next_step"]},
            "criterion_verdicts": criteria[scale], "scenario_verdict": "FAIL" if scale in {"meso", "macro"} else "UNKNOWN",
            "gabriel_verdict": unit["evidence"]["result"]["report"]["verdict"],
            "profile": examination_profile(scale), "artifact": artifacts[scale]})
    return {"simulation": True, "source_class": "reconstruction_analytique",
            "incident": "L'anomalie du signal muet", "grid_version": EXAMINATION_GRID_VERSION,
            "stages": stages, "executed_units": executed, "memory_reloads": len(executed),
            "independent_read_completed": units["micro-independent"]["continuity"]["state"] == "completed",
            "meta_objection_preserved": objection_preserved,
            "history_preserved": history_preserved, "ledger_kind": "local_sha256_hash_chain",
            "ledger_head": brain.ledger.head(), "checkpoint": brain.state["state_label"],
            "human_seal": False, "canonical_revision_applied": False, "execution_authority": False,
            "live_sensor_observed": False, "aws_drive_observed": False, "continuous_service_observed": False}


def main():
    parser = argparse.ArgumentParser(description="Run signal-muet in an isolated temporary memory")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    with tempfile.TemporaryDirectory(prefix="conscience-c-simulation-") as root:
        report = run_simulation(root)
    rendered = json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")


if __name__ == "__main__":
    main()
