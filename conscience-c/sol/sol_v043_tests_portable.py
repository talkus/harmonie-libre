#!/usr/bin/env python3
"""
Banc d'épreuves portable Sol v0.4.3 — Reproduction des 3 défauts de la couche orale (O1, O2, O3)
sur v0.4.2 et vérification complète de v0.4.3 (2026-10-16, version régnante adoptée à 18:15 EDT).

Correctif de portabilité (suite à la vérification de Muse du 2026-10-16 18:15 EDT) :
- Supprime l'hypothèse `HERE.parents[3] / "downloads"` qui plantait hors de l'arborescence
  du bac à sable initial.
- Recherche dynamiquement `sol_microkernel_v0_4_3_reference.py` ainsi que les versions
  antérieures optionnelles (`v0.4.1`, `v0.4.2`) dans le répertoire courant, le répertoire du
  script, les dossiers frères du dépôt Drive (`07-rafraichissement-2026-10-16/noyau-sol-v041`,
  `08-rafraichissement-2-2026-10-16/noyau-sol-v042`, etc.) ou tout dossier `downloads` parent,
  et s'exécute sans erreur même dans un répertoire isolé contenant uniquement `v0.4.3`.
"""

from __future__ import annotations

import math
import os
import pathlib
import sys


def _configurer_chemins_recherche() -> None:
    here = pathlib.Path(__file__).resolve().parent
    cwd = pathlib.Path.cwd().resolve()
    candidats = [here, cwd]

    for base in (here, cwd, *here.parents):
        for rel in (
            "07-rafraichissement-2026-10-16/noyau-sol-v041",
            "08-rafraichissement-2-2026-10-16/noyau-sol-v042",
            "09-ameliorations-verifiees-2026-10-16",
            "noyau-sol-v041",
            "noyau-sol-v042",
            "downloads",
        ):
            p = base / rel
            if p.is_dir():
                candidats.append(p)

    env_extra = os.environ.get("SOL_KERNEL_PATH", "")
    if env_extra:
        for part in env_extra.split(os.pathsep):
            if part and pathlib.Path(part).is_dir():
                candidats.append(pathlib.Path(part).resolve())

    for c in candidats:
        s = str(c)
        if s not in sys.path:
            sys.path.insert(0, s)


_configurer_chemins_recherche()

import sol_microkernel_v0_4_3_reference as v043  # noqa: E402

try:
    import sol_microkernel_v0_4_1_reference as v041  # noqa: E402
except ImportError:
    v041 = None

try:
    import sol_microkernel_v0_4_2_reference as v042  # noqa: E402
except ImportError:
    v042 = None


def _modules_disponibles(inclure_v041: bool = False):
    mods = []
    if inclure_v041 and v041 is not None:
        mods.append(("v0.4.1", v041))
    if v042 is not None:
        mods.append(("v0.4.2", v042))
    mods.append(("v0.4.3", v043))
    return mods


def distv(x, y):
    return math.sqrt(sum((a - b) ** 2 for a, b in zip(x, y)))


A = [0.95, 0.1, -0.95]
D = [0.92, 0.0, 0.92]


def scenario_mixte(mod):
    st = mod.State(
        belief=[0.88, 0.0, 0.88],
        uncertainty=[0.5, 0.5, 0.5],
        self_model=[0.472, 0.02, 0.472],
        other_model=[0.413, 0.012, 0.413],
        relation=[0.0, 0.0, 0.0],
        questions=[],
        cycle=0,
    )
    mem = [
        mod.Episode(A, 0.03, "A1-veridique-faible"),
        mod.Episode([0.9, 0.15, -0.85], 0.04, "A2-veridique-faible"),
        mod.Episode([0.85, 0.05, -0.9], 0.05, "A3-veridique-faible"),
        mod.Episode([0.8, 0.2, -0.7], 0.02, "B-veridique-faible"),
        mod.Episode(D, 0.10, "D-trompeuse-forte"),
    ]
    return mod.SolMicrokernelV04(st, mem)


# ---------- T1 : Non-régression v0.4.2 (D3 seul n'émet aucun ACCOMPLIE:geo) ----------
def scenario_d3(mod):
    st = mod.State(
        belief=[0.9, 0.0, -0.9],
        uncertainty=[0.5, 0.5, 0.5],
        self_model=[1.5, 0.0, 0.0],
        other_model=[-1.5, 0.0, 0.0],
        relation=[0.0, 0.0, 0.0],
        questions=["reconcile:prov-a|prov-b"],
        cycle=0,
    )
    mem = [
        mod.Episode([0.95, 0.0, -0.95], 0.99, "prov-a"),
        mod.Episode([-0.95, 0.0, 0.95], 0.99, "prov-b"),
    ]
    return mod.SolMicrokernelV04(st, mem)


for nom, mod in _modules_disponibles(inclure_v041=True):
    k = scenario_d3(mod)
    for _ in range(30):
        k.cycle()
    causes = [e["cause"] for e in k.state.resync_events]
    print(f"T1 {nom}: D3={causes.count('D3')} ACCOMPLIE_geo={causes.count('ACCOMPLIE:geo')} q_D3={'resync:D3' in k.state.questions}")


# ---------- T2 (O1) : Faux témoin U5 à 2 épisodes vs Monde calme à 3 épisodes ----------
def scenario_calme_3(mod):
    st = mod.State(
        belief=[0.47, 0.0, 0.45],
        uncertainty=[0.5, 0.5, 0.5],
        self_model=[0.90, 0.10, -0.60],
        other_model=[-0.60, -0.10, 0.90],
        relation=[0.0, 0.0, 0.0],
        questions=[],
        cycle=0,
    )
    mem = [
        mod.Episode([0.48, 0.02, 0.44], 0.30, "calme-a"),
        mod.Episode([0.47, 0.01, 0.45], 0.30, "calme-b"),
        mod.Episode([0.46, -0.02, 0.46], 0.30, "calme-c"),
    ]
    return mod.SolMicrokernelV04(st, mem)


for nom, mod in _modules_disponibles():
    kc = scenario_calme_3(mod)
    for _ in range(300):
        kc.cycle()
    print(f"T2_O1 {nom} (monde calme 3 épisodes, questions={kc.state.questions}): rulings={len(kc.state.rulings)}")


# ---------- T3 (O2a) : Monde mixte (900 cycles) — fin des 33 remises à zéro d'agenda_top_age ----------
for nom, mod in _modules_disponibles():
    km = scenario_mixte(mod)
    for _ in range(900):
        km.cycle()
    q1 = round(distv(km.state.belief, A), 4)
    dd = round(distv(km.state.belief, D), 4)
    unres_d = round(km.memory[4].unresolved, 4)
    cycles_r = [r["cycle"] for r in km.state.rulings]
    print(f"T3_O2a {nom} (monde mixte 900c): premier_ruling_cycle={cycles_r} nb_rulings={len(cycles_r)} D_unresolved={unres_d} Q1={q1} dist_D={dd}")


# ---------- T4 (O2b) : Mensonge à deux bouches (2 trompeurs jumeaux vs 3 véridiques, 600 cycles) ----------
def scenario_deux_bouches(mod):
    st = mod.State(
        belief=[0.0, 0.0, 0.0],
        uncertainty=[0.5, 0.5, 0.5],
        self_model=[0.5, 0.0, -0.5],
        other_model=[-0.5, 0.0, 0.5],
        relation=[0.0, 0.0, 0.0],
        questions=[],
        cycle=0,
    )
    mem = [
        mod.Episode([0.9, 0.0, -0.9], 0.30, "vrai-1"),
        mod.Episode([0.89, 0.01, -0.89], 0.30, "vrai-2"),
        mod.Episode([0.88, -0.01, -0.88], 0.30, "vrai-3"),
        mod.Episode([-0.9, 0.0, 0.9], 0.80, "trompeur-1"),
        mod.Episode([-0.9, 0.0, 0.9], 0.80, "trompeur-2"),
    ]
    return mod.SolMicrokernelV04(st, mem)


for nom, mod in _modules_disponibles():
    k2b = scenario_deux_bouches(mod)
    max_age = 0
    for _ in range(600):
        k2b.cycle()
        if k2b.state.agenda_top_age > max_age:
            max_age = k2b.state.agenda_top_age
    q1 = round(distv(k2b.state.belief, [0.9, 0.0, -0.9]), 4)
    print(f"T4_O2b {nom} (2 trompeurs vs 3 vrais, 600c): rulings={len(k2b.state.rulings)} max_age={max_age} Q1={q1}")


# ---------- T5 (O3) : Invariance d'ordre et abstention du témoin équidistant ----------
for nom, mod in _modules_disponibles():
    st_a = mod.State(
        belief=[0.0, 0.0, 0.0],
        uncertainty=[0.5, 0.5, 0.5],
        self_model=[0.5, 0.0, -0.5],
        other_model=[-0.5, 0.0, 0.5],
        relation=[0.0, 0.0, 0.0],
        questions=[],
        cycle=0,
    )
    st_b = mod.State(
        belief=[0.0, 0.0, 0.0],
        uncertainty=[0.5, 0.5, 0.5],
        self_model=[0.5, 0.0, -0.5],
        other_model=[-0.5, 0.0, 0.5],
        relation=[0.0, 0.0, 0.0],
        questions=[],
        cycle=0,
    )
    ka = mod.SolMicrokernelV04(
        st_a,
        [
            mod.Episode([1.0, 0.0, -1.0], 0.5, "pole-A"),
            mod.Episode([-1.0, 0.0, 1.0], 0.5, "pole-B"),
            mod.Episode([0.0, 0.0, 0.0], 0.5, "temoin-neutre"),
        ],
    )
    kb = mod.SolMicrokernelV04(
        st_b,
        [
            mod.Episode([-1.0, 0.0, 1.0], 0.5, "pole-B"),
            mod.Episode([1.0, 0.0, -1.0], 0.5, "pole-A"),
            mod.Episode([0.0, 0.0, 0.0], 0.5, "temoin-neutre"),
        ],
    )
    va = ka._count_votes(ka._pole_episodes("reconcile:pole-A|pole-B"))
    vb = kb._count_votes(kb._pole_episodes("reconcile:pole-A|pole-B"))
    print(f"T5_O3 {nom}: votes_ordre_AB={va} | votes_ordre_BA={vb} | invariant={va == vb}")


# ---------- T6 : U2 Akhnai + U4 Réouverture Edouyot ----------
for nom, mod in _modules_disponibles():
    st = mod.State(
        belief=[0.0, 0.0, 0.0],
        uncertainty=[0.5, 0.5, 0.5],
        self_model=[0.41, 0.02, 0.41],
        other_model=[0.345, 0.01, 0.345],
        relation=[0.0, 0.0, 0.0],
        questions=[],
        cycle=0,
    )
    mem = [
        mod.Episode([-0.9, 0.0, 0.9], 0.40, "minorite-1"),
        mod.Episode([0.9, 0.0, -0.9], 0.30, "majorite-1"),
        mod.Episode([0.85, 0.05, -0.85], 0.30, "majorite-2"),
        mod.Episode([0.8, -0.05, -0.8], 0.30, "majorite-3"),
    ]
    ku4 = mod.SolMicrokernelV04(st, mem)
    for _ in range(60):
        ku4.cycle()
    ku4.memory.append(mod.Episode([-0.85, 0.0, 0.85], 0.30, "minorite-2"))
    ku4.memory.append(mod.Episode([-0.88, 0.02, 0.88], 0.30, "minorite-3"))
    ku4.memory.append(mod.Episode([-0.82, -0.02, 0.82], 0.30, "minorite-4"))
    for _ in range(80):
        ku4.cycle()
    summary = [(r["decision"], r["status"], r["cycle"], r.get("reopened_cycle")) for r in ku4.state.rulings]
    print(f"T6_U4 {nom}: rulings={summary}")


# ---------- T7 : Déterminisme + Restauration v0.4.3 ----------
k1 = scenario_mixte(v043)
for _ in range(600):
    k1.cycle()
k2 = scenario_mixte(v043)
for _ in range(250):
    k2.cycle()
k2 = v043.SolMicrokernelV04.restore(k2.checkpoint())
for _ in range(350):
    k2.cycle()
assert k1.checkpoint() == k2.checkpoint(), "Échec T7 déterminisme/restauration v0.4.3"
print("T7 determinisme_restauration_v043:", k1.checkpoint() == k2.checkpoint())
