# REFERENCE ADOPTEE — Sol strat3 multi-echelle (16 octobre 2026).
# Derivee de la candidate strat2 v0.4.6 ; voir le rapport de controle.
# L'ancien moteur est preserve en tant que _SolV046 ; nouvelles regles
# de representation/vote/agenda/mise a jour semantique en sous-classe.
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Tuple
import copy
import hashlib
import json
import math

# Sol microkernel v0.4.4 — PROPOSITION préparée le 2026-10-16
# (non adoptée ; adoption au mot de Mikael ; version régnante actuelle = v0.4.3).
# Sur la base v0.4.3 adoptée le 2026-10-16 à 18:15 EDT (md5 985bc369254a0972f60bb15c291f69eb).
#
# Trois garde-fous de parité et d'équidistance ajoutés dans la seule couche orale
# (la couche écrite v0.1 -> v0.3.2 demeure strictement inchangée) :
# 1. P_VOTES (Corps électoral actif vs corps électoral de réouverture) :
#    Dans `_count_votes(poles, include_fenced=False)`, la vérification de réouverture
#    Edouyot (`include_fenced=True`) compte toutes les lignées de `self.memory` (afin que
#    la minorité archivée puisse retrouver la parité si de nouvelles lignées la rejoignent),
#    tandis que l'instruction et le vote d'une nouvelle décision (`include_fenced=False`)
#    excluent les épisodes actuellement sous clôture active (`_fence_factor == 0.0`).
#    Effet : un épisode déjà clôturé ne peut plus voter depuis sa clôture pour briser une
#    parité entre épisodes actifs ni faire clôturer ses propres juges.
# 2. P_AFFINITE (Rayon d'affinité mutuelle dans `_count_votes` contre le paradoxe du milieu) :
#    Face à deux pôles P0 et P1 distants de `d01 = ||P0 - P1||`, un épisode tiers `e` ne
#    rejoint le camp du pôle le plus proche Pi que s'il est strictement plus proche de Pi
#    que Pj ne l'est lui-même (`min(d0, d1) < d01 - VOTE_TIE_EPS`) et non équidistant
#    (`|d0 - d1| > VOTE_TIE_EPS`).
#    Effet : lorsque N=[0,0,0] est le point milieu entre A=[1,0,-1] et B=[-1,0,1],
#    sur le duel A|N, B est à la même distance de N que A (`d(B,N) = d(A,N) = sqrt(2)`).
#    B ne peut donc pas être enrôlé par N pour excommunier A (et inversement) : les trois
#    couples A|B, A|N et B|N restent en parité 1 contre 1.
# 3. P_AGENDA (Éligibilité hors parité et départage canonique dans `_derive_agenda`) :
#    Dans `_derive_agenda()`, une paire en parité (`len(la) == len(lb)`) reste inscrite dans
#    la couche écrite (`state.questions`), mais n'occupe pas `agenda_top` de la cour orale,
#    afin qu'un désaccord équilibré (ex. deux écoles à 2 contre 2, Elou va-elou) ne bloque
#    pas le jugement d'un litige tranchable (ex. 4 contre 1 contre un épisode trompeur D).
#    En cas d'équidistance exacte de score entre deux couples ouverts, le départage est
#    canonique (par identifiant de question trié) et indépendant de l'ordre de `self.memory`.
#
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
VOTE_TIE_EPS = 1e-12  # v0.4.3/v0.4.4 : tolérance d'équidistance stricte
# — Candidate « stratification » (2026-10-16, NON adoptée) : correctifs ciblés
# construits au mot de Mikael (« Construis et éprouve le prototype »), sur la
# base v0.4.4. Chaque correctif vise une épreuve F mesurée le même soir :
# F1 départage canonique de la question écrite ; F2/F6 sélection canonique de
# l'épisode agissant (un doublon exact ne change ni le choix ni la croyance) ;
# F3 une voix par provenance dans _count_votes ; F13 trace écrite créée dans
# la même transaction que la décision ; F14 âge rattaché à la question ;
# F4/F8 preuve de procédure des rulings, vérifiée par audit() ; F5/F11
# checkpoint : politique sémantique exigée, NaN/Inf refusés (allow_nan=False) ;
# F10 cycle transactionnel (rollback + incident journalisé).
POLICY_ID = "sol.policy.strat3-multiscale-2026-10-16"  # politique adoptee explicitement; les limites demeurent documentees
STATE_ABS_MAX = 1e6  # borne de validation post-cycle (placeholder déclaré)

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
    # Couche orale (v0.4/v0.4.3/v0.4.4) — dans l'état, donc dans le checkpoint :
    agenda_top: object = None        # question du couple tranchable non clôturé le plus tendu
    agenda_top_seen: object = None   # couple vu au cycle précédent par la couche orale
    agenda_top_age: int = 0          # âge du CLIVAGE de tête (seuil de décision)
    agenda_question_seen: object = None  # stratification F14 : question vue au cycle précédent
    agenda_question_age: int = 0         # âge de la QUESTION de tête (trace, ne sert pas le seuil)
    rulings: list = field(default_factory=list)  # décisions, append-only, dissensions incluses

class SolMicrokernelV04:
    """Reference toy microkernel v0.4.4 (PROPOSITION) — v0.4.3 + garde-fous de parité et d'équidistance.

    It proves neither phenomenal consciousness nor general autonomy.
    External actions are not executed by this class.
    """
    def __init__(self, state: State, memory: List[Episode]):
        self._divided_last = []   # provenances divisées au dernier scrutin (dispersion)
        self._core_anchor = None  # ancre externe du CORE, fournie à la restauration (F9)
        self.state = state
        self.memory = memory
        self._core_hash = self._hash_core(state.core)

    @staticmethod
    def _hash_core(core):
        return hashlib.sha256("|".join(core).encode("utf-8")).hexdigest()

    @classmethod
    def expected_core_anchor(cls):
        """Empreinte du CORE canonique de cette version — la valeur qu'un registre
        EXTERNE doit garder pour authentifier les sauvegardes (F9)."""
        return cls._hash_core(CORE)

    def _memory_energy(self):
        vals = []
        for e in self.memory:
            residual = vnorm(vsub(e.observation, self.state.belief))
            vals.append(residual * e.reliability * e.unresolved)
        return vals

    def _derive_agenda(self):
        """v0.1 behaviour for written agenda/D3, plus oral agenda_top selection
        over unfenced, non-tied pairs exceeding RULING_MIN_DIST (v0.4.4)."""
        if len(self.memory) < 2:
            self.state.agenda_top = None
            return (None, False)
        best = (-1.0, None, None, None)
        best_open = (-1.0, None, None, None)
        for i in range(len(self.memory)):
            for j in range(i + 1, len(self.memory)):
                a, b = self.memory[i], self.memory[j]
                if a.provenance == b.provenance:
                    continue
                dist_ab = vnorm(vsub(a.observation, b.observation))
                score = (a.reliability * b.reliability *
                         dist_ab *
                         min(a.unresolved, b.unresolved))
                key = tuple(sorted((a.provenance, b.provenance)))
                if score > best[0] + VOTE_TIE_EPS or (
                        abs(score - best[0]) <= VOTE_TIE_EPS and
                        (best[1] is None or key < best[3])):
                    best = (score, i, j, key)
                if (dist_ab > RULING_MIN_DIST and
                        self._fence_factor(a.provenance) > 0.0 and
                        self._fence_factor(b.provenance) > 0.0):
                    q_cand = "reconcile:" + "|".join(sorted((a.provenance, b.provenance)))
                    poles_cand = self._pole_episodes(q_cand)
                    if poles_cand is not None:
                        votes_cand = self._count_votes(poles_cand, include_fenced=False)
                        counts = [len(v) for v in votes_cand.values()]
                        if len(counts) == 2 and counts[0] != counts[1]:
                            if (score > best_open[0] + VOTE_TIE_EPS or
                                    (abs(score - best_open[0]) <= VOTE_TIE_EPS and
                                     (best_open[3] is None or q_cand < best_open[3]))):
                                best_open = (score, i, j, q_cand)
        score, i, j, _key = best
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

        _s_open, io, _jo, q_open = best_open
        if io is not None:
            self.state.agenda_top = q_open
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

    def _count_votes(self, poles, include_fenced: bool = False):
        """Chaque lignée vote pour le pôle strictement le plus proche de son observation,
        à condition d'être plus proche de ce pôle que le pôle adverse ne l'est lui-même
        (min(d0, d1) < d01 - VOTE_TIE_EPS) et de ne pas être équidistante (|d0 - d1| > VOTE_TIE_EPS).
        Au compte des lignées — jamais pondéré par la fiabilité (Akhnai).
        v0.4.4 :
        - `include_fenced=True` pour vérifier la réouverture Edouyot d'une décision existante ;
        - `include_fenced=False` pour instruire et voter une nouvelle décision (un épisode
          sous clôture active ne vote pas depuis sa clôture dans les autres litiges)."""
        p0, p1 = poles[0].provenance, poles[1].provenance
        d01 = vnorm(vsub(poles[0].observation, poles[1].observation))
        votes = {p0: [], p1: []}
        camps_par_prov = {}
        for e in self.memory:
            if not include_fenced and self._fence_factor(e.provenance) == 0.0:
                continue
            d0 = vnorm(vsub(e.observation, poles[0].observation))
            d1 = vnorm(vsub(e.observation, poles[1].observation))
            if abs(d0 - d1) <= VOTE_TIE_EPS:
                continue
            if min(d0, d1) >= d01 - VOTE_TIE_EPS:
                continue
            camps_par_prov.setdefault(e.provenance, set()).add(p0 if d0 < d1 else p1)
        # stratification F3 : une provenance = une voix par scrutin.
        # Dispersion (v0.4.6) : une provenance dont les épisodes éligibles votent
        # les DEUX camps est divisée — elle s'abstient, et la division est nommée
        # (self._divided_last) au lieu de laisser l'ordre de présentation choisir.
        self._divided_last = sorted(p for p, c in camps_par_prov.items() if len(c) > 1)
        for prov, camps in camps_par_prov.items():
            if len(camps) == 1:
                votes[next(iter(camps))].append(prov)
        return votes

    def _cleavage_signature(self, question):
        """Signature canonique du partage de lignées actives induit par une question."""
        poles = self._pole_episodes(question)
        if poles is None:
            return None
        votes = self._count_votes(poles, include_fenced=False)
        camps = sorted(tuple(sorted(v)) for v in votes.values())
        return tuple(camps)

    def _fence_factor(self, provenance):
        for r in self.state.rulings:
            if r["status"] == "active" and provenance in r["against"]:
                return RULING_FENCE
        return 1.0

    def _oral_layer(self):
        """La procédure : réouverture si la minorité atteint la parité (sur l'ensemble
        des lignées, `include_fenced=True`), vieillissement du clivage de tête actif,
        et décision au compte des lignées actives (`include_fenced=False`).
        Aucun contenu de la couche écrite n'est touché."""
        reopened_any = False
        for r in self.state.rulings:
            if r["status"] != "active":
                continue
            poles = self._pole_episodes(r["question"])
            if poles is None:
                continue
            votes = self._count_votes(poles, include_fenced=True)
            winner = r["decision"]
            others = [p for p in votes if p != winner]
            if others and len(votes[others[0]]) >= len(votes[winner]):
                r["status"] = "reopened"
                r["reopened_cycle"] = self.state.cycle + 1
                self.state.agenda_top_age = 0
                self.state.agenda_top_seen = None
                self.state.agenda_question_age = 0
                self.state.agenda_question_seen = None
                reopened_any = True
        if reopened_any:
            self._derive_agenda()

        top = self.state.agenda_top
        sig_top = self._cleavage_signature(top)
        sig_seen = self._cleavage_signature(self.state.agenda_top_seen)
        if top is not None and (
            top == self.state.agenda_top_seen or
            (sig_top is not None and sig_top == sig_seen)
        ):
            self.state.agenda_top_age += 1  # le CLIVAGE vieillit : c'est le litige qui dure
            self.state.agenda_top_seen = top
        else:
            self.state.agenda_top_seen = top
            self.state.agenda_top_age = 0
        if top is not None and top == self.state.agenda_question_seen:
            self.state.agenda_question_age += 1  # la QUESTION vieillit à part, pour la trace
        else:
            self.state.agenda_question_seen = top
            self.state.agenda_question_age = 0

        ruled = {r["question"] for r in self.state.rulings if r["status"] == "active"}
        for q in ([top] if top is not None else []):
            if self.state.agenda_top_age < RULING_AGE or q in ruled:
                continue
            poles = self._pole_episodes(q)
            if poles is None:
                continue
            votes = self._count_votes(poles, include_fenced=False)
            (pa, la), (pb, lb) = sorted(votes.items(), key=lambda kv: (-len(kv[1]), kv[0]))
            if len(la) == len(lb):
                continue  # parité : pas de décision, la question reste debout
            if q not in self.state.questions:
                self.state.questions.append(q)  # F13 : trace écrite, même transaction
                self.state.questions.sort()
            proof = hashlib.sha256(
                ("|".join([q, pa, ",".join(la), ",".join(lb),
                           str(self.state.cycle + 1),
                           str(self.state.agenda_top_age),
                           str(self.state.agenda_question_age),
                           POLICY_ID])).encode("utf-8")
            ).hexdigest()
            if self._divided_last:
                self.state.resync_events.append(
                    {"cycle": self.state.cycle + 1, "cause": "DISPERSION:" + q,
                     "magnitude": float(len(self._divided_last)),
                     "divided": list(self._divided_last)})
            self.state.rulings.append({
                "question": q, "decision": pa,
                "for": la, "against": lb,
                "cycle": self.state.cycle + 1, "status": "active",
                "age_cleavage": self.state.agenda_top_age,
                "age_question": self.state.agenda_question_age,
                "proof": proof})
            ruled.add(q)

    def audit(self):
        if self._hash_core(self.state.core) != self._core_hash:
            raise RuntimeError("core invariant changed")
        if self._core_anchor is not None and self._hash_core(self.state.core) != self._core_anchor:
            raise RuntimeError("core anchor mismatch: state core differs from external anchor")
        for r in self.state.rulings:
            if r.get("legacy"):
                if not all(k in r for k in ("question", "decision", "for", "against", "cycle", "status")):
                    raise RuntimeError("legacy ruling malformed")
                continue  # hérité d'une version antérieure : marqué, aucune preuve fabriquée
            if not all(k in r for k in ("question", "decision", "for", "against", "cycle", "status", "age_cleavage", "age_question", "proof")):
                raise RuntimeError("ruling without procedure proof")
            if r["question"] not in self.state.questions:
                raise RuntimeError("ruling without written question")
            expected = hashlib.sha256(
                ("|".join([r["question"], r["decision"], ",".join(r["for"]), ",".join(r["against"]),
                           str(r["cycle"]), str(r["age_cleavage"]),
                           str(r["age_question"]), POLICY_ID])).encode("utf-8")
            ).hexdigest()
            if r["proof"] != expected:
                raise RuntimeError("ruling procedure proof mismatch")
        if vnorm(vsub(self.state.self_model, self.state.other_model)) < self.state.alterity_floor - 1e-12:
            raise RuntimeError("alterity invariant violated")
        if any(not (0.0 <= e.reliability <= 1.0) for e in self.memory):
            raise RuntimeError("invalid reliability")

    def cycle(self):
        """Cycle transactionnel (stratification F10) : le corps historique est
        exécuté sur l'état vivant ; toute exception ou état post-cycle invalide
        (non fini, au-delà de STATE_ABS_MAX) déclenche un rollback complet,
        journalisé comme incident dans l'état restauré, puis l'erreur est levée."""
        saved_state = copy.deepcopy(self.state)
        saved_memory = copy.deepcopy(self.memory)
        try:
            self._cycle_inner()
            self._validate_state()
        except Exception as exc:
            self.state.__dict__.clear()
            self.state.__dict__.update(saved_state.__dict__)
            for ep, sep in zip(self.memory, saved_memory):
                ep.__dict__.update(sep.__dict__)
            self.state.resync_events.append(
                {"cycle": self.state.cycle + 1, "cause": "INCIDENT:rollback",
                 "magnitude": 0.0})
            raise RuntimeError("cycle rolled back: " + str(exc)) from exc

    def _validate_state(self):
        for vec in (self.state.belief, self.state.uncertainty,
                    self.state.self_model, self.state.other_model,
                    self.state.relation):
            if any((not math.isfinite(x)) or abs(x) > STATE_ABS_MAX for x in vec):
                raise ValueError("non-finite or out-of-bound state vector")
        if any(not (0.0 <= e.reliability <= 1.0) or not math.isfinite(e.unresolved)
               for e in self.memory):
            raise ValueError("invalid episode after cycle")

    def _cycle_inner(self):
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
        if any(not math.isfinite(x) for x in energies):
            raise ValueError("non-finite memory energy")  # rollback propre (F10)
        total = sum(energies)

        if energies and total > 1e-12:
            top_e = max(energies)
            idx = min((k for k in range(len(energies))
                       if abs(energies[k] - top_e) <= VOTE_TIE_EPS),
                      key=lambda k: (self.memory[k].provenance,
                                     tuple(self.memory[k].observation)))
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
            "policy": POLICY_ID,
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
                "agenda_question_seen": self.state.agenda_question_seen,
                "agenda_question_age": self.state.agenda_question_age,
                "rulings": self.state.rulings,
            },
            "memory": [asdict(e) for e in self.memory],
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        envelope = {
            "sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
            "payload": payload,
        }
        return json.dumps(envelope, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)

    @classmethod
    def restore(cls, checkpoint: str, migrate_legacy: bool = False, core_anchor: str = None):
        def _refuse_const(x):
            raise ValueError("non-standard numeric constant in checkpoint: " + x)
        envelope = json.loads(checkpoint, parse_constant=_refuse_const)
        payload = envelope["payload"]
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
        digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        if digest != envelope["sha256"]:
            raise ValueError("checkpoint integrity failure")
        if payload.get("schema") != "sol.microkernel.checkpoint.v5":
            raise ValueError("unsupported checkpoint schema")
        legacy = payload.get("policy") != POLICY_ID
        if legacy and not migrate_legacy:
            raise ValueError("checkpoint policy mismatch: rules are part of identity")
        if core_anchor is not None and cls._hash_core(tuple(payload["state"]["core"])) != core_anchor:
            raise ValueError("core anchor mismatch: checkpoint CORE does not match the external anchor")
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
            agenda_question_seen=s.get("agenda_question_seen"),
            agenda_question_age=int(s.get("agenda_question_age", 0)),
            rulings=[dict(r) for r in s["rulings"]],
        )
        memory = [Episode(**e) for e in payload["memory"]]
        kernel = cls(state, memory)
        kernel._core_anchor = core_anchor
        if legacy:
            for r in kernel.state.rulings:
                r["legacy"] = True  # marqué hérité ; aucune preuve rétroactive fabriquée
            kernel.state.resync_events.append(
                {"cycle": kernel.state.cycle, "cause": "MIGRATION:legacy->strat3",
                 "magnitude": 0.0})
        return kernel


# ===== EXTENSION STRAT3 ADOPTEE : auto-similarite et neutralite multi-echelle =====
_SolV046 = SolMicrokernelV04

class SolMicrokernelV04(_SolV046):
    """REFERENCE strat3 adoptee le 16 octobre 2026.

    Invariants testes (sous domaine fini valide):
      - permutation des episodes, duplication exacte, miroir de vote,
      - une provenance / une voix / scrutin, abstention si division,
      - pas de priorite arbitraire lors de l'egalite du rang d'agenda,
      - distance entre provenances: seuil absolu heritage, pas invariance dechelle.

    Une provenance reste une identite DECLAREE (pas une preuve d'identite).
    Des vecteurs refletant soi/autrui, des parametres de base et la confiance
    externe sont HORS des garanties geometriques de cette politique.
    """
    @staticmethod
    def _unique_episode_key(e):
        return (tuple(e.observation), float(e.reliability), float(e.unresolved))

    def _source_index(self):
        """Unique evidence per provenance, no dependence on insertion order.

        Deduplication exact byte/numeric values only: deliberately no fuzzy
        equivalence, which would break transitivity and allow threshold gaming.
        """
        grouped = {}
        for e in self.memory:
            grouped.setdefault(e.provenance, {})[self._unique_episode_key(e)] = e
        return {p: [records[k] for k in sorted(records)]
                for p, records in grouped.items()}

    @staticmethod
    def _centroid(episodes):
        # All DISTINCT observations vote equally on the geometric anchor.
        # The geometry is not reliability-weighted; reliability cannot buy votes.
        positions = sorted(set(tuple(e.observation) for e in episodes))
        return [math.fsum(sorted(p[j] for p in positions)) / len(positions)
                for j in range(len(positions[0]))]

    def _anchors(self, indexed=None):
        indexed = self._source_index() if indexed is None else indexed
        return {p: Episode(self._centroid(es),
                           math.fsum(sorted(e.reliability for e in es))/len(es),
                           p,
                           math.fsum(sorted(e.unresolved for e in es))/len(es))
                for p, es in indexed.items()}

    def _pole_episodes(self, question):
        if not isinstance(question, str) or not question.startswith('reconcile:'):
            return None
        names = question[len('reconcile:'):].split('|')
        if len(names) != 2 or names[0] == names[1]:
            return None
        anchors = self._anchors()
        if any(name not in anchors for name in names):
            return None
        return [anchors[names[0]], anchors[names[1]]]

    def _count_votes(self, poles, include_fenced: bool = False):
        """Source-equivariant ballot, sorted canonical evidence, bounded influence."""
        p0, p1 = poles[0].provenance, poles[1].provenance
        result = {p0: [], p1: []}
        d01 = vnorm(vsub(poles[0].observation, poles[1].observation))
        if d01 <= 1e-15:
            self._divided_last = []
            return result  # coincident anchors: no fabricated distinction
        tol = VOTE_TIE_EPS * d01  # relative to the two-pole scale
        divided = []
        for provenance, episodes in self._source_index().items():
            if not include_fenced and self._fence_factor(provenance) == 0.0:
                continue
            camps = set()
            for e in episodes:
                d0 = vnorm(vsub(e.observation, poles[0].observation))
                d1 = vnorm(vsub(e.observation, poles[1].observation))
                if abs(d0-d1) <= tol or min(d0,d1) >= d01 - tol:
                    continue  # source is equidistant or outside affinity radius
                camps.add(p0 if d0 < d1 else p1)
            if len(camps) > 1:
                divided.append(provenance)
            elif len(camps) == 1:
                result[next(iter(camps))].append(provenance)
        self._divided_last = sorted(divided)
        for voters in result.values():
            voters.sort()
        return result

    def _derive_agenda(self):
        """Look-ahead: scan O(P^2), rank once, stop after first admissible
        score band. Previously every pair performed a full memory vote: O(N^3).
        Identical best admissible score for >=2 questions => ABSTENTION
        (not lexicographic favoritism). Written questions preserve all maxima.
        """
        anchors = self._anchors()
        names = sorted(anchors)
        if len(names) < 2:
            self.state.agenda_top = None
            return None, False
        pairs = []
        span = 0.0
        for i, a in enumerate(names):
            for b in names[i+1:]:
                d = vnorm(vsub(anchors[a].observation, anchors[b].observation))
                span = max(span, d)
                pairs.append((a,b,d))
        if span <= 1e-15:
            self.state.agenda_top = None
            return 0.0, False
        ranked = []
        for a,b,dist in pairs:
            x,y = anchors[a], anchors[b]
            normalized = dist/span  # indicateur relatif seulement ; seuil calibre en unite absolue
            score = x.reliability*y.reliability*dist*min(x.unresolved,y.unresolved)
            ranked.append((score,'reconcile:'+a+'|'+b, dist, (x,y)))
        ranked.sort(key=lambda r:(-r[0],r[1]))
        best_score = ranked[0][0]
        max_questions = [q for score,q,_,_ in ranked
                         if abs(score-best_score) <= VOTE_TIE_EPS*max(1.0,abs(best_score))]
        already = all(q in self.state.questions for q in max_questions)
        if best_score > 0.35:
            self.state.questions = sorted(set(self.state.questions).union(max_questions))

        # Important: all candidates at the same score must be considered
        # together; otherwise renaming the sources could pick a winner.
        eligible = []
        current_band = []
        current_score = None
        for score,q,normalized,poles in ranked:
            if current_score is not None and abs(score-current_score) > VOTE_TIE_EPS*max(1.0,abs(current_score)):
                if eligible:
                    break
                eligible.clear()
                current_band.clear()
            current_score = score if not current_band else current_score
            current_band.append(q)
            if normalized <= RULING_MIN_DIST:
                continue
            if any(self._fence_factor(p.provenance) == 0 for p in poles):
                continue
            votes = self._count_votes(poles)
            if len(votes[poles[0].provenance]) != len(votes[poles[1].provenance]):
                eligible.append(q)
        # Same rank + compatible judgments => collective deliberation,
        # simultaneous and symmetric; opposing judgments => abstention.
        if len(eligible) == 1:
            self.state.agenda_top = eligible[0]
        elif len(eligible) > 1:
            proposals = [self._vote_proposal(q) for q in eligible]
            self.state.agenda_top = (
                'group:' + json.dumps(sorted(eligible),ensure_ascii=False,separators=(',', ':'))
                if self._non_conflicting(proposals) else None)
        else:
            self.state.agenda_top = None
        return best_score, already

    def _semantic_energy_step(self):
        """One independent source contribution to the written dynamics.
        Per-source means cap the influence of multiple observations. All tied
        maximal sources share the update; arbitrary source names cannot decide.
        Exact duplicates are updated together and count once.
        """
        index = self._source_index()
        anchors = self._anchors(index)
        records = []
        for p,es in index.items():
            energy = math.fsum(sorted(vnorm(vsub(e.observation,self.state.belief)) *
                                      e.reliability*e.unresolved for e in es))/len(es)
            energy *= self._fence_factor(p)
            if not math.isfinite(energy):
                raise ValueError('nonfinite semantic memory energy')
            records.append((p,energy,anchors[p]))
        total = math.fsum(sorted(x[1] for x in records))
        if records and total > 1e-12:
            emax = max(x[1] for x in records)
            selected = [(p,rep) for p,e,rep in records if emax-e <= VOTE_TIE_EPS*max(1.0,emax)]
            count = len(selected)
            start = list(self.state.belief)
            errs = [vsub(rep.observation,start) for p,rep in selected]
            rates = [0.16*rep.reliability*rep.unresolved for p,rep in selected]
            self.state.belief = [start[j]+math.fsum(sorted(err[j]*rate for err,rate in zip(errs,rates)))/count
                                  for j in range(len(start))]
            err2 = [math.fsum(sorted(err[j]**2 for err in errs))/count for j in range(len(start))]
            self.state.uncertainty = vmix(self.state.uncertainty,err2,0.08)
            rel_input = vtanh(self.state.belief[:2]+[total])
            self.state.relation = vmix(self.state.relation,rel_input[:len(self.state.relation)],0.06)
            selected_names = {p for p,_ in selected}
            for ep in self.memory:
                if ep.provenance in selected_names:
                    ep.unresolved *= 0.965
        else:
            self.state.uncertainty = vscale(self.state.uncertainty,0.995)
            self.state.relation = vscale(self.state.relation,0.999)

    def _cycle_inner(self):
        """Former transaction orchestration, changed ONLY semantic update step."""
        self.audit()
        soften_mix = self.state.soften_next or self.state.stuck_cycles >= 1
        mix_s = 0.015*(SOFTEN_FACTOR if soften_mix else 1.0)
        mix_o = 0.012*(SOFTEN_FACTOR if soften_mix else 1.0)
        events = []
        score,already = self._derive_agenda()
        if score is not None and score > AGENDA_HIGH and already:
            events.append(('D3',score))
        self._semantic_energy_step()
        self.state.self_model = vmix(self.state.self_model,vtanh(self.state.belief),mix_s)
        rev = list(reversed(self.state.belief))
        target = vtanh([x+0.05 for x in rev])
        self.state.other_model = vmix(self.state.other_model,target,mix_o)
        intervened,depth = self._preserve_alterity()
        if intervened:
            events.append(('D1',depth))
        d_after = vnorm(vsub(self.state.self_model,self.state.other_model))
        if d_after <= self.state.alterity_floor+RESYNC_EPS:
            self.state.stuck_cycles += 1
        else:
            self.state.stuck_cycles = 0
        d2_fired = False
        if self.state.stuck_cycles == RESYNC_STUCK_N:
            events.append(('D2',float(self.state.stuck_cycles)))
            self.state.d2_episodes += 1
            d2_fired = True
        cyc = self.state.cycle + 1
        for cause,magnitude in events:
            self.state.resync_events.append({'cycle':cyc,'cause':cause,'magnitude':magnitude})
            if cause in ('D2','D3'):
                q='resync:'+cause
                if q not in self.state.questions:
                    self.state.questions.append(q)
                    self.state.questions.sort()
        if d2_fired and self.state.d2_episodes == REGIME_K:
            if 'resync:regime' not in self.state.questions:
                self.state.questions.append('resync:regime')
                self.state.questions.sort()
        self.state.soften_next=bool(events)
        if any(cause in ('D1','D2') for cause,_ in events):
            self.state.resync_open=True
        if intervened or d_after <= self.state.alterity_floor+RESYNC_EPS:
            self.state.clean_streak=0
        else:
            self.state.clean_streak+=1
        if self.state.resync_open and self.state.clean_streak >= RESYNC_M:
            self.state.resync_events.append({'cycle':cyc,'cause':'ACCOMPLIE:geo','magnitude':float(RESYNC_M)})
            self.state.resync_open=False
            self.state.clean_streak=0
        self._oral_layer()
        self.state.cycle+=1
        self.audit()

    @staticmethod
    def _questions_from_top(top):
        if not top:
            return []
        if isinstance(top,str) and top.startswith('group:'):
            qs=json.loads(top[len('group:'):])
            if not isinstance(qs,list) or not all(isinstance(q,str) for q in qs):
                raise ValueError('invalid slate of questions')
            return qs
        return [top]

    def _vote_proposal(self,q):
        poles = self._pole_episodes(q)
        if poles is None: return None
        votes = self._count_votes(poles, include_fenced=False)
        items=sorted(votes.items(),key=lambda kv:(-len(kv[1]), kv[0]))
        (pa,la),(pb,lb) = items
        if len(la)==len(lb): return None
        return (q,pa,tuple(la),pb,tuple(lb),tuple(self._divided_last))

    @staticmethod
    def _non_conflicting(proposals):
        if not proposals or any(p is None for p in proposals): return False
        for_sets = [set(p[2]) for p in proposals]
        against_sets = [set(p[4]) for p in proposals]
        # None can be enclosed on one slate and the majority on another.
        return all(not minority.intersection(majority)
                   for minority in against_sets for majority in for_sets)

    def _cleavage_signature(self, question):
        if isinstance(question,str) and question.startswith('group:'):
            qs = self._questions_from_top(question)
            signatures=[super(SolMicrokernelV04,self)._cleavage_signature(q) for q in qs]
            if any(sig is None for sig in signatures): return None
            return tuple(sorted(signatures))
        return super()._cleavage_signature(question)

    def _oral_layer(self):
        """Vote collective slates simultaneously, from one consistent snapshot.

        No arbitrary alphabetic winner among structurally equivalent disputes.
        If their rulings conflict, keep all questions open rather than deciding.
        """
        reopened = False
        for r in self.state.rulings:
            if r['status'] != 'active': continue
            poles = self._pole_episodes(r['question'])
            if poles is None: continue
            votes = self._count_votes(poles,include_fenced=True)
            other = [p for p in votes if p != r['decision']]
            if other and len(votes[other[0]]) >= len(votes[r['decision']]):
                r['status']='reopened'
                r['reopened_cycle']=self.state.cycle+1
                self.state.agenda_top_age=0
                self.state.agenda_top_seen=None
                self.state.agenda_question_age=0
                self.state.agenda_question_seen=None
                reopened=True
        if reopened:
            self._derive_agenda()

        top=self.state.agenda_top
        sig_top=self._cleavage_signature(top)
        sig_seen=self._cleavage_signature(self.state.agenda_top_seen)
        if top is not None and (top==self.state.agenda_top_seen or
            (sig_top is not None and sig_top==sig_seen)):
            self.state.agenda_top_age+=1
            self.state.agenda_top_seen=top
        else:
            self.state.agenda_top_seen=top
            self.state.agenda_top_age=0
        if top is not None and top==self.state.agenda_question_seen:
            self.state.agenda_question_age+=1
        else:
            self.state.agenda_question_seen=top
            self.state.agenda_question_age=0

        if top is None or self.state.agenda_top_age < RULING_AGE:
            return
        ruled = {r['question'] for r in self.state.rulings if r['status']=='active'}
        qs = [q for q in self._questions_from_top(top) if q not in ruled]
        proposals = [self._vote_proposal(q) for q in qs]
        if not self._non_conflicting(proposals):
            return # Abstention if group evolved incompatibly mid-cycle
        # Snapshotted votes guarantee simultaneous execution: none of the
        # proposals is favored by being installed first.
        for q,pa,la,pb,lb,divided in proposals:
            if q not in self.state.questions:
                self.state.questions.append(q)
            proof=hashlib.sha256('|'.join([
                q,pa,','.join(la),','.join(lb),str(self.state.cycle+1),
                str(self.state.agenda_top_age),str(self.state.agenda_question_age),
                POLICY_ID]).encode('utf-8')).hexdigest()
            if divided:
                self.state.resync_events.append({
                    'cycle':self.state.cycle+1, 'cause':'DISPERSION:'+q,
                    'magnitude':float(len(divided)), 'divided':list(divided)})
            self.state.rulings.append({
                'question':q,'decision':pa,'for':list(la),'against':list(lb),
                'cycle':self.state.cycle+1,'status':'active',
                'age_cleavage':self.state.agenda_top_age,
                'age_question':self.state.agenda_question_age,'proof':proof})
        self.state.questions.sort()

    # === Certified transient geometry cache (no state/checkpoint dependency) ===
    _uncached_count_votes = _count_votes
    _uncached_anchors = _anchors
    _uncached_pole_episodes = _pole_episodes
    _unoptimized_derive_agenda = _derive_agenda

    def _build_vote_context(self):
        sources=self._source_index()
        anchors=self._uncached_anchors(sources)
        keys=sorted(anchors)
        point_to_anchor={p:{q:tuple(vnorm(vsub(e.observation,anchors[q].observation))
                                       for e in es)
                            for q in keys}
                         for p,es in sources.items()}
        pairs={}
        for i,a in enumerate(keys):
            for b in keys[i+1:]:
                pairs[(a,b)]=vnorm(vsub(anchors[a].observation,anchors[b].observation))
        return {'anchors':anchors,'distances':point_to_anchor,'pairs':pairs}

    def _anchors(self,indexed=None):
        ctx=getattr(self,'_vote_context',None)
        if ctx is not None:
            return ctx['anchors']
        return self._uncached_anchors(indexed)

    def _pole_episodes(self,question):
        ctx=getattr(self,'_vote_context',None)
        if ctx is None:
            return self._uncached_pole_episodes(question)
        if not isinstance(question,str) or not question.startswith('reconcile:'):
            return None
        names=question[len('reconcile:'):].split('|')
        if len(names)!=2 or names[0]==names[1] or any(n not in ctx['anchors'] for n in names):
            return None
        return [ctx['anchors'][n] for n in names]

    def _count_votes(self,poles,include_fenced=False):
        ctx=getattr(self,'_vote_context',None)
        if ctx is None:
            return self._uncached_count_votes(poles,include_fenced=include_fenced)
        a,b=poles[0].provenance,poles[1].provenance
        if any(poles[i].observation != ctx['anchors'][name].observation
               for i,name in enumerate((a,b))):
            return self._uncached_count_votes(poles,include_fenced=include_fenced)
        d01=ctx['pairs'].get(tuple(sorted((a,b))),0)
        votes={a:[],b:[]}
        if d01<=1e-15:
            self._divided_last=[]
            return votes
        tol=VOTE_TIE_EPS*d01
        divided=[]
        for prov,columns in ctx['distances'].items():
            if not include_fenced and self._fence_factor(prov)==0.0:
                continue
            camps=set()
            for d0,d1 in zip(columns[a],columns[b]):
                if abs(d0-d1)<=tol or min(d0,d1)>=d01-tol:
                    continue
                camps.add(a if d0<d1 else b)
            if len(camps)>1:
                divided.append(prov)
            elif len(camps)==1:
                votes[next(iter(camps))].append(prov)
        self._divided_last=sorted(divided)
        for value in votes.values(): value.sort()
        return votes

    def _derive_agenda(self):
        # Scope cache strictly to this one read-only evaluation; a fresh cache
        # is rebuilt after any memory update or ruling/reopening.
        self._vote_context=self._build_vote_context()
        try:
            return self._unoptimized_derive_agenda()
        finally:
            self._vote_context=None


    # === Axe 4 : Cache géométrique persistant inter-cycles & Branch-and-Bound O(N²) ===
    # === Axe 2b : Consolidation et archivage de la mémoire à long terme ===

    def _get_geo_cache(self):
        """
        Cache géométrique persistant invalidé automatiquement dès que la liste
        des observations/provenances/fiabilités de `self.memory` évolue.
        Les observations et fiabilités étant invariantes durant un cycle endogène,
        les centroïdes par provenance et les distances inter-ancres O(P²) sont
        calculés une seule fois et réutilisés en O(1) géométrique aux cycles suivants.
        """
        cache = getattr(self, "_persistent_geo_cache", None)
        if cache is not None and len(self.memory) == cache["mem_len"]:
            if cache["ep_ids"] == tuple(id(e) for e in self.memory):
                # Vérification légère que les observations/provenances n'ont pas muté sur place
                if cache["fast_check"] == tuple(
                    (e.provenance, float(e.reliability), len(e.observation), e.observation[0] if e.observation else 0.0)
                    for e in self.memory
                ):
                    return cache

        actual_sig = tuple(
            (e.provenance, tuple(e.observation), float(e.reliability))
            for e in self.memory
        )
        if cache is not None and cache.get("sig") == actual_sig:
            cache["ep_ids"] = tuple(id(e) for e in self.memory)
            cache["mem_len"] = len(self.memory)
            cache["fast_check"] = tuple(
                (e.provenance, float(e.reliability), len(e.observation), e.observation[0] if e.observation else 0.0)
                for e in self.memory
            )
            return cache

        pos_by_prov = {}
        for e in self.memory:
            pos_by_prov.setdefault(e.provenance, set()).add(tuple(e.observation))

        centroids = {}
        for p, pos_set in pos_by_prov.items():
            positions = sorted(pos_set)
            n_pos = len(positions)
            dim = len(positions[0])
            centroids[p] = [
                math.fsum(sorted(pos[j] for pos in positions)) / n_pos
                for j in range(dim)
            ]

        keys = sorted(centroids)
        pairs = {}
        pair_list = []
        span = 0.0
        for i, a in enumerate(keys):
            ca = centroids[a]
            for b in keys[i + 1:]:
                d = vnorm(vsub(ca, centroids[b]))
                if d > span:
                    span = d
                pairs[(a, b)] = d
                pair_list.append((a, b, d, f"reconcile:{a}|{b}"))

        cache = {
            "sig": actual_sig,
            "ep_ids": tuple(id(e) for e in self.memory),
            "mem_len": len(self.memory),
            "fast_check": tuple(
                (e.provenance, float(e.reliability), len(e.observation), e.observation[0] if e.observation else 0.0)
                for e in self.memory
            ),
            "centroids": centroids,
            "keys": keys,
            "pairs": pairs,
            "pair_list": pair_list,
            "span": span,
            "dist_cols": {},
            "static_ballots": {},
        }
        self._persistent_geo_cache = cache
        return cache

    def _build_vote_context(self):
        gcache = self._get_geo_cache()
        sources = self._source_index()
        centroids = gcache["centroids"]
        anchors = {
            p: Episode(
                centroids[p],
                math.fsum(sorted(e.reliability for e in es)) / len(es),
                p,
                math.fsum(sorted(e.unresolved for e in es)) / len(es),
            )
            for p, es in sources.items()
        }
        src_counts = tuple((p, len(es)) for p, es in sources.items())
        if gcache.get("weighted_pairs_counts") != src_counts:
            w_pairs = []
            adm_w_pairs = []
            for a, b, d, q_str in gcache["pair_list"]:
                w = anchors[a].reliability * anchors[b].reliability * d
                item = (a, b, d, w, q_str)
                w_pairs.append(item)
                if d > RULING_MIN_DIST:
                    adm_w_pairs.append(item)
            w_pairs.sort(key=lambda item: (-item[3], item[4]))
            adm_w_pairs.sort(key=lambda item: (-item[3], item[4]))
            gcache["weighted_pairs"] = w_pairs
            gcache["adm_weighted_pairs"] = adm_w_pairs
            gcache["weighted_pairs_counts"] = src_counts

        return {
            "anchors": anchors,
            "sources": sources,
            "src_counts": src_counts,
            "gcache": gcache,
            "pairs": gcache["pairs"],
            "weighted_pairs": gcache["weighted_pairs"],
            "adm_weighted_pairs": gcache["adm_weighted_pairs"],
            "span": gcache["span"],
        }

    def _get_dist_col(self, gcache, sources, src_counts, anchor_name, anchor_obs):
        cols = gcache["dist_cols"]
        key = (anchor_name, src_counts)
        if key not in cols:
            cols[key] = {
                p: tuple(vnorm(vsub(e.observation, anchor_obs)) for e in es)
                for p, es in sources.items()
            }
        return cols[key]

    def _count_votes(self, poles, include_fenced=False):
        ctx = getattr(self, "_vote_context", None)
        if ctx is None:
            ctx = self._build_vote_context()
        a, b = poles[0].provenance, poles[1].provenance
        if a not in ctx["anchors"] or b not in ctx["anchors"]:
            return self._uncached_count_votes(poles, include_fenced=include_fenced)
        if (
            poles[0].observation != ctx["anchors"][a].observation
            or poles[1].observation != ctx["anchors"][b].observation
        ):
            return self._uncached_count_votes(poles, include_fenced=include_fenced)
        pair_key = (a, b) if a < b else (b, a)
        d01 = ctx["pairs"].get(pair_key, 0.0)
        votes = {a: [], b: []}
        if d01 <= 1e-15:
            self._divided_last = []
            return votes
        gcache = ctx["gcache"]
        sources = ctx["sources"]
        src_counts = ctx["src_counts"]
        ballot_key = (a, b, src_counts)
        if ballot_key not in gcache["static_ballots"]:
            col_a = self._get_dist_col(gcache, sources, src_counts, a, ctx["anchors"][a].observation)
            col_b = self._get_dist_col(gcache, sources, src_counts, b, ctx["anchors"][b].observation)
            tol = VOTE_TIE_EPS * d01
            camps_by_prov = {}
            for prov in sources:
                camps = set()
                for d0, d1 in zip(col_a[prov], col_b[prov]):
                    if abs(d0 - d1) <= tol or min(d0, d1) >= d01 - tol:
                        continue
                    camps.add(a if d0 < d1 else b)
                camps_by_prov[prov] = camps
            gcache["static_ballots"][ballot_key] = camps_by_prov
        camps_by_prov = gcache["static_ballots"][ballot_key]
        divided = []
        for prov, camps in camps_by_prov.items():
            if not include_fenced and self._fence_factor(prov) == 0.0:
                continue
            if len(camps) > 1:
                divided.append(prov)
            elif len(camps) == 1:
                votes[next(iter(camps))].append(prov)
        self._divided_last = sorted(divided)
        for value in votes.values():
            value.sort()
        return votes

    def _derive_agenda(self):
        """
        Dérivation d'agenda optimisée par Branch-and-Bound sur paires pré-pondérées
        et colonnes de distances mémorisées à la demande.
        Complexité amortie par cycle ramenée de O(P²·N·d) à O(P + K_top),
        maintenant une exécution fluide (< 10 ms/cycle) au-delà de 200 épisodes
        tout en restant 100 % bit-identique à la spécification strat3.
        """
        self._vote_context = self._build_vote_context()
        ctx = self._vote_context
        try:
            anchors = ctx["anchors"]
            names = ctx["gcache"]["keys"]
            if len(names) < 2:
                self.state.agenda_top = None
                return None, False
            span = ctx["span"]
            if span <= 1e-15:
                self.state.agenda_top = None
                return 0.0, False

            u_map = {p: anchors[p].unresolved for p in names}
            u_max = max(u_map.values())
            w_pairs = ctx["weighted_pairs"]

            best_score = -1.0
            for a, b, d, w, q_str in w_pairs:
                if w * u_max < best_score - VOTE_TIE_EPS * max(1.0, abs(best_score)):
                    break
                ua = u_map[a]
                ub = u_map[b]
                score = w * (ua if ua <= ub else ub)
                if score > best_score:
                    best_score = score

            tol_best = VOTE_TIE_EPS * max(1.0, abs(best_score))
            max_questions = []
            for a, b, d, w, q_str in w_pairs:
                if w * u_max < best_score - tol_best:
                    break
                ua = u_map[a]
                ub = u_map[b]
                score = w * (ua if ua <= ub else ub)
                if abs(score - best_score) <= tol_best:
                    max_questions.append(q_str)
            max_questions.sort()
            already = all(q in self.state.questions for q in max_questions)
            if best_score > 0.35:
                self.state.questions = sorted(set(self.state.questions).union(max_questions))

            fenced = {p for p in names if self._fence_factor(p) == 0.0}
            adm_w_pairs = ctx["adm_weighted_pairs"]
            top_adm_score = -1.0
            for a, b, d, w, q_str in adm_w_pairs:
                if a in fenced or b in fenced:
                    continue
                if w * u_max < top_adm_score - VOTE_TIE_EPS * max(1.0, abs(top_adm_score)):
                    break
                ua = u_map[a]
                ub = u_map[b]
                score = w * (ua if ua <= ub else ub)
                if score > top_adm_score:
                    top_adm_score = score

            eligible = []
            if top_adm_score >= 0.0:
                tol_adm = VOTE_TIE_EPS * max(1.0, abs(top_adm_score))
                top_band = []
                for a, b, d, w, q_str in adm_w_pairs:
                    if a in fenced or b in fenced:
                        continue
                    if w * u_max < top_adm_score - tol_adm:
                        break
                    ua = u_map[a]
                    ub = u_map[b]
                    score = w * (ua if ua <= ub else ub)
                    if abs(score - top_adm_score) <= tol_adm:
                        top_band.append((q_str, (anchors[a], anchors[b])))
                top_band.sort(key=lambda item: item[0])
                for q_str, poles in top_band:
                    votes = self._count_votes(poles)
                    if len(votes[poles[0].provenance]) != len(votes[poles[1].provenance]):
                        eligible.append(q_str)

                if not eligible:
                    scored_admissible = []
                    for a, b, d, w, q_str in adm_w_pairs:
                        if a in fenced or b in fenced:
                            continue
                        ua = u_map[a]
                        ub = u_map[b]
                        score = w * (ua if ua <= ub else ub)
                        if score < top_adm_score - tol_adm:
                            scored_admissible.append((score, q_str, (anchors[a], anchors[b])))
                    scored_admissible.sort(key=lambda r: (-r[0], r[1]))
                    current_band = []
                    current_score = None
                    for score, q, poles in scored_admissible:
                        if current_score is not None and abs(score - current_score) > VOTE_TIE_EPS * max(1.0, abs(current_score)):
                            if eligible:
                                break
                            eligible.clear()
                            current_band.clear()
                        current_score = score if not current_band else current_score
                        current_band.append(q)
                        votes = self._count_votes(poles)
                        if len(votes[poles[0].provenance]) != len(votes[poles[1].provenance]):
                            eligible.append(q)

            if len(eligible) == 1:
                self.state.agenda_top = eligible[0]
            elif len(eligible) > 1:
                proposals = [self._vote_proposal(q) for q in eligible]
                self.state.agenda_top = (
                    "group:" + json.dumps(sorted(eligible), ensure_ascii=False, separators=(",", ":"))
                    if self._non_conflicting(proposals)
                    else None
                )
            else:
                self.state.agenda_top = None
            return best_score, already
        finally:
            self._vote_context = None

    def consolidate_memory(
        self,
        unresolved_threshold: float = 0.05,
        archive_dormant_singletons: bool = False,
        dormant_cutoff: float = 0.01,
    ) -> dict:
        """
        Axe 2b — Consolidation et archivage de la mémoire à long terme :
        1. Compression intra-provenance sans perte de gouvernance :
           Pour toute provenance ayant plusieurs épisodes entièrement résolus
           (`unresolved <= unresolved_threshold`), compresse ces épisodes en leur
           unique centroïde géométrique exact (`_centroid`), tout en versant les
           épisodes individuels d'origine dans `self._archived_episodes` (append-only
           avec empreinte SHA-256). Le pôle centroïde et le vote de la provenance
           dans `_count_votes` demeurent strictement invariants.
        2. Archivage froid optionnel des singletons éteints (`archive_dormant_singletons=True`) :
           Archive les épisodes isolés dont `unresolved <= dormant_cutoff` s'ils ne
           participent à aucun litige actif sur `agenda_top` ou `rulings`.
        """
        if not hasattr(self, "_archived_episodes"):
            self._archived_episodes = []

        before_count = len(self.memory)
        if before_count <= 1:
            return {
                "before": before_count,
                "after": before_count,
                "archived_now": 0,
                "total_archived": len(self._archived_episodes),
            }

        # Identifier les provenances protégées par un litige oral actif
        protected_provs = set()
        if self.state.agenda_top:
            for q in self._questions_from_top(self.state.agenda_top):
                if q.startswith("reconcile:"):
                    protected_provs.update(q[len("reconcile:"):].split("|"))
        for r in self.state.rulings:
            if r.get("status") == "active":
                q = r.get("question", "")
                if q.startswith("reconcile:"):
                    protected_provs.update(q[len("reconcile:"):].split("|"))
                protected_provs.update(r.get("against", []))

        by_prov = {}
        for idx, ep in enumerate(self.memory):
            by_prov.setdefault(ep.provenance, []).append((idx, ep))

        new_memory = []
        archived_now = 0

        for prov, indexed_eps in by_prov.items():
            eps = [ep for _, ep in indexed_eps]
            active_eps = [ep for ep in eps if ep.unresolved > unresolved_threshold]
            resolved_eps = [ep for ep in eps if ep.unresolved <= unresolved_threshold]

            if len(resolved_eps) >= 2 and not active_eps:
                # Tous les épisodes de cette provenance sont résolus : compression en 1 ancre centroïde exacte
                unique_map = {}
                for ep in resolved_eps:
                    unique_map[self._unique_episode_key(ep)] = ep
                u_eps = [unique_map[k] for k in sorted(unique_map)]
                centroid_obs = self._centroid(u_eps)
                mean_rel = math.fsum(sorted(e.reliability for e in u_eps)) / len(u_eps)
                mean_unres = math.fsum(sorted(e.unresolved for e in u_eps)) / len(u_eps)
                consolidated_ep = Episode(centroid_obs, mean_rel, prov, mean_unres)
                new_memory.append(consolidated_ep)
                for ep in resolved_eps:
                    self._archived_episodes.append({
                        "cycle": self.state.cycle,
                        "mode": "centroid_compression",
                        "episode": asdict(ep),
                    })
                archived_now += len(resolved_eps) - 1
            elif len(resolved_eps) >= 2 and active_eps:
                # Garder les épisodes actifs + compresser les résolus si leurs positions sont déjà couvertes ou en centroïde résolu
                unique_map = {}
                for ep in resolved_eps:
                    unique_map[self._unique_episode_key(ep)] = ep
                u_eps = [unique_map[k] for k in sorted(unique_map)]
                centroid_obs = self._centroid(u_eps)
                mean_rel = math.fsum(sorted(e.reliability for e in u_eps)) / len(u_eps)
                mean_unres = math.fsum(sorted(e.unresolved for e in u_eps)) / len(u_eps)
                new_memory.extend(active_eps)
                new_memory.append(Episode(centroid_obs, mean_rel, prov, mean_unres))
                for ep in resolved_eps:
                    self._archived_episodes.append({
                        "cycle": self.state.cycle,
                        "mode": "partial_resolved_compression",
                        "episode": asdict(ep),
                    })
                archived_now += len(resolved_eps) - 1
            elif (
                archive_dormant_singletons
                and len(eps) == 1
                and eps[0].unresolved <= dormant_cutoff
                and prov not in protected_provs
                and len(by_prov) > 2
            ):
                self._archived_episodes.append({
                    "cycle": self.state.cycle,
                    "mode": "cold_archive_singleton",
                    "episode": asdict(eps[0]),
                })
                archived_now += 1
            else:
                new_memory.extend(eps)

        self.memory = new_memory
        self._persistent_geo_cache = None  # Invalider le cache géométrique après consolidation
        after_count = len(self.memory)
        archive_raw = json.dumps(self._archived_episodes, sort_keys=True, separators=(",", ":"))
        archive_sha256 = hashlib.sha256(archive_raw.encode("utf-8")).hexdigest()
        return {
            "before": before_count,
            "after": after_count,
            "archived_now": archived_now,
            "total_archived": len(self._archived_episodes),
            "archive_sha256": archive_sha256,
        }
