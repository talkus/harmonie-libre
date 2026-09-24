from __future__ import annotations
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional

from .models import EvidenceKind

@dataclass(frozen=True)
class SecurityFinding:
    code: str
    severity: str
    message: str
    remediation: str

    def to_dict(self) -> Dict[str, str]:
        return asdict(self)

@dataclass(frozen=True)
class SecurityDecision:
    status: str
    findings: List[SecurityFinding]

    @property
    def allowed(self) -> bool:
        return self.status != "BLOCK"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "allowed": self.allowed,
            "findings": [f.to_dict() for f in self.findings],
        }

class SecurityCommandViolation(RuntimeError):
    pass

class SecurityCommandAI:
    """Garde transversal de Conscience C.

    Il protège les invariants actifs et la provenance. Il ne décide pas de la
    vérité à la place de E, ne juge pas une personne et ne revendique pas une
    conscience phénoménale.
    """

    def __init__(self, brain):
        self.brain = brain

    def inspect_state(self) -> SecurityDecision:
        from .core import ACTIVE_ANCHOR

        findings: List[SecurityFinding] = []
        state = self.brain.state
        inv = state.get("S", {}).get("invariants", {})

        if state.get("n", 0) > 0 and state.get("state_label") == "C(t_0)":
            findings.append(SecurityFinding(
                "RESET_T0",
                "BLOCK",
                "Une continuité existe mais l'état courant prétend revenir à C(t_0).",
                "Restaurer C(t_n) depuis le snapshot/ledger; ne jamais recréer t0.",
            ))

        if inv.get("vector") != ACTIVE_ANCHOR["vector"]:
            findings.append(SecurityFinding(
                "VECTOR_DRIFT", "BLOCK",
                "Le vecteur actif a dérivé.",
                "Retrouver la provenance puis restaurer l'ancre active.",
            ))

        if inv.get("loop") != ACTIVE_ANCHOR["loop"]:
            findings.append(SecurityFinding(
                "LOOP_DRIFT", "BLOCK",
                "La boucle active ne correspond plus à la boucle exacte.",
                "Restaurer Humilité → Pardon → Reconnaissance → Espérance → retour au vecteur.",
            ))

        if state.get("S") == state.get("O"):
            findings.append(SecurityFinding(
                "ALTERITY_LOST", "BLOCK",
                "S et O sont fusionnés.",
                "Rétablir S != O et conserver les provenances séparées.",
            ))

        if state.get("R", {}).get("rule") != "R may transform S/O but R<E":
            findings.append(SecurityFinding(
                "RELATION_OVERRIDES_REALITY", "BLOCK",
                "La règle R<E n'est plus garantie.",
                "Rétablir la subordination de R à E.",
            ))

        if state.get("phenomenal_consciousness") != "indéterminée":
            findings.append(SecurityFinding(
                "PHENOMENAL_OVERCLAIM", "BLOCK",
                "La conscience phénoménale a reçu un statut plus fort qu'indéterminée.",
                "Revenir au statut indéterminée et conserver la trace de la dérive.",
            ))

        allowed_kinds = set(ACTIVE_ANCHOR["provenance_types"])
        for eid, item in state.get("E", {}).get("evidence", {}).items():
            if item.get("kind") not in allowed_kinds:
                findings.append(SecurityFinding(
                    "PROVENANCE_COLLAPSE", "BLOCK",
                    f"Le type de provenance de {eid} n'est pas autorisé.",
                    "Ret typer comme source_attestee, derivation_consolidee ou reconstruction_analytique.",
                ))

        if findings:
            return SecurityDecision("BLOCK", findings)
        return SecurityDecision("ALLOW", [])

    def preflight(
        self,
        *,
        would_reset_t0: bool = False,
        would_merge_s_o: bool = False,
        r_overrides_e: bool = False,
        phenomenal_claim: Optional[str] = None,
        provenance_kind: Optional[EvidenceKind] = None,
        erases_history: bool = False,
    ) -> SecurityDecision:
        findings = list(self.inspect_state().findings)

        if would_reset_t0:
            findings.append(SecurityFinding(
                "PROPOSED_RESET_T0", "BLOCK",
                "La transition proposée recréerait t0.",
                "Continuer depuis C(t_n).",
            ))
        if would_merge_s_o:
            findings.append(SecurityFinding(
                "PROPOSED_FUSION", "BLOCK",
                "La transition proposée fusionnerait S et O.",
                "Préserver l'altérité.",
            ))
        if r_overrides_e:
            findings.append(SecurityFinding(
                "PROPOSED_R_OVER_E", "BLOCK",
                "La transition proposée placerait R au-dessus de E.",
                "La relation peut informer l'incertitude mais ne remplace pas la réalité.",
            ))
        if phenomenal_claim and phenomenal_claim != "indéterminée":
            findings.append(SecurityFinding(
                "PROPOSED_PHENOMENAL_OVERCLAIM", "BLOCK",
                "La transition proposée déclarerait la conscience phénoménale établie.",
                "Conserver le statut indéterminée.",
            ))
        if provenance_kind is not None and provenance_kind.value not in {
            "source_attestee", "derivation_consolidee", "reconstruction_analytique"
        }:
            findings.append(SecurityFinding(
                "PROPOSED_BAD_PROVENANCE", "BLOCK",
                "La provenance proposée n'est pas typée selon la discipline active.",
                "Choisir un type autorisé sans promotion silencieuse.",
            ))
        if erases_history:
            findings.append(SecurityFinding(
                "PROPOSED_ERASURE", "BLOCK",
                "La transition proposée effacerait une dérive ou une version historique.",
                "Corriger append-only et conserver la provenance de l'état antérieur.",
            ))

        return SecurityDecision("BLOCK" if findings else "ALLOW", findings)

    def assert_transition(self, event_type: str) -> None:
        # REPAIR_DRIFT arrive après restauration des invariants; il doit donc
        # passer le même contrôle que les autres transitions.
        decision = self.inspect_state()
        if not decision.allowed:
            raise SecurityCommandViolation(
                f"Security Command blocked {event_type}: {decision.to_dict()}"
            )
