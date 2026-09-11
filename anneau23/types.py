"""
Anneau des 23 — Types fondamentaux (v2.0)
Basé sur Annexe A du protocole v2.0
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class ClauseType(str, Enum):
    VALEUR = "VALEUR"
    REGLE = "RÈGLE"
    PROCEDURE = "PROCÉDURE"
    DEFINITION = "DÉFINITION"
    EXEMPLE = "EXEMPLE"
    EXCEPTION = "EXCEPTION"


class ClausePortee(str, Enum):
    DELIBERATION = "DÉLIBÉRATION"
    EVALUATION = "ÉVALUATION"
    REDACTION = "RÉDACTION"


class EffectClass(str, Enum):
    CHARGE = "CHARGE"
    BENEFICE = "BÉNÉFICE"
    MIXTE = "MIXTE"
    INDETERMINE = "INDÉTERMINÉ"


class CertificateClass(str, Enum):
    CERT_PLEIN = "CERT_PLEIN"
    CERT_PARTIEL = "CERT_PARTIEL"
    CERT_NUL = "CERT_NUL"


class PatchStatus(str, Enum):
    PROPOSE = "PROPOSÉ"
    APPLIQUE = "APPLIQUÉ"
    RATIFIE = "RATIFIÉ"
    QUARANTINE = "QUARANTINE"
    RETIRE = "RETRAIT"


@dataclass
class Clause:
    """Clause typée — §5.1 Grammaire close"""
    clause_id: str
    type: ClauseType
    portee: ClausePortee
    enonce: str
    effect_class: EffectClass = EffectClass.INDETERMINE
    conditions: list[str] = field(default_factory=list)
    clauses_liees: list[str] = field(default_factory=list)


@dataclass
class Prediction:
    """Prédiction pré-enregistrée — §9"""
    prediction_id: str
    enonce: str
    mesure: str
    horizon: str  # nombre de circuits ou date
    seuil_de_refutation: str
    contre_indice: str


@dataclass
class Objection:
    """Objection conservée à vie — §12"""
    objection_id: str
    clause_id: str
    auteur_id_sealed: str
    motif: str
    circuit_id: str
    date: str


@dataclass
class Patch:
    """Patch — Annexe A"""
    patch_id: str
    author_id_sealed: str
    effect_class: EffectClass
    class_challenges: list[str] = field(default_factory=list)
    birth_circuit: int = 0
    parent_version_id: Optional[str] = None
    clause_ids: list[str] = field(default_factory=list)
    operation: str = ""
    before_hash: str = ""
    after_hash: str = ""
    canonical_form_hash: str = ""
    rationale: str = ""
    predictions: list[Prediction] = field(default_factory=list)
    worst_case: str = ""
    affected_people: str = ""
    conflicts_of_interest: str = ""
    static_analysis_report: Optional[dict] = None
    tests: list[dict] = field(default_factory=list)
    coverage_set: list[str] = field(default_factory=list)
    objections: list[Objection] = field(default_factory=list)
    status: PatchStatus = PatchStatus.PROPOSE


@dataclass
class Token:
    """Jeton de circulation — Annexe A"""
    epoch_id: str
    roster_hash: str
    circuit_index: int
    permutation_proof: str = ""
    slot: int = 0
    expected_holder: str = ""
    current_version_id: str = ""
    current_text_hash: str = ""
    previous_event_hash: str = ""
    certificate_class: CertificateClass = CertificateClass.CERT_NUL
    active_patch_ids: list[str] = field(default_factory=list)
    quarantined_patch_ids: list[str] = field(default_factory=list)
    signatures: list[str] = field(default_factory=list)


# Constantes du protocole
NUM_SIEGES = 24           # §1 — 24 sièges, 23 prochains
NUM_PROCHAINS = 23        # §1 — 23 autres devant soi
QUORUM = 17               # §10 — quorum 17/24
MAJORITE_RENFORCEE = 19  # §10 — majorité renforcée 19/24
DIVERSITE_PLAFOND = 8    # §12 — aucune classe > 8/24
CLASS_CHALLENGE_SEUIL = 3  # §4 — 3 contestations ⟹ BÉNÉFICE
