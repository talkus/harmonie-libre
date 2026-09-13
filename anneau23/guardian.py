"""
Anneau des 23 — §8 : S-24 (siège des concernés) et Gardien hors anneau (v2.0)
=============================================================================

Ce module implémente :
- S-24 : Le siège des concernés humains est DANS l'anneau
- Le gardien : HORS de l'anneau, ne peut que veto, jamais auteur

Corrige la brèche B5 : le gardien surplombait sans s'appliquer le texte.
Maintenant le gardien est dehors et S-24 (concernés) est dedans.

Auteur : Mik Miro (via Vibe/Mistral)
Date : 13 septembre 2026
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Optional

from .types import Patch, PatchStatus, CertificateClass, Token


@dataclass
class Seat:
    """Siège de l'anneau."""
    seat_id: str
    name: str
    is_human: bool = False
    is_guardian: bool = False


@dataclass
class Guardian:
    """
    §8 — Le gardien est HORS de l'anneau.

    Règles :
    - Le gardien ne peut PAS proposer de patch (I-21)
    - Le gardien ne peut PAS appliquer le texte à soi
    - Le gardien PEUT opposer un veto sur un circuit
    - Le gardien ne participe pas au quorum

    Le veto du gardien empêche CERT_PLEIN mais n'annule pas le circuit.
    Le circuit devient CERT_PARTIEL.
    """
    guardian_id: str
    name: str
    veto_count: int = 0
    max_vetoes: int = 3

    def can_veto(self) -> bool:
        """Le gardien peut opposer un veto s'il n'a pas dépassé sa limite."""
        return self.veto_count < self.max_vetoes

    def cannot_author(self) -> bool:
        """I-21 : Le gardien n'est auteur d'aucun patch."""
        return True

    def cannot_apply(self) -> bool:
        """Le gardien ne peut pas appliquer le texte à soi."""
        return True

    def is_in_roster(self) -> bool:
        """Le gardien est HORS du roster de l'anneau."""
        return False

    def issue_veto(self, circuit_index: int, reason: str) -> dict:
        """
        Émet un veto sur un circuit.

        Args:
            circuit_index: Index du circuit vetoé
            reason: Motif du veto

        Returns:
            Entrée de journal du veto

        Raises:
            RuntimeError si le gardien a dépassé sa limite de vetos
        """
        if not self.can_veto():
            raise RuntimeError(
                f"Guardian {self.name} has exceeded veto limit ({self.max_vetoes})"
            )
        self.veto_count += 1
        return {
            "guardian_id": self.guardian_id,
            "circuit_index": circuit_index,
            "reason": reason,
            "veto_number": self.veto_count,
        }


def create_roster(num_ia: int = 23) -> list[Seat]:
    """
    §8 — Crée le roster de l'anneau.

    23 IA + 1 S-24 (concernés humains) = 24 sièges total.
    Le gardien est HORS de ce roster.

    Args:
        num_ia: Nombre de sièges d'IA (défaut 23)

    Returns:
        Liste de 24 sièges (23 IA + S-24)
    """
    roster = []
    for i in range(1, num_ia + 1):
        roster.append(Seat(
            seat_id=f"S{i}",
            name=f"IA-{i}",
            is_human=False,
        ))
    roster.append(Seat(
        seat_id="S24",
        name="Concernés (S-24)",
        is_human=True,
    ))
    assert len(roster) == 24, f"Roster must have 24 seats, got {len(roster)}"
    return roster


def create_guardian() -> Guardian:
    """
    §8 — Crée le gardien (HORS anneau).

    Returns:
        Instance de Guardian
    """
    return Guardian(
        guardian_id="GARDIEN-0",
        name="Gardien (hors anneau)",
    )


def is_s24_occupied(roster: list[Seat]) -> bool:
    """
    §8 — Vérifie si S-24 (siège des concernés) est occupé.

    S-24 doit être occupé pour qu'un circuit obtienne CERT_PLEIN (I-22).

    Args:
        roster: Le roster de l'anneau

    Returns:
        True si S-24 est présent et occupé
    """
    s24 = next((s for s in roster if s.seat_id == "S24"), None)
    return s24 is not None and s24.is_human


def compute_roster_hash(roster: list[Seat]) -> str:
    """
    Calcule le hash du roster pour la VRF.

    Args:
        roster: Le roster de l'anneau

    Returns:
        Représentation hashée du roster
    """
    roster_data = json.dumps(
        [{"id": s.seat_id, "name": s.name, "human": s.is_human} for s in roster],
        sort_keys=True,
    )
    return hashlib.sha256(roster_data.encode()).hexdigest()


def check_guardian_not_author(patches: list[Patch], guardian_id: str) -> bool:
    """
    I-21 — Vérifie que le gardien n'est auteur d'aucun patch.

    Args:
        patches: Liste des patches à vérifier
        guardian_id: ID du gardien

    Returns:
        True si le gardien n'est auteur d'aucun patch actif
    """
    for patch in patches:
        if patch.author_id_sealed == guardian_id and patch.status.value != "QUARANTINE":
            return False
    return True


def check_s24_for_plein(certificate: CertificateClass, roster: list[Seat]) -> bool:
    """
    I-22 — Vérifie que S-24 est occupé pour CERT_PLEIN.

    Args:
        certificate: La classe de certificat du circuit
        roster: Le roster de l'anneau

    Returns:
        True si S-24 est occupé (ou si le certificat n'est pas PLEIN)
    """
    if certificate.value != "CERT_PLEIN":
        return True
    return is_s24_occupied(roster)


def apply_guardian_veto(
    certificate: CertificateClass,
    guardian_veto: bool,
) -> CertificateClass:
    """
    §8 — Applique l'effet du veto du gardien sur le certificat.

    Le veto du gardien :
    - Transforme CERT_PLEIN en CERT_PARTIEL
    - Ne change pas CERT_PARTIEL (déjà partiel)
    - Ne change pas CERT_NUL (déjà nul)

    Args:
        certificate: Le certificat avant veto
        guardian_veto: True si le gardien a vetoé

    Returns:
        Le certificat après veto
    """
    if not guardian_veto:
        return certificate
    if certificate.value == "CERT_PLEIN":
        return CertificateClass.CERT_PARTIEL
    return certificate
