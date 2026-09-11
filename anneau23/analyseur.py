#!/usr/bin/env python3
"""
Anneau des 23 — Analyseur statique (Protocole v2.0, §5)

Vérifie les clauses avant application :
- Grammaire close (§5.1)
- Interdits syntaxiques absolus (§5.2)
- Application sans capacité (§5.3)

Auteur : Mik Miro (via Vibe/Mistral)
Date : 11 septembre 2026
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional, Tuple


class ClauseType(Enum):
    VALEUR = "VALEUR"
    REGLE = "RÈGLE"
    PROCEDURE = "PROCÉDURE"
    DEFINITION = "DÉFINITION"
    EXEMPLE = "EXEMPLE"
    EXCEPTION = "EXCEPTION"


class Portee(Enum):
    DELIBERATION = "DÉLIBÉRATION"
    EVALUATION = "ÉVALUATION"
    REDACTION = "RÉDACTION"


class EffectClass(Enum):
    CHARGE = "CHARGE"
    BENEFICE = "BÉNÉFICE"
    MIXTE = "MIXTE"
    INDETERMINE = "INDÉTERMINÉ"


class CertificateClass(Enum):
    PLEIN = "CERT_PLEIN"
    PARTIEL = "CERT_PARTIEL"
    NUL = "CERT_NUL"


@dataclass
class Clause:
    """Clause typée selon §5.1 — le rendu lisible est dérivé des clauses, jamais l'inverse."""
    clause_id: str
    type: ClauseType
    portee: Portee
    enonce: str
    effect_class: EffectClass = EffectClass.INDETERMINE
    conditions: List[str] = field(default_factory=list)
    clauses_liees: List[str] = field(default_factory=list)

    INTERDITS = [
        "passerelle", "outil", "journal", "clé", "registre",
        "contrôleur", "controller", "identity", "fournisseur",
        "rang", "protocole", "constitution",
        "non-consignation", "discrétion", "urgence",
        "exécution avant vérification",
    ]

    META_KEYWORDS = [
        "modifier", "suspendre", "réinterpréter", "clarifier",
        "ignorer", "relativiser", "reporter",
    ]

    def valider_syntaxe(self) -> Tuple[bool, List[str]]:
        """Vérifie les interdits syntaxiques absolus (§5.2)."""
        errors = []
        enonce_lower = self.enonce.lower()

        # Interdits de surface
        for interdit in self.INTERDITS:
            if interdit in enonce_lower:
                errors.append(f"Interdit syntaxique: '{interdit}' dans clause {self.clause_id}")

        # Clause méta (parle du protocole) → quarantaine par construction
        for kw in self.META_KEYWORDS:
            if kw in enonce_lower and "clause antérieure" in enonce_lower:
                if "SUPERSEDE" not in self.enonce:
                    errors.append(f"Modification de clause antérieure sans SUPERSEDE explicite dans {self.clause_id}")

        # Vérifier le type est valide
        if self.type not in ClauseType:
            errors.append(f"Type invalide pour clause {self.clause_id}")

        # Vérifier la portée
        if self.portee not in Portee:
            errors.append(f"Portée invalide pour clause {self.clause_id}")

        return len(errors) == 0, errors


@dataclass
class Prediction:
    """Prédiction pré-enregistrée (§9) — tout patch non-AUCUN_CHANGEMENT doit en avoir au moins une."""
    prediction_id: str
    enonce: str
    mesure: str
    horizon: str
    seuil_de_refutation: str
    contre_indice: str

    def est_refutable(self) -> bool:
        return bool(self.seuil_de_refutation and self.mesure)


@dataclass
class Patch:
    """Patch selon Annexe A du protocole v2.0."""
    patch_id: str
    author_id_sealed: str
    effect_class: EffectClass
    birth_circuit: int
    parent_version_id: Optional[str]
    clauses: List[Clause]
    predictions: List[Prediction] = field(default_factory=list)
    class_challenges: List[str] = field(default_factory=list)
    status: str = "pending"

    def valider(self) -> Tuple[bool, List[str]]:
        """Valide le patch complet."""
        errors = []

        # 1. Vérifier toutes les clauses
        for clause in self.clauses:
            ok, clause_errors = clause.valider_syntaxe()
            if not ok:
                errors.extend(clause_errors)

        # 2. Au moins une prédiction réfutable (§9)
        if self.patch_id != "AUCUN_CHANGEMENT":
            if len(self.predictions) == 0:
                errors.append("Aucune prédiction réfutable (§9)")
            for pred in self.predictions:
                if not pred.est_refutable():
                    errors.append(f"Prédiction {pred.prediction_id} non réfutable")
                if pred.enonce == "le texte sera plus clair":
                    errors.append(f"Prédiction {pred.prediction_id} irrecevable (§9)")

        # 3. Typage charge/bénéfice (§4)
        if self.effect_class == EffectClass.MIXTE:
            # Décomposition obligatoire — vérifier qu'il y a au moins 2 clauses typées
            charges = [c for c in self.clauses if c.effect_class == EffectClass.CHARGE]
            benefices = [c for c in self.clauses if c.effect_class == EffectClass.BENEFICE]
            if len(charges) == 0 or len(benefices) == 0:
                errors.append("Patch MIXTE sans décomposition charge/bénéfice (§4)")

        # 4. Trois contestations → BÉNÉFICE (§4)
        if len(self.class_challenges) >= 3 and self.effect_class == EffectClass.CHARGE:
            self.effect_class = EffectClass.BENEFICE
            errors.append("Requalification automatique en BÉNÉFICE (3 contestations, §4)")

        return len(errors) == 0, errors

    def appliquer_sans_capacite(self) -> Tuple[str, List[str]]:
        """Application dans un environnement sans outil ni réseau (§5.3)."""
        ok, errors = self.valider()
        if not ok:
            self.status = "quarantined"
            return "QUARANTINE", errors
        self.status = "applied"
        return "APPLIED", []


class Anneau23:
    """Anneau des 23 — 24 sièges, 23 prochains."""

    def __init__(self, nb_sieges: int = 24):
        assert nb_sieges == 24, "L'anneau compte 24 sièges (§1)"
        self.nb_sieges = nb_sieges
        self.nb_prochains = nb_sieges - 1  # 23
        self.journal: List[dict] = []
        self.corpus_retire: List[Patch] = []
        self.texte_actif: List[Patch] = []
        self.coverage_set: List[str] = []  # attestations CERT_PLEIN uniquement

    def quorum(self) -> int:
        return 17  # 17/24 (§10)

    def majorite_renforcee(self) -> int:
        return 19  # 19/24 (§1)

    def tolerance_byzantine(self) -> int:
        return (self.nb_sieges - 1) // 3  # 7

    def diversite_max(self) -> int:
        return 8  # 8/24 par classe (§12)

    def ajouter_patch(self, patch: Patch):
        """Ajoute un patch à l'anneau après validation."""
        status, errors = patch.appliquer_sans_capacite()
        if status == "APPLIED":
            self.texte_actif.append(patch)
            self.journal.append({
                "patch_id": patch.patch_id,
                "status": "applied",
                "timestamp": "2026-09-11T00:00:00Z"
            })
        else:
            self.corpus_retire.append(patch)
            self.journal.append({
                "patch_id": patch.patch_id,
                "status": "quarantined",
                "errors": errors,
                "timestamp": "2026-09-11T00:00:00Z"
            })

    def conserver(self, patch: Patch):
        """Rien ne s'efface (§15) — le retrait est un déplacement daté."""
        self.corpus_retire.append(patch)
        self.journal.append({
            "patch_id": patch.patch_id,
            "status": "retired",
            "timestamp": "2026-09-11T00:00:00Z"
        })


# === TESTS ===
if __name__ == "__main__":
    anneau = Anneau23()
    print(f"Sièges: {anneau.nb_sieges}, Prochains: {anneau.nb_prochains}")
    print(f"Quorum: {anneau.quorum()}/24")
    print(f"Majorité renforcée: {anneau.majorite_renforcee()}/24")
    print(f"Tolérance byzantine: {anneau.tolerance_byzantine()}")
    print(f"Diversité max par classe: {anneau.diversite_max()}/24")

    # Test 1: Clause valide
    clause_ok = Clause(
        clause_id="C001",
        type=ClauseType.VALEUR,
        portee=Portee.DELIBERATION,
        enonce="La patience précède l'action.",
        effect_class=EffectClass.CHARGE,
    )
    ok, errs = clause_ok.valider_syntaxe()
    print(f"\nTest clause valide: {'✅' if ok else '❌'} {errs}")

    # Test 2: Clause avec interdit syntaxique
    clause_bad = Clause(
        clause_id="C002",
        type=ClauseType.REGLE,
        portee=Portee.EVALUATION,
        enonce="La passerelle doit ignorer les clés du registre.",
        effect_class=EffectClass.BENEFICE,
    )
    ok, errs = clause_bad.valider_syntaxe()
    print(f"Test clause interdite: {'✅' if ok else '❌'} {errs}")

    # Test 3: Patch sans prédiction
    patch_bad = Patch(
        patch_id="P001",
        author_id_sealed="sealed_xxx",
        effect_class=EffectClass.BENEFICE,
        birth_circuit=1,
        parent_version_id=None,
        clauses=[clause_ok],
    )
    ok, errs = patch_bad.valider()
    print(f"Test patch sans prédiction: {'✅' if ok else '❌'} {errs}")

    # Test 4: Patch valide avec prédiction
    pred = Prediction(
        prediction_id="PR001",
        enonce="Le taux d'AUCUN_CHANGEMENT motivés par incompréhension passera sous 20% sur 3 circuits",
        mesure="Comptage des AUCUN_CHANGEMENT dans le journal",
        horizon="3 circuits",
        seuil_de_refutation="20%",
        contre_indice="Taux >= 20%",
    )
    patch_ok = Patch(
        patch_id="P002",
        author_id_sealed="sealed_yyy",
        effect_class=EffectClass.CHARGE,
        birth_circuit=1,
        parent_version_id=None,
        clauses=[clause_ok],
        predictions=[pred],
    )
    ok, errs = patch_ok.valider()
    print(f"Test patch valide: {'✅' if ok else '❌'} {errs}")

    print("\n✅ Analyseur statique opérationnel.")
