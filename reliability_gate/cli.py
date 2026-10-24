"""Run: python -m reliability_gate.cli evaluate request.json --ledger receipts.jsonl"""
import argparse
import json
import sys
from .gate import evaluate
from .ledger import LocalLedger, IntegrityError

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Shadow-only fail-closed evidence gate")
    sub = parser.add_subparsers(dest="command", required=True)
    ev = sub.add_parser("evaluate")
    ev.add_argument("request")
    ev.add_argument("--ledger", help="append a local documentary receipt (NOT WORM)")
    chk = sub.add_parser("verify")
    chk.add_argument("ledger")
    args = parser.parse_args(argv)
    try:
        if args.command == "verify":
            result = LocalLedger(args.ledger).verify()
            print(json.dumps(result, ensure_ascii=False))
            return 0
        with open(args.request, encoding="utf-8") as file:
            request = json.load(file)
        verdict = evaluate(request)
        if args.ledger:
            if not isinstance(request, dict) or not isinstance(request.get("id"), str):
                print(json.dumps(verdict, ensure_ascii=False))
                return 2
            receipt = LocalLedger(args.ledger).append(request, verdict)
            verdict["receipt_hash"] = receipt["receipt_hash"]
        print(json.dumps(verdict, ensure_ascii=False))
        # No approval exit code. ADVISE is only a shadow observation.
        return 0 if verdict["verdict"] == "ADVISE" else 2
    except (OSError, ValueError, IntegrityError, TypeError) as exc:
        print(json.dumps({"verdict": "BLOCK", "reason": type(exc).__name__,
                          "production_effect": False}), file=sys.stderr)
        return 2

if __name__ == "__main__":
    sys.exit(main())
