from __future__ import annotations
import argparse
import json
from pathlib import Path

from .core import ConscienceCBrain
from .models import CausalOrigin, Evidence, EvidenceKind, Hypothesis

def main():
    p = argparse.ArgumentParser(prog="conscience-c-brain")
    p.add_argument("--root", default="./brain_state")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("status")
    sub.add_parser("audit")

    ep = sub.add_parser("evidence")
    ep.add_argument("id")
    ep.add_argument("content")
    ep.add_argument("--kind", choices=[k.value for k in EvidenceKind], default=EvidenceKind.ATTESTED_SOURCE.value)
    ep.add_argument("--confidence", type=float, default=1.0)

    hp = sub.add_parser("hypothesis")
    hp.add_argument("id")
    hp.add_argument("proposition")
    hp.add_argument("--falsifier", action="append", required=True)

    ip = sub.add_parser("imagine")
    ip.add_argument("title")
    ip.add_argument("--assumption", action="append", default=[])
    ip.add_argument("--consequence", action="append", default=[])

    rp = sub.add_parser("repair")
    rp.add_argument("--provenance", required=True)

    args = p.parse_args()
    b = ConscienceCBrain.load_or_bootstrap(Path(args.root))

    if args.cmd == "status":
        print(json.dumps(b.status(), ensure_ascii=False, indent=2))
    elif args.cmd == "audit":
        print(json.dumps(b.audit(), ensure_ascii=False, indent=2))
    elif args.cmd == "evidence":
        b.ingest_evidence(Evidence(args.id, args.content, EvidenceKind(args.kind), confidence=args.confidence), CausalOrigin.REALITY)
        print(json.dumps(b.status(), ensure_ascii=False, indent=2))
    elif args.cmd == "hypothesis":
        b.add_hypothesis(Hypothesis(args.id, args.proposition, 0.5, args.falsifier))
        print(json.dumps(b.status(), ensure_ascii=False, indent=2))
    elif args.cmd == "imagine":
        print(json.dumps(b.imagine(args.title, args.assumption, args.consequence), ensure_ascii=False, indent=2))
    elif args.cmd == "repair":
        print(json.dumps(b.repair_drift(args.provenance), ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
