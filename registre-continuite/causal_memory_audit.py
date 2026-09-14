"""Audit de causalite du graphe d evenements."""
from __future__ import annotations
import duckdb

def verify_causal_graph(db_path: str, relation_id: str) -> dict:
    con = duckdb.connect(db_path, read_only=True)
    violations = []
    reinstatements_analyzed = 0
    reinstatements = con.execute("""
        SELECT status_change_id, old_status, new_status, change_kind,
               reason, changed_at, changed_by, decision_id,
               caused_by_event_id, correlation_id, reinstates_change_id
        FROM relation_status_history
        WHERE relation_id = ? AND change_kind = 'reinstatement'
        ORDER BY changed_at ASC
    """, [relation_id]).fetchall()
    for row in reinstatements:
        reinstatements_analyzed += 1
        (eid, old_st, new_st, kind, reason, changed_at, changed_by, dec_id, caused_by, corr_id, reinstates_id) = row
        if reinstates_id is None:
            violations.append({'event_id': eid, 'code': 'MISSING_REINSTATES_CHANGE_ID', 'detail': 'reinstates_change_id null'})
            continue
        target = con.execute("""
            SELECT status_change_id, relation_id, new_status, change_kind, changed_at, correlation_id
            FROM relation_status_history WHERE status_change_id = ?
        """, [reinstates_id]).fetchone()
        if target is None:
            violations.append({'event_id': eid, 'code': 'MISSING_TARGET', 'detail': f'Cible {reinstates_id} introuvable'})
            continue
        (t_id, t_rel, t_new, t_kind, t_at, t_corr) = target
        if t_rel != relation_id: violations.append({'event_id': eid, 'code': 'CROSS_RELATION_TARGET', 'detail': f'Cible sur {t_rel}'})
        if t_at >= changed_at: violations.append({'event_id': eid, 'code': 'NON_PRIOR_TARGET', 'detail': 'Cible posterieure'})
        if t_kind not in ('withdrawal', 'rejection', 'dispute'): violations.append({'event_id': eid, 'code': 'TARGET_NOT_REVOCATION', 'detail': f'Type {t_kind}'})
        if t_new not in ('withdrawn', 'rejected', 'disputed'): violations.append({'event_id': eid, 'code': 'TARGET_NOT_DISABLED_STATE', 'detail': f'Statut {t_new}'})
        if t_corr != corr_id: violations.append({'event_id': eid, 'code': 'CORRELATION_MISMATCH', 'detail': f'{corr_id} != {t_corr}'})
        repair_count = con.execute("SELECT COUNT(*) FROM reparation_actions WHERE repairs_event_id = ? AND status = 'verified'", [reinstates_id]).fetchone()[0]
        if repair_count == 0: violations.append({'event_id': eid, 'code': 'NO_VERIFIED_REPAIR', 'detail': 'Aucune reparation verified'})
        active_wd = con.execute("""
            SELECT COUNT(*) FROM relation_status_history rsh
            WHERE rsh.relation_id = ? AND rsh.change_kind IN ('withdrawal', 'rejection', 'dispute')
              AND rsh.changed_at < ? AND rsh.status_change_id <> ?
              AND NOT EXISTS (SELECT 1 FROM relation_status_history rein WHERE rein.reinstates_change_id = rsh.status_change_id)
              AND NOT EXISTS (SELECT 1 FROM reparation_actions rep WHERE rep.repairs_event_id = rsh.status_change_id AND rep.status = 'verified')
        """, [relation_id, changed_at, reinstates_id]).fetchone()[0]
        if active_wd > 0: violations.append({'event_id': eid, 'code': 'UNREPAIRED_PRIOR_WITHDRAWAL', 'detail': f'{active_wd} retrait(s) non repare(s)'})
    con.close()
    return {'causal_verdict': 'ALIGNED' if not violations else 'MISALIGNED', 'reinstatements_analyzed': reinstatements_analyzed, 'violations_count': len(violations), 'violations': violations}
