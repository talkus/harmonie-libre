#!/usr/bin/env python3
"""Vérifie le contrat de synchronisation Empire contre les CSV canoniques, sans modèle externe."""
import hashlib
import json
from pathlib import Path
from valider import verifier, charger

ROOT = Path(__file__).resolve().parent
ALLOWED = ("axes.csv", "portes.csv", "transitions.csv")
CYCLES = ("I", "II", "III", "IV", "V", "VI")

def valider_synchronisation():
    contract = json.loads((ROOT / "empire-sync-v1.1.1.json").read_text(encoding="utf-8"))
    canonical = json.loads((ROOT / "empreintes.json").read_text(encoding="utf-8"))
    assert contract["version"] == canonical["version"] == "1.1.1"
    assert contract["source_of_truth"] == canonical["source_of_truth"] == list(ALLOWED)
    assert set(contract["files"]) == set(canonical["files"]) == set(ALLOWED)
    assert contract["roles"]["codex"] == "sole_repository_writer"
    assert contract["export_policy"]["external_model_call_completed"] is False
    assert contract["manual"]["role"] == "GRAMMAR"
    assert contract["manual"]["text_supplied_in_this_change"] is False
    for filename in ALLOWED:
        actual = (ROOT / filename).read_bytes()
        record = contract["files"][filename]
        assert record == canonical["files"][filename], f"Contrat discordant pour {filename}"
        assert len(actual) == record["bytes"], f"Taille discordante : {filename}"
        assert hashlib.sha256(actual).hexdigest() == record["sha256"], f"SHA256 discordant : {filename}"

    result = verifier()
    for field in ("portes", "transitions", "familles", "pivots", "axes"):
        assert result[field] == contract["expected"][field], f"Compte discordant : {field}"

    doors = charger("portes.csv")
    changes = contract["corrections"]["E5"]
    by_id = {int(d["n"]): d for d in doors}
    for name, spec in (("Argile", changes["argile"]), ("Sable", changes["sable"])):
        row = by_id[spec["n"]]
        assert row["nom"] == name and int(row["position_chemin"]) == spec["position_chemin"]
        assert row["cycle"] == spec["cycle"]
    assert changes["boundary_transition"] == "T24"
    assert contract["corrections"]["T12"] == {"arrives": "Miroir", "cycle": "II"}
    assert contract["corrections"]["T60"] == {"arrives": "Porte", "cycle": "VI"}
    assert len(contract["reserved_v2_0"]) == 2
    assert all(entry["status"] == "NOT_APPLIED" for entry in contract["reserved_v2_0"])
    assert by_id[53]["famille"] == "F13"
    assert result["cycles"] == contract["expected"]["cycles"]
    transitions = charger("transitions.csv")
    counts = {cycle: sum(t["cycle"] == cycle for t in transitions) for cycle in CYCLES}
    assert counts == contract["expected"]["transitions_by_cycle"]
    return {
        "status": "PASS",
        "canonical_csv_unchanged": True,
        "verified_lexicon": {"axes": 9, "portes": 72, "transitions": 71},
        "cycles": counts,
        "errata_E5": "Argile II (24) → Sable III (25)",
        "empire_packet": "READY_NOT_DISPATCHED",
        "v2_0_proposals": "UNAPPLIED"
    }

if __name__ == "__main__":
    print(json.dumps(valider_synchronisation(), ensure_ascii=False))
