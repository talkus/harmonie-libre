"""Sol v0.5: API de scrutin stateless et sans effets externes."""
from __future__ import annotations

import hashlib
import json
import math
import os
import sys
from http.server import BaseHTTPRequestHandler

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from sol_parite_equidistance_globale_candidate_v05 import (
    SolMicrokernelGlobalParityV05Candidate,
    State,
    Episode,
)

VERSION = "0.5"
SHA256 = "044fb876a4f135b001b17b7d876181714dbd39caced93d1e2f9a28a69a3f1024"
MAX_BODY = 24576
MAX_EPISODES = 64
MAX_DIMENSIONS = 16


def _fail(message):
    raise ValueError(message)


def evaluate(payload):
    if not isinstance(payload, dict):
        _fail("Corps JSON: objet requis")
    pairs = payload.get("poles", [])
    if not (isinstance(pairs, list) and len(pairs) == 2
            and all(isinstance(p, str) and 0 < len(p) <= 64 and "|" not in p for p in pairs)
            and pairs[0] != pairs[1]):
        _fail("poles: deux identifiants distincts sont requis")
    raw = payload.get("episodes", [])
    if not (isinstance(raw, list) and 2 <= len(raw) <= MAX_EPISODES):
        _fail("episodes: entre 2 et 64 observations")
    entries = []
    dims = None
    for e in raw:
        if not isinstance(e, dict):
            _fail("Chaque episode doit etre un objet")
        p = e.get("provenance")
        v = e.get("observation")
        if not isinstance(p, str) or not 0 < len(p) <= 64 or "|" in p:
            _fail("provenance invalide")
        if not isinstance(v, list) or not 1 <= len(v) <= MAX_DIMENSIONS:
            _fail("observation invalide")
        if dims is None:
            dims = len(v)
        if len(v) != dims:
            _fail("Toutes les observations doivent avoir la meme dimension")
        if any(type(x) not in (int, float) or not math.isfinite(x) or abs(x) > 1e6 for x in v):
            _fail("Coordonnees non finies ou hors limites")
        rel = e.get("reliability", 1.0)
        unr = e.get("unresolved", 1.0)
        if (type(rel) not in (int, float) or not math.isfinite(rel) or not 0 <= rel <= 1
            or type(unr) not in (int, float) or not math.isfinite(unr) or not 0 <= unr <= 1):
            _fail("reliability et unresolved doivent etre dans [0,1]")
        entries.append(Episode(list(map(float, v)), float(rel), p, float(unr)))
    if not all(any(e.provenance == p for e in entries) for p in pairs):
        _fail("Chaque pole doit avoir au moins une observation")
    state = State(
        belief=[0.0] * dims, uncertainty=[0.5] * dims,
        self_model=[0.5] + [0.0] * (dims - 1),
        other_model=[-0.5] + [0.0] * (dims - 1),
        relation=[0.0] * dims, questions=[], cycle=0,
    )
    kernel = SolMicrokernelGlobalParityV05Candidate(state, entries)
    poles = kernel._pole_episodes("reconcile:" + "|".join(pairs))
    if poles is None:
        _fail("Pôles introuvables")
    votes = kernel._count_votes(poles)
    votes = {p: sorted(votes[p]) for p in pairs}
    counts = {p: len(votes[p]) for p in pairs}
    return {
        "version": VERSION,
        "model": "sol.strat3.global-parity.v0.5",
        "mode": "stateless_voting_only",
        "poles": pairs,
        "votes_by_provenance": votes,
        "counts": counts,
        "parity": counts[pairs[0]] == counts[pairs[1]],
        "abstaining_divided_provenances": kernel._divided_last,
        "independent_external_actions": False,
        "note": "Simulation stateless; les identites de provenance ne sont pas authentifiees.",
    }


class handler(BaseHTTPRequestHandler):
    def _send(self, status, payload):
        body = json.dumps(payload, ensure_ascii=False, allow_nan=False, sort_keys=True).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        digest = hashlib.sha256(open(os.path.join(ROOT, "sol_parite_equidistance_globale_candidate_v05.py"), "rb").read()).hexdigest()
        if digest != SHA256:
            self._send(503, {"status": "integrity_mismatch"})
            return
        self._send(200, {
            "status": "ready", "version": VERSION, "sha256": digest,
            "mode": "stateless_voting_only", "storage": "none",
            "external_actions": False, "endpoints": {"GET": "/api", "POST": "/api"},
        })

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            if size < 0 or size > MAX_BODY:
                self._send(413, {"error": "corps absent ou superieur a 24 KiB"})
                return
            incoming = json.loads(self.rfile.read(size))
            result = evaluate(incoming)
            self._send(200, result)
        except (ValueError, TypeError, KeyError) as exc:
            self._send(400, {"error": str(exc)[:200]})
        except Exception:
            self._send(500, {"error": "evaluation_failed"})
