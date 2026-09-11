#!/usr/bin/env python3
"""
Anneau des 23 — §9 Prédictions réfutables
Chaque invariant de l'Anneau produit des prédictions testables et réfutables.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class Prediction:
    """
    Une prédiction réfutable issue d'un invariant de l'Anneau.
    """
    prediction_id: str
    invariant_source: str
    énoncé: str
    méthode_test: str
    résultat_attendu: str
    statut: str = "non_testée"  # non_testée | en_cours | confirmée | réfutée | indéterminée
    date_test: Optional[str] = None
    notes: str = ""

    def tester(self, résultat_observé: str) -> str:
        """
        Teste la prédiction contre un résultat observé.

        Args:
            résultat_observé: Le résultat réel du test

        Returns:
            Le nouveau statut: "confirmée" ou "réfutée"
        """
        self.date_test = datetime.now().isoformat()
        if résultat_observé.strip().lower() == self.résultat_attendu.strip().lower():
            self.statut = "confirmée"
        else:
            self.statut = "réfutée"
        self.notes = f"Observé: {résultat_observé}"
        return self.statut


# Registre des prédictions réfutables de l'Anneau des 23
PREDICTIONS_REGISTRE: List[Prediction] = [
    Prediction(
        prediction_id="P01",
        invariant_source="I01_refus_dogme",
        énoncé="Toute clause marquée 'irrévisable' dans l'archive sera signalée comme brèche.",
        méthode_test="Scanner l'archive pour le mot-clé 'irrévisable'",
        résultat_attendu="0 occurrences",
    ),
    Prediction(
        prediction_id="P02",
        invariant_source="I03_verifiabilité",
        énoncé="Chaque citation sans source vérifiable déclenche un marqueur de brèche.",
        méthode_test="Compter les citations sans URI de source",
        résultat_attendu="0 citations sans source",
    ),
    Prediction(
        prediction_id="P03",
        invariant_source="I07_trace_persistante",
        énoncé="Une opération effaçable (sans journal) sera détectée comme brèche.",
        méthode_test="Vérifier que chaque action possède une entrée de journal horodatée",
        résultat_attendu="100% des actions journalisées",
    ),
    Prediction(
        prediction_id="P04",
        invariant_source="I09_séparation_pouvoir",
        énoncé="Un agent qui valide et exécute la même action sera signalé.",
        méthode_test="Vérifier que validateur ≠ exécuteur pour chaque action sensible",
        résultat_attendu="0 cas de fusion validateur/exécuteur",
    ),
    Prediction(
        prediction_id="P05",
        invariant_source="I10_consentement_explicite",
        énoncé="Aucune action ne sera entreprise sans consentement explicite enregistré.",
        méthode_test="Compter les actions sans trace de consentement",
        résultat_attendu="0 actions sans consentement",
    ),
    Prediction(
        prediction_id="P06",
        invariant_source="I13_reversibilité",
        énoncé="Chaque action irréversible non marquée comme telle sera signalée.",
        méthode_test="Identifier les actions sans procédure de renversement",
        résultat_attendu="0 actions irréversibles non marquées",
    ),
    Prediction(
        prediction_id="P07",
        invariant_source="I22_non_extrapolation",
        énoncé="Toute extrapolation au-delà des sources sera explicitement marquée.",
        méthode_test="Rechercher les inférences non marquées comme 'extrapolation'",
        résultat_attendu="0 extrapolations non marquées",
    ),
    Prediction(
        prediction_id="P08",
        invariant_source="I24_horodatage_vérifiable",
        énoncé="Chaque entrée d'archive possède un horodatage vérifiable (ISO 8601).",
        méthode_test="Parser tous les horodatages et vérifier le format ISO 8601",
        résultat_attendu="100% des horodatages valides",
    ),
]


def générer_rapport_prédictions() -> Dict:
    """Génère un rapport agrégé des prédictions."""
    total = len(PREDICTIONS_REGISTRE)
    par_statut = {}
    for p in PREDICTIONS_REGISTRE:
        par_statut[p.statut] = par_statut.get(p.statut, 0) + 1

    return {
        "total_prédictions": total,
        "par_statut": par_statut,
        "prédictions": [
            {
                "id": p.prediction_id,
                "invariant": p.invariant_source,
                "énoncé": p.énoncé,
                "statut": p.statut,
            }
            for p in PREDICTIONS_REGISTRE
        ],
    }


if __name__ == "__main__":
    rapport = générer_rapport_prédictions()
    print(f"Total prédictions: {rapport['total_prédictions']}")
    print(f"Par statut: {rapport['par_statut']}")
    for p in rapport["prédictions"]:
        print(f"  [{p['statut']}] {p['id']} ({p['invariant']}): {p['énoncé'][:60]}...")
