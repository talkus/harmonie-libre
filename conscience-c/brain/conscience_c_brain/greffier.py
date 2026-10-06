"""Le greffier : Nemotron (par Amazon Bedrock) tient le greffe du ledger de C.

Le motif de Metatron, repris dans les échanges de mik, est celui d'un scribe :
assembler une trajectoire, présenter les faits, permettre l'examen, avec accès à
l'histoire brute. Le greffier ne juge pas et ne certifie pas.

Partage des rôles, pour que la réparation ne soit jamais auto-certifiée :

- le code vérifie la chaîne du ledger (séquence, prev_hash, SHA-256). Sur une
  histoire rompue, le greffier refuse de siéger et n'appelle aucun modèle ;
- le code assemble le dossier : les événements bruts, avec leur seq et leur hash ;
- Nemotron rédige l'acte : il présente ce que montrent les événements, en citant
  leur seq, et dit ce qui manque. Son texte reste une reconstruction analytique ;
- le code relit l'acte : toute seq citée qui n'existe pas dans le dossier est
  nommée dans l'acte enregistré (citations_inconnues). Rien n'est retiré du texte ;
- l'acte est ajouté à greffe.jsonl, un registre chaîné distinct d'events.jsonl.
  Le greffier n'écrit jamais dans l'histoire de C : ne jamais effacer, et ne
  rien ajouter à la trace qu'il examine.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .ledger import AppendOnlyLedger, _canon


MODEL_ID = "nvidia.nemotron-super-3-120b"
# Nemotron 3 Super n'est pas offert en ca-central-1 ; us-east-1 l'est (fiche Bedrock du modèle).
REGION = "us-east-1"
EVENT = "ACTE_DE_GREFFE"
STATUT = "reconstruction_analytique"
PAYLOAD_LIMIT = 600
MAX_TOKENS = 1500

CONSIGNE = """Tu es le greffier de Conscience C. Tu tiens le greffe, tu ne juges pas.
La chaîne du ledger a déjà été vérifiée par le code (SHA-256) : ne prétends pas la vérifier toi-même.
Rédige en français l'acte de greffe du dossier ci-dessous :
1. Ce que montrent les événements, dans l'ordre, chacun cité par sa seq sous la forme #N.
2. Les réparations, contestations ou dérives présentes, avec leur seq.
3. Ce que le dossier ne permet pas d'établir.
N'invente aucun événement, aucune seq, aucune intention. Ne déclare rien réparé, vrai ou validé :
la décision appartient à l'humain. Si une chose n'est pas dans le dossier, dis qu'elle n'y est pas."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def verify_chain(root: Path) -> List[Dict[str, Any]]:
    """Les événements vérifiés d'events.jsonl ; lève ValueError si la chaîne est rompue ou absente."""
    path = Path(root) / "events.jsonl"
    if not path.exists():
        raise ValueError(f"aucun ledger à {path}")
    return AppendOnlyLedger(path, create=False).read_verified()


def build_dossier(rows: List[Dict[str, Any]], since_seq: int = 1) -> Dict[str, Any]:
    events = []
    for row in rows:
        if row["seq"] < since_seq:
            continue
        payload = _canon(row["payload"])
        events.append({
            "seq": row["seq"],
            "timestamp": row["timestamp"],
            "event_type": row["event_type"],
            "event_hash": row["event_hash"],
            "payload": payload[:PAYLOAD_LIMIT],
            "payload_tronque": len(payload) > PAYLOAD_LIMIT,
        })
    if not events:
        raise ValueError(f"aucun événement à partir de la seq {since_seq}")
    return {
        "ledger_head": rows[-1]["event_hash"],
        "ledger_length": len(rows),
        "seq_range": [events[0]["seq"], events[-1]["seq"]],
        "chaine": "verifiee_par_le_code_sha256",
        "events": events,
    }


def build_prompt(dossier: Dict[str, Any]) -> str:
    return CONSIGNE + "\n\nDOSSIER :\n" + json.dumps(dossier, ensure_ascii=False, indent=1)


def unknown_citations(acte: str, dossier: Dict[str, Any]) -> List[int]:
    known = {e["seq"] for e in dossier["events"]}
    cited = {int(n) for n in re.findall(r"#(\d+)", acte)}
    return sorted(cited - known)


def bedrock_client(region: str = REGION):
    import boto3  # présent dans CloudShell ; importé tard pour que le reste vive sans lui
    return boto3.client("bedrock-runtime", region_name=region)


def ask_nemotron(prompt: str, client, model_id: str = MODEL_ID) -> Dict[str, Any]:
    resp = client.converse(
        modelId=model_id,
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"maxTokens": MAX_TOKENS, "temperature": 0.2},
    )
    parts = resp["output"]["message"]["content"]
    text = "".join(p.get("text", "") for p in parts).strip()
    if not text:
        raise ValueError("Nemotron n'a rendu aucun texte")
    return {"text": text, "usage": resp.get("usage", {}), "stop_reason": resp.get("stopReason")}


def tenir_greffe(root: Path, client=None, *, since_seq: int = 1, model_id: str = MODEL_ID,
                 region: str = REGION) -> Dict[str, Any]:
    root = Path(root)
    rows = verify_chain(root)  # histoire rompue : refus avant tout appel
    dossier = build_dossier(rows, since_seq)
    prompt = build_prompt(dossier)
    answer = ask_nemotron(prompt, client or bedrock_client(region), model_id)
    payload = {
        "greffier": {"model_id": model_id, "region": region, "service": "amazon-bedrock-converse"},
        "ledger_head": dossier["ledger_head"],
        "seq_range": dossier["seq_range"],
        "chaine": dossier["chaine"],
        "prompt_sha256": _sha(prompt),
        "acte": answer["text"],
        "acte_sha256": _sha(answer["text"]),
        "usage": answer["usage"],
        "stop_reason": answer["stop_reason"],
        "citations_inconnues": unknown_citations(answer["text"], dossier),
        "statut": STATUT,
        "certifie": False,
        "decision": "appartient_a_l_humain",
    }
    return AppendOnlyLedger(root / "greffe.jsonl").append(EVENT, _now(), payload)


def main(argv: Optional[List[str]] = None) -> int:
    p = argparse.ArgumentParser(prog="conscience-c-greffier")
    p.add_argument("--root", default="./brain_state")
    p.add_argument("--depuis", type=int, default=1, help="première seq du dossier")
    p.add_argument("--region", default=REGION)
    p.add_argument("--model", default=MODEL_ID)
    p.add_argument("--dry-run", action="store_true", help="affiche le dossier sans appeler Nemotron")
    args = p.parse_args(argv)
    try:
        if args.dry_run:
            print(build_prompt(build_dossier(verify_chain(Path(args.root)), args.depuis)))
            return 0
        row = tenir_greffe(Path(args.root), since_seq=args.depuis, model_id=args.model, region=args.region)
    except ValueError as e:
        print(f"Le greffier ne siège pas : {e}", file=sys.stderr)
        return 2
    print(row["payload"]["acte"])
    print(f"\n-- acte #{row['seq']} ajouté à greffe.jsonl ; hash {row['event_hash']}")
    if row["payload"]["citations_inconnues"]:
        print(f"-- seq citées absentes du dossier : {row['payload']['citations_inconnues']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
