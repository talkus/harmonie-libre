#!/usr/bin/env python3
"""
Anneau des 23 — §7 Ordonnancement par VRF
Permutation déterministe et vérifiable des clauses de l'Anneau.
"""

import hashlib
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class VRFResultat:
    """Résultat d'une permutation VRF."""
    seed: str
    permutation: List[int]
    preuve: str  # hash vérifiable de la permutation


def vrf_permutation(seed: str, n: int) -> VRFResultat:
    """
    Génère une permutation déterministe et vérifiable de [0, n-1]
    à partir d'une graine (seed).

    Utilise un hachage SHA-256 itéré pour produire un ordre
    reproductible et auditable.

    Args:
        seed: Graine de la permutation (ex: horodatage ISO + mission_id)
        n: Nombre d'éléments à permuter

    Returns:
        VRFResultat contenant la permutation et sa preuve cryptographique.
    """
    if n <= 0:
        raise ValueError("n doit être positif")

    # Générer n valeurs de hachage déterministes
    hashes = []
    for i in range(n):
        data = f"{seed}:{i}".encode("utf-8")
        h = hashlib.sha256(data).hexdigest()
        hashes.append((i, h))

    # Trier par valeur de hachage pour obtenir la permutation
    sorted_hashes = sorted(hashes, key=lambda x: x[1])
    permutation = [idx for idx, _ in sorted_hashes]

    # Preuve: hash de concaténation de tous les hachages triés
    preuve_data = "|".join(h for _, h in sorted_hashes)
    preuve = hashlib.sha256(preuve_data.encode("utf-8")).hexdigest()

    return VRFResultat(
        seed=seed,
        permutation=permutation,
        preuve=preuve,
    )


def verifier_permutation(seed: str, n: int, permutation: List[int], preuve: str) -> bool:
    """
    Vérifie qu'une permutation VRF est correcte en recalculant
    la permutation à partir de la graine.

    Args:
        seed: Graine utilisée
        n: Taille de la permutation
        permutation: La permutation à vérifier
        preuve: La preuve cryptographique

    Returns:
        True si la permutation est valide, False sinon.
    """
    resultat_attendu = vrf_permutation(seed, n)

    if permutation != resultat_attendu.permutation:
        return False

    if preuve != resultat_attendu.preuve:
        return False

    # Vérifier que c'est bien une permutation (tous les éléments uniques)
    if sorted(permutation) != list(range(n)):
        return False

    return True


def ordonnancer_clauses(seed: str, nb_clauses: int = 23) -> List[int]:
    """
    Ordonne les 23 clauses de l'Anneau selon une permutation VRF.

    Args:
        seed: Graine d'ordonnancement (ex: "2026-09-11:mission-001")
        nb_clauses: Nombre de clauses (défaut: 23)

    Returns:
        Liste des indices de clauses dans l'ordre VRF.
    """
    resultat = vrf_permutation(seed, nb_clauses)
    return resultat.permutation


if __name__ == "__main__":
    # Exemple d'utilisation
    seed = "2026-09-11:anneau23:audit-001"
    ordre = ordonnancer_clauses(seed)
    print(f"Ordre VRF pour seed='{seed}':")
    print(f"  {ordre}")

    # Vérification
    resultat = vrf_permutation(seed, 23)
    est_valide = verifier_permutation(seed, 23, resultat.permutation, resultat.preuve)
    print(f"  Vérification: {'OK' if est_valide else 'ÉCHEC'}")
    print(f"  Preuve: {resultat.preuve[:32]}...")
