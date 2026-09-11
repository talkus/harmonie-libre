#!/usr/bin/env python3
"""
Anneau des 23 — Module VRF (Verifiable Random Function)
Version: 2.0
Date: 2026-09-11

Génération et vérification de permutations cryptographiques
pour la sélection déterministe des agents validateurs.
"""

import hashlib
import json
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class VRFResult:
    """Résultat d'une évaluation VRF."""
    output: bytes
    proof: bytes
    seed: str
    
    def to_hex(self) -> Tuple[str, str]:
        return self.output.hex(), self.proof.hex()


class Anneau23VRF:
    """
    VRF basée sur SHA-256 pour l'Anneau des 23.
    
    La permutation générée détermine l'ordre des 23 agents
    validateurs pour chaque cycle de validation.
    """
    
    NOMBRE_AGENTS = 23
    
    def __init__(self, seed: str):
        self.seed = seed
    
    def _hash(self, data: str) -> bytes:
        """Hachage SHA-256 déterministe."""
        return hashlib.sha256(data.encode('utf-8')).digest()
    
    def evaluer(self) -> VRFResult:
        """
        Évalue la VRF et produit un output + proof.
        """
        output = self._hash(self.seed)
        proof = self._hash(f"{self.seed}:proof")
        return VRFResult(output=output, proof=proof, seed=self.seed)
    
    def generer_permutation(self) -> List[int]:
        """
        Génère une permutation de Fisher-Yates déterministe
        basée sur la seed VRF.
        """
        n = self.NOMBRE_AGENTS
        perm = list(range(n))
        
        for i in range(n - 1, 0, -1):
            data = f"{self.seed}:{i}:{n}".encode('utf-8')
            h = hashlib.sha256(data).digest()
            j = int.from_bytes(h[:8], 'big') % (i + 1)
            perm[i], perm[j] = perm[j], perm[i]
        
        return perm
    
    def verifier_permutation(self, perm: List[int]) -> bool:
        """
        Vérifie qu'une permutation correspond bien à la seed.
        """
        if sorted(perm) != list(range(self.NOMBRE_AGENTS)):
            return False
        return perm == self.generer_permutation()
    
    def selectionner_validateurs(self, k: int = 12) -> List[int]:
        """
        Sélectionne les k premiers validateurs selon la permutation.
        Par défaut, 12 agents sur 23 pour atteindre le seuil de majorité.
        """
        perm = self.generer_permutation()
        return perm[:k]
    
    def cycle_hash(self, cycle_numero: int) -> str:
        """
        Génère le hash d'un cycle de validation.
        """
        return self._hash(f"{self.seed}:cycle:{cycle_numero}").hex()


def demo():
    """Démonstration du module VRF."""
    print("=== Démonstration VRF Anneau des 23 ===\n")
    
    vrf = Anneau23VRF(seed="cycle-2026-09-11-mik")
    
    # Évaluation VRF
    result = vrf.evaluer()
    output_hex, proof_hex = result.to_hex()
    print(f"VRF Output: {output_hex[:32]}...")
    print(f"VRF Proof:  {proof_hex[:32]}...")
    
    # Permutation
    perm = vrf.generer_permutation()
    print(f"\nPermutation: {perm}")
    print(f"Vérification: {'✅ Valide' if vrf.verifier_permutation(perm) else '❌ Invalide'}")
    
    # Sélection des validateurs
    validateurs = vrf.selectionner_validateurs(12)
    print(f"\nValidateurs sélectionnés (12/23): {validateurs}")
    
    # Hash du cycle
    cycle_hash = vrf.cycle_hash(1)
    print(f"Hash du cycle 1: {cycle_hash[:32]}...")


if __name__ == "__main__":
    demo()
