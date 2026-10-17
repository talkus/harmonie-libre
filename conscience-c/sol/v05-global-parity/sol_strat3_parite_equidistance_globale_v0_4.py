"""
SOL — Branchement des 4 Leviers Périphériques + Parité & Équidistance Globale Augmentée sur strat3 (v0.4)

Intègre de manière transparente et modulaire (sans altérer la couche écrite scellée) :
 1. Indexation spatiale incrémentale d'Agenda O(N log N) + Branch-and-Bound et cache de scrutin O(1)
 2. Archivage hiérarchique append-only avec racine Merkle RFC 6962 (HierarchicalArchive)
 3. Calibrage adaptatif du seuil de quasi-doublons (compute_adaptive_threshold & Mahalanobis)
 4. Hystérésis temporelle des réouvertures Edouyot (HysteresisPolicy)
 5. Parité et équidistance globale multi-échelle (SCHOOL_REL_RADIUS = 0.15) :
    - P_VOTES : Corps électoral actif vs corps électoral de réouverture Edouyot
    - P_AFFINITE_GLOBALE :
      a) Rayon d'affinité mutuelle invariant d'échelle (min(d0, d1) < d01 - tol)
      b) Équidistance d'école multi-échelle : abstention de tout témoin tiers hors école locale
         (min(d0, d1) > 0.15 * d01) dont les intervalles de distance aux deux écoles locales
         se chevauchent (P6 : protection contre le décentrage barycentrique d'une école)
      c) Contrepoids médian global : un pôle n'emporte la majorité locale que si elle concorde
         avec la majorité de demi-espace médian global (half0 > half1), protégeant tout témoin
         médian charnière placé entre deux écoles en parité (P7, P8)
    - P_AGENDA : Délibération collective symétrique (group:[...]) sur ex-aequo compatibles
      et abstention sur clivages opposés (P5, P10).
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Callable
import copy
import hashlib
import json
import math
import time

from sol_strat3_multiechelle_v0_3_optimized import (
    SolMicrokernelV04 as Strat3BaseKernel,
    Episode,
    State,
    CORE,
    POLICY_ID,
    RULING_MIN_DIST,
    RULING_AGE,
    VOTE_TIE_EPS,
    vnorm,
    vsub,
    vadd,
    vscale,
    vtanh,
    vmix,
)
from sol_improvements_v0_4_axes import (
    IncrementalAgendaIndex,
    HierarchicalArchive,
    merkle_root,
    HysteresisPolicy,
    adaptive_normalized_threshold,
    mahalanobis_diagonal,
)

SCHOOL_REL_RADIUS = 0.15  # Rayon relatif d'école locale (invariant d'échelle : 0.15 * d01)


class SolMicrokernelStrat3Improved(Strat3BaseKernel):
    def __init__(self, state: State, memory: List[Episode]):
        super().__init__(state, memory)
        self.archive = HierarchicalArchive()
        self.hysteresis = HysteresisPolicy(min_majority_margin=1, min_cycles_closed=15)
        self._agenda_index = None

    def _source_index(self):
        gcache = self._get_geo_cache()
        if "source_index" in gcache:
            return gcache["source_index"]
        idx = super()._source_index()
        gcache["source_index"] = idx
        return idx


    def _anchors(self, indexed=None):
        ctx = getattr(self, "_vote_context", None)
        if ctx is not None:
            return ctx["anchors"]
        gcache = self._get_geo_cache()
        sources = indexed if indexed is not None else self._source_index()
        centroids = gcache["centroids"]
        return {
            p: Episode(
                centroids[p],
                math.fsum(sorted(e.reliability for e in es)) / len(es),
                p,
                math.fsum(sorted(e.unresolved for e in es)) / len(es),
            )
            for p, es in sources.items()
        }

    def _ensure_agenda_index(self):
        if self._agenda_index is None:
            self._agenda_index = IncrementalAgendaIndex(min_dist=RULING_MIN_DIST)
            anchors = self._anchors()
            self._agenda_index.rebuild(list(anchors.values()))
        return self._agenda_index

    def _count_votes(self, poles, include_fenced: bool = False):
        """
        Scrutin équivariant de parité et d'équidistance globale multi-échelle :
        - Invariant par permutation, duplication exacte, réflexion, renommage et échelle (0.2x..5x).
        - Intègre le rayon d'affinité mutuelle, l'équidistance d'école (intervalles de distance
          aux écoles locales <= 0.15 * d01) et le contrepoids médian global (demi-espaces).
        - Mis en cache par (couple, effectif par source, état de clôture) pour exécution O(1) amortie.
        """
        p0, p1 = poles[0].provenance, poles[1].provenance
        obs0, obs1 = poles[0].observation, poles[1].observation
        d01 = vnorm(vsub(obs0, obs1))
        if d01 <= 1e-15:
            self._divided_last = []
            return {p0: [], p1: []}

        ctx = getattr(self, "_vote_context", None)
        if ctx is None:
            ctx = self._build_vote_context()
        gcache = ctx["gcache"]
        sources = ctx["sources"]
        anchors = ctx["anchors"]
        src_counts = ctx["src_counts"]

        # Vérifier si les pôles correspondent aux ancres canoniques pour le cache
        is_canonical_poles = (
            p0 in anchors
            and p1 in anchors
            and obs0 == anchors[p0].observation
            and obs1 == anchors[p1].observation
        )
        fenced_set = (
            frozenset()
            if include_fenced
            else frozenset(p for p in sources if self._fence_factor(p) == 0.0)
        )
        if is_canonical_poles:
            cache_key = ("global_eq_v1", p0, p1, src_counts, fenced_set)
            cached = gcache["static_ballots"].get(cache_key)
            if cached is not None:
                v0, v1, div_last = cached
                self._divided_last = list(div_last)
                return {p0: list(v0), p1: list(v1)}

        tol = VOTE_TIE_EPS * d01
        school_rad = SCHOOL_REL_RADIUS * d01

        # 1. Identifier les écoles locales S0 et S1 autour des deux pôles (invariant d'échelle)
        s0_names = [p0]
        s1_names = [p1]
        s0_obs = [obs0]
        s1_obs = [obs1]
        for prov, anc in anchors.items():
            if prov in fenced_set or prov in (p0, p1):
                continue
            if is_canonical_poles:
                da0 = ctx["pairs"].get((prov, p0) if prov < p0 else (p0, prov), 0.0)
                da1 = ctx["pairs"].get((prov, p1) if prov < p1 else (p1, prov), 0.0)
            else:
                da0 = vnorm(vsub(anc.observation, obs0))
                da1 = vnorm(vsub(anc.observation, obs1))
            if da0 > tol and da0 <= school_rad and da0 < da1 - tol:
                s0_names.append(prov)
                s0_obs.append(anc.observation)
            elif da1 > tol and da1 <= school_rad and da1 < da0 - tol:
                s1_names.append(prov)
                s1_obs.append(anc.observation)

        has_schools = len(s0_obs) > 1 or len(s1_obs) > 1
        if is_canonical_poles:
            col0 = self._get_dist_col(gcache, sources, src_counts, p0, obs0)
            col1 = self._get_dist_col(gcache, sources, src_counts, p1, obs1)
            s0_cols = [
                self._get_dist_col(gcache, sources, src_counts, name, anchors[name].observation)
                for name in s0_names
            ] if has_schools else None
            s1_cols = [
                self._get_dist_col(gcache, sources, src_counts, name, anchors[name].observation)
                for name in s1_names
            ] if has_schools else None

        votes = {p0: [], p1: []}
        divided = []
        half0, half1 = 0, 0

        for prov, episodes in sources.items():
            if prov in fenced_set:
                continue
            camps_local = set()
            camps_half = set()
            if is_canonical_poles:
                d0_list = col0[prov]
                d1_list = col1[prov]
                for idx_ep, (d0, d1) in enumerate(zip(d0_list, d1_list)):
                    if abs(d0 - d1) <= tol:
                        continue
                    if has_schools and min(d0, d1) > school_rad:
                        max_d0 = max(c[prov][idx_ep] for c in s0_cols)
                        min_d0 = min(c[prov][idx_ep] for c in s0_cols)
                        max_d1 = max(c[prov][idx_ep] for c in s1_cols)
                        min_d1 = min(c[prov][idx_ep] for c in s1_cols)
                        if max_d0 >= min_d1 - tol and max_d1 >= min_d0 - tol:
                            continue
                    side = p0 if d0 < d1 else p1
                    camps_half.add(side)
                    if min(d0, d1) < d01 - tol:
                        camps_local.add(side)
            else:
                for e in episodes:
                    d0 = vnorm(vsub(e.observation, obs0))
                    d1 = vnorm(vsub(e.observation, obs1))
                    if abs(d0 - d1) <= tol:
                        continue
                    if has_schools and min(d0, d1) > school_rad:
                        dists0 = [vnorm(vsub(e.observation, m)) for m in s0_obs]
                        dists1 = [vnorm(vsub(e.observation, m)) for m in s1_obs]
                        if max(dists0) >= min(dists1) - tol and max(dists1) >= min(dists0) - tol:
                            continue
                    side = p0 if d0 < d1 else p1
                    camps_half.add(side)
                    if min(d0, d1) < d01 - tol:
                        camps_local.add(side)

            if len(camps_half) == 1:
                if next(iter(camps_half)) == p0:
                    half0 += 1
                else:
                    half1 += 1

            if len(camps_local) > 1:
                divided.append(prov)
            elif len(camps_local) == 1:
                votes[next(iter(camps_local))].append(prov)

        self._divided_last = sorted(divided)
        votes[p0].sort()
        votes[p1].sort()

        # Contrepoids médian global : la majorité locale doit concorder avec la majorité de demi-espace
        if (len(votes[p0]) > len(votes[p1]) and half0 <= half1) or (
            len(votes[p1]) > len(votes[p0]) and half1 <= half0
        ):
            votes[p0] = []
            votes[p1] = []

        if is_canonical_poles:
            gcache["static_ballots"][cache_key] = (
                tuple(votes[p0]),
                tuple(votes[p1]),
                tuple(self._divided_last),
            )
        return votes


    def _cleavage_signature(self, question):
        if isinstance(question, str) and question.startswith("group:"):
            qs = self._questions_from_top(question)
            signatures = [super(Strat3BaseKernel, self)._cleavage_signature(q) for q in qs]
            if any(sig is None for sig in signatures):
                return None
            uniq = sorted(set(signatures))
            return uniq[0] if len(uniq) == 1 else tuple(uniq)
        return super()._cleavage_signature(question)

    def _oral_layer(self):
        self._vote_context = self._build_vote_context()
        try:
            return self._oral_layer_inner()
        finally:
            self._vote_context = None

    def _oral_layer_inner(self):
        reopened = False
        for r in self.state.rulings:
            if r["status"] != "active":
                continue
            poles = self._pole_episodes(r["question"])
            if poles is None:
                continue
            votes = self._count_votes(poles, include_fenced=True)
            winner = r["decision"]
            other = [p for p in votes if p != winner]
            if other:
                opp_count = len(votes[other[0]])
                win_count = len(votes[winner])
                may_reopen, _reason = self.hysteresis.may_reopen(
                    ruling=r,
                    current_cycle=self.state.cycle,
                    for_count=opp_count,
                    against_count=win_count,
                )
                if may_reopen and opp_count >= win_count:
                    r["status"] = "reopened"
                    r["reopened_cycle"] = self.state.cycle + 1
                    self.state.agenda_top_age = 0
                    self.state.agenda_top_seen = None
                    self.state.agenda_question_age = 0
                    self.state.agenda_question_seen = None
                    reopened = True

        if reopened:
            self._derive_agenda()

        top = self.state.agenda_top
        sig_top = self._cleavage_signature(top)
        sig_seen = self._cleavage_signature(self.state.agenda_top_seen)
        if top is not None and (
            top == self.state.agenda_top_seen or (sig_top is not None and sig_top == sig_seen)
        ):
            self.state.agenda_top_age += 1
            self.state.agenda_top_seen = top
        else:
            self.state.agenda_top_seen = top
            self.state.agenda_top_age = 0
        if top is not None and top == self.state.agenda_question_seen:
            self.state.agenda_question_age += 1
        else:
            self.state.agenda_question_seen = top
            self.state.agenda_question_age = 0

        if top is None or self.state.agenda_top_age < RULING_AGE:
            return
        ruled = {r["question"] for r in self.state.rulings if r["status"] == "active"}
        qs = [q for q in self._questions_from_top(top) if q not in ruled]
        proposals = [self._vote_proposal(q) for q in qs]
        if not self._non_conflicting(proposals):
            return

        for q, pa, la, pb, lb, divided in proposals:
            if q not in self.state.questions:
                self.state.questions.append(q)
            proof = hashlib.sha256(
                "|".join([
                    q, pa, ",".join(la), ",".join(lb), str(self.state.cycle + 1),
                    str(self.state.agenda_top_age), str(self.state.agenda_question_age),
                    POLICY_ID,
                ]).encode("utf-8")
            ).hexdigest()
            if divided:
                self.state.resync_events.append({
                    "cycle": self.state.cycle + 1,
                    "cause": "DISPERSION:" + q,
                    "magnitude": float(len(divided)),
                    "divided": list(divided),
                })
            self.state.rulings.append({
                "question": q,
                "decision": pa,
                "for": list(la),
                "against": list(lb),
                "cycle": self.state.cycle + 1,
                "status": "active",
                "age_cleavage": self.state.agenda_top_age,
                "age_question": self.state.agenda_question_age,
                "proof": proof,
            })
        self.state.questions.sort()

    def consolidate_memory(
        self,
        unresolved_threshold: float = 0.05,
        archive_dormant_singletons: bool = False,
        dormant_cutoff: float = 0.01,
    ) -> dict:
        before_count = len(self.memory)
        if before_count <= 1:
            return {
                "before": before_count,
                "after": before_count,
                "archived_now": 0,
                "total_archived": len(self.archive.entries),
                "merkle_root": self.archive.root,
            }

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
                unique_map = {self._unique_episode_key(ep): ep for ep in resolved_eps}
                u_eps = [unique_map[k] for k in sorted(unique_map)]
                centroid_obs = self._centroid(u_eps)
                mean_rel = math.fsum(sorted(e.reliability for e in u_eps)) / len(u_eps)
                mean_unres = math.fsum(sorted(e.unresolved for e in u_eps)) / len(u_eps)
                new_memory.append(Episode(centroid_obs, mean_rel, prov, mean_unres))
                for ep in resolved_eps:
                    self.archive.append(ep, cycle=self.state.cycle, reason="centroid_compression")
                archived_now += len(resolved_eps) - 1
            elif len(resolved_eps) >= 2 and active_eps:
                unique_map = {self._unique_episode_key(ep): ep for ep in resolved_eps}
                u_eps = [unique_map[k] for k in sorted(unique_map)]
                centroid_obs = self._centroid(u_eps)
                mean_rel = math.fsum(sorted(e.reliability for e in u_eps)) / len(u_eps)
                mean_unres = math.fsum(sorted(e.unresolved for e in u_eps)) / len(u_eps)
                new_memory.extend(active_eps)
                new_memory.append(Episode(centroid_obs, mean_rel, prov, mean_unres))
                for ep in resolved_eps:
                    self.archive.append(ep, cycle=self.state.cycle, reason="partial_resolved_compression")
                archived_now += len(resolved_eps) - 1
            elif (
                archive_dormant_singletons
                and len(eps) == 1
                and eps[0].unresolved <= dormant_cutoff
                and prov not in protected_provs
                and len(by_prov) > 2
            ):
                self.archive.append(eps[0], cycle=self.state.cycle, reason="cold_archive_singleton")
                archived_now += 1
            else:
                new_memory.extend(eps)

        self.memory = new_memory
        self._persistent_geo_cache = None
        self._agenda_index = None

        after_count = len(self.memory)
        return {
            "before": before_count,
            "after": after_count,
            "archived_now": archived_now,
            "total_archived": len(self.archive.entries),
            "merkle_root": self.archive.root,
        }

# Alias canonique pour les suites de vérification formelle
SolMicrokernelV04 = SolMicrokernelStrat3Improved
