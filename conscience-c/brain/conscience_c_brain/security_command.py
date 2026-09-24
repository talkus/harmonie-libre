from __future__ import annotations
from dataclasses import dataclass, asdict
from enum import Enum
from typing import Any, Dict, List

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

@dataclass
class SecurityCommandDecision:
    verdict: SecurityVerdict
    reasons: List[str]
    live_security_claim: str
    human_seal_required: bool
    reality_priority_enforced: bool = True
    def to_dict(self) -> Dict[str, Any]:
        d=asdict(self); d["verdict"]=self.verdict.value; return d

class SecurityCommandGuard:
    """Deterministic adapter for SECURITY_COMMAND / AEGIS-24.
    Not the AEGIS AI ring; never claims live protection without attestation.
    """
    HIGH_RISK_FIELDS=("irreversible","changes_permissions","touches_secrets","spends_money","legal_commitment","production_change")
    def evaluate(self,x:SecurityCommandInput)->SecurityCommandDecision:
        reasons=[]
        live="LIVE_ATTESTED" if x.aegis_live_attested else "REGISTERED_NOT_LIVE"
        if x.reality_conflict:
            return SecurityCommandDecision(SecurityVerdict.BLOCK,["SECURITY_COMMAND≺E: conflict with attested reality/evidence"],live,False)
        high_risk=any(getattr(x,f) for f in self.HIGH_RISK_FIELDS)
        if not x.provenance_complete:
            reasons.append("provenance incomplete")
            if x.external_effect or high_risk:
                return SecurityCommandDecision(SecurityVerdict.SUSPEND,reasons+["external/high-risk action cannot proceed without provenance"],live,True)
        if x.mode==SecurityMode.SHADOW_READ_ONLY:
            return SecurityCommandDecision(SecurityVerdict.ADVISE,reasons+["shadow/read-only: observe and advise only"],live,False)
        if x.mode==SecurityMode.HUMAN_REQUIRED and not x.human_seal:
            return SecurityCommandDecision(SecurityVerdict.HUMAN_SEAL_REQUIRED,reasons+["human action/seal required"],live,True)
        if high_risk or (x.external_effect and x.irreversible):
            if not x.human_seal:
                return SecurityCommandDecision(SecurityVerdict.HUMAN_SEAL_REQUIRED,reasons+["high-risk/irreversible effect requires human seal"],live,True)
            if x.independent_checks<2:
                return SecurityCommandDecision(SecurityVerdict.SUSPEND,reasons+["fewer than 2 independent checks"],live,True)
        if x.mode==SecurityMode.GUARD and x.external_effect and not x.aegis_live_attested:
            return SecurityCommandDecision(SecurityVerdict.SUSPEND,reasons+["AEGIS live state not attested; local deterministic guard only"],live,high_risk)
        return SecurityCommandDecision(SecurityVerdict.ALLOW,reasons+["security contract satisfied"],live,high_risk)
