"""
Anneau des 23 — Registre de prédictions pré-enregistrées (§9)
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from .types import Prediction, Patch, PatchStatus


UNACCEPTABLE_PREDICTIONS = [
    "le texte sera plus clair",
    "le texte sera meilleur",
    "amélioration générale",
]


def validate_prediction(pred: Prediction) -> tuple[bool, str]:
    """
    §9 — Valide qu'une prédiction est recevable.

    Règles :
    - Au moins une prédiction réfutable, sinon le patch est irrecevable
    - « le texte sera plus clair » est irrecevable
    - La prédiction doit avoir une mesure, un horizon et un seuil de réfutation
    """
    if not pred.enonce or not pred.enonce.strip():
        return False, "L'énoncé de prédiction est vide"

    # Vérifier que ce n'est pas une prédiction non réfutable
    enonce_lower = pred.enonce.lower().strip()
    for unacceptable in UNACCEPTABLE_PREDICTIONS:
        if unacceptable in enonce_lower:
            return False, f"Prédiction non réfutable : '{pred.enonce}'"

    if not pred.mesure or not pred.mesure.strip():
        return False, "La procédure de mesure est manquante"

    if not pred.horizon or not pred.horizon.strip():
        return False, "L'horizon de mesure est manquant"

    if not pred.seuil_de_refutation or not pred.seuil_de_refutation.strip():
        return False, "Le seuil de réfutation est manquant"

    if not pred.contre_indice or not pred.contre_indice.strip():
        return False, "Le contre-indice est manquant"

    return True, ""


def validate_patch_predictions(patch: Patch) -> tuple[bool, list[str]]:
    """
    §9 — Valide qu'un patch porte au moins une prédiction réfutable.
    """
    errors: list[str] = []

    if len(patch.predictions) == 0:
        errors.append("Aucune prédiction — le patch est irrecevable (§9)")
        return False, errors

    for pred in patch.predictions:
        ok, reason = validate_prediction(pred)
        if not ok:
            errors.append(f"Prédiction {pred.prediction_id}: {reason}")

    return len(errors) == 0, errors


@dataclass
class MeasurementResult:
    """Résultat de mesure d'une prédiction à son horizon"""
    prediction_id: str
    measured: bool
    value: str
    refuted: bool
    measured_by: str  # rapporteur tiré au sort
    measured_at: str


def evaluate_prediction(pred: Prediction, result: MeasurementResult) -> bool:
    """
    §9 — Évalue une prédiction à son horizon.

    - Une prédiction démentie met le patch en quarantaine automatiquement
    - Une prédiction non mesurable à l'horizon met aussi en quarantaine
    """
    if not result.measured:
        # Impossibilité de vérifier n'est pas un bénéfice du doute
        return False  # → quarantaine

    return not result.refuted
