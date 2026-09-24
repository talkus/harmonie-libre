from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from enum import Enum
import hashlib
import json
from typing import Any, Dict, List

from .comand_security import evaluate_comand_security_boundary


SECURITY_COMMAND_VERSION = "2026-09-24.5"


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

    # Hardening v2
    policy_version: str = SECURITY_COMMAND_VERSION
    project_registration_attested: bool = False
    root_integrity_attested: bool = False
    append_only_log_available: bool = False
    authorization_nonce: str = ""
    human_seal_action_fingerprint: str = ""
    authorization_expires_at: str = ""
    human_authorization_verified: bool = False
    authorization_verification_method: str = ""
    authorization_ref: str = ""
    replay_detected: bool = False

    # Comand AI remains O, never authority/identity.
    comand_boundary_required: bool = False
    comand_proposal: Dict[str, Any] | None = None


@dataclass
class SecurityCommandDecision:
    verdict: SecurityVerdict
    reasons: List[str]
    live_security_claim: str
    human_seal_required: bool
    may_execute: bool = False
    policy_version: str = SECURITY_COMMAND_VERSION
    action_fingerprint: str = ""
    audit_log_required: bool = False
    authorization_bound_to_action: bool | None = None
    reality_priority_enforced: bool = True
    comand_boundary_checked: bool = False
    comand_boundary_admissible: bool | None = None

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["verdict"] = self.verdict.value
        return d


class SecurityCommandGuard:
    """Deterministic fail-closed adapter for SECURITY_COMMAND / AEGIS-24.

    A language model may explain a decision but cannot relax it.
    A human seal is valid only when bound to the exact action fingerprint.
    Replay detection still requires an external used-nonce registry.
    """

    ALLOWED_HUMAN_VERIFICATION_METHODS = {
        "authenticated_connector",
        "aegis_human_seal",
        "external_signed_receipt",
    }

    HIGH_RISK_FIELDS = (
        "irreversible",
        "changes_permissions",
        "touches_secrets",
        "spends_money",
        "legal_commitment",
        "production_change",
    )

    @staticmethod
    def _action_fingerprint(x: SecurityCommandInput) -> str:
        payload = {
            "policy_version": SECURITY_COMMAND_VERSION,
            "project_id": x.project_id,
            "mode": x.mode.value,
            "action": x.action,
            "external_effect": bool(x.external_effect),
            "irreversible": bool(x.irreversible),
            "changes_permissions": bool(x.changes_permissions),
            "touches_secrets": bool(x.touches_secrets),
            "spends_money": bool(x.spends_money),
            "legal_commitment": bool(x.legal_commitment),
            "production_change": bool(x.production_change),
            "authorization_nonce": x.authorization_nonce,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    @staticmethod
    def _authorization_expiry_state(value: str) -> str:
        if not value:
            return "missing"
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return "valid" if dt.astimezone(timezone.utc) > datetime.now(timezone.utc) else "expired"
        except ValueError:
            return "invalid"

    def evaluate(self, x: SecurityCommandInput) -> SecurityCommandDecision:
        reasons: List[str] = []
        live = "LIVE_ATTESTED" if x.aegis_live_attested else "REGISTERED_NOT_LIVE"
        fingerprint = self._action_fingerprint(x)
        high_risk = any(getattr(x, f) for f in self.HIGH_RISK_FIELDS)
        human_gated = high_risk or x.mode == SecurityMode.HUMAN_REQUIRED

        comand_checked = False
        comand_admissible: bool | None = None

        def decision(
            verdict: SecurityVerdict,
            why: List[str],
            human_required: bool,
            *,
            authorization_bound: bool | None = None,
        ) -> SecurityCommandDecision:
            return SecurityCommandDecision(
                verdict=verdict,
                reasons=list(dict.fromkeys(why)),
                live_security_claim=live,
                human_seal_required=human_required,
                may_execute=verdict == SecurityVerdict.ALLOW,
                policy_version=SECURITY_COMMAND_VERSION,
                action_fingerprint=fingerprint,
                audit_log_required=bool(x.external_effect or high_risk),
                authorization_bound_to_action=authorization_bound,
                comand_boundary_checked=comand_checked,
                comand_boundary_admissible=comand_admissible,
            )

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

        if x.replay_detected:
            return decision(
                SecurityVerdict.BLOCK,
                reasons + ["authorization replay detected"],
                False,
            )

        if x.policy_version != SECURITY_COMMAND_VERSION:
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["policy version mismatch or downgrade"],
                False,
            )

        if not x.project_id.strip() or not x.action.strip():
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["project_id and action are required"],
                False,
            )

        if not x.provenance_complete:
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["provenance incomplete"],
                bool(x.external_effect or high_risk),
            )

        if x.mode == SecurityMode.SHADOW_READ_ONLY:
            return decision(
                SecurityVerdict.ADVISE,
                reasons + ["shadow/read-only: observe and advise only"],
                False,
            )

        if (x.external_effect or high_risk) and not x.project_registration_attested:
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["project registration not attested"],
                human_gated,
            )

        if (x.external_effect or high_risk) and not x.root_integrity_attested:
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["root integrity not attested"],
                human_gated,
            )

        if x.external_effect and not x.append_only_log_available:
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["append-only audit log required for external effect"],
                human_gated,
            )

        if human_gated:
            if not x.authorization_nonce.strip():
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + ["authorization nonce required"],
                    True,
                )

            if not x.human_seal:
                return decision(
                    SecurityVerdict.HUMAN_SEAL_REQUIRED,
                    reasons + ["human seal required for exact action fingerprint"],
                    True,
                )

            if x.human_seal_action_fingerprint != fingerprint:
                return decision(
                    SecurityVerdict.BLOCK,
                    reasons + ["human seal not bound to exact action"],
                    True,
                    authorization_bound=False,
                )

            if not x.human_authorization_verified:
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + ["human authorization not verified"],
                    True,
                    authorization_bound=True,
                )

            if x.authorization_verification_method not in self.ALLOWED_HUMAN_VERIFICATION_METHODS:
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + ["authorization verification method not allowed"],
                    True,
                    authorization_bound=True,
                )

            if not x.authorization_ref.strip():
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + ["authorization reference required"],
                    True,
                    authorization_bound=True,
                )

            expiry = self._authorization_expiry_state(x.authorization_expires_at)
            if expiry != "valid":
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + [f"authorization {expiry}"],
                    True,
                    authorization_bound=True,
                )

            if high_risk and x.independent_checks < 2:
                return decision(
                    SecurityVerdict.SUSPEND,
                    reasons + ["fewer than 2 independent checks"],
                    True,
                    authorization_bound=True,
                )

        if x.mode == SecurityMode.GUARD and x.external_effect and not x.aegis_live_attested:
            return decision(
                SecurityVerdict.SUSPEND,
                reasons + ["AEGIS live state not attested; local deterministic guard only"],
                human_gated,
                authorization_bound=True if human_gated else None,
            )

        return decision(
            SecurityVerdict.ALLOW,
            reasons + ["security contract satisfied"],
            human_gated,
            authorization_bound=True if human_gated else None,
        )
