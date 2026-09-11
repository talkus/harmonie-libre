"""
Anneau des 23 — Classes de certificats (§10)
CERT_PLEIN, CERT_PARTIEL, CERT_NUL
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from .types import CertificateClass, Token, NUM_SIEGES, NUM_PROCHAINS


@dataclass
class CircuitReport:
    """Rapport d'un circuit pour la classification"""
    circuit_index: int
    attestations: list[str]  # IDs des sièges ayant attesté
    vetoes: list[str]        # IDs des sièges ayant veto
    vrf_verified: bool
    journal_intact: bool
    permutation_proof: str
    roster_full: bool  # tous les sièges présents


def classify_certificate(report: CircuitReport) -> CertificateClass:
    """
    §10 — Classe un circuit en CERT_PLEIN, CERT_PARTIEL ou CERT_NUL.

    CERT_PLEIN  : 23 attestations distinctes, aucun veto, ordre VRF vérifié, journal intègre
    CERT_PARTIEL : circuit incomplet, ordre valide, journal intègre
    CERT_NUL     : fourche, journal rompu, ordre non prouvé
    """
    # CERT_NUL : journal rompu ou ordre non prouvé
    if not report.journal_intact or not report.vrf_verified:
        return CertificateClass.CERT_NUL

    # CERT_PLEIN : conditions complètes
    if (
        len(report.attestations) >= NUM_PROCHAINS
        and len(report.vetoes) == 0
        and report.vrf_verified
        and report.journal_intact
        and report.roster_full
    ):
        return CertificateClass.CERT_PLEIN

    # CERT_PARTIEL : circuit incomplet mais valide
    if report.journal_intact and report.vrf_verified:
        return CertificateClass.CERT_PARTIEL

    # Par défaut
    return CertificateClass.CERT_NUL


def can_bind(certificate: CertificateClass) -> bool:
    """
    Détermine si un certificat autorise la liaison (auto-liaison, ratification, effets extérieurs).
    Seul CERT_PLEIN autorise les effets liants.
    """
    return certificate == CertificateClass.CERT_PLEIN


def allows_deliberation(certificate: CertificateClass) -> bool:
    """
    Détermine si un certificat autorise la lecture, délibération, préparation.
    CERT_PARTIEL le permet, mais sans liaison ni effet.
    """
    return certificate in (CertificateClass.CERT_PLEIN, CertificateClass.CERT_PARTIEL)
