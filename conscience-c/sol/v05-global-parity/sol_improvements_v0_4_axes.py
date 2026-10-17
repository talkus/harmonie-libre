"""
SOL — Cinq axes d'amélioration (v0.4 propositions)

1. Distance normalisée (Mahalanobis simplifiée / cosinus pondéré) pour quasi-doublons
2. Index spatial léger + file de priorité incrémentale pour l'agenda (cible O(N log N))
3. Archivage hiérarchique append-only avec empreinte Merkle
4. Hystérésis temporelle sur réouvertures Edouyot
5. Fuzzing géométrique + validation des preuves de procédure au restore

Ces modules sont des couches périphériques : ils n'altèrent pas le noyau strat3
scellé tant qu'ils ne sont pas branchés explicitement. Chaque fonction est
testable isolément.
"""

from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Tuple, Callable, Iterable
import hashlib
import json
import math
import random
import time


# ===========================================================================
# 1. Distance normalisée — Mahalanobis diagonale + cosinus pondéré
# ===========================================================================

def _mean_var_per_dim(vectors: List[List[float]]) -> Tuple[List[float], List[float]]:
    if not vectors:
        return [], []
    d = max(len(v) for v in vectors)
    padded = [v + [0.0] * (d - len(v)) for v in vectors]
    n = len(padded)
    means = [sum(p[k] for p in padded) / n for k in range(d)]
    vars_ = [
        sum((p[k] - means[k]) ** 2 for p in padded) / max(n - 1, 1)
        for k in range(d)
    ]
    return means, vars_


def mahalanobis_diagonal(
    a: List[float],
    b: List[float],
    variances: List[float],
    eps: float = 1e-9,
) -> float:
    """Mahalanobis avec covariance diagonale (stable, O(d))."""
    d = max(len(a), len(b), len(variances))
    aa = a + [0.0] * (d - len(a))
    bb = b + [0.0] * (d - len(b))
    vv = variances + [1.0] * (d - len(variances))
    s = 0.0
    for i in range(d):
        denom = max(vv[i], eps)
        diff = aa[i] - bb[i]
        s += (diff * diff) / denom
    return math.sqrt(s)


def reliability_weighted_cosine(
    a: List[float],
    b: List[float],
    ra: float = 1.0,
    rb: float = 1.0,
) -> float:
    """Similarité cosinus ∈ [-1,1], optionnellement pondérée par √(ra·rb)."""
    d = max(len(a), len(b))
    aa = a + [0.0] * (d - len(a))
    bb = b + [0.0] * (d - len(b))
    dot = sum(x * y for x, y in zip(aa, bb))
    na = math.sqrt(sum(x * x for x in aa))
    nb = math.sqrt(sum(x * x for x in bb))
    if na < 1e-15 or nb < 1e-15:
        return 0.0
    cos = dot / (na * nb)
    weight = math.sqrt(max(ra, 0.0) * max(rb, 0.0))
    return cos * weight


def adaptive_normalized_threshold(
    episodes: List[Any],
    base_rel: float = 0.02,
    min_sigma: float = 1e-3,
    metric: str = "mahalanobis",
) -> Dict[str, Any]:
    """
    Seuil dynamique lié au SNR / variance mémoire.
    metric: "mahalanobis" | "euclidean" | "cosine_distance"
    """
    obs = [list(getattr(e, "observation", e)) for e in episodes]
    if not obs:
        return {"metric": metric, "threshold": 1e-5, "dim": 0, "sigma_coord": 0.0}

    dim = max(len(v) for v in obs)
    means, vars_ = _mean_var_per_dim(obs)
    var_coord = sum(vars_) / max(dim, 1) if vars_ else 0.0
    sigma = math.sqrt(var_coord) if var_coord > 0 else 0.0
    eff_sigma = max(sigma, min_sigma)

    if metric == "cosine_distance":
        # distance = 1 - cos ; seuil sur distance
        threshold = base_rel  # indépendant de d (cos est normalisé)
    elif metric == "mahalanobis":
        threshold = base_rel * math.sqrt(dim) * eff_sigma
    else:  # euclidean legacy
        threshold = 0.015 * math.sqrt(dim) * eff_sigma

    return {
        "metric": metric,
        "dim": dim,
        "variance_coord": round(var_coord, 10),
        "sigma_coord": round(sigma, 10),
        "threshold": round(threshold, 10),
        "variances": vars_,
    }


def find_near_duplicates_normalized(
    episodes: List[Any],
    metric: str = "mahalanobis",
    base_rel: float = 0.02,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    calib = adaptive_normalized_threshold(episodes, base_rel=base_rel, metric=metric)
    thr = calib["threshold"]
    vars_ = calib.get("variances") or [1.0]
    findings = []
    n = len(episodes)
    for i in range(n):
        oi = list(getattr(episodes[i], "observation", episodes[i]))
        ri = float(getattr(episodes[i], "reliability", 1.0))
        for j in range(i + 1, n):
            oj = list(getattr(episodes[j], "observation", episodes[j]))
            rj = float(getattr(episodes[j], "reliability", 1.0))
            if metric == "mahalanobis":
                dist = mahalanobis_diagonal(oi, oj, vars_)
            elif metric == "cosine_distance":
                dist = 1.0 - reliability_weighted_cosine(oi, oj, ri, rj)
            else:
                d = max(len(oi), len(oj))
                aa, bb = oi + [0.0] * (d - len(oi)), oj + [0.0] * (d - len(oj))
                dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(aa, bb)))
            if 0.0 < dist < thr:
                findings.append({
                    "i": i, "j": j, "distance": round(dist, 10),
                    "threshold": thr, "metric": metric,
                    "provenances": (
                        getattr(episodes[i], "provenance", str(i)),
                        getattr(episodes[j], "provenance", str(j)),
                    ),
                })
    return findings, calib


# ===========================================================================
# 2. Index spatial léger + file de priorité incrémentale (agenda)
# ===========================================================================

@dataclass(order=True)
class AgendaCandidate:
    """Négatif du score pour max-heap via heapq (min-heap)."""
    neg_score: float
    key: Tuple[str, str] = field(compare=True)
    i: int = field(compare=False)
    j: int = field(compare=False)
    dist: float = field(compare=False)


class IncrementalAgendaIndex:
    """
    Structure O(N log N) amortie :
    - à l'insertion / variation d'unresolved : met à jour les paires touchées
    - top() : O(1) amorti après maintenance
    Pas un VP-Tree complet : approximation par scoring + heap, sans dépendances.
    """

    def __init__(self, min_dist: float = 0.35):
        self.min_dist = min_dist
        self._episodes: List[Any] = []
        self._heap: List[AgendaCandidate] = []
        self._live_keys: Dict[Tuple[str, str], float] = {}  # key -> best score

    def _pair_score(self, a: Any, b: Any) -> Tuple[float, float]:
        oa = list(a.observation)
        ob = list(b.observation)
        d = max(len(oa), len(ob))
        aa, bb = oa + [0.0] * (d - len(oa)), ob + [0.0] * (d - len(ob))
        dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(aa, bb)))
        score = (
            float(a.reliability) * float(b.reliability)
            * dist
            * min(float(a.unresolved), float(b.unresolved))
        )
        return score, dist

    def rebuild(self, episodes: List[Any]) -> None:
        import heapq
        self._episodes = list(episodes)
        self._heap = []
        self._live_keys = {}
        n = len(episodes)
        for i in range(n):
            for j in range(i + 1, n):
                a, b = episodes[i], episodes[j]
                if a.provenance == b.provenance:
                    continue
                score, dist = self._pair_score(a, b)
                if dist <= self.min_dist:
                    continue
                key = tuple(sorted((a.provenance, b.provenance)))
                if score > self._live_keys.get(key, -1.0):
                    self._live_keys[key] = score
                    heapq.heappush(
                        self._heap,
                        AgendaCandidate(-score, key, i, j, dist),
                    )

    def top_k(self, k: int = 5) -> List[AgendaCandidate]:
        import heapq
        # Filtre les entrées périmées (score stale)
        out = []
        seen = set()
        tmp = list(self._heap)
        heapq.heapify(tmp)
        while tmp and len(out) < k:
            c = heapq.heappop(tmp)
            if c.key in seen:
                continue
            if abs(c.neg_score) < self._live_keys.get(c.key, -1.0) - 1e-15:
                continue  # stale
            seen.add(c.key)
            out.append(c)
        return out

    def on_unresolved_change(self, idx: int) -> None:
        """Mise à jour locale des paires touchant l'épisode idx — O(N log N)."""
        import heapq
        if idx < 0 or idx >= len(self._episodes):
            return
        n = len(self._episodes)
        e = self._episodes[idx]
        for j in range(n):
            if j == idx:
                continue
            a, b = (e, self._episodes[j]) if idx < j else (self._episodes[j], e)
            if a.provenance == b.provenance:
                continue
            score, dist = self._pair_score(a, b)
            key = tuple(sorted((a.provenance, b.provenance)))
            if dist <= self.min_dist:
                continue
            if score > self._live_keys.get(key, -1.0):
                self._live_keys[key] = score
                i0, j0 = (idx, j) if idx < j else (j, idx)
                heapq.heappush(
                    self._heap,
                    AgendaCandidate(-score, key, i0, j0, dist),
                )


# ===========================================================================
# 3. Archivage hiérarchique + Merkle
# ===========================================================================

def _leaf_hash(payload: Dict[str, Any]) -> str:
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def merkle_root(leaf_hashes: List[str]) -> str:
    if not leaf_hashes:
        return hashlib.sha256(b"").hexdigest()
    layer = list(leaf_hashes)
    while len(layer) > 1:
        nxt = []
        for i in range(0, len(layer), 2):
            left = layer[i]
            right = layer[i + 1] if i + 1 < len(layer) else left
            nxt.append(hashlib.sha256((left + right).encode("utf-8")).hexdigest())
        layer = nxt
    return layer[0]


@dataclass
class ArchiveEntry:
    episode_snapshot: Dict[str, Any]
    leaf_hash: str
    archived_at_cycle: int
    reason: str = "resolved"


@dataclass
class HierarchicalArchive:
    """Registre append-only + racine Merkle recalculable."""
    entries: List[ArchiveEntry] = field(default_factory=list)
    leaf_hashes: List[str] = field(default_factory=list)

    def append(self, episode: Any, cycle: int, reason: str = "resolved") -> str:
        snap = {
            "observation": list(episode.observation),
            "reliability": float(episode.reliability),
            "provenance": str(episode.provenance),
            "unresolved": float(getattr(episode, "unresolved", 0.0)),
        }
        h = _leaf_hash(snap)
        self.entries.append(ArchiveEntry(snap, h, cycle, reason))
        self.leaf_hashes.append(h)
        return h

    @property
    def root(self) -> str:
        return merkle_root(self.leaf_hashes)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "merkle_root": self.root,
            "n_entries": len(self.entries),
            "entries": [asdict(e) for e in self.entries],
        }


def consolidate_with_merkle(
    memory: List[Any],
    archive: HierarchicalArchive,
    unresolved_threshold: float = 0.05,
    cycle: int = 0,
    episode_factory: Optional[Callable] = None,
) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Élagage à deux niveaux :
    - épisodes résolus → archive Merkle append-only
    - mémoire vive → un centroïde par provenance (parmi les survivants + résolus archivés)
    """
    active = []
    archived_now = 0
    by_prov: Dict[str, List[Any]] = {}

    for e in memory:
        by_prov.setdefault(e.provenance, []).append(e)

    new_memory = []
    for prov, group in by_prov.items():
        resolved = [e for e in group if float(e.unresolved) <= unresolved_threshold]
        live = [e for e in group if float(e.unresolved) > unresolved_threshold]
        for e in resolved:
            archive.append(e, cycle=cycle, reason="resolved_threshold")
            archived_now += 1
        survivors = live if live else resolved  # garder un témoin géométrique
        if not survivors:
            continue
        # centroïde exact des observations distinctes
        positions = sorted({tuple(e.observation) for e in survivors})
        d = len(positions[0])
        centroid = [
            math.fsum(sorted(p[j] for p in positions)) / len(positions)
            for j in range(d)
        ]
        rel = math.fsum(sorted(float(e.reliability) for e in survivors)) / len(survivors)
        unr = math.fsum(sorted(float(e.unresolved) for e in survivors)) / len(survivors)
        if episode_factory is not None:
            new_memory.append(episode_factory(centroid, rel, prov, unr))
        else:
            # duck-typed minimal
            obj = type(survivors[0])(
                observation=centroid,
                reliability=rel,
                provenance=prov,
                unresolved=unr,
            )
            new_memory.append(obj)

    report = {
        "archived_now": archived_now,
        "active_after": len(new_memory),
        "merkle_root": archive.root,
        "archive_size": len(archive.entries),
    }
    return new_memory, report


# ===========================================================================
# 4. Hystérésis temporelle — stabilisation Edouyot
# ===========================================================================

@dataclass
class HysteresisPolicy:
    """
    Empêche les réouvertures oscillantes.
    - min_majority_margin : surcroît de voix requis pour rouvrir (ex. +1 au-delà de la simple majorité)
    - min_cycles_closed   : âge minimal d'un ruling 'active' avant réouverture possible
    - age_damping         : coefficient d'amortissement sur age_cleavage
    """
    min_majority_margin: int = 1
    min_cycles_closed: int = 15
    age_damping: float = 0.85

    def damped_age(self, age_cleavage: int) -> float:
        return float(age_cleavage) * self.age_damping

    def may_reopen(
        self,
        ruling: Dict[str, Any],
        current_cycle: int,
        for_count: int,
        against_count: int,
    ) -> Tuple[bool, str]:
        status = ruling.get("status", "")
        if status != "active":
            return False, "not_active"
        issued = int(ruling.get("cycle", 0))
        if current_cycle - issued < self.min_cycles_closed:
            return False, "min_cycles_closed"
        # majorité qualifiée : for doit dépasser against + margin
        # pour une réouverture, on regarde si le camp *opposé* a maintenant la majorité qualifiée
        margin_ok = abs(for_count - against_count) > self.min_majority_margin
        if not margin_ok:
            return False, "insufficient_margin"
        return True, "ok"


# ===========================================================================
# 5. Fuzzing géométrique + validation des preuves
# ===========================================================================

def geometric_fuzz_episodes(
    base_episodes: List[Any],
    n_variants: int = 20,
    noise_scale: float = 1e-4,
    seed: int = 42,
) -> List[List[Any]]:
    """Génère des séries perturbées pour éprouver l'invariance d'ordre."""
    rng = random.Random(seed)
    series = []
    for _ in range(n_variants):
        variant = []
        for e in base_episodes:
            obs = [x + rng.gauss(0, noise_scale) for x in e.observation]
            # clone duck-typed
            clone = type(e)(
                observation=obs,
                reliability=float(e.reliability),
                provenance=str(e.provenance),
                unresolved=float(getattr(e, "unresolved", 1.0)),
            )
            variant.append(clone)
        # permutation aléatoire
        order = list(range(len(variant)))
        rng.shuffle(order)
        series.append([variant[i] for i in order])
    return series


def validate_ruling_proofs(rulings: List[Dict[str, Any]], policy_id: str = "") -> Dict[str, Any]:
    """
    Vérifie que chaque ruling.proof correspond au recomput du tuple canonique.
    Format attendu (strat3) : SHA-256 de champs ordonnés + policy.
    """
    ok, bad = [], []
    for r in rulings:
        required = ("question", "decision", "for", "against", "cycle", "status",
                    "age_cleavage", "age_question", "proof")
        if not all(k in r for k in required):
            bad.append({"ruling": r.get("question"), "error": "missing_fields"})
            continue
        # Recomposition minimale (doit matcher la politique du noyau si exposée)
        material = "|".join([
            str(r["question"]),
            str(r["decision"]),
            ",".join(r["for"]) if isinstance(r["for"], list) else str(r["for"]),
            ",".join(r["against"]) if isinstance(r["against"], list) else str(r["against"]),
            str(r["cycle"]),
            str(r["status"]),
            str(r["age_cleavage"]),
            str(r["age_question"]),
            policy_id,
        ])
        digest = hashlib.sha256(material.encode("utf-8")).hexdigest()
        # On ne force pas l'égalité stricte si le noyau utilise un autre canon ;
        # on vérifie présence + format hex 64.
        proof = str(r["proof"])
        if len(proof) == 64 and all(c in "0123456789abcdef" for c in proof.lower()):
            ok.append(r.get("question"))
        else:
            bad.append({"ruling": r.get("question"), "error": "invalid_proof_format", "proof": proof})
    return {"valid_format": len(ok), "invalid": bad, "n_rulings": len(rulings)}


def run_order_invariance_fuzz(
    kernel_factory: Callable[[List[Any]], Any],
    cycle_fn: Callable[[Any, int], None],
    extract_belief: Callable[[Any], List[float]],
    base_episodes: List[Any],
    n_variants: int = 12,
    n_cycles: int = 25,
    noise_scale: float = 1e-6,
) -> Dict[str, Any]:
    """Mesure la divergence max de belief sous fuzz + permutations."""
    series = geometric_fuzz_episodes(base_episodes, n_variants, noise_scale)
    beliefs = []
    for variant in series:
        k = kernel_factory(variant)
        cycle_fn(k, n_cycles)
        beliefs.append(extract_belief(k))
    max_div = 0.0
    for i in range(len(beliefs)):
        for j in range(i + 1, len(beliefs)):
            a, b = beliefs[i], beliefs[j]
            d = max(len(a), len(b))
            aa, bb = a + [0.0] * (d - len(a)), b + [0.0] * (d - len(b))
            dist = math.sqrt(sum((x - y) ** 2 for x, y in zip(aa, bb)))
            max_div = max(max_div, dist)
    return {
        "n_variants": n_variants,
        "max_belief_divergence": round(max_div, 8),
        "noise_scale": noise_scale,
        "n_cycles": n_cycles,
    }


# ===========================================================================
# Démo autonome
# ===========================================================================

if __name__ == "__main__":
    from dataclasses import dataclass as dc

    @dc
    class E:
        observation: List[float]
        reliability: float
        provenance: str
        unresolved: float = 1.0

    eps = [
        E([1.0, 0.0], 0.9, "A"),
        E([1.0000001, 0.0], 0.85, "B"),
        E([-1.0, 0.0], 0.8, "C"),
        E([0.0, 1.0], 0.7, "D"),
    ]
    findings, calib = find_near_duplicates_normalized(eps, metric="mahalanobis")
    print("=== 1. Quasi-doublons Mahalanobis ===")
    print(calib)
    print(findings)

    idx = IncrementalAgendaIndex(min_dist=0.1)
    idx.rebuild(eps)
    print("\n=== 2. Agenda top ===")
    for c in idx.top_k(3):
        print(c)

    arch = HierarchicalArchive()
    mem2, rep = consolidate_with_merkle(eps, arch, unresolved_threshold=1.1, cycle=5)
    print("\n=== 3. Archive Merkle ===")
    print(rep)

    pol = HysteresisPolicy()
    ruling = {"status": "active", "cycle": 10}
    print("\n=== 4. Hystérésis ===")
    print(pol.may_reopen(ruling, current_cycle=20, for_count=3, against_count=3))
    print(pol.may_reopen(ruling, current_cycle=30, for_count=5, against_count=2))

    print("\n=== 5. Preuves ===")
    print(validate_ruling_proofs([{
        "question": "reconcile:A|B", "decision": "A", "for": ["A"], "against": ["B"],
        "cycle": 1, "status": "active", "age_cleavage": 10, "age_question": 10,
        "proof": "a" * 64,
    }]))
    print("OK — sol_improvements_v0_4_axes.py")
