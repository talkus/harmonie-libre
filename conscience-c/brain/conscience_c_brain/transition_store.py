"""Recoverable local journal/snapshot commits, not a distributed transaction.

Supported: cooperating POSIX writers on one local filesystem. A durable intent
contains the exact target snapshot BEFORE append. Recovery only publishes that
snapshot if the exact prepared row is already the verified journal tail. It
never re-executes a business operation, truncates a journal, or invents history.
The hashes detect inconsistency; they are NOT independent authentication.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

from .ledger import AppendOnlyLedger, _hash


class RecoveryRequired(ValueError):
    """Preserve the files for explicit investigation; do not guess a repair."""


class StaleWriter(ValueError):
    """Reload: another cooperating writer committed since this snapshot was read."""


def snapshot_bytes(state):
    return json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True,
                      allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest() if data is not None else None


def _strict_json(data):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON field")
            result[key] = value
        return result
    def bad_constant(value):
        raise ValueError("non-finite JSON number")
    return json.loads(data, object_pairs_hook=pairs, parse_constant=bad_constant)


def _sync_directory(path):
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def atomic_write(path, data):
    """Flush a temporary sibling, replace one file atomically, then sync its dir."""
    fd, name = tempfile.mkstemp(prefix=".transition-tmp-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
        _sync_directory(path.parent)
    finally:
        if os.path.exists(name):
            os.unlink(name)


class TransitionStore:
    INTENT_FIELDS = frozenset({"format", "transaction_id", "before_snapshot_hash",
        "before_head", "before_count", "event", "after_snapshot",
        "after_snapshot_hash", "intent_hash"})

    def __init__(self, root):
        self.root = Path(root)
        self.state_path = self.root / "state.json"
        self.journal_path = self.root / "events.jsonl"
        self.pending_path = self.root / "transition.pending.json"
        self.receipts_path = self.root / "transition-receipts"
        self.last_recovery = "none"

    @contextmanager
    def _locked(self):
        try:
            import fcntl
        except ImportError as exc:
            raise RecoveryRequired("coordinated storage currently requires POSIX flock") from exc
        self.root.mkdir(parents=True, exist_ok=True)
        with (self.root / ".transition.lock").open("a+b") as lock:
            try:
                fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise StaleWriter("another storage operation holds the lock") from exc
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _stage(self, name):
        """No-op boundary overridden in fault-injection tests; no production hook."""

    def _snapshot(self):
        return self.state_path.read_bytes() if self.state_path.exists() else None

    def _rows(self):
        try:
            rows = AppendOnlyLedger(self.journal_path, create=False).read_verified()
            # A torn final append is NOT silently completed or truncated.
            raw = self.journal_path.read_bytes()
            if raw and not raw.endswith(b"\n"):
                raise ValueError("incomplete journal line")
            for index, row in enumerate(rows):
                if index == 0:
                    if row["event_type"] != "BOOTSTRAP_T0":
                        raise ValueError("missing bootstrap boundary")
                elif (type(row["payload"].get("n")) is not int
                      or row["payload"]["n"] != index
                      or row["event_type"] == "BOOTSTRAP_T0"):
                    raise ValueError("invalid transition count")
            return rows
        except (ValueError, OSError, TypeError, KeyError, UnicodeError) as exc:
            raise RecoveryRequired("journal requires explicit recovery: " + str(exc)) from exc

    @staticmethod
    def _check_snapshot(state, rows):
        n = state.get("n")
        if (not rows or type(n) is not int or n != len(rows) - 1
                or state.get("state_label") != f"C(t_{n})"
                or state.get("last_event_hash") != rows[-1]["event_hash"]):
            raise RecoveryRequired("snapshot/ledger boundary mismatch")

    def load(self):
        """Load or recover to a recorded boundary; return None only for a new root."""
        with self._locked():
            self.last_recovery = "none"
            if self.pending_path.exists():
                self._recover()
            data = self._snapshot()
            if not self.journal_path.exists():
                if data is not None or self._has_commits():
                    raise RecoveryRequired("journal missing; refusing to recreate t0")
                return None
            rows = self._rows()
            if data is None:
                if rows or self._has_commits():
                    raise RecoveryRequired("snapshot missing without usable intent")
                return None
            try:
                state = _strict_json(data)
                self._check_snapshot(state, rows)
            except (ValueError, TypeError, AttributeError) as exc:
                raise RecoveryRequired("snapshot requires explicit recovery: " + str(exc)) from exc
            return state, digest(data)

    def _has_commits(self):
        return self.receipts_path.exists() and any(self.receipts_path.glob("*.committed.json"))

    def commit(self, state, event_type, timestamp, payload, expected_token, expected_head):
        """Compare-and-swap snapshot, prepare, append, publish, finalize."""
        with self._locked():
            if self.pending_path.exists():
                raise RecoveryRequired("unfinished transition; reload before any new write")
            before = self._snapshot()
            if digest(before) != expected_token:
                raise StaleWriter("snapshot changed; reload before committing")
            if not self.journal_path.exists():
                if before is not None or expected_head != "GENESIS" or self._has_commits():
                    raise RecoveryRequired("journal missing; no automatic reinitialization")
                atomic_write(self.journal_path, b"")
            rows = self._rows()
            head = rows[-1]["event_hash"] if rows else "GENESIS"
            if head != expected_head:
                raise StaleWriter("journal advanced; reload before committing")
            if before is not None:
                self._check_snapshot(_strict_json(before), rows)
            elif rows or self._has_commits():
                raise RecoveryRequired("missing snapshot is not a new t0")
            if not isinstance(payload, dict) or not isinstance(event_type, str) or not event_type:
                raise ValueError("invalid transition payload/type")
            if ((not rows and event_type != "BOOTSTRAP_T0")
                    or (rows and event_type == "BOOTSTRAP_T0")):
                raise RecoveryRequired("bootstrap may only initialize an empty history")
            if rows and (type(payload.get("n")) is not int or payload["n"] != len(rows)):
                raise RecoveryRequired("proposed transition count mismatch")
            txid = uuid.uuid4().hex
            event = {"seq": len(rows) + 1, "event_type": event_type,
                     "timestamp": timestamp, "payload": copy.deepcopy(payload),
                     "prev_hash": head, "transaction_id": txid}
            # Keep the historical journal hash algorithm; do not rehash old rows.
            event["event_hash"] = _hash(event)
            after = copy.deepcopy(state)
            after["last_event_hash"] = event["event_hash"]
            self._check_snapshot(after, rows + [event])
            encoded = snapshot_bytes(after)
            intent = {"format": "C-TRANSITION-1", "transaction_id": txid,
                      "before_snapshot_hash": digest(before), "before_head": head,
                      "before_count": len(rows), "event": event,
                      "after_snapshot": after, "after_snapshot_hash": digest(encoded)}
            intent["intent_hash"] = _hash(intent)
            self._stage("before_prepare")
            atomic_write(self.pending_path, snapshot_bytes(intent))
            self._stage("after_prepare")
            with self.journal_path.open("ab") as stream:
                stream.write(json.dumps(event, ensure_ascii=False, sort_keys=True,
                                        allow_nan=False).encode("utf-8") + b"\n")
                stream.flush()
                os.fsync(stream.fileno())
            self._stage("after_append")
            atomic_write(self.state_path, encoded)
            self._stage("after_snapshot")
            self._finish(intent, "committed")
            return copy.deepcopy(after), digest(encoded), copy.deepcopy(event)

    def _finish(self, intent, outcome):
        self.receipts_path.mkdir(exist_ok=True)
        _sync_directory(self.root)
        receipt = {"format": "C-TRANSITION-RECEIPT-1", "outcome": outcome,
                   "transaction_id": intent["transaction_id"],
                   "intent_hash": intent["intent_hash"],
                   "before_head": intent["before_head"],
                   "event_hash": intent["event"]["event_hash"],
                   "after_snapshot_hash": intent["after_snapshot_hash"]}
        if outcome == "aborted":
            receipt["uncommitted_intent"] = intent
        target = self.receipts_path / (intent["transaction_id"] + "." + outcome + ".json")
        data = snapshot_bytes(receipt)
        if target.exists():
            if target.read_bytes() != data:
                raise RecoveryRequired("conflicting transaction receipt")
        else:
            atomic_write(target, data)
        self._stage("after_receipt")
        self.pending_path.unlink()
        _sync_directory(self.root)

    def _recover(self):
        try:
            intent = _strict_json(self.pending_path.read_bytes())
            if not isinstance(intent, dict) or set(intent) != self.INTENT_FIELDS:
                raise ValueError("invalid intent schema")
            if intent["format"] != "C-TRANSITION-1":
                raise ValueError("unknown intent version")
            txid = intent["transaction_id"]
            if (not isinstance(txid, str) or len(txid) != 32
                    or any(c not in "0123456789abcdef" for c in txid)):
                raise ValueError("invalid transaction id")
            if intent["intent_hash"] != _hash({k: v for k, v in intent.items() if k != "intent_hash"}):
                raise ValueError("intent hash mismatch")
            count = intent["before_count"]
            if type(count) is not int or count < 0:
                raise ValueError("invalid intent boundary")
            event = intent["event"]
            if (event["seq"] != count + 1 or type(event["seq"]) is not int
                    or event.get("transaction_id") != txid
                    or event["prev_hash"] != intent["before_head"]
                    or event["event_hash"] != _hash({k: v for k, v in event.items() if k != "event_hash"})):
                raise ValueError("invalid prepared event")
            encoded = snapshot_bytes(intent["after_snapshot"])
            if intent["after_snapshot_hash"] != digest(encoded):
                raise ValueError("prepared snapshot hash mismatch")
            rows = self._rows()
            if len(rows) not in {count, count + 1}:
                raise ValueError("journal not at a prepared boundary")
            prefix_head = rows[count - 1]["event_hash"] if count else "GENESIS"
            if prefix_head != intent["before_head"]:
                raise ValueError("prepared prefix differs from journal")
            self._check_snapshot(intent["after_snapshot"], rows[:count] + [event])
            before_match = digest(self._snapshot()) == intent["before_snapshot_hash"]
            after_match = self._snapshot() == encoded
            if len(rows) == count:
                if not before_match:
                    raise ValueError("snapshot advanced without recorded event")
                self._finish(intent, "aborted")
                self.last_recovery = "aborted_before_append"
                return
            if snapshot_bytes(rows[-1]) != snapshot_bytes(event):
                raise ValueError("journal tail differs from prepared event")
            if not before_match and not after_match:
                raise ValueError("snapshot differs from both recorded boundaries")
            if not after_match:
                atomic_write(self.state_path, encoded)
            self._finish(intent, "committed")
            self.last_recovery = "completed_interrupted_commit"
        except (ValueError, OSError, TypeError, KeyError, AttributeError) as exc:
            raise RecoveryRequired("pending transition needs explicit recovery: " + str(exc)) from exc
