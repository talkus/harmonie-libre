from __future__ import annotations
import hashlib
import json
from pathlib import Path
from typing import Any, Dict, List

def _canon(obj: Dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def _hash(obj: Dict[str, Any]) -> str:
    return hashlib.sha256(_canon(obj).encode("utf-8")).hexdigest()

class AppendOnlyLedger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text("", encoding="utf-8")

    def read(self) -> List[Dict[str, Any]]:
        rows = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
        return rows

    def verify(self) -> None:
        prev = "GENESIS"
        expected_seq = 1
        for row in self.read():
            if row.get("seq") != expected_seq:
                raise ValueError(f"ledger sequence broken at {expected_seq}")
            if row.get("prev_hash") != prev:
                raise ValueError(f"ledger prev_hash broken at {expected_seq}")
            body = {k: v for k, v in row.items() if k != "event_hash"}
            if row.get("event_hash") != _hash(body):
                raise ValueError(f"ledger hash broken at {expected_seq}")
            prev = row["event_hash"]
            expected_seq += 1

    def head(self) -> str:
        rows = self.read()
        return rows[-1]["event_hash"] if rows else "GENESIS"

    def append(self, event_type: str, timestamp: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.verify()
        rows = self.read()
        row = {
            "seq": len(rows) + 1,
            "timestamp": timestamp,
            "event_type": event_type,
            "payload": payload,
            "prev_hash": rows[-1]["event_hash"] if rows else "GENESIS",
        }
        row["event_hash"] = _hash(row)
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
        return row
