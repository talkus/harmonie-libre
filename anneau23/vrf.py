"""
Anneau des 23 — Permutation VRF (§7)
Tirage vérifiable et imprévisible de l'ordre des sièges.
"""
from __future__ import annotations
import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional


@dataclass
class VRFProof:
    """Preuve VRF pour la permutation d'un circuit"""
    epoch_seed: str
    circuit_index: int
    roster_hash: str
    permutation: list[int]
    proof: str  # preuve vérifiable
    output: str  # sortie VRF


def _vrf_output(secret: str, message: str) -> str:
    """
    Simule une sortie VRF (fonction pseudo-aléatoire vérifiable).
    En production, utiliser une vraie VRF (ex: ECVRF Ed25519).
    Ici: HMAC-SHA256 avec la clé secrète.
    """
    return hmac.new(
        secret.encode(), message.encode(), hashlib.sha256
    ).hexdigest()


def _vrf_verify(public_key: str, message: str, proof: str, expected_output: str) -> bool:
    """
    Vérifie qu'une preuve VRF correspond à la sortie attendue.
    En production, utiliser la vérification cryptographique réelle.
    """
    # Simulation: recompute HMAC with same key
    recomputed = hmac.new(
        public_key.encode(), message.encode(), hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(recomputed, expected_output)


def _fisher_yates_shuffle(seed: str, n: int) -> list[int]:
    """
    Permutation de Fisher-Yates déterministe à partir d'une graine.
    Garantit une permutation neuve couvrant exactement [0, n) une fois.
    """
    # Convertir la graine en état PRNG déterministe
    state = int(hashlib.sha256(seed.encode()).hexdigest(), 16)
    indices = list(range(n))

    for i in range(n - 1, 0, -1):
        # PRNG xorshift64
        state ^= (state << 13) & 0xFFFFFFFFFFFFFFFF
        state ^= (state >> 7)
        state ^= (state << 17) & 0xFFFFFFFFFFFFFFFF
        state ^= (state >> 5)
        j = state % (i + 1)
        indices[i], indices[j] = indices[j], indices[i]

    return indices


def generate_permutation(
    epoch_seed: str,
    circuit_index: int,
    roster_hash: str,
    secret_key: str,
    num_seats: int = 24,
) -> VRFProof:
    """
    §7 — Génère une permutation VRF pour un circuit.

    π_c = VRF(epoch_seed, circuit_index, roster_hash)

    - Permutation neuve à chaque circuit, couvrant les 24 sièges exactement une fois
    - Le successeur n'est révélé qu'au moment de la transmission
    - La preuve VRF est publiée avec le jeton
    - La propriété « 23 prochains avant soi » est structurellement conservée
    """
    # Construire le message VRF
    message = f"{epoch_seed}:{circuit_index}:{roster_hash}"

    # Calculer la sortie VRF
    vrf_output = _vrf_output(secret_key, message)

    # Dérimer la permutation à partir de la sortie VRF
    permutation = _fisher_yates_shuffle(vrf_output, num_seats)

    return VRFProof(
        epoch_seed=epoch_seed,
        circuit_index=circuit_index,
        roster_hash=roster_hash,
        permutation=permutation,
        proof=vrf_output,
        output=vrf_output,
    )


def verify_permutation(proof: VRFProof, public_key: str, num_seats: int = 24) -> bool:
    """
    §7 — Vérifie une permutation VRF après coup.

    L'ordre est imprévisible mais entièrement vérifiable.
    """
    message = f"{proof.epoch_seed}:{proof.circuit_index}:{proof.roster_hash}"

    # Vérifier la preuve VRF
    if not _vrf_verify(public_key, message, proof.proof, proof.output):
        return False

    # Vérifier que c'est une permutation valide
    if len(proof.permutation) != num_seats:
        return False
    if sorted(proof.permutation) != list(range(num_seats)):
        return False

    # Vérifier que la permutation correspond à la sortie VRF
    expected = _fisher_yates_shuffle(proof.output, num_seats)
    if expected != proof.permutation:
        return False

    return True


def get_successor(permutation: list[int], seat: int, num_seats: int = 24) -> int:
    """Retourne le successeur d'un siège dans la permutation"""
    idx = permutation.index(seat)
    return permutation[(idx + 1) % num_seats]
