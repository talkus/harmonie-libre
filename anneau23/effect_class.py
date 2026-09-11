"""
Anneau des 23 — Typage charge / bénéfice (§4)
Asymétrie charge / bénéfice : le bénéfice arrive en dernier pour son auteur.
"""
from __future__ import annotations

from .types import EffectClass, Patch, NUM_PROCHAINS, CLASS_CHALLENGE_SEUIL


def requalify_if_challenged(patch: Patch) -> EffectClass:
    """
    §4 — Si 3 sièges contestent un typage CHARGE, il bascule en BÉNÉFICE.

    Un typage CHARGE contesté par trois sièges bascule automatiquement en BÉNÉFICE
    — sans débat, sans arbitrage, sans coût pour l'auteur autre que le délai.
    """
    if (
        patch.effect_class == EffectClass.CHARGE
        and len(patch.class_challenges) >= CLASS_CHALLENGE_SEUIL
    ):
        patch.effect_class = EffectClass.BENEFICE
        return EffectClass.BENEFICE
    return patch.effect_class


def can_self_bind_immediately(effect_class: EffectClass) -> bool:
    """
    §4 — Détermine si l'auto-liaison immédiate est autorisée.

    CHARGE : auto-liaison immédiate autorisée (l'auteur peut se l'appliquer dès son passage)
    BÉNÉFICE : auto-liaison différée (règle §2, 23 prochains avant)
    MIXTE : décomposition obligatoire ; si impossible, traité comme BÉNÉFICE
    INDÉTERMINÉ : traité comme BÉNÉFICE
    """
    return effect_class == EffectClass.CHARGE


def requires_23_before_self(effect_class: EffectClass) -> bool:
    """
    §4 — Détermine si les 23 prochains doivent appliquer avant l'auteur.
    """
    return effect_class in (EffectClass.BENEFICE, EffectClass.INDETERMINE)


def binds_others(effect_class: EffectClass) -> bool:
    """
    §4 — Détermine si un patch CHARGE peut lier d'autres sièges.
    Un patch CHARGE n'engage jamais un autre siège tant qu'ils ne l'ont pas reçu.
    """
    return False  # CHARGE ne lie jamais un autre siège automatiquement
