"""Audit de memoire duale : double lecture du journal (chronologique + inverse)."""
from __future__ import annotations
import duckdb

def run_dual_reading_audit(db_path: str, relation_id: str) -> dict:
    con = duckdb.connect(db_path, read_only=True)
    events = con.execute("""
        SELECT status_change_id, old_status, new_status, change_kind,
               changed_at, correlation_id, reinstates_change_id,
               caused_by_event_id, decision_id
        FROM relation_status_history WHERE relation_id = ?
        ORDER BY changed_at ASC
    """, [relation_id]).fetchall()
    con.close()
    discontinuities = 0
    retrograde_violations = 0
    events_count = len(events)
    if events_count == 0:
        return {'concordance_verdict': 'ALIGNED', 'discontinuities_count': 0, 'retrograde_violations_count': 0, 'events_analyzed': 0}
    # Lecture chronologique : continuite
    for i in range(1, events_count):
        prev_ev = events[i - 1]
        curr_ev = events[i]
        if curr_ev[3] == 'reinstatement':
            if curr_ev[6] is None: discontinuities += 1
        elif prev_ev[2] != curr_ev[1]: discontinuities += 1
    # Lecture inverse : retrograde
    for i in range(events_count - 2, -1, -1):
        later_ev = events[i + 1]
        earlier_ev = events[i]
        if later_ev[3] == 'reinstatement': pass
        elif later_ev[1] != earlier_ev[2]: retrograde_violations += 1
    verdict = 'ALIGNED' if discontinuities == 0 and retrograde_violations == 0 else 'MISALIGNED'
    return {'concordance_verdict': verdict, 'discontinuities_count': discontinuities, 'retrograde_violations_count': retrograde_violations, 'events_analyzed': events_count}
