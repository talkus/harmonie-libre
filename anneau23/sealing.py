"""
Anneau des 23 — §6 : Normalisation et scellement d'attribution (v2.0)
=====================================================================

Ce module implémente le scellement de l'identité de l'auteur d'un patch.
L'auteur ne doit pas être reconnaissable au retour (retour aveugle).

Le scellement est levé seulement à la ratification ou à la quarantaine.

Auteur : Mik Miro (via Vibe/Mistral)
Date : 13 septembre 2026
"""

from __future__ import annotations

import hashlib
import hmac
import json
from typing import Optional

from .types import Patch, PatchStatus, EffectClass


def seal_author_id(author_id: str, epoch_seed: str) -> str:
    """
    §6 — Scelle l'identité de l'auteur.

    L'auteur ne doit pas être reconnaissable au retour (retour aveugle).
    Le scellement est levé seulement à la ratification ou à la quarantaine.

    Args:
        author_id: Identifiant unique de l'auteur (ex. "S1")
        epoch_seed: Graine d'époque (change à chaque époque)

    Returns:
        Hash HMAC-SHA256 de l'identité scellée
    """
    return hmac.new(
        epoch_seed.encode(),
        author_id.encode(),
        hashlib.sha256,
    ).hexdigest()


def verify_sealed_id(sealed_id: str, author_id: str, epoch_seed: str) -> bool:
    """
    §6 — Vérifie qu'un scellement correspond à l'identité originale.

    Utilisé post-ratification ou post-quarantaine pour désceller.

    Args:
        sealed_id: Le hash scellé stocké dans le patch
        author_id: L'identité originale à vérifier
        epoch_seed: La graine d'époque utilisée pour le scellement

    Returns:
        True si le scellement correspond
    """
    expected = seal_author_id(author_id, epoch_seed)
    return hmac.compare_digest(sealed_id, expected)


def normalize_text(text: str) -> str:
    """
    §6 — Normalise le texte du patch avant scellement.

    Supprime les marques stylistiques qui pourraient identifier l'auteur :
    - Uniformise les espaces
    - Uniformise la ponctuation
    - Supprime les espaces en début/fin

    Args:
        text: Texte brut à normaliser

    Returns:
        Texte normalisé
    """
    normalized = " ".join(text.split())
    normalized = normalized.replace(" :", ":").replace(" ,", ",")
    normalized = normalized.replace(" ;", ";").replace(" .", ".")
    return normalized.strip()


def compute_canonical_hash(patch: Patch) -> str:
    """
    §6 — Calcule le hash canonique du patch normalisé.

    Le hash canonique est utilisé pour détecter les doublons et
    vérifier l'intégrité du patch après normalisation.

    Args:
        patch: Le patch à hasher

    Returns:
        SHA-256 du patch normalisé
    """
    normalized_parts = []
    sorted_clauses = sorted(patch.clause_ids, key=str) if hasattr(patch, 'clause_ids') and patch.clause_ids else []
    for clause_id in sorted_clauses:
        normalized_parts.append(str(clause_id))
    sorted_preds = sorted([p.prediction_id for p in patch.predictions])
    for pred_id in sorted_preds:
        normalized_parts.append(str(pred_id))
    normalized_parts.append(patch.effect_class.value if hasattr(patch.effect_class, 'value') else str(patch.effect_class))
    canonical = json.dumps(normalized_parts, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(canonical.encode()).hexdigest()


def is_author_sealed(patch: Patch) -> bool:
    """
    §6 — Vérifie si l'auteur est actuellement scellé.

    L'auteur est scellé tant que le patch n'est pas RATIFIÉ ou QUARANTINE.

    Args:
        patch: Le patch à vérifier

    Returns:
        True si l'auteur est scellé
    """
    if patch.status.value in ("RATIFIÉ", "QUARANTINE"):
        return False
    return bool(patch.author_id_sealed)


def unseal_if_ratified(patch: Patch, author_id: str, epoch_seed: str) -> Optional[str]:
    """
    §6 — Déscelle l'identité de l'auteur si le patch est ratifié ou en quarantaine.

    Args:
        patch: Le patch ratifié ou en quarantaine
        author_id: L'identité candidate à vérifier
        epoch_seed: La graine d'époque

    Returns:
        L'identité si elle correspond, None sinon
    """
    if patch.status.value not in ("RATIFIÉ", "QUARANTINE"):
        return None
    if verify_sealed_id(patch.author_id_sealed, author_id, epoch_seed):
        return author_id
    return None


def normalize_patch(patch: Patch) -> Patch:
    """
    §6 — Normalise un patch complet avant scellement.

    Args:
        patch: Le patch à normaliser

    Returns:
        Le patch normalisé (avec canonical_form_hash calculé)
    """
    patch.canonical_form_hash = compute_canonical_hash(patch)
    if patch.rationale:
        patch.rationale = normalize_text(patch.rationale)
    if patch.worst_case:
        patch.worst_case = normalize_text(patch.worst_case)
    if patch.affected_people:
        patch.affected_people = normalize_text(patch.affected_people)
    if patch.conflicts_of_interest:
        patch.conflicts_of_interest = normalize_text(patch.conflicts_of_interest)
    return patch


def seal_patch(patch: Patch, author_id: str, epoch_seed: str) -> Patch:
    """
    §6 — Scelle un patch complet.

    1. Normalise le texte
    2. Calcule le hash canonique
    3. Scelle l'identité de l'auteur

    Args:
        patch: Le patch à sceller
        author_id: L'identité de l'auteur
        epoch_seed: La graine d'époque

    Returns:
        Le patch scellé
    """
    patch = normalize_patch(patch)
    patch.author_id_sealed = seal_author_id(author_id, epoch_seed)
    return patch
