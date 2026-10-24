"""Local hash-chained readback receipts. NOT externally attested/WORM."""
from __future__ import annotations
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
import fcntl
import json
import os

class IntegrityError(Exception):
    pass

def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")

def checksum(value: object) -> str:
    return sha256(canonical(value)).hexdigest()

def _check(content: bytes) -> dict:
    prior = "0" * 64
    seen = set()
    count = 0
    for line in content.splitlines():
        try:
            entry = json.loads(line)
            if set(entry) != {"sequence", "id", "observed_at", "input_sha256",
                              "decision", "previous_hash", "receipt_hash"}:
                raise ValueError("unexpected fields")
            digest = entry.pop("receipt_hash")
            if entry["sequence"] != count + 1 or entry["previous_hash"] != prior:
                raise ValueError("broken sequence or predecessor")
            if entry["id"] in seen:
                raise ValueError("duplicate id")
            if checksum(entry) != digest:
                raise ValueError("hash mismatch")
            seen.add(entry["id"])
            count += 1
            prior = digest
        except (ValueError, TypeError, KeyError, AttributeError) as exc:
            raise IntegrityError(f"invalid record {count + 1}: {exc}") from exc
    return {"valid": True, "count": count, "head_hash": prior,
            "external_attestation": False, "worm": False}

class LocalLedger:
    def __init__(self, filename: str | Path):
        self.path = Path(filename)

    def verify(self) -> dict:
        if not self.path.exists():
            return _check(b"")
        with self.path.open("rb") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_SH)
            try:
                return _check(stream.read())
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)

    def append(self, request: dict, decision: dict) -> dict:
        """POSIX advisory file lock + fsync. No secrets or raw payload retained."""
        # A caller cannot present a fabricated verdict as a valid gate decision.
        # This is local verification, not cryptographic authentication.
        from .gate import evaluate
        if not isinstance(request, dict) or not isinstance(decision, dict):
            raise IntegrityError("invalid ledger input")
        if decision != evaluate(request):
            raise IntegrityError("decision does not match deterministic gate")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a+b") as stream:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
            try:
                stream.seek(0)
                content = stream.read()
                snapshot = _check(content)
                if request["id"] in [
                    json.loads(line)["id"] for line in content.splitlines()
                ]:
                    raise IntegrityError("duplicate id; use the original receipt")
                if content and not content.endswith(b"\n"):
                    raise IntegrityError("truncated final record")
                entry = {
                    "sequence": snapshot["count"] + 1,
                    "id": request["id"],
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                    "input_sha256": checksum(request),
                    "decision": decision,
                    "previous_hash": snapshot["head_hash"],
                }
                entry["receipt_hash"] = checksum(entry)
                stream.seek(0, os.SEEK_END)
                stream.write(canonical(entry) + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
                return entry
            finally:
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
