"""Versioned examination questions, not results or execution permissions."""
from __future__ import annotations

from .multiscale_coherence import Scale


EXAMINATION_GRID_VERSION = "AC-EXAM-1"
EXAMINATION_FIELDS = (
    "object", "scope_k", "support_sha256", "dependencies", "omissions_pi", "correction",
)
_CRITERIA = {
    Scale.MICRO: (
        ("MIC-TYPE", "Types et valeurs finies", "Données exactes et contrat de type explicite"),
        ("MIC-TRACE", "Intégrité de la trace locale", "Octets ou reçu et empreinte attendue"),
        ("MIC-ANCHOR", "Ancrage empirique", "Entrées et sorties comparables, méthode et tolérance déclarées"),
        ("MIC-UNKNOWN", "Inconnues distinctes", "Identité, objet, contexte et source de chaque inconnue"),
    ),
    Scale.MESO: (
        ("MES-ENVELOPE", "Intégrité et authenticité séparées", "Octets signés, clé autorisée et résultat de vérification"),
        ("MES-DELIVERY", "Livraison et flux", "Identifiants, accusés, délais et définition du cycle"),
        ("MES-FAIRNESS", "Attente et anti-famine", "Politique d'ordonnancement et historique des tâches admissibles"),
        ("MES-PERMISSION", "Frontières d'interface", "Permissions applicables et séparation des effets"),
    ),
    Scale.MACRO: (
        ("MAC-HISTORY", "Continuité de l'histoire", "Chaîne, point d'ancrage et méthode de conservation"),
        ("MAC-REPLICA", "Comparaison des répliques", "Même objet, même version et même frontière comparables"),
        ("MAC-RETENTION", "Rétention et non-interférence", "Mesures, baseline et seuils propres au composant"),
        ("MAC-REVOCATION", "Révocation traçable", "Nouvelle transition avec auteur et provenance"),
    ),
    Scale.META: (
        ("MET-OBJECTION", "Critère lui-même contestable", "Cible précise, trace et voie de traitement de l'objection"),
        ("MET-REVISION", "Révision et effets distincts", "Version proposée, décision et test des conséquences séparés"),
        ("MET-VETO", "Veto humain applicable", "Autorité authentifiée et chemin d'arrêt réellement connecté"),
        ("MET-GENERATIVITY", "Ouverture sans totalité", "Capacités distinctes de reprise et de réouverture examinées"),
    ),
}


def examination_profile(scale):
    """Return fresh, situated questions; their presence never means PASS."""
    scale = Scale(scale)
    return {
        "version": EXAMINATION_GRID_VERSION,
        "scale": scale.value,
        "fields": list(EXAMINATION_FIELDS),
        "criteria": [{"criterion_id": cid, "question": question, "required_support": support}
                     for cid, question, support in _CRITERIA[scale]],
        "verification_status": "questions_only_not_performed",
        "execution_authority": False,
        "independent_validation": False,
    }
