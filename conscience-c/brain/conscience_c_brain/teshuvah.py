"""Teshuvah (תְּשׁוּבָה) : retour et réponse, comme cycle de correction traçable.

La teshuvah n'est pas un événement terminal qui affirme que la réparation est
accomplie. C'est la relation causale entre des événements immuables :

    D (dérive) -> R (reconnaissance) -> A (aveu) -> P (réparation proposée)
    -> C (correction appliquée) -> S (garde-fou) -> V (vérification)

et V != auto-déclaration : la vérification doit reposer sur un nouvel état
observable, enregistré après le retour, et ne peut pas venir de l'acteur qui a
reconnu l'écart.

Trois couches restent séparées :
- FACT : ce qui s'est passé (preuves, événements du ledger) ; jamais modifié ici ;
- INTERPRETATION : ce que le système en avait conclu (un claim) ;
- CURRENT_MODEL : ce que le système comprend maintenant (claim actif).

L'histoire reste immuable. L'interprétation active reste corrigeable. La
réparation doit devenir observable. Le retour doit pouvoir être vérifié. La
mémoire conserve aussi le chemin du retour.

Shevirat ha-kelim (שְׁבִירַת הַכֵּלִים), la brisure des vases : un claim qui se
brise ne devient pas simplement faux. Ses étincelles (ce qui restait vrai en
lui) sont nommées, puis chacune est relevée dans la compréhension nouvelle ou
explicitement laissée, avec sa raison. Aucune correction ne jette une étincelle
en silence. Les vases qui se tiennent seuls (un seul appui, partagé avec aucun
autre claim, sans parole de l'autre) sont signalés comme fragiles avant de se
briser.
"""
from __future__ import annotations

import copy

from .models import CausalOrigin, EvidenceKind


CLAIM_PROVENANCE = ("user_stated", "user_inferred", "system_hypothesis")
CLAIM_STATUSES = ("active", "contested", "under_repair", "superseded", "retracted", "archived")

# Cycle de vie d'un cycle de teshuvah. repair_applied (« réparation déclarée »)
# et repair_verified (« retour observé et vérifié ») ne sont pas la même chose.
PHASES = ("contested", "under_repair", "repair_applied", "repair_verified", "cicatrized", "archived")

# Influence décisionnelle résiduelle de la dérive selon la phase. Valeurs
# expérimentales (reconstruction analytique, « mémoire pondérée ») : ne jamais
# effacer, réduire l'influence.
DRIFT_INFLUENCE = {
    "contested": 1.0,
    "under_repair": 1.0,
    "repair_applied": 0.5,
    "repair_verified": 0.25,
    "cicatrized": 0.1,
    "archived": 0.01,
}

_EVENT_TYPES = {
    "RECORD_CLAIM": "documentary_only",
    "TESHUVAH_INITIATED": "documentary_only",
    "TESHUVAH_SPARKS_NAMED": "documentary_only",
    "TESHUVAH_ACKNOWLEDGED": "documentary_only",
    "TESHUVAH_REPAIR_PROPOSED": "documentary_only",
    "TESHUVAH_REPAIR_APPLIED": "requires_current_canon_check",
    "TESHUVAH_SAFEGUARD_CREATED": "documentary_only",
    "TESHUVAH_RETURN_OBSERVED": "requires_external_reverification",
    "TESHUVAH_NON_RECURRENCE_VERIFIED": "requires_external_reverification",
    "TESHUVAH_RECURRENCE_DETECTED": "requires_external_reverification",
    "TESHUVAH_CICATRIZED": "documentary_only",
    "TESHUVAH_ARCHIVED": "documentary_only",
    "TESHUVAH_CLOSED": "documentary_only",
}

_OBSERVABLE_KINDS = {EvidenceKind.ATTESTED_SOURCE.value, EvidenceKind.CONSOLIDATED_DERIVATION.value}


def _text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} must be a nonblank string")
    return value


def _texts(values, field):
    if not isinstance(values, (list, tuple)) or not values:
        raise ValueError(f"{field} must be a nonempty list")
    return [_text(v, field) for v in values]


class TeshuvahMixin:
    # ------------------------------------------------------------------ état

    def _teshuvah_state(self):
        return self.state.setdefault("teshuvah", {"claims": {}, "cycles": {}, "safeguards": {}})

    def _cycle(self, teshuvah_id):
        cycle = self._teshuvah_state()["cycles"].get(teshuvah_id)
        if cycle is None:
            raise ValueError(f"unknown teshuvah_id: {teshuvah_id}")
        return cycle

    def _require_phase(self, cycle, *allowed):
        if cycle["phase"] not in allowed:
            raise ValueError(f"teshuvah {cycle['teshuvah_id']} is {cycle['phase']}; expected one of {list(allowed)}")

    def _set_claim_status(self, claim_id, status, event_label, reason):
        claim = self._teshuvah_state()["claims"][claim_id]
        claim["status_history"].append({"from": claim["status"], "to": status, "by": event_label, "reason": reason})
        claim["status"] = status

    def _set_phase(self, cycle, phase, event_label):
        cycle["phase_history"].append({"from": cycle["phase"], "to": phase, "by": event_label})
        cycle["phase"] = phase
        cycle["drift_influence"] = DRIFT_INFLUENCE[phase] if "custom_influence" not in cycle else cycle["custom_influence"]

    def _ingest_row(self, evidence_id):
        for row in self.ledger.read_verified():
            if row["event_type"] == "INGEST_EVIDENCE" and row["payload"]["evidence"]["evidence_id"] == evidence_id:
                return row
        raise ValueError(f"evidence {evidence_id} has no recorded ingestion event")

    def _commit(self, event_type, payload, origin=CausalOrigin.MIXED):
        # The brain adopts a fresh copy of the committed state: never mutate
        # staged objects after this call. Event hashes are read from the ledger.
        return self._transition(event_type, copy.deepcopy(payload), origin)

    def _commit_cycle(self, event_type, cycle, payload):
        result = copy.deepcopy(cycle)
        event = self._commit(event_type, {"teshuvah_id": cycle["teshuvah_id"], **payload})
        return {**result, "event_hash": event["event_hash"]}

    def _cycle_rows(self, teshuvah_id):
        return [row for row in self.ledger.read_verified()
                if row["event_type"] in _EVENT_TYPES and row["payload"].get("teshuvah_id") == teshuvah_id]

    def _last_cycle_seq(self, teshuvah_id, event_type):
        rows = [r for r in self._cycle_rows(teshuvah_id) if r["event_type"] == event_type]
        if not rows:
            raise ValueError(f"no {event_type} recorded for {teshuvah_id}")
        return rows[-1]["seq"]

    def classify_replay_event(self, row):
        cls = _EVENT_TYPES.get(row.get("event_type"))
        return cls if cls else super().classify_replay_event(row)

    # ---------------------------------------------------------------- claims

    def record_claim(self, statement, provenance_kind, provenance, facts=(), confidence=None, replaces=None):
        """Enregistre une INTERPRETATION fondée sur des FACTS (preuves ou événements)."""
        _text(statement, "statement")
        _text(provenance, "provenance")
        if provenance_kind not in CLAIM_PROVENANCE:
            raise ValueError(f"provenance_kind must be one of {CLAIM_PROVENANCE}")
        if confidence is not None and not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        facts = list(facts)
        known_events = {row["event_hash"] for row in self.ledger.read_verified()}
        for ref in facts:
            if ref not in self.state["E"]["evidence"] and ref not in known_events:
                raise ValueError(f"fact reference is neither recorded evidence nor a ledger event: {ref}")
        ts = self._teshuvah_state()
        claim_id = f"CL{len(ts['claims']) + 1:04d}"
        claim = {
            "claim_id": claim_id,
            "layer": "interpretation",
            "statement": statement,
            "facts": facts,
            "provenance_kind": provenance_kind,
            "provenance": provenance,
            "confidence": confidence,
            "status": "active",
            "status_history": [],
            "replaces": replaces,
            "replaced_by": None,
        }
        ts["claims"][claim_id] = claim
        result = copy.deepcopy(claim)
        event = self._commit("RECORD_CLAIM", {"claim": claim}, CausalOrigin.SELF)
        return {**result, "event_hash": event["event_hash"]}

    def claim(self, claim_id):
        claim = self._teshuvah_state()["claims"].get(claim_id)
        return copy.deepcopy(claim) if claim else None

    def usable_claims(self, sensitive=False):
        """Claims utilisables dans C(t). Une décision sensible n'utilise que des claims actifs."""
        claims = self._teshuvah_state()["claims"].values()
        allowed = {"active"} if sensitive else {"active", "contested"}
        return [copy.deepcopy(c) for c in claims if c["status"] in allowed]

    def claim_layers(self, claim_id):
        """FACT / INTERPRETATION / CURRENT_MODEL pour une compréhension corrigée."""
        claims = self._teshuvah_state()["claims"]
        if claim_id not in claims:
            raise ValueError(f"unknown claim_id: {claim_id}")
        original = claims[claim_id]
        current = original
        seen = {claim_id}
        while current.get("replaced_by"):
            nxt = current["replaced_by"]
            if nxt in seen:
                raise ValueError("claim replacement cycle")
            seen.add(nxt)
            current = claims[nxt]
        return {
            "fact": list(original["facts"]),
            "interpretation": {"claim_id": original["claim_id"], "statement": original["statement"],
                               "status": original["status"]},
            "current_model": None if current["status"] != "active" else {
                "claim_id": current["claim_id"], "statement": current["statement"]},
            "principle": "a correction may change the interpretation without declaring the fact false",
        }

    # ----------------------------------------------------------------- cycle

    def initiate_teshuvah(self, drift_kind, description, provenance, claim_ids=(), drift_events=()):
        """D : la dérive est détectée. Les claims visés deviennent contested ; rien n'est effacé."""
        _text(drift_kind, "drift_kind")
        _text(description, "description")
        _text(provenance, "provenance")
        claim_ids, drift_events = list(claim_ids), list(drift_events)
        if not claim_ids and not drift_events:
            raise ValueError("a teshuvah must name the claims or events it concerns")
        ts = self._teshuvah_state()
        for cid in claim_ids:
            if cid not in ts["claims"]:
                raise ValueError(f"unknown claim_id: {cid}")
            if ts["claims"][cid]["status"] not in {"active", "contested"}:
                raise ValueError(f"claim {cid} is {ts['claims'][cid]['status']}; it is not part of C(t)")
        known = {row["event_hash"] for row in self.ledger.read_verified()}
        for ref in drift_events:
            if ref not in known:
                raise ValueError(f"drift event not found in verified ledger: {ref}")
        teshuvah_id = f"TSH{len(ts['cycles']) + 1:04d}"
        cycle = {
            "teshuvah_id": teshuvah_id,
            "origin": {"drift_kind": drift_kind, "description": description,
                       "claim_ids": claim_ids, "drift_events": drift_events, "provenance": provenance},
            "phase": "contested",
            "phase_history": [],
            "drift_influence": DRIFT_INFLUENCE["contested"],
            "acknowledgment": None,
            "repair": {"proposed": None, "applied": None},
            "safeguards": [],
            "sparks": {},
            "return": None,
            "verification": {"status": "pending"},
            "recurrences": [],
            "lesson": None,
            "closed": False,
        }
        ts["cycles"][teshuvah_id] = cycle
        for cid in claim_ids:
            self._set_claim_status(cid, "contested", teshuvah_id, description)
        return self._commit_cycle("TESHUVAH_INITIATED", cycle, {"origin": cycle["origin"]})

    def name_sparks(self, teshuvah_id, sparks, provenance):
        """Brisure : nommer ce qui restait vrai dans les claims brisés.

        sparks : liste de {"claim_id", "content", "facts"?}. Une étincelle n'est
        pas le claim : c'est la part de vérité qu'une correction doit relever.
        """
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "contested", "under_repair")
        _text(provenance, "provenance")
        if not isinstance(sparks, list) or not sparks:
            raise ValueError("sparks must be a nonempty list")
        claims = self._teshuvah_state()["claims"]
        for sp in sparks:
            if not isinstance(sp, dict) or sp.get("claim_id") not in cycle["origin"]["claim_ids"]:
                raise ValueError("each spark must come from a claim broken in this teshuvah")
            _text(sp.get("content"), "spark.content")
            facts = list(sp.get("facts", []))
            if not set(facts) <= set(claims[sp["claim_id"]]["facts"]):
                raise ValueError("a spark may only cite facts its broken claim rested on")
        named = []
        for sp in sparks:
            spark_id = f"{teshuvah_id}-SP{len(cycle['sparks']) + 1:02d}"
            spark = {"spark_id": spark_id, "claim_id": sp["claim_id"], "content": sp["content"],
                     "facts": list(sp.get("facts", [])), "provenance": provenance,
                     "status": "scattered", "history": []}
            cycle["sparks"][spark_id] = spark
            named.append(spark)
        return self._commit_cycle("TESHUVAH_SPARKS_NAMED", cycle, {"sparks": named})

    def acknowledge_teshuvah(self, teshuvah_id, responsible_actor, what_went_wrong, impact, drift_cause, provenance):
        """R + A : nommer l'écart dans une trace structurée, pas recalculer en silence."""
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "contested")
        ack = {
            "responsible_actor": _text(responsible_actor, "responsible_actor"),
            "what_went_wrong": _text(what_went_wrong, "what_went_wrong"),
            "impact": _text(impact, "impact"),
            "drift_cause": _text(drift_cause, "drift_cause"),
            "provenance": _text(provenance, "provenance"),
        }
        cycle["acknowledgment"] = ack
        self._set_phase(cycle, "under_repair", "acknowledged")
        for cid in cycle["origin"]["claim_ids"]:
            self._set_claim_status(cid, "under_repair", teshuvah_id, what_went_wrong)
        return self._commit_cycle("TESHUVAH_ACKNOWLEDGED", cycle, {"acknowledgment": ack})

    def propose_teshuvah_repair(self, teshuvah_id, plan, provenance, external_repair_required=False):
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "under_repair")
        proposal = {"plan": _text(plan, "plan"), "provenance": _text(provenance, "provenance"),
                    "external_repair_required": bool(external_repair_required)}
        cycle["repair"]["proposed"] = proposal
        return self._commit_cycle("TESHUVAH_REPAIR_PROPOSED", cycle, {"proposal": proposal})

    def apply_teshuvah_repair(self, teshuvah_id, corrections, applied_by, provenance, released_sparks=None):
        """C : changer l'état interprété actif, jamais l'histoire.

        corrections : liste de {"claim_id", "action": "supersede"|"retract",
        "reason", et pour supersede "replacement": {"statement", "provenance_kind",
        "provenance", "facts"?}, "raised_sparks"?: [spark_id]}.
        released_sparks : {spark_id: raison} pour chaque étincelle non relevée.
        Toute étincelle nommée doit être relevée ou laissée explicitement.
        """
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "under_repair")
        if cycle["repair"]["proposed"] is None:
            raise ValueError("a repair must be proposed before it is applied")
        _text(applied_by, "applied_by")
        _text(provenance, "provenance")
        if not isinstance(corrections, list):
            raise ValueError("corrections must be a list")
        targets = set(cycle["origin"]["claim_ids"])
        if targets and {c.get("claim_id") for c in corrections if isinstance(c, dict)} != targets:
            raise ValueError("every contested claim of this teshuvah must receive an explicit correction")
        ts = self._teshuvah_state()
        # Valider tout avant toute mutation.
        for c in corrections:
            if not isinstance(c, dict) or c.get("action") not in {"supersede", "retract"}:
                raise ValueError("each correction needs action supersede or retract")
            if c.get("claim_id") not in targets:
                raise ValueError(f"claim {c.get('claim_id')} is not under repair in this teshuvah")
            _text(c.get("reason"), "reason")
            if c["action"] == "supersede":
                rep = c.get("replacement")
                if not isinstance(rep, dict):
                    raise ValueError("supersede requires a replacement claim")
                _text(rep.get("statement"), "replacement.statement")
                _text(rep.get("provenance"), "replacement.provenance")
                if rep.get("provenance_kind") not in CLAIM_PROVENANCE:
                    raise ValueError(f"replacement.provenance_kind must be one of {CLAIM_PROVENANCE}")
            elif c.get("raised_sparks"):
                raise ValueError("a retraction has no replacement to raise sparks into; release them instead")
            for sid in c.get("raised_sparks", []):
                if sid in cycle["sparks"] and cycle["sparks"][sid]["claim_id"] != c["claim_id"]:
                    raise ValueError(f"spark {sid} belongs to another broken claim")
        released = dict(released_sparks or {})
        raised = [sid for c in corrections for sid in c.get("raised_sparks", [])]
        for sid, reason in released.items():
            _text(reason, f"released_sparks.{sid}")
        accounted = raised + list(released)
        if len(accounted) != len(set(accounted)) or set(accounted) != set(cycle["sparks"]):
            raise ValueError("every named spark must be raised into a replacement or explicitly released, exactly once")
        applied = []
        for c in corrections:
            cid = c["claim_id"]
            old = ts["claims"][cid]
            entry = {"claim_id": cid, "action": c["action"], "reason": c["reason"]}
            if c["action"] == "supersede":
                rep = c["replacement"]
                new_id = f"CL{len(ts['claims']) + 1:04d}"
                ts["claims"][new_id] = {
                    "claim_id": new_id, "layer": "interpretation", "statement": rep["statement"],
                    "facts": list(rep.get("facts", old["facts"])), "provenance_kind": rep["provenance_kind"],
                    "provenance": rep["provenance"], "confidence": rep.get("confidence"),
                    "status": "active", "status_history": [], "replaces": cid, "replaced_by": None,
                    "created_by_teshuvah": teshuvah_id,
                }
                old["replaced_by"] = new_id
                self._set_claim_status(cid, "superseded", teshuvah_id, c["reason"])
                entry["replacement_claim_id"] = new_id
                for sid in c.get("raised_sparks", []):
                    spark = cycle["sparks"][sid]
                    spark["history"].append({"from": spark["status"], "to": "raised", "into": new_id})
                    spark["status"], spark["raised_into"] = "raised", new_id
                ts["claims"][new_id]["raised_sparks"] = list(c.get("raised_sparks", []))
                entry["raised_sparks"] = list(c.get("raised_sparks", []))
            else:
                self._set_claim_status(cid, "retracted", teshuvah_id, c["reason"])
            applied.append(entry)
        for sid, reason in released.items():
            spark = cycle["sparks"][sid]
            spark["history"].append({"from": spark["status"], "to": "released", "reason": reason})
            spark["status"], spark["release_reason"] = "released", reason
        record = {"corrections": applied, "applied_by": applied_by, "provenance": provenance,
                  "released_sparks": released, "status": "repair_claimed_not_verified"}
        cycle["repair"]["applied"] = record
        self._set_phase(cycle, "repair_applied", "repair_applied")
        return self._commit_cycle("TESHUVAH_REPAIR_APPLIED", cycle, {
            "applied": record,
            "new_claims": {e["replacement_claim_id"]: ts["claims"][e["replacement_claim_id"]]
                           for e in applied if "replacement_claim_id" in e},
            "principle": "earlier claims and their facts stay in history; only the active interpretation changes",
        })

    def create_safeguard(self, teshuvah_id, rule, test_case, provenance):
        """S : une règle ou un test qui empêche la répétition."""
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "under_repair", "repair_applied")
        ts = self._teshuvah_state()
        safeguard_id = f"SG{len(ts['safeguards']) + 1:04d}"
        sg = {"safeguard_id": safeguard_id, "teshuvah_id": teshuvah_id, "rule": _text(rule, "rule"),
              "test_case": _text(test_case, "test_case"), "provenance": _text(provenance, "provenance"),
              "status": "active"}
        ts["safeguards"][safeguard_id] = sg
        cycle["safeguards"].append(safeguard_id)
        result = copy.deepcopy(sg)
        event = self._commit("TESHUVAH_SAFEGUARD_CREATED", {"teshuvah_id": teshuvah_id, "safeguard": sg})
        return {**result, "event_hash": event["event_hash"]}

    def _observable_after(self, evidence_id, after_seq, label):
        if evidence_id not in self.state["E"]["evidence"]:
            raise ValueError(f"{label} evidence must be recorded in E first: {evidence_id}")
        evidence = self.state["E"]["evidence"][evidence_id]
        if evidence["kind"] not in _OBSERVABLE_KINDS:
            raise ValueError(f"{label} needs observable evidence, not {evidence['kind']}")
        row = self._ingest_row(evidence_id)
        if row["seq"] <= after_seq:
            raise ValueError(f"{label} evidence predates the step it would confirm; a new observable state is required")
        if row["payload"].get("origin") == CausalOrigin.SELF.value:
            raise ValueError(f"{label} evidence originates from S; the system cannot certify its own return")
        return row

    def observe_return(self, teshuvah_id, evidence_id, what_enabled_return, provenance):
        """Retour observé : une preuve enregistrée après la correction montre la nouvelle conduite."""
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "repair_applied")
        _text(provenance, "provenance")
        enabled = _texts(what_enabled_return, "what_enabled_return")
        row = self._observable_after(evidence_id, self._last_cycle_seq(teshuvah_id, "TESHUVAH_REPAIR_APPLIED"), "return")
        ret = {"evidence_id": evidence_id, "evidence_event_hash": row["event_hash"],
               "what_enabled_return": enabled, "provenance": provenance}
        cycle["return"] = ret
        return self._commit_cycle("TESHUVAH_RETURN_OBSERVED", cycle, {"return": ret})

    def verify_non_recurrence(self, teshuvah_id, evidence_id, verifier, provenance):
        """V : non-récidive vérifiée sur un état observable postérieur au retour.

        Refusé si le vérificateur est l'acteur qui a reconnu ou appliqué la
        réparation : la réparation ne peut pas être auto-certifiée. Le logiciel
        ne peut pas authentifier l'identité ni l'indépendance du vérificateur ;
        le statut l'indique explicitement.
        """
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "repair_applied")
        if cycle["return"] is None:
            raise ValueError("no return has been observed yet")
        if not cycle["safeguards"]:
            raise ValueError("verification requires at least one safeguard against recurrence")
        _text(verifier, "verifier")
        _text(provenance, "provenance")
        if verifier in {cycle["acknowledgment"]["responsible_actor"], cycle["repair"]["applied"]["applied_by"]}:
            raise ValueError("repair cannot be self-certified: verifier must differ from the responsible and applying actors")
        row = self._observable_after(evidence_id, self._last_cycle_seq(teshuvah_id, "TESHUVAH_RETURN_OBSERVED"), "verification")
        verification = {
            "status": "verified_on_observable_state",
            "evidence_id": evidence_id,
            "evidence_event_hash": row["event_hash"],
            "verifier": verifier,
            "provenance": provenance,
            "external_authentication": "not_performed",
            "checks_performed": ["evidence_recorded_after_return", "evidence_kind_observable",
                                 "evidence_origin_not_self", "verifier_differs_from_actor", "safeguard_present"],
        }
        cycle["verification"] = verification
        self._set_phase(cycle, "repair_verified", "non_recurrence_verified")
        return self._commit_cycle("TESHUVAH_NON_RECURRENCE_VERIFIED", cycle, {"verification": verification})

    def record_teshuvah_recurrence(self, teshuvah_id, description, provenance, evidence_id=None):
        """Récidive : le cycle revient en réparation, sans effacer ni retour ni vérification antérieurs."""
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "repair_applied", "repair_verified", "cicatrized", "archived")
        if evidence_id is not None and evidence_id not in self.state["E"]["evidence"]:
            raise ValueError(f"unknown evidence_id: {evidence_id}")
        rec = {"description": _text(description, "description"), "provenance": _text(provenance, "provenance"),
               "evidence_id": evidence_id, "phase_at_recurrence": cycle["phase"]}
        cycle["recurrences"].append(rec)
        cycle.pop("custom_influence", None)
        cycle["closed"] = False
        if cycle["verification"].get("status") != "pending":
            cycle.setdefault("verification_history", []).append(cycle["verification"])
            cycle["verification"] = {"status": "pending"}
        if cycle["return"] is not None:
            cycle.setdefault("return_history", []).append(cycle["return"])
            cycle["return"] = None
        if cycle["repair"]["applied"] is not None:
            cycle["repair"].setdefault("applied_history", []).append(cycle["repair"]["applied"])
            cycle["repair"]["applied"] = None
            cycle["repair"].setdefault("proposed_history", []).append(cycle["repair"]["proposed"])
            cycle["repair"]["proposed"] = None
        for spark in cycle["sparks"].values():
            if spark["status"] != "scattered":
                spark["history"].append({"from": spark["status"], "to": "scattered", "by": "recurrence"})
                spark["status"] = "scattered"
                spark.pop("raised_into", None)
                spark.pop("release_reason", None)
        self._set_phase(cycle, "under_repair", "recurrence_detected")
        return self._commit_cycle("TESHUVAH_RECURRENCE_DETECTED", cycle, {
            "recurrence": rec,
            "principle": "recurrence is information about durability; prior return and verification stay in history",
        })

    def cicatrize_teshuvah(self, teshuvah_id, lesson, provenance, current_influence=None):
        """La trace demeure ; elle cesse progressivement de gouverner l'état courant."""
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "repair_verified")
        if current_influence is not None:
            if not 0.0 <= current_influence <= 1.0:
                raise ValueError("current_influence must be between 0 and 1")
            cycle["custom_influence"] = current_influence
        cycle["lesson"] = {"lesson": _text(lesson, "lesson"), "provenance": _text(provenance, "provenance")}
        self._set_phase(cycle, "cicatrized", "cicatrized")
        return self._commit_cycle("TESHUVAH_CICATRIZED", cycle, {
            "lesson": cycle["lesson"], "drift_influence": cycle["drift_influence"]})

    def archive_teshuvah(self, teshuvah_id, provenance):
        cycle = self._cycle(teshuvah_id)
        self._require_phase(cycle, "cicatrized")
        _text(provenance, "provenance")
        cycle.pop("custom_influence", None)
        self._set_phase(cycle, "archived", "archived")
        return self._commit_cycle("TESHUVAH_ARCHIVED", cycle, {
            "provenance": provenance, "principle": "archive is not deletion"})

    def teshuvah_closure_status(self, teshuvah_id):
        """Conditions objectives de clôture ; aucune n'est une simple déclaration."""
        cycle = self._cycle(teshuvah_id)
        checks = {
            "acknowledged": cycle["acknowledgment"] is not None,
            "repair_applied": cycle["repair"]["applied"] is not None,
            "safeguard_created": bool(cycle["safeguards"]),
            "sparks_accounted": all(sp["status"] != "scattered" for sp in cycle["sparks"].values()),
            "return_observed": cycle["return"] is not None,
            "non_recurrence_verified": cycle["verification"].get("status") == "verified_on_observable_state",
            "no_open_recurrence": cycle["phase"] in {"repair_verified", "cicatrized", "archived"},
        }
        return {"teshuvah_id": teshuvah_id, "checks": checks, "closable": all(checks.values())}

    def close_teshuvah(self, teshuvah_id, provenance):
        _text(provenance, "provenance")
        cycle = self._cycle(teshuvah_id)
        status = self.teshuvah_closure_status(teshuvah_id)
        if not status["closable"]:
            missing = [k for k, ok in status["checks"].items() if not ok]
            raise ValueError(f"teshuvah cannot be closed; missing: {missing}")
        if cycle["closed"]:
            raise ValueError(f"teshuvah already closed: {teshuvah_id}")
        cycle["closed"] = True
        return self._commit_cycle("TESHUVAH_CLOSED", cycle, {"checks": status["checks"], "provenance": provenance})

    # ------------------------------------------------------------------ vues

    def teshuvah(self, teshuvah_id):
        return copy.deepcopy(self._cycle(teshuvah_id))

    def teshuvah_trace(self, teshuvah_id):
        """La teshuvah comme relation causale entre événements immuables du ledger."""
        self._cycle(teshuvah_id)
        return [{"seq": r["seq"], "event_type": r["event_type"], "event_hash": r["event_hash"],
                 "prev_hash": r["prev_hash"]} for r in self._cycle_rows(teshuvah_id)]

    def teshuvah_cycles(self):
        return [copy.deepcopy(c) for c in self._teshuvah_state()["cycles"].values()]

    def drift_memory(self):
        """Qu'est-ce qui nous a fait dériver ?"""
        out = []
        for c in self._teshuvah_state()["cycles"].values():
            out.append({
                "teshuvah_id": c["teshuvah_id"], "drift_kind": c["origin"]["drift_kind"],
                "drift_cause": (c["acknowledgment"] or {}).get("drift_cause"),
                "phase": c["phase"], "drift_influence": c["drift_influence"],
                "recurrences": len(c["recurrences"]),
            })
        return out

    def return_memory(self):
        """Qu'est-ce qui nous a permis de revenir ? Retours observés, y compris ceux qu'une récidive a suivis."""
        out = []
        for c in self._teshuvah_state()["cycles"].values():
            returns = list(c.get("return_history", [])) + ([c["return"]] if c["return"] else [])
            for r in returns:
                out.append({
                    "teshuvah_id": c["teshuvah_id"],
                    "what_enabled_return": list(r["what_enabled_return"]),
                    "evidence_id": r["evidence_id"],
                    "held": r is c["return"] and c["phase"] in {"repair_verified", "cicatrized", "archived"},
                    "lesson": (c["lesson"] or {}).get("lesson") if r is c["return"] else None,
                    "raised_sparks": [sp["content"] for sp in c["sparks"].values()
                                      if r is c["return"] and sp["status"] == "raised"],
                })
        return out

    def sparks(self, teshuvah_id):
        return [copy.deepcopy(sp) for sp in self._cycle(teshuvah_id)["sparks"].values()]

    def solitary_vessels(self):
        """Vases du Tohou : claims actifs qui se tiennent seuls.

        Un appui au plus, partagé avec aucun autre claim actif, et pas de parole
        explicite de l'autre (user_stated). Signal de fragilité à examiner,
        jamais un verdict de fausseté. Reconstruction analytique.
        """
        active = [c for c in self._teshuvah_state()["claims"].values() if c["status"] == "active"]
        out = []
        for c in active:
            if c["provenance_kind"] == "user_stated" or len(c["facts"]) > 1:
                continue
            shared = any(set(c["facts"]) & set(o["facts"]) for o in active if o is not c)
            if not shared:
                out.append({"claim_id": c["claim_id"], "statement": c["statement"], "facts": list(c["facts"]),
                            "provenance_kind": c["provenance_kind"],
                            "status": "fragility_signal_not_falsity"})
        return out

    def redemption_index(self):
        """Cycles vérifiés durablement / cycles ouverts. Indicateur expérimental, pas une mesure de vertu."""
        cycles = list(self._teshuvah_state()["cycles"].values())
        if not cycles:
            return None
        durable = sum(1 for c in cycles if c["phase"] in {"repair_verified", "cicatrized", "archived"})
        return {"durable": durable, "total": len(cycles), "index": durable / len(cycles),
                "status": "experimental_indicator_not_virtue_measure"}
