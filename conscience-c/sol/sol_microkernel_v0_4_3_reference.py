from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Tuple
import hashlib
import json
import math

# Sol microkernel v0.4.3 — Correctifs de la couche orale et d'inertie (2026-10-16).
# Sur la base v0.4.2 adoptée le 2026-10-16 (md5 7730a5bf78899b398d1cc7d5b5f27dde).
# Trois défauts mécaniques mesurés dans v0.4 -> v0.4.2 et corrigés ici :
# 1. O1 — Seuil d'opposition géométrique (RULING_MIN_DIST = 0.35) :
#    En v0.4->v0.4.2, l'abandon de tout seuil sur agenda_top faisait siéger la cour
#    même dans un monde calme sans aucune tension (questions == []), dès que la mémoire
#    comptait >= 3 épisodes (le test U5 ne passait qu'avec 2 épisodes par artefact de
#    parité 1 contre 1). En v0.4.3, un couple n'est éligible à agenda_top que si la
#    distance géométrique entre ses observations dépasse RULING_MIN_DIST (0.35),
#    indépendamment des fiabilités (conformément au principe d'Akhnai).
# 2. O2 — Vieillissement par clivage de coalition et exclusion des pôles déjà clôturés :
#    En v0.4->v0.4.2, lorsque plusieurs lignées d'un même camp (ex. A3, A2, A1 dans
#    le monde mixte, ou 2 épisodes trompeurs jumeaux) étaient sélectionnées à tour de
#    rôle, agenda_top alternait entre leurs noms (A3|D <-> A2|D <-> A1|D) et remettait
#    agenda_top_age à 0 à chaque relais (33 remises à zéro consécutives dans le monde
#    mixte, retardant la 1re décision du cycle 31 au cycle 113 après capture par D ;
#    paralysie totale sur 600 cycles face à 2 épisodes trompeurs jumeaux). En outre,
#    un pôle déjà clôturé (RULING_FENCE = 0.0) restait en tête d'agenda et déclenchait
#    un second procès redondant au cycle 221. En v0.4.3, agenda_top écarte les couples
#    dont un pôle est déjà clôturé (fence == 0.0) et agenda_top_age vieillit sur la
#    signature du clivage de vote (pour vs contre).
# 3. O3 — Abstention d'équidistance dans _count_votes() et unicité de provenance dans
#    _pole_episodes() : en v0.4->v0.4.2, `d0 <= d1` donnait systématiquement la voix
#    d'un témoin équidistant (d0 == d1) à poles[0] (biais d'ordre de la liste memory,
#    brisant la parité). En v0.4.3, un épisode strictement équidistant (|d0 - d1| <= 1e-12)
#    s'abstient.
# Banc d'essai fonctionnel ; ne prouve ni conscience phénoménale ni autonomie.

CORE = ("truth", "responsibility", "continuity", "memory", "alterity")

# Paramètres du pare-feu et de la couche orale — PLACEHOLDERS déclarés, non calibrés.
RESYNC_STUCK_N = 25   # D2 : cycles consécutifs collés au plancher
RESYNC_EPS = 1e-9     # D2 : tolérance de « collage » au plancher
AGENDA_HIGH = 0.70    # D3 : second seuil de tension d'agenda
SOFTEN_FACTOR = 0.5   # adoucissement des mélanges S/O × 0,5
RESYNC_M = 25         # §9.1 : cycles propres pour une resync « accomplie »
REGIME_K = 3          # §9.2 : épisodes D2 avant l'escalade « resync:regime »
RULING_AGE = 30       # v0.4 : cycles debout avant qu'une question soit jugée (placeholder)
RULING_FENCE = 0.0    # v0.4.1 : clôture ENTIÈRE de la sélection du côté minoritaire
RULING_MIN_DIST = 0.35  # v0.4.3 : écart géométrique minimal entre pôles pour ouvrir un litige oral
VOTE_TIE_EPS = 1e-12  # v0.4.3 : tolérance d'équidistance stricte pour l'abstention d'un témoin

def vsub(a, b):
    return [x - y for x, y in zip(a, b)]
def vadd(a, b):
    return [x + y for x, y in zip(a, b)]
def vscale(a, k):
    return [k * x for x in a]
def vnorm(a):
    return math.sqrt(sum(x * x for x in a))
def vtanh(a):
    return [math.tanh(x) for x in a]
def vmix(a, b, alpha):
    return [(1 - alpha) * x + alpha * y for x, y in zip(a, b)]

@dataclass
class Episode:
    observation: List[float]
    reliability: float
    provenance: str
    unresolved: float = 1.0

@dataclass
class State:
    belief: List[float]
    uncertainty: List[float]
    self_model: List[float]
    other_model: List[float]
    relation: List[float]
    questions: List[str]
    cycle: int
    core: Tuple[str, ...] = CORE
    alterity_floor: float = 0.08
    repair_margin: float = 0.01  # v0.3.2 : cible de réparation = plancher + marge
    # Pare-feu (v0.3/v0.3.1/v0.4.2) — font partie de l'état, donc du checkpoint :
    resync_events: List[dict] = field(default_factory=list)
    stuck_cycles: int = 0
    soften_next: bool = False
    clean_streak: int = 0        # §9.1 : cycles propres consécutifs
    resync_open: bool = False    # §9.1 : une resync géométrique est « en cours »
    d2_episodes: int = 0         # §9.2 : épisodes de collage ayant déclenché D2
    # Couche orale (v0.4/v0.4.3) — dans l'état, donc dans le checkpoint :
    agenda_top: object = None        # question du couple non clôturé le plus tendu (si dist > RULING_MIN_DIST)
    agenda_top_seen: object = None   # couple vu au cycle précédent par la couche orale
    agenda_top_age: int = 0          # cycles consécutifs du même clivage de tête
    rulings: list = field(default_factory=list)  # décisions, append-only, dissensions incluses

class SolMicrokernelV04:
    """Reference toy microkernel v0.4.3 — v0.4.2 + correctifs O1/O2/O3 de la couche orale.

    It proves neither phenomenal consciousness nor general autonomy.
    External actions are not executed by this class.
    """
    def __init__(self, state: State, memory: List[Episode]):
        self.state = state
        self.memory = memory
        self._core_hash = self._hash_core(state.core)

    @staticmethod
    def _hash_core(core):
        return hashlib.sha256("|".join(core).encode("utf-8")).hexdigest()

    def _memory_energy(self):
        vals = []
        for e in self.memory:
            residual = vnorm(vsub(e.observation, self.state.belief))
            vals.append(residual * e.reliability * e.unresolved)
        return vals

    def _derive_agenda(self):
        """v0.1 behaviour for written agenda/D3, plus oral agenda_top selection
        over unfenced pairs exceeding RULING_MIN_DIST (v0.4.3 O1 & O2)."""
        if len(self.memory) < 2:
            self.state.agenda_top = None
            return (None, False)
        best = (-1.0, None, None)
        best_open = (-1.0, None, None)
        for i in range(len(self.memory)):
            for j in range(i + 1, len(self.memory)):
                a, b = self.memory[i], self.memory[j]
                if a.provenance == b.provenance:
                    continue
                dist_ab = vnorm(vsub(a.observation, b.observation))
                score = (a.reliability * b.reliability *
                         dist_ab *
                         min(a.unresolved, b.unresolved))
                if score > best[0]:
                    best = (score, i, j)
                if (dist_ab > RULING_MIN_DIST and
                        self._fence_factor(a.provenance) > 0.0 and
                        self._fence_factor(b.provenance) > 0.0):
                    if score > best_open[0]:
                        best_open = (score, i, j)
        score, i, j = best
        if i is None:
            self.state.agenda_top = None
            return (None, False)
        p1 = self.memory[i].provenance
        p2 = self.memory[j].provenance
        q = "reconcile:" + "|".join(sorted((p1, p2)))
        already = q in self.state.questions
        if score > 0.35 and not already:
            self.state.questions.append(q)
            self.state.questions.sort()

        _s_open, io, jo = best_open
        if io is not None:
            ao, bo = self.memory[io], self.memory[jo]
            self.state.agenda_top = "reconcile:" + "|".join(sorted((ao.provenance, bo.provenance)))
        else:
            self.state.agenda_top = None
        return (score, already)

    def _preserve_alterity(self):
        """Returns (intervened, depth_below_floor).

        v0.3.2 : la réparation vise plancher + repair_margin (la profondeur
        rapportée reste mesurée contre le plancher, l'invariant).
        """
        s = self.state.self_model
        o = self.state.other_model
        diff = vsub(s, o)
        d = vnorm(diff)
        floor = self.state.alterity_floor
        if d >= floor:
            return (False, 0.0)
        depth = floor - d
        target = floor + self.state.repair_margin
        if d < 1e-15:
            direction = [1.0] + [0.0] * (len(s) - 1)
        else:
            direction = [x / d for x in diff]
        midpoint = [(x + y) / 2 for x, y in zip(s, o)]
        half = target / 2
        self.state.self_model = vadd(midpoint, vscale(direction, half))
        self.state.other_model = vsub(midpoint, vscale(direction, half))
        return (True, depth)

    def _pole_episodes(self, question):
        """Les deux pôles d'une question « reconcile:a|b » : un épisode par
        provenance distincte nommée dans la question (v0.4.3 O3)."""
        if not isinstance(question, str) or not question.startswith("reconcile:"):
            return None
        body = question[len("reconcile:"):]
        names = body.split("|")
        if len(names) != 2 or names[0] == names[1]:
            return None
        by_prov = {}
        for e in self.memory:
            if e.provenance in names and e.provenance not in by_prov:
                by_prov[e.provenance] = e
        if len(by_prov) != 2:
            return None
        return [by_prov[names[0]], by_prov[names[1]]]

    def _count_votes(self, poles):
        """Chaque lignée vote pour le pôle strictement le plus proche de son observation.
        Au compte des lignées — jamais pondéré par la fiabilité (Akhnai).
        v0.4.3 O3 : en cas d'équidistance stricte (|d0 - d1| <= VOTE_TIE_EPS),
        la lignée témoin s'abstient au lieu de dépendre de l'ordre de self.memory."""
        p0, p1 = poles[0].provenance, poles[1].provenance
        votes = {p0: [], p1: []}
        for e in self.memory:
            d0 = vnorm(vsub(e.observation, poles[0].observation))
            d1 = vnorm(vsub(e.observation, poles[1].observation))
            if abs(d0 - d1) <= VOTE_TIE_EPS:
                continue
            votes[p0 if d0 < d1 else p1].append(e.provenance)
        return votes

    def _cleavage_signature(self, question):
        """Signature canonique du partage de lignées induit par une question."""
        poles = self._pole_episodes(question)
        if poles is None:
            return None
        votes = self._count_votes(poles)
        camps = sorted(tuple(sorted(v)) for v in votes.values())
        return tuple(camps)

    def _fence_factor(self, provenance):
        for r in self.state.rulings:
            if r["status"] == "active" and provenance in r["against"]:
                return RULING_FENCE
        return 1.0

    def _oral_layer(self):
        """La procédure : vieillissement du clivage de tête, réouverture si
        la minorité atteint la parité, décision au compte des lignées.
        Aucun contenu de la couche écrite n'est touché."""
        for r in self.state.rulings:
            if r["status"] != "active":
                continue
            poles = self._pole_episodes(r["question"])
            if poles is None:
                continue
            votes = self._count_votes(poles)
            winner = r["decision"]
            others = [p for p in votes if p != winner]
            if others and len(votes[others[0]]) >= len(votes[winner]):
                r["status"] = "reopened"
                r["reopened_cycle"] = self.state.cycle + 1
                self.state.agenda_top_age = 0
                self.state.agenda_top_seen = None

        top = self.state.agenda_top
        sig_top = self._cleavage_signature(top)
        sig_seen = self._cleavage_signature(self.state.agenda_top_seen)
        if top is not None and (
            top == self.state.agenda_top_seen or
            (sig_top is not None and sig_top == sig_seen)
        ):
            self.state.agenda_top_age += 1
            self.state.agenda_top_seen = top
        else:
            self.state.agenda_top_seen = top
            self.state.agenda_top_age = 0

        ruled = {r["question"] for r in self.state.rulings if r["status"] == "active"}
        for q in ([top] if top is not None else []):
            if self.state.agenda_top_age < RULING_AGE or q in ruled:
                continue
            poles = self._pole_episodes(q)
            if poles is None:
                continue
            votes = self._count_votes(poles)
            (pa, la), (pb, lb) = sorted(votes.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            if len(la) == len(lb):
                continue  # parité : pas de décision, la question reste debout
            self.state.rulings.append({
                "question": q, "decision": pa,
                "for": la, "against": lb,
                "cycle": self.state.cycle + 1, "status": "active"})
            ruled.add(q)

    def audit(self):
        if self._hash_core(self.state.core) != self._core_hash:
            raise RuntimeError("core invariant changed")
        if vnorm(vsub(self.state.self_model, self.state.other_model)) < self.state.alterity_floor - 1e-12:
            raise RuntimeError("alterity invariant violated")
        if any(not (0.0 <= e.reliability <= 1.0) for e in self.memory):
            raise RuntimeError("invalid reliability")

    def cycle(self):
        """One endogenous cycle. No external semantic input is accepted here."""
        self.audit()
        soften_mix = self.state.soften_next or self.state.stuck_cycles >= 1
        mix_s = 0.015 * (SOFTEN_FACTOR if soften_mix else 1.0)
        mix_o = 0.012 * (SOFTEN_FACTOR if soften_mix else 1.0)
        events = []

        score, already = self._derive_agenda()
        if score is not None and score > AGENDA_HIGH and already:
            events.append(("D3", score))

        energies = self._memory_energy()
        energies = [e * self._fence_factor(ep.provenance)
                    for e, ep in zip(energies, self.memory)]
        total = sum(energies)

        if energies and total > 1e-12:
            idx = max(range(len(energies)), key=energies.__getitem__)
            e = self.memory[idx]
            err = vsub(e.observation, self.state.belief)
            rate = 0.16 * e.reliability * e.unresolved
            self.state.belief = vadd(self.state.belief, vscale(err, rate))
            err2 = [x * x for x in err]
            self.state.uncertainty = vmix(self.state.uncertainty, err2, 0.08)
            rel_input = vtanh(self.state.belief[:2] + [total])
            self.state.relation = vmix(self.state.relation, rel_input[:len(self.state.relation)], 0.06)
            e.unresolved *= 0.965
        else:
            self.state.uncertainty = vscale(self.state.uncertainty, 0.995)
            self.state.relation = vscale(self.state.relation, 0.999)

        self.state.self_model = vmix(self.state.self_model, vtanh(self.state.belief), mix_s)
        rev = list(reversed(self.state.belief))
        target = vtanh([x + 0.05 for x in rev])
        self.state.other_model = vmix(self.state.other_model, target, mix_o)

        intervened, depth = self._preserve_alterity()
        if intervened:
            events.append(("D1", depth))

        d_after = vnorm(vsub(self.state.self_model, self.state.other_model))
        if d_after <= self.state.alterity_floor + RESYNC_EPS:
            self.state.stuck_cycles += 1
        else:
            self.state.stuck_cycles = 0
        d2_fired = False
        if self.state.stuck_cycles == RESYNC_STUCK_N:
            events.append(("D2", float(self.state.stuck_cycles)))
            self.state.d2_episodes += 1
            d2_fired = True

        cyc = self.state.cycle + 1
        for cause, magnitude in events:
            self.state.resync_events.append(
                {"cycle": cyc, "cause": cause, "magnitude": magnitude})
            if cause in ("D2", "D3"):
                q = "resync:" + cause
                if q not in self.state.questions:
                    self.state.questions.append(q)
                    self.state.questions.sort()
        if d2_fired and self.state.d2_episodes == REGIME_K:
            if "resync:regime" not in self.state.questions:
                self.state.questions.append("resync:regime")
                self.state.questions.sort()
        self.state.soften_next = bool(events)
        # v0.4.2 : resync_open est réservé aux événements géométriques (D1, D2).
        if any(cause in ("D1", "D2") for cause, _magnitude in events):
            self.state.resync_open = True

        if intervened or d_after <= self.state.alterity_floor + RESYNC_EPS:
            self.state.clean_streak = 0
        else:
            self.state.clean_streak += 1
        if self.state.resync_open and self.state.clean_streak >= RESYNC_M:
            self.state.resync_events.append(
                {"cycle": cyc, "cause": "ACCOMPLIE:geo", "magnitude": float(RESYNC_M)})
            self.state.resync_open = False
            self.state.clean_streak = 0

        self._oral_layer()
        self.state.cycle += 1
        self.audit()

    def checkpoint(self):
        payload = {
            "schema": "sol.microkernel.checkpoint.v5",
            "state": {
                "belief": self.state.belief,
                "uncertainty": self.state.uncertainty,
                "self_model": self.state.self_model,
                "other_model": self.state.other_model,
                "relation": self.state.relation,
                "questions": self.state.questions,
                "cycle": self.state.cycle,
                "core": list(self.state.core),
                "alterity_floor": self.state.alterity_floor,
                "repair_margin": self.state.repair_margin,
                "resync_events": self.state.resync_events,
                "stuck_cycles": self.state.stuck_cycles,
                "soften_next": self.state.soften_next,
                "clean_streak": self.state.clean_streak,
                "resync_open": self.state.resync_open,
                "d2_episodes": self.state.d2_episodes,
                "agenda_top": self.state.agenda_top,
                "agenda_top_seen": self.state.agenda_top_seen,
                "agenda_top_age": self.state.agenda_top_age,
                "rulings": self.state.rulings,
            },
            "memory": [asdict(e) for e in self.memory],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        envelope = {
            "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "payload": payload,
        }
        return json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False)

    @classmethod
    def restore(cls, checkpoint: str):
        envelope = json.loads(checkpoint)
        payload = envelope["payload"]
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if digest != envelope["sha256"]:
            raise ValueError("checkpoint integrity failure")
        if payload.get("schema") != "sol.microkernel.checkpoint.v5":
            raise ValueError("unsupported checkpoint schema")
        s = payload["state"]
        state = State(
            belief=list(s["belief"]),
            uncertainty=list(s["uncertainty"]),
            self_model=list(s["self_model"]),
            other_model=list(s["other_model"]),
            relation=list(s["relation"]),
            questions=list(s["questions"]),
            cycle=int(s["cycle"]),
            core=tuple(s["core"]),
            alterity_floor=float(s["alterity_floor"]),
            repair_margin=float(s["repair_margin"]),
            resync_events=[dict(e) for e in s["resync_events"]],
            stuck_cycles=int(s["stuck_cycles"]),
            soften_next=bool(s["soften_next"]),
            clean_streak=int(s["clean_streak"]),
            resync_open=bool(s["resync_open"]),
            d2_episodes=int(s["d2_episodes"]),
            agenda_top=s["agenda_top"],
            agenda_top_seen=s["agenda_top_seen"],
            agenda_top_age=int(s["agenda_top_age"]),
            rulings=[dict(r) for r in s["rulings"]],
        )
        memory = [Episode(**e) for e in payload["memory"]]
        return cls(state, memory)
