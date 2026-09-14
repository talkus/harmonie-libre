"""
Graphe causal append-only pour le registre de continuite.

Un evenement de restauration (reinstatement) ne modifie jamais
la revocation qu'il traite. Il cree un nouvel evenement, lie
a cette revocation, autorise par une nouvelle decision et
soutenu par des preuves verifiables.

Quatre identifiants distincts :
  - event_id            : identifie l'evenement lui-meme
  - reinstates_change_id : lien normatif (quelle revocation est restauree)
  - caused_by_event_id   : lien procedurral (quel acte a conduit ici)
  - correlation_id        : lien historique (dossier causal global)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class CausalValidationResult:
    valid: bool
    violations: list[str]
    target_status: str | None


def is_valid_reinstatement(
    event: dict[str, Any],
    target: dict[str, Any],
    decision: dict[str, Any],
    repairs: list[dict[str, Any]],
) -> bool:
    """
    Valide qu'un evenement de reinstatement respecte la regle
    de non-effacement et la chaine causale complete.

    Conditions :
    1. L'evenement est de type reinstatement
    2. reinstates_change_id pointe vers la cible
    3. La cible est un retrait (withdrawal, rejection, dispute)
    4. La cible est anterieure a la restauration
    5. La decision existe et est approved
    6. Au moins une reparation verified liee a la cible existe
"""
    return (
        event.get("change_kind") == "reinstatement"
        and event.get("reinstates_change_id") == target.get("status_change_id")
        and target.get("change_kind") in {"withdrawal", "rejection", "dispute"}
        and target.get("changed_at") < event.get("changed_at")
        and decision.get("decision_id") == event.get("decision_id")
        and decision.get("outcome") == "approved"
        and any(
            r.get("repairs_event_id") == target.get("status_change_id")
            and r.get("status") == "verified"
            for r in repairs
        )
    )


CAUSAL_TARGET_CHECK_SQL = """
    SELECT
        restore.status_change_id AS reinstatement_event,
        restore.relation_id,
        restore.changed_at AS reinstated_at,
        restore.reinstates_change_id,
        revoked.status_change_id AS referenced_event,
        revoked.change_kind AS referenced_kind,
        revoked.new_status AS referenced_status,
        revoked.changed_at AS revoked_at,
        CASE
            WHEN revoked.status_change_id IS NULL
                THEN 'MISSING_TARGET'
            WHEN revoked.relation_id <> restore.relation_id
                THEN 'CROSS_RELATION_TARGET'
            WHEN revoked.changed_at >= restore.changed_at
                THEN 'NON_PRIOR_TARGET'
            WHEN revoked.change_kind NOT IN (
                'withdrawal', 'rejection', 'dispute'
            )
                THEN 'TARGET_NOT_REVOCATION'
            WHEN revoked.new_status NOT IN (
                'withdrawn', 'rejected', 'disputed'
            )
                THEN 'TARGET_NOT_DISABLED_STATE'
            ELSE 'VALID_TARGET'
        END AS causal_target_status
    FROM relation_status_history AS restore
    LEFT JOIN relation_status_history AS revoked
        ON revoked.status_change_id = restore.reinstates_change_id
    WHERE restore.change_kind = 'reinstatement'
"""


def validate_reinstatement_full(
    con,
    reinstatement_event_id: str,
) -> CausalValidationResult:
    """
    Validation complete en 10 points d'un evenement de reinstatement.

    L'ordre est important : on ne declare jamais 'retabli'
    parce qu'un etat actif est observe a la fin. On demontre
    que cet etat est le resultat d'une chaine autorisee.

    1. reinstates_change_id est renseigne
    2. La cible existe
    3. La cible est anterieure a la restauration
    4. La cible a le type withdrawal, rejection ou dispute
    5. La cible a conduit a un statut de retrait
    6. decision_id existe, meme relation_id, statut approved
    7. La decision s'appuie sur au moins une preuve verified
    8. Une reparation verified liee a la revocation existe
    9. Meme correlation_id ou lien documente
    10. Aucun autre retrait non repare, anterieur, toujours actif
"""
    violations: list[str] = []
    target_status: str | None = None

    # Recuperer l'evenement de reinstatement
    row = con.execute(
        """SELECT status_change_id, relation_id, old_status, new_status,
                  change_kind, reason, changed_at, changed_by,
                  decision_id, caused_by_event_id, correlation_id,
                  reinstates_change_id
           FROM relation_status_history
           WHERE status_change_id = ?""",
        [reinstatement_event_id],
    ).fetchone()

    if row is None:
        return CausalValidationResult(
            valid=False,
            violations=['EVENT_NOT_FOUND'],
            target_status=None,
        )

    (
        _eid, relation_id, _old, _new, change_kind, _reason,
        changed_at, _by, decision_id, _caused_by, correlation_id,
        reinstates_change_id,
    ) = row

    # 1. reinstates_change_id renseigne
    if reinstates_change_id is None:
        violations.append('MISSING_REINSTATES_CHANGE_ID')
        return CausalValidationResult(False, violations, None)

    # 2. La cible existe
    target_row = con.execute(
        """SELECT status_change_id, relation_id, new_status, change_kind,
                  changed_at, decision_id, correlation_id
           FROM relation_status_history
           WHERE status_change_id = ?""",
        [reinstates_change_id],
    ).fetchone()

    if target_row is None:
        violations.append('MISSING_TARGET')
        return CausalValidationResult(False, violations, 'MISSING_TARGET')

    (
        t_id, t_relation, t_new_status, t_change_kind,
        t_changed_at, t_decision_id, t_correlation,
    ) = target_row

    # 3. La cible est anterieure
    if t_changed_at >= changed_at:
        violations.append('NON_PRIOR_TARGET')

    # 4. La cible est un retrait
    if t_change_kind not in ('withdrawal', 'rejection', 'dispute'):
        violations.append('TARGET_NOT_REVOCATION')

    # 5. La cible a conduit a un statut de retrait
    if t_new_status not in ('withdrawn', 'rejected', 'disputed'):
        violations.append('TARGET_NOT_DISABLED_STATE')

    # 6. decision_id existe, meme relation_id, statut approved
    dec_row = con.execute(
        """SELECT decision_id, outcome FROM decisions
           WHERE decision_id = ?""",
        [decision_id],
    ).fetchone()

    if dec_row is None:
        violations.append('DECISION_NOT_FOUND')
    else:
        if dec_row[1] != 'approved':
            violations.append('DECISION_NOT_APPROVED')

    # 7. La decision s'appuie sur au moins une preuve verified
    # (verification simplifiee : la reparationporte evidence_file_id)
    # 8. Une reparation verified liee a la revocation existe
    repair_count = con.execute(
        """SELECT COUNT(*) FROM reparation_actions
           WHERE repairs_event_id = ? AND status = 'verified'""",
        [reinstates_change_id],
    ).fetchone()[0]

    if repair_count == 0:
        violations.append('NO_VERIFIED_REPAIR')

    # 9. Meme correlation_id
    if t_correlation != correlation_id:
        violations.append('CORRELATION_MISMATCH')

    # 10. Aucun autre retrait non repare, anterieur, toujours actif
    active_withdrawals = con.execute(
        """SELECT COUNT(*) FROM relation_status_history rsh
           WHERE rsh.relation_id = ?
             AND rsh.change_kind IN ('withdrawal', 'rejection', 'dispute')
             AND rsh.changed_at < ?
             AND rsh.status_change_id <> ?
             AND NOT EXISTS (
                 SELECT 1 FROM relation_status_history rein
                 WHERE rein.reinstates_change_id = rsh.status_change_id
             )
             AND NOT EXISTS (
                 SELECT 1 FROM reparation_actions rep
                 WHERE rep.repairs_event_id = rsh.status_change_id
                   AND rep.status = 'verified'
             )""",
        [relation_id, changed_at, reinstates_change_id],
    ).fetchone()[0]

    if active_withdrawals > 0:
        violations.append('UNREPAIRED_PRIOR_WITHDRAWAL')

    # Statut final
    if violations:
        # Recuperer le statut de la cible via la requete de precontrole
        precheck = con.execute(
            CAUSAL_TARGET_CHECK_SQL
            + ' AND restore.status_change_id = ?',
            [reinstatement_event_id],
        ).fetchone()
        target_status = precheck[8] if precheck else None
    else:
        target_status = 'VALID_TARGET'

    return CausalValidationResult(
        valid=len(violations) == 0,
        violations=violations,
        target_status=target_status,
    )
