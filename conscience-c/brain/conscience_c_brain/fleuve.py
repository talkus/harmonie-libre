"""Nahar Dinur (נְהַר דִּי־נוּר), le fleuve de feu, comme passage de purification de C(t).

Daniel 7,10 : « un fleuve de feu coulait et sortait de devant lui ». Le même feu
renouvelle les justes qui s'y baignent et consume ce qui corrompt ; des anges en
naissent et y retournent, renouvelés chaque matin.

Dans la mémoire de C, le fleuve est un passage, jamais un effacement :

- il commence par vérifier la chaîne du ledger (la Voie lactée : la trace est la
  lumière qu'il traverse, et il refuse de couler sur une histoire rompue) ;
- il examine chaque claim actif selon son intégrité. Un claim intègre est
  renouvelé ; un claim qui se tient seul est renouvelé mais signalé fragile ;
- un claim corrompu (contredit par une preuve, fondé sur une preuve réfutée, ou
  affirmé avec la confiance d'un fait sans aucun fait) voit son influence active
  consumée : le fleuve ouvre une teshuvah, le claim devient contested et sort
  des décisions sensibles. Le claim, ses faits et ses événements restent dans
  l'histoire. Ne jamais effacer, réduire l'influence ; et R-001 : le fleuve ne
  remplace ni ne retire rien lui-même, il ne fait que nommer l'écart (D) ;
- les engagements couronnés sont renouvelés à chaque passage ; ceux qui sont en
  garde attendent le retour vérifié et ne sont pas renouvelés ;
- aucun passage ne déclare C pur. Le fleuve coule : l'état final où l'erreur ne
  peut plus exister n'est pas un état que le système peut s'attribuer.
"""
from __future__ import annotations

import copy

from .models import CausalOrigin, EvidenceKind


_EVENT = "FLEUVE_PASSAGE"
# Confiance à partir de laquelle un claim sans aucun fait se présente comme un fait.
FACT_LIKE_CONFIDENCE = 0.8
_CONTRADICTING_KINDS = {EvidenceKind.ATTESTED_SOURCE.value, EvidenceKind.CONSOLIDATED_DERIVATION.value}
_IN_FIRE = {"contested", "under_repair"}


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


class FleuveMixin:
    def _fleuve_state(self):
        return self.state.setdefault("fleuve", {"passages": {}})

    def classify_replay_event(self, row):
        if row.get("event_type") == _EVENT:
            return "documentary_only"
        return super().classify_replay_event(row)

    def _ingest_hash(self, rows, evidence_id):
        for row in rows:
            if row["event_type"] == "INGEST_EVIDENCE" and row["payload"]["evidence"]["evidence_id"] == evidence_id:
                return row["event_hash"]
        return None

    def _corruption(self, claim, rows):
        """Ce qui corrompt un claim, avec la dérive qui le nomme et ses traces. Vide s'il est intègre."""
        evidence = self.state["E"]["evidence"]
        found = []
        contradicting = [e for e in evidence.values()
                         if e.get("claim_ref") == claim["claim_id"] and e.get("stance") == "contradicts"
                         and e["kind"] in _CONTRADICTING_KINDS]
        if contradicting:
            found.append({"drift_kind": "contradiction", "signal": "contradicted_by_evidence",
                          "evidence_ids": [e["evidence_id"] for e in contradicting]})
        refuted = [f for f in claim["facts"]
                   if f in evidence and evidence[f]["kind"] == EvidenceKind.HISTORICAL_REFUTED.value]
        if refuted:
            found.append({"drift_kind": "reality_mismatch", "signal": "rests_on_refuted_evidence",
                          "evidence_ids": refuted})
        if (not claim["facts"] and claim["provenance_kind"] != "user_stated"
                and (claim.get("confidence") or 0.0) >= FACT_LIKE_CONFIDENCE):
            found.append({"drift_kind": "provenance_failure", "signal": "fact_like_without_facts",
                          "evidence_ids": []})
        for item in found:
            item["drift_events"] = [h for h in (self._ingest_hash(rows, e) for e in item["evidence_ids"]) if h]
        return found

    def fleuve_examine(self):
        """Le pare-feu, sans écrire : le verdict que le prochain passage rendrait."""
        rows = self.ledger.read_verified()
        fragile = {v["claim_id"] for v in self.solitary_vessels()}
        verdicts = []
        for claim in self._teshuvah_state()["claims"].values():
            if claim["status"] in _IN_FIRE:
                verdicts.append({"claim_id": claim["claim_id"], "verdict": "in_fire",
                                 "open_teshuvah": self._open_cycles_for(claim["claim_id"])})
                continue
            if claim["status"] != "active":
                continue
            corruption = self._corruption(claim, rows)
            if corruption:
                verdicts.append({"claim_id": claim["claim_id"], "verdict": "consumed", "corruption": corruption})
            else:
                verdicts.append({"claim_id": claim["claim_id"],
                                 "verdict": "renewed_fragile" if claim["claim_id"] in fragile else "renewed"})
        commitments = self._teshuvah_state()["commitments"]
        return {
            "ledger": {"events": len(rows), "head": rows[-1]["event_hash"] if rows else "GENESIS",
                       "chain": "verified"},
            "claims": verdicts,
            "commitments": [{"commitment_id": cid, "verdict": "awaits_return" if rec["custody"] else "renewed"}
                            for cid, rec in commitments.items()],
        }

    def pass_through_fleuve(self, provenance):
        """Un passage du fleuve : renouvelle ce qui est intègre, consume l'influence de ce qui corrompt.

        Chaque claim consumé reçoit sa propre teshuvah (D seulement) ; la
        reconnaissance, la réparation et la vérification restent à faire par
        le cycle de teshuvah, avec un acteur et une preuve, jamais par le fleuve.
        """
        _text(provenance, "provenance")
        examined = self.fleuve_examine()
        passage_id = f"FL{len(self._fleuve_state()['passages']) + 1:04d}"
        source = f"fleuve:{passage_id}"
        for verdict in examined["claims"]:
            if verdict["verdict"] != "consumed":
                continue
            first = verdict["corruption"][0]
            signals = ", ".join(c["signal"] for c in verdict["corruption"])
            opened = self.initiate_teshuvah(
                first["drift_kind"], f"Le fleuve consume l'influence active de {verdict['claim_id']} : {signals}.",
                source, claim_ids=[verdict["claim_id"]],
                drift_events=sorted({h for c in verdict["corruption"] for h in c["drift_events"]}))
            verdict["teshuvah_id"] = opened["teshuvah_id"]
            verdict["influence"] = "consumed_in_sensitive_decisions; trace kept"
        renewed = [c["commitment_id"] for c in examined["commitments"] if c["verdict"] == "renewed"]
        for cid in renewed:
            self._teshuvah_state()["commitments"][cid].setdefault("renewals", []).append(passage_id)
        passage = {
            "passage_id": passage_id,
            "provenance": provenance,
            "ledger_before": examined["ledger"],
            "claims": examined["claims"],
            "commitments": examined["commitments"],
            "governance": self.governance_audit(),
            "error_free_claimed": False,
            "principle": "the river consumes active influence, never the archived trace; no passage declares C pure",
        }
        # Each teshuvah opened above adopted a fresh state: stage on the current one.
        self._fleuve_state()["passages"][passage_id] = passage
        result = copy.deepcopy(passage)
        event = self._transition(_EVENT, copy.deepcopy(passage), CausalOrigin.SELF)
        return {**result, "event_hash": event["event_hash"]}

    def fleuve_passages(self):
        return [copy.deepcopy(p) for p in self._fleuve_state()["passages"].values()]
