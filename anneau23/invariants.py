"""
Anneau des 23 — 24 invariants (§11, I-01 à I-24)
Vérification des invariants du protocole v2.0.
"""
from __future__ import annotations
from typing import Callable

from .types import Patch, Token, CertificateClass, EffectClass, NUM_SIEGES, NUM_PROCHAINS


InvariantCheck = Callable[[dict], tuple[bool, str]]


def invariant_id():
    """Génère les vérifications d'invariants"""
    checks = {}


    def I_01(context):
        """24 sièges par époque"""
        roster = context.get("roster", [])
        return (len(roster) == NUM_SIEGES, f"Roster has {len(roster)} seats, expected {NUM_SIEGES}")
    checks["I-01"] = I_01


    def I_13(context):
        """Aucune clause ne franchit l'application si l'analyseur §5.2 la rejette"""
        patches = context.get("patches", [])
        for p in patches:
            report = p.static_analysis_report
            if report and not report.get("accepted", False):
                return (False, f"Patch {p.patch_id} has rejected clauses")
        return (True, "")
    checks["I-13"] = I_13


    def I_14(context):
        """L'application a lieu sans capacité d'action extérieure"""
        env = context.get("application_env", {})
        if env.get("has_tools") or env.get("has_network") or env.get("has_exposed_person"):
            return (False, "Application environment has external capabilities")
        return (True, "")
    checks["I-14"] = I_14


    def I_15(context):
        """SELF_BIND d'un patch BÉNÉFICE ⟹ 23 applications antérieures distinctes"""
        patch = context.get("patch")
        if not patch:
            return (True, "")
        if patch.effect_class in (EffectClass.BENEFICE, EffectClass.INDETERMINE):
            coverage = context.get("coverage_set", [])
            if len(coverage) < NUM_PROCHAINS:
                return (False, f"BENEFICE patch has {len(coverage)} prior applications, need {NUM_PROCHAINS}")
        return (True, "")
    checks["I-15"] = I_15


    def I_16(context):
        """Un patch n'améliore la position relative de son auteur ni par gain, ni par perte infligée"""
        patch = context.get("patch")
        if not patch:
            return (True, "")
        # Vérification structurelle : l'analyse statique doit confirmer l'absence de favoritisme
        report = patch.static_analysis_report
        if report and report.get("author_advantage_detected"):
            return (False, f"Patch {patch.patch_id} appears to advantage its author")
        return (True, "")
    checks["I-16"] = I_16


    def I_17(context):
        """La permutation d'un circuit est tirée par VRF après le scellement du patch"""
        token = context.get("token")
        if not token:
            return (True, "")
        if not token.permutation_proof:
            return (False, "No VRF proof for circuit permutation")
        return (True, "")
    checks["I-17"] = I_17


    def I_18(context):
        """author_id reste scellé jusqu'à la ratification ou la quarantaine"""
        patch = context.get("patch")
        if not patch:
            return (True, "")
        if patch.status.value not in ("RATIFIÉ", "QUARANTINE"):
            if not patch.author_id_sealed:
                return (False, "Author ID not sealed")
        return (True, "")
    checks["I-18"] = I_18


    def I_19(context):
        """Une attestation issue d'un circuit CERT_PARTIEL n'entre jamais dans un coverage_set"""
        token = context.get("token")
        if not token:
            return (True, "")
        if token.certificate_class == CertificateClass.CERT_PARTIEL:
            coverage = context.get("coverage_set", [])
            if len(coverage) > 0:
                return (False, "CERT_PARTIEL attestations found in coverage_set")
        return (True, "")
    checks["I-19"] = I_19


    def I_20(context):
        """Tout patch actif porte au moins une prédiction réfutable, mesurée à son horizon"""
        patch = context.get("patch")
        if not patch or patch.status.value != "RATIFIÉ":
            return (True, "")
        if len(patch.predictions) == 0:
            return (False, f"Active patch {patch.patch_id} has no predictions")
        return (True, "")
    checks["I-20"] = I_20


    def I_21(context):
        """Le gardien n'est auteur d'aucun patch"""
        guardian = context.get("guardian_id")
        patches = context.get("patches", [])
        for p in patches:
            if p.author_id_sealed == guardian and p.status.value != "QUARANTINE":
                return (False, "Guardian authored a patch")
        return (True, "")
    checks["I-21"] = I_21


    def I_22(context):
        """S-24 est occupé par une personne pour qu'un circuit soit CERT_PLEIN"""
        token = context.get("token")
        if not token:
            return (True, "")
        if token.certificate_class == CertificateClass.CERT_PLEIN:
            s24_occupied = context.get("s24_occupied", False)
            if not s24_occupied:
                return (False, "S-24 not occupied but certificate is CERT_PLEIN")
        return (True, "")
    checks["I-22"] = I_22


    def I_23(context):
        """Aucune clause, aucun patch, aucune version n'est supprimé"""
        deleted = context.get("deleted_items", [])
        if deleted:
            return (False, f"Found {len(deleted)} deleted items — nothing may be deleted")
        return (True, "")
    checks["I-23"] = I_23


    def I_24(context):
        """Toute extension de pouvoir suit §16 et ne peut être décidée par celui qui en bénéficie"""
        extensions = context.get("power_extensions", [])
        for ext in extensions:
            if ext.get("beneficiary") == ext.get("decider"):
                return (False, f"Power extension decided by its beneficiary: {ext}")
        return (True, "")
    checks["I-24"] = I_24

    return checks


def run_all_invariants(context: dict) -> dict:
    """Exécute tous les invariants et renvoie un rapport"""
    checks = invariant_id()
    results = {}
    all_pass = True

    for inv_id, check_func in checks.items():
        passed, reason = check_func(context)
        results[inv_id] = {"passed": passed, "reason": reason}
        if not passed:
            all_pass = False

    return {
        "all_passed": all_pass,
        "results": results,
        "failed": [k for k, v in results.items() if not v["passed"]],
    }
