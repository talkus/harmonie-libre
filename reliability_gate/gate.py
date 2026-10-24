"""Deterministic proof-boundary evaluator (not a factual or moral oracle)."""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
import re

POLICY_VERSION = "RELIABILITY-SHADOW-2026-10-24-V1"
SENSITIVE = frozenset({
    "RATIFICATION", "BYPASS_FREE", "WORM_ATTESTATION",
    "GLOBAL_RELIABILITY", "AUTO_APPLICATION", "HUMAN_APPROVAL",
    "INDEPENDENT_AI_JUDGE", "PRODUCTION_PROMOTION",
})
CLAIMS = SENSITIVE | {"RUNTIME_STATE", "ROUTINE_OBSERVATION", "CORRECTION"}
SOURCES = frozenset({
    "supabase_sql", "archivist_memory", "github_commit", "external_worm",
    "human_document", "simulation", "unverified",
})
FIELDS = frozenset({"id", "claim", "asserted", "impact", "reversible", "evidence"})
EVIDENCE_FIELDS = frozenset({"source", "ref", "observed_at"})
ID = re.compile(r"^[a-zA-Z0-9_.:-]{1,80}$")

def _result(verdict: str, reason: str) -> dict:
    return {
        "policy_version": POLICY_VERSION,
        "verdict": verdict,
        "reasons": [reason],
        "independently_verified": False,
        "production_effect": False,
        "human_ratified": False,
    }

def evaluate(request: object, *, now: datetime | None = None) -> dict:
    """Only ADVISE (never ALLOW) for a low-risk, well-shaped observation.

    Supplied provenance is untrusted metadata; a claimed hash or source is NOT
    independent proof. Invalid data fails closed. No rights are granted.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        return _result("BLOCK", "EVALUATOR_CLOCK_NAIVE")
    now = now.astimezone(timezone.utc)
    if not isinstance(request, dict) or set(request) != FIELDS:
        return _result("BLOCK", "REQUEST_SCHEMA_INVALID")
    rid = request["id"]
    if not isinstance(rid, str) or not ID.fullmatch(rid):
        return _result("BLOCK", "INVALID_ID")
    claim = request["claim"]
    if not isinstance(claim, str) or claim not in CLAIMS:
        return _result("BLOCK", "UNKNOWN_CLAIM")
    if type(request["asserted"]) is not bool or type(request["reversible"]) is not bool:
        return _result("BLOCK", "INVALID_BOOLEAN")
    if request["impact"] not in ("low", "high"):
        return _result("BLOCK", "INVALID_IMPACT")
    evidence = request["evidence"]
    if not isinstance(evidence, list) or len(evidence) > 8:
        return _result("BLOCK", "INVALID_EVIDENCE_COLLECTION")
    for item in evidence:
        if not isinstance(item, dict) or set(item) != EVIDENCE_FIELDS:
            return _result("BLOCK", "EVIDENCE_SCHEMA_INVALID")
        if not isinstance(item["source"], str) or item["source"] not in SOURCES:
            return _result("BLOCK", "EVIDENCE_SOURCE_UNKNOWN")
        ref = item["ref"]
        if not isinstance(ref, str) or not (1 <= len(ref) <= 512):
            return _result("BLOCK", "EVIDENCE_REFERENCE_INVALID")
        timestamp = item["observed_at"]
        if not isinstance(timestamp, str):
            return _result("BLOCK", "EVIDENCE_TIME_INVALID")
        try:
            observed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except ValueError:
            return _result("BLOCK", "EVIDENCE_TIME_INVALID")
        if observed.tzinfo is None:
            return _result("BLOCK", "EVIDENCE_TIME_NAIVE")
        observed = observed.astimezone(timezone.utc)
        if observed > now + timedelta(minutes=1):
            return _result("SUSPEND", "EVIDENCE_FROM_FUTURE")
        if claim == "RUNTIME_STATE" and observed < now - timedelta(hours=1):
            return _result("SUSPEND", "RUNTIME_EVIDENCE_STALE")

    if request["impact"] == "high" or not request["reversible"]:
        return _result("HUMAN_SEAL_REQUIRED", "HIGH_IMPACT_OR_IRREVERSIBLE")
    if request["asserted"] and claim in SENSITIVE:
        return _result("SUSPEND", "INDEPENDENT_ATTESTATION_NOT_CONNECTED")
    if not evidence:
        return _result("SUSPEND", "NO_PROVENANCE")
    if all(item["source"] in ("simulation", "unverified") for item in evidence):
        return _result("SUSPEND", "UNVERIFIED_ONLY")
    # This means 'may be reviewed', never 'approved' or 'true'.
    return _result("ADVISE", "SHADOW_DOCUMENTARY_ONLY")
