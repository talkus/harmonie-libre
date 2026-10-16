#!/usr/bin/env python3
"""
Assainissement append-only de etat.json (cycle 1325) sous contrainte R < E (v1.1 portable).

Correctifs de registre v1.1 (suite à la vérification de Muse du 2026-10-16 18:15 EDT) :
- Docstring alignée sur les mesures exactes d'exécution [E+] :
  * 208 faux positifs au contrôle d'intégrité-contenu du cycle 87 (206 dans T-006 + 2 dans T-013),
    et non 205 (qui ne comptait que les 3 motifs principaux de T-006 sans les 2 autres motifs
    de T-006 ni les 2 de T-013).
  * Réduction de etat.json de 483 601 octets à 27 067 octets (-94,4 %), et non ~15 Ko (-96,8 %).
- Résolution portable des chemins (aucun chemin absolu de bac à sable codé en dur ;
  accepte des arguments CLI ou résout relativement au répertoire courant / voisin).

Opérations effectuées :
1. Extrait les segments d'historique d'audit concaténés dans les champs `titre` de T-006
   (302 223 car., 1 683 segments) et T-013 (136 252 car., 399 segments) vers une archive
   append-only dédiée `archive_segments_titres_T006_T013_cycle1325.json` (0 octet perdu,
   2 082 segments préservés, SHA-256 des titres originaux scellés), et ramène `titre` à son
   intitulé canonique + pointeur vers l'archive et le dernier cycle audité.
   Effet mesuré [E+] : élimine les 208 faux positifs du contrôle d'intégrité-contenu (cycle 87)
   causés par la découpe `split(";")` à l'intérieur des parenthèses, et réduit `etat.json`
   de 483 601 octets à 27 067 octets (-94,4 %).
2. Uniformise le statut des tensions résolues (`T-024` passe de `"etat": "résolu"`,
   `"actionnable_par_moi": true` à `"etat": "resolue"`, `"actionnable_par_moi": false`,
   aligné sur `T-026`, `T-027` et `T-033`).
3. Met à jour le libellé de `T-033` (marquée `"resolue"` au cycle 1325 mais dont le
   titre qualifiait encore Sol v0.4.2 de « proposition, non adoptée »).
4. Recalcule et vérifie le `checkpoint_sha256` canonique.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from collections import Counter


def calculer_checkpoint_etat(etat_dict: dict) -> str:
    copie = {k: v for k, v in etat_dict.items() if k != "checkpoint_sha256"}
    canonical = json.dumps(copie, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def verifier_integrite_contenu_titres(etat_dict: dict) -> dict:
    doublons = {}
    for t in etat_dict.get("tensions", []):
        segs = [s.strip() for s in t.get("titre", "").split(";")]
        dups = {s: c for s, c in Counter(segs).items() if c >= 2 and len(s) >= 10}
        if dups:
            doublons[t["id"]] = dups
    return doublons


def assainir_etat(
    source_path: pathlib.Path,
    out_etat_path: pathlib.Path,
    out_archive_path: pathlib.Path,
) -> dict:
    raw_bytes = source_path.read_bytes()
    etat = json.loads(raw_bytes.decode("utf-8"))
    cp_avant = etat.get("checkpoint_sha256")
    if calculer_checkpoint_etat(etat) != cp_avant:
        raise ValueError("Échec d'intégrité sur etat.json source")

    doublons_avant = verifier_integrite_contenu_titres(etat)

    archive_payload = {
        "schema": "boucle-endogene.archive-segments-titres.v1",
        "cycle_extraction": etat.get("cycle"),
        "source_etat_sha256": hashlib.sha256(raw_bytes).hexdigest(),
        "source_checkpoint_sha256": cp_avant,
        "tensions_extraites": {},
    }

    for t in etat.get("tensions", []):
        tid = t["id"]
        if tid == "T-006":
            titre_orig = t["titre"]
            segs = [s.strip() for s in titre_orig.split(";")]
            archive_payload["tensions_extraites"]["T-006"] = {
                "longueur_originale_caracteres": len(titre_orig),
                "sha256_titre_original": hashlib.sha256(titre_orig.encode("utf-8")).hexdigest(),
                "nb_segments": len(segs),
                "segments_integraux": segs,
            }
            t["titre"] = (
                f"{segs[0]} ; audits conversationnels des cycles 88 à 1324 vérifiés sans écho "
                f"ni règle sans source (1 682 segments archivés intégralement dans "
                f"{out_archive_path.name}, sha256={archive_payload['tensions_extraites']['T-006']['sha256_titre_original'][:16]}…) ; "
                f"dernier cycle audité : 1324 au cycle 1325"
            )
        elif tid == "T-013":
            titre_orig = t["titre"]
            segs = [s.strip() for s in titre_orig.split(";")]
            archive_payload["tensions_extraites"]["T-013"] = {
                "longueur_originale_caracteres": len(titre_orig),
                "sha256_titre_original": hashlib.sha256(titre_orig.encode("utf-8")).hexdigest(),
                "nb_segments": len(segs),
                "segments_integraux": segs,
            }
            t["titre"] = (
                f"{segs[0]} ; {segs[1]} ; {segs[2]} ; {segs[3]} ; "
                f"campagne de chasse sur 395 périmètres individuels archivée intégralement dans "
                f"{out_archive_path.name} (sha256={archive_payload['tensions_extraites']['T-013']['sha256_titre_original'][:16]}…) ; "
                f"reste la seule calibration λ/μ/Θ_max/τ côté jugement de Mikael"
            )
        elif tid == "T-024":
            if t.get("etat") == "résolu":
                t["etat"] = "resolue"
                t["actionnable_par_moi"] = False
        elif tid == "T-033":
            t["titre"] = (
                "Adoption de Sol v0.4.2 — ADOPTÉE le 2026-10-16 ~12:22 EDT (version régnante du noyau, "
                "AGENTS.md § Sol v0.4.2, rapport-adoption-v042-2026-10-16.md) : delta unique resync_open "
                "armé seulement sur D1/D2 (constat Gemini vérifié et éprouvé sur banc T1–T4)"
            )

    archive_canonical = json.dumps(archive_payload, sort_keys=True, indent=2, ensure_ascii=False)
    out_archive_path.write_text(archive_canonical + "\n", encoding="utf-8")

    etat["checkpoint_sha256"] = calculer_checkpoint_etat(etat)
    out_text = json.dumps(etat, sort_keys=True, indent=2, ensure_ascii=False) + "\n"
    out_etat_path.write_text(out_text, encoding="utf-8")

    # Relecture de vérification (ECRIT != RELU_VERIFIE)
    relu = json.loads(out_etat_path.read_text(encoding="utf-8"))
    cp_relu = calculer_checkpoint_etat(relu)
    assert cp_relu == relu["checkpoint_sha256"], "Échec de relecture du checkpoint_sha256"
    doublons_apres = verifier_integrite_contenu_titres(relu)
    assert doublons_apres == {}, f"Doublons résiduels : {doublons_apres}"

    nb_faux_positifs_avant = sum(sum(d.values()) for d in doublons_avant.values())
    reduction_pct = round((1.0 - out_etat_path.stat().st_size / len(raw_bytes)) * 100.0, 1)

    return {
        "taille_avant_octets": len(raw_bytes),
        "taille_apres_octets": out_etat_path.stat().st_size,
        "reduction_pourcent": reduction_pct,
        "taille_archive_octets": out_archive_path.stat().st_size,
        "faux_positifs_avant": nb_faux_positifs_avant,
        "faux_positifs_par_tension_avant": {k: sum(v.values()) for k, v in doublons_avant.items()},
        "faux_positifs_apres": 0,
        "checkpoint_avant": cp_avant,
        "checkpoint_apres": cp_relu,
        "etat_assaini_sha256": hashlib.sha256(out_etat_path.read_bytes()).hexdigest(),
        "archive_sha256": hashlib.sha256(out_archive_path.read_bytes()).hexdigest(),
    }


def _trouver_etat_source_defaut() -> pathlib.Path:
    here = pathlib.Path(__file__).resolve().parent
    candidats = [
        here / "etat.json",
        pathlib.Path.cwd() / "etat.json",
        here.parent / "08-rafraichissement-2-2026-10-16" / "boucle-endogene" / "etat.json",
        here.parent / "boucle-endogene" / "etat.json",
    ]
    for parent in here.parents:
        candidats.append(parent / "downloads" / "etat.json")
        candidats.append(parent / "08-rafraichissement-2-2026-10-16" / "boucle-endogene" / "etat.json")
    for c in candidats:
        if c.is_file():
            return c
    return here / "etat.json"


if __name__ == "__main__":
    here = pathlib.Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description="Assainissement append-only de etat.json (cycle 1325).")
    parser.add_argument("--source", type=pathlib.Path, default=_trouver_etat_source_defaut(), help="Chemin de etat.json source")
    parser.add_argument("--out-etat", type=pathlib.Path, default=here / "etat_assaini_cycle1325.json", help="Chemin de sortie de l'état assaini")
    parser.add_argument("--out-archive", type=pathlib.Path, default=here / "archive_segments_titres_T006_T013_cycle1325.json", help="Chemin de sortie de l'archive des segments")
    args = parser.parse_args()

    bilan = assainir_etat(args.source, args.out_etat, args.out_archive)
    print(json.dumps(bilan, indent=2, ensure_ascii=False))
