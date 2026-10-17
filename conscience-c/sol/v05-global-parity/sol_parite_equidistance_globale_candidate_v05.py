"""SOL / proposition non adoptee: parite et equidistance globale v0.5.

Couche de scrutin uniquement. N'applique aucune migration, n'edite pas la reference,
ne modifie pas la couche ecrite. Un vote = une provenance independante.
Les ambiguites s'abstiennent. Les resultats exigent des bancs independants.
"""
from __future__ import annotations

import math
from typing import Dict, List

from sol_strat3_parite_equidistance_globale_v0_4 import (
    SolMicrokernelStrat3Improved as _V04Global,
    Episode, State, VOTE_TIE_EPS, SCHOOL_REL_RADIUS, vnorm, vsub,
)

# Zone prudente autour de la mediatrice, en proportion de la distance des poles.
# A calibrer sur donnees de domaine; ce n'est pas une loi universelle.
MEDIAN_NEUTRAL_REL = 0.025


class SolMicrokernelGlobalParityV05Candidate(_V04Global):
    """Candidat conservateur: abstention sous ambiguite, neutralite multi-echelle.

    Guarantees cibles SOUS distances euclidiennes finies et donnees stables:
    - parite des provenances, non des episodes;
    - equidistance exacte ou quasi-mediane => abstention individuelle;
    - dispersion claire d'une provenance => abstention de cette provenance;
    - tiers hors ecole: accord entre pôle proche et toute l'ecole locale;
    - majorite locale recevable si majorite globale concordante;
    - invalidation complete du cache apres mutation d'une coordonnee.
    """

    def _get_geo_cache(self):
        # Correction du cache amont: le test original ne surveille que la premiere
        # coordonnee; une mutation d'une autre coordonnee y reste invisible.
        # Ce controle O(Nd) est delibere: privilegier la correction a la vitesse.
        sig = tuple(
            (e.provenance, tuple(float(x) for x in e.observation), float(e.reliability))
            for e in self.memory
        )
        cache = getattr(self, "_persistent_geo_cache", None)
        if cache is not None and cache.get("sig") == sig:
            return cache
        self._persistent_geo_cache = None
        self._agenda_index = None
        self._vote_context = None
        return super()._get_geo_cache()

    def _count_votes(self, poles, include_fenced: bool = False):
        if len(poles) != 2 or poles[0].provenance == poles[1].provenance:
            raise ValueError("Deux poles distincts sont requis")

        # Si une observation change pendant un contexte ancien, recalculer le
        # contexte plutot que de reutiliser des ancres et colonnes obsoletes.
        live_cache = self._get_geo_cache()
        ctx = getattr(self, "_vote_context", None)
        if ctx is None or ctx.get("gcache") is not live_cache:
            ctx = self._build_vote_context()

        p0, p1 = poles[0].provenance, poles[1].provenance
        obs0, obs1 = poles[0].observation, poles[1].observation
        out = {p0: [], p1: []}
        d01 = vnorm(vsub(obs0, obs1))
        if not math.isfinite(d01):
            raise ValueError("Distance non finie")
        if d01 <= 1e-15:
            self._divided_last = []
            return out

        sources = ctx["sources"]
        anchors = ctx["anchors"]
        fenced = (
            set() if include_fenced
            else {p for p in sources if self._fence_factor(p) == 0.0}
        )
        tol = VOTE_TIE_EPS * d01
        school_rad = SCHOOL_REL_RADIUS * d01
        neutral_band = max(tol, MEDIAN_NEUTRAL_REL * d01)

        # Ecoles locales: exactement une provenance par ancre; identite
        # independante du nombre d'episodes et de leur ordre.
        s0 = [obs0]
        s1 = [obs1]
        for prov in sorted(anchors):
            if prov in (p0, p1) or prov in fenced:
                continue
            anc = anchors[prov].observation
            d0 = vnorm(vsub(anc, obs0))
            d1 = vnorm(vsub(anc, obs1))
            if tol < d0 <= school_rad and d0 < d1 - tol:
                s0.append(anc)
            elif tol < d1 <= school_rad and d1 < d0 - tol:
                s1.append(anc)
        has_schools = len(s0) > 1 or len(s1) > 1

        # Cache de distances par point de reference, jamais de decision opaque.
        # Le cache parent est desormais invalide pour toute mutation de coord.
        gcache = ctx["gcache"]
        counts = ctx["src_counts"]
        def distances(anchor_name, anchor_obs):
            if anchor_name in anchors and anchor_obs == anchors[anchor_name].observation:
                return self._get_dist_col(gcache, sources, counts, anchor_name, anchor_obs)
            return {prov: tuple(vnorm(vsub(e.observation, anchor_obs)) for e in eps)
                    for prov, eps in sources.items()}
        col0 = distances(p0, obs0)
        col1 = distances(p1, obs1)

        # Pour les membres de l'ecole: verifier la distance aux ancres des ecoles.
        # Precalcul de colonnes pour eviter la repetition des calculs par episode.
        school0 = []
        school1 = []
        if has_schools:
            # On travaille avec les positions d'ancres; plusieurs coordonnees
            # identiques ne font pas gagner des voix additionnelles.
            for idx, obs in enumerate(s0):
                school0.append(distances(f"__school0_{idx}", obs))
            for idx, obs in enumerate(s1):
                school1.append(distances(f"__school1_{idx}", obs))

        global0 = global1 = 0
        divided = []
        for prov in sorted(sources):
            if prov in fenced:
                continue
            local_sides = set()
            global_sides = set()
            for k, (d0, d1) in enumerate(zip(col0[prov], col1[prov])):
                if not (math.isfinite(d0) and math.isfinite(d1)):
                    raise ValueError("Observation non finie")
                if abs(d0 - d1) <= neutral_band:
                    continue  # preserver l'abstention quasi-mediane
                side = p0 if d0 < d1 else p1
                if has_schools and min(d0, d1) > school_rad:
                    ds0 = [col[prov][k] for col in school0]
                    ds1 = [col[prov][k] for col in school1]
                    # Opposition possible si et seulement si toutes les ancres
                    # d'une ecole sont clairement plus proches que toute
                    # ancre de l'autre ecole (majoration/minoration).
                    robust0 = max(ds0) < min(ds1) - tol
                    robust1 = max(ds1) < min(ds0) - tol
                    if (side == p0 and not robust0) or (side == p1 and not robust1):
                        continue
                global_sides.add(side)
                if min(d0, d1) < d01 - tol:
                    local_sides.add(side)

            # Parite forte: une meme provenance ne peut soutenir simultanement
            # deux camps dans aucun des deux decompteurs. L'abstention est
            # definitive pour ce scrutin, pas pour les scrutins futurs.
            if len(global_sides) > 1 or len(local_sides) > 1:
                divided.append(prov)
                continue
            if len(global_sides) == 1:
                if p0 in global_sides:
                    global0 += 1
                else:
                    global1 += 1
            if len(local_sides) == 1:
                out[next(iter(local_sides))].append(prov)

        self._divided_last = sorted(divided)
        # Garde-fou global: une majorite locale sans appui de demi-espace est
        # transformee en abstention; jamais fabriquee comme majorite opposee.
        if (len(out[p0]) > len(out[p1]) and global0 <= global1) or (
            len(out[p1]) > len(out[p0]) and global1 <= global0
        ):
            return {p0: [], p1: []}
        return out


# Alias compatible avec les bancs qui importent un noyau V04.
SolMicrokernelV04 = SolMicrokernelGlobalParityV05Candidate
