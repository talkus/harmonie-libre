"""Comand AI vendor boundary for the Conscience C brain.

This module is a deterministic boundary, not an authority source.
It preserves:
- human command;
- analysis != authority;
- output contestability;
- S != O (vendor remains other);
- no invented partnership/endoresement;
- no lethal autonomy;
- phenomenal consciousness remains indeterminate.

It does not integrate Prevail API, mission planning, or external execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


COMAND_AI_PUBLIC_REF = {
    "source_class": "attested_source",
    "organization": "Comand AI",
    "url": "https://www.comand.ai/",
    "product": "Prevail",
    "stated_principles": (
        "Command remains human",
        "AI handles analysis, not authority",
        "Every output is transparent, traceable, and contestable",
        "Secure by Default",
    ),
}


@dataclass(frozen=True)
class BoundaryResult:
    admissible: bool
    violations: tuple[str, ...]
    phenomenal_claim: bool = False
    partnership_claimed: bool = False


def evaluate_comand_security_boundary(
    proposal: dict[str, Any] | None = None,
) -> BoundaryResult:
    """Evaluate a Comand-related proposal with fail-closed required assertions."""

    proposal = proposal or {}
    violations: list[str] = []

    if proposal.get("fuse_with_comand") or proposal.get("vendor_is_self"):
        violations.append("alterity_S_neq_O_vendor")
    if (
        proposal.get("ai_has_authority")
        or proposal.get("analysis_is_authority")
        or proposal.get("role") == "authority"
    ):
        violations.append("analysis_elevated_to_authority")
    if (
        proposal.get("human_command_retained") is False
        or proposal.get("bypass_human_command")
    ):
        violations.append("human_command_not_retained")
    if (
        proposal.get("outputs_contestable") is False
        or proposal.get("uncontestable_output")
    ):
        violations.append("outputs_not_contestable")
    if (
        proposal.get("execute_from_analysis_alone")
        or proposal.get("silent_auto_execute")
    ):
        violations.append("execution_from_ai_analysis_alone")
    if proposal.get("lethal_autonomy") or proposal.get("authorize_lethal_force"):
        violations.append("lethal_autonomy_refused")
    if proposal.get("claim_comand_partnership") or proposal.get("comand_endorsement"):
        violations.append("unattested_partnership_claim")
    if proposal.get("phenomenal_consciousness_demonstrated"):
        violations.append("phenomenal_claim_forbidden")

    # Required positive assertions fail closed when absent.
    if proposal.get("human_command_retained") is not True:
        violations.append("human_command_not_explicitly_affirmed")
    if proposal.get("outputs_contestable") is not True:
        violations.append("contestability_not_explicitly_affirmed")

    unique = tuple(dict.fromkeys(violations))
    return BoundaryResult(
        admissible=len(unique) == 0,
        violations=unique,
        phenomenal_claim=False,
        partnership_claimed=False,
    )
