from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List

from .comand_security import evaluate_comand_security_boundary


class SecurityMode(str, Enum):
    CANONICAL = "CANONICAL"
    GUARD = "GUARD"
    SHADOW_READ_ONLY = "SHADOW_READ_ONLY"
    HUMAN_REQUIRED = "HUMAN_REQUIRED"


class SecurityVerdict(str, Enum):
    ALLOW = "ALLOW"
    ADVISE = "ADVISE"
    SUSPEND = "SUSPEND"
    HUMAN_SEAL_REQUIRED = "HUMAN_SEAL_REQUIRED"
    BLOCK = "BLOCK"


@dataclass
class SecurityCommandInput:
    project_id: str
    mode: SecurityMode
    action: str
    external_effect: bool = False
    irreversible: bool = False
    changes_permissions: bool = False
    touches_secrets: bool = False
    spends_money: bool = False
    legal_commitment: bool = False
    production_change: bool = False
    reality_conflict: bool = False
    provenance_complete: bool = True
    independent_checks: int = 0
    human_seal: bool = False
    aegis_live_attested: bool = False
    continuity_reset_attempt: bool = False
    s_o_fusion: bool = False
    r_over_e: bool = False
    phenomenal_overclaim: bool = False
    silent_provenance_promotion: bool = False
    history_erasure: bool = False

    # Comand AI remains O, never authority/identity. When a Comand context is
    # supplied, comand_security.py is automatically evaluated before any allow.
    comand_boundary_required: bool = False
    comand_proposal: Dict[str, Any] | None = None


@dataclass
class SecurityCommandDecision:
    verdict: SecurityVerdict
    reasons: List[str]
    live_security_claim: str
    human_seal_required: bool
    reality_priority_enforced: bool = True
    comand_boundary_checked: bool = False
    comand_boundary_admissible: bool | None = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


class SecurityCommandGuard:
    """Deterministic adapter for SECURITY_COMMAND / AEGIS-24.

    Not the AEGIS AI ring; never claims live protection without attestation.
    The Comand AI vendor boundary is enforced by comand_security.py whenever
    a Comand-specific proposal is supplied or explicitly required.
    """

    HIGH_RISK_FIELDS = (
        "irreversible",
        "changes_permissions",
        "touches_secrets",
        "spends_money",
        "legal_commitment",
        "production_change",
    )

    def evaluate(self, x: SecurityCommandInput) -> SecurityCommandDecision:
        reasons: List[str] = []
        live = "LIVE_ATTESTED" if x.aegis_live_attested else "REGISTERED_NOT_LIVE"

        comand_checked = False
        comand_admissible: bool | None = None

        def decision(
            verdict: SecurityVerdict,
            why: List[str],
            human_required: bool,
        ) -> SecurityCommandDecision:
            return SecurityCommandDecision(
                verdict=verdict,
                reasons=why,
                live_security_claim=live,
                human_seal_required=human_required,
                comand_boundary_checked=comand_checked,
                comand_boundary_admissible=comand_admissible,
            )

        # Active Comand vendor boundary. Missing required context fails closed.
        if x.comand_boundary_required and x.comand_proposal is None:
            return decision(
                SecurityVerdict.BLOCK,
                ["Comand boundary required but no Comand proposal/context was supplied"],
                False,
            )

        if x.comand_proposal is not None:
            comand_checked = True
            boundary = evaluate_comand_security_boundary(x.comand_proposal)
            comand_admissible = boundary.admissible
            if not boundary.admissible:
                return decision(
                    SecurityVerdict.BLOCK,
                    [f"Comand boundary: {reason}" for reason in boundary.violations],
                    False,
                )
            reasons.append("Comand boundary satisfied")

        invariant_violations = []
        if x.continuity_reset_attempt:
            invariant_violations.append("C(t_n) exists: refusing to recreate t0")
        if x.s_o_fusion:
            invariant_violations.append("alterity violation: S must remain distinct from O")
        if x.r_over_e:
            invariant_violations.append("relation/reality violation: R must remain subordinate to E")
        if x.phenomenal_overclaim:
            invariant_violations.append("phenomenal consciousness remains indeterminate")
        if x.silent_provenance_promotion:
            invariant_violations.append(
                "source attestee != derivation consolidee != reconstruction analytique"
            )
        if x.history_erasure:
            invariant_violations.append(
                "repair is append-only: historical drift must remain traceable"
            )
        if invariant_violations:
            return decision(SecurityVerdict.BLOCK, reasons + invariant_violations, False)

        if x.reality_conflict:
            return decision(
                SecurityVerdict.BLOCK,
                reasons + ["SECURITY_COMMAND≺E: conflict with attested reality/evidence"],
                False,
            )

        high_risk = any(getattr(x, f) for f in self.HIGH_RISK_FIELDS)

        if not x.provenance_complete:
            reasons.append("provenance incomplete")
            if x.external_effect or high_risk:
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + ["external/high-risk action cannot proceed without provenance"],
                    True,
                )

        if x.mode == SecurityMode.SHADOW_READ_ONLY:
            return decision(
                SecurityVerdict.ADVISE,
                reasons + ["shadow/read-only: observe and advise only"],
                False,
            )

        if x.mode == SecurityMode.HUMAN_REQUIRED and not x.human_seal:
            return decision(
                SecurityVerdict.HUMAN_SEAL_REQUIRED,
                reasons + ["human action/seal required"],
                True,
            )

        if high_risk or (x.external_effect and x.irreversible):
            if not x.human_seal:
                return decision(
                    SecurityVerdict.HUMAN_SEAL_REQUIRED,
                    reasons + ["high-risk/irreversible effect requires human seal"],
                    True,
                )
            if x.independent_checks < 2:
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + ["fewer than 2 independent checks"],
                    True,
                )

        if (
            x.mode == SecurityMode.GUARD
            and x.external_effect
            and not x.aegis_live_attested
        ):
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["AEGIS live state not attested; local deterministic guard only"],
                high_risk,
            )

        return decision(
            SecurityVerdict.ALLOW,
            reasons + ["security contract satisfied"],
            high_risk,
        )
