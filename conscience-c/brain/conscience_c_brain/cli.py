from __future__ import annotations
import argparse
import json
from pathlib import Path

from .core import ConscienceCBrain
from .models import CausalOrigin, Evidence, EvidenceKind, Hypothesis
from .multiscale_coherence import Scale

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

    gp = sub.add_parser("gabriel-examine", help="examine one recorded claim without changing it")
    gp.add_argument("claim_id")
    gp.add_argument("--scope", required=True)
    gp.add_argument("--observer", required=True)
    gp.add_argument("--subject")
    gp.add_argument("--scale", choices=[s.value for s in Scale], default="micro")
    gp.add_argument("--at-time")
    gp.add_argument("--record", action="store_true", help="append the diagnostic to the journal")
    gp.add_argument("--provenance")
    gp.add_argument("--reexamines")
    gp.add_argument("--revision-reason")
    sub.add_parser("gabriel-report").add_argument("report_ref")
    for command in ("gabriel-contest", "gabriel-correct", "gabriel-open-repair"):
        command_parser = sub.add_parser(command)
        command_parser.add_argument("report_ref")
        command_parser.add_argument("--actor", required=True)
        command_parser.add_argument("--provenance", required=True)
        if command != "gabriel-open-repair":
            command_parser.add_argument("--reason", required=True)
        if command == "gabriel-correct":
            command_parser.add_argument("--evidence-ref", action="append", required=True)

    args = p.parse_args()
    if args.cmd.startswith("gabriel-"):
        if not (Path(args.root) / "state.json").is_file():
            p.error("Gabriel requires an existing memory; refusing to bootstrap a new one")
        if args.cmd == "gabriel-examine" and args.record and not args.provenance:
            p.error("--record requires --provenance")
    b = ConscienceCBrain.load_or_bootstrap(Path(args.root))

    if args.cmd.startswith("gabriel-"):
        try:
            if args.cmd == "gabriel-examine":
                context = dict(scope_ref=args.scope, observer_ref=args.observer, subject_ref=args.subject,
                               scale=args.scale, at_time=args.at_time)
                if args.record:
                    result = b.record_gabriel_examination(args.claim_id, provenance=args.provenance,
                        reexamines=args.reexamines, revision_reason=args.revision_reason, **context)
                else:
                    result = b.gabriel_examine(args.claim_id, **context)
            elif args.cmd == "gabriel-report":
                result = b.gabriel_report(args.report_ref)
            elif args.cmd == "gabriel-open-repair":
                result = b.open_gabriel_repair(args.report_ref, requested_by=args.actor, provenance=args.provenance)
            else:
                context = dict(reason=args.reason, actor=args.actor, provenance=args.provenance)
                if args.cmd == "gabriel-correct":
                    result = b.correct_gabriel(args.report_ref, evidence_refs=args.evidence_ref, **context)
                else:
                    result = b.contest_gabriel(args.report_ref, **context)
        except ValueError as exc:
            p.error(str(exc))
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif args.cmd == "status":
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
