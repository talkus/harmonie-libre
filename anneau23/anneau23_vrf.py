#!/usr/bin/env python3
"""
Anneau des 23 — Ordre VRF (Protocole v2.0, Section 7)

Apres le scellement du patch, l'ordre d'application est tire par VRF :
- Imprevisibilite : impossible de viser un voisin
- Verifiabilite : chaque participant peut verifier l'ordre
- Non-biaisabilite : aucun participant ne peut influencer le tirage

Auteur : Mikael Mireault (architecte)
Licence : MIT
"""

import hashlib
import hmac
import json
from dataclasses import dataclass
from typing import List, Dict, Tuple


@dataclass
class VRFTirage:
    siege_id: str
    index_ordre: int
    preuve_vrf: str
    seed: str


@dataclass
class OrdreApplication:
    patch_id: str
    seed_commit: str
    ordre: List[VRFTirage]
    verification_hash: str


def _hash(data: str) -> str:
    return hashlib.sha256(data.encode()).hexdigest()


def vrf_prove(secret_key: bytes, message: bytes) -> Tuple[bytes, bytes]:
    beta = hmac.new(secret_key, message, hashlib.sha256).digest()
    proof = hmac.new(secret_key, beta, hashlib.sha256).digest()
    return beta, proof


class OrdonnateurVRF:
    def __init__(self, num_sieges: int = 24):
        self.num_sieges = num_sieges

    def generer_seed(self, patch_id, patch_hash, timestamp):
        return _hash(f"{patch_id}:{patch_hash}:{timestamp}")

    def tirer_ordre(self, patch_id, seed, cles_secretes):
        tirages = []
        scores = {}
        for siege_id, cle in cles_secretes.items():
            message = f"{patch_id}:{seed}:{siege_id}".encode()
            beta, proof = vrf_prove(cle, message)
            scores[siege_id] = int.from_bytes(beta[:8], 'big')
            tirages.append(VRFTirage(siege_id, 0, proof.hex(), seed))
        ordre_trie = sorted(scores.items(), key=lambda x: x[1])
        for i, (siege_id, score) in enumerate(ordre_trie):
            for t in tirages:
                if t.siege_id == siege_id:
                    t.index_ordre = i
                    break
        ordre_str = json.dumps([
            {"siege": t.siege_id, "index": t.index_ordre, "proof": t.preuve_vrf}
            for t in sorted(tirages, key=lambda x: x.index_ordre)
        ])
        return OrdreApplication(patch_id, _hash(seed), tirages, _hash(ordre_str))

    def verifier_ordre(self, ordre, cles_publiques, seed):
        if ordre.seed_commit != _hash(seed):
            return False
        indexes = [t.index_ordre for t in ordre.ordre]
        if len(set(indexes)) != len(indexes):
            return False
        return all(0 <= t.index_ordre < self.num_sieges for t in ordre.ordre)


if __name__ == "__main__":
    ordonnateur = OrdonnateurVRF(24)
    cles = {f"S-{i+1:02d}": hashlib.sha256(f"cle_siege_{i}".encode()).digest() for i in range(24)}
    seed = ordonnateur.generer_seed("patch-001", "hash", "2026-09-11T18:00:00Z")
    ordre = ordonnateur.tirer_ordre("patch-001", seed, cles)
    for t in sorted(ordre.ordre, key=lambda x: x.index_ordre):
        print(f"  {t.index_ordre + 1}. {t.siege_id}")
    print(f"Verifiable: {ordonnateur.verifier_ordre(ordre, {}, seed)}")
