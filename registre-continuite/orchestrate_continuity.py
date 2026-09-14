#!/usr/bin/env python3
"""
orchestrate_continuity.py -- Registre de continuite gouverne (minimal, executable).

Corrections vs iteration precedente :
  a) FK corrigee : E3.caused_by_event_id pointe vers E_R (l'evenement repair
     dans relation_status_history), pas vers R1 (reparation_id dans
     reparation_actions). reparation_actions.reparation_id est une FK
     vers relation_status_history.status_change_id (change_kind='repair').
  b) write_transition() : seul point d'entree pour ecrire dans
     relation_status_history. OCC via relation_streams + RETURNING.
     Aucun autre chemin de code n'insere directement.
  c) Pas d'affirmation non testee : pas d'attestation cryptographique,
     pas de gatekeeper Parquet, pas de node n8n, pas de projection de
     capacites. Ce fichier contient uniquement ce qui est implemente.

Cycle : E1 (establishment) -> E2 (withdrawal) -> E_R (repair event) ->
        R1 (reparation detail) -> E3 (reinstatement)

Requirements : duckdb >= 0.10 (pour RETURNING sur UPDATE).
"""

import duckdb
from datetime import datetime, timedelta, timezone
import hashlib
import uuid


# =================================================================
# SCHEMA (tout en un, pas de fichier SQL externe)
# =================================================================

SCHEMA_SQL = '''
CREATE TABLE relations (
    relation_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    target_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'candidate',
    created_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE decisions (
    decision_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('approved', 'rejected', 'pending')),
    reasoning TEXT,
    decided_by TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL
);

CREATE TABLE file_manifest (
    file_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    sha256_hash TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending', 'verified', 'rejected', 'archived')),
    verified_by TEXT,
    verified_at TIMESTAMPTZ
);

CREATE TABLE relation_streams (
    relation_id TEXT PRIMARY KEY,
    current_version INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE relation_status_history (
    status_change_id TEXT PRIMARY KEY,
    relation_id TEXT NOT NULL,
    aggregate_version INTEGER NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    change_kind TEXT NOT NULL CHECK (change_kind IN (
        'establishment', 'transition', 'withdrawal',
        'rejection', 'dispute', 'repair', 'reinstatement'
    )),
    reason TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL,
    changed_by TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    caused_by_event_id TEXT,
    correlation_id TEXT NOT NULL,
    reinstates_change_id TEXT,
    FOREIGN KEY (caused_by_event_id)
        REFERENCES relation_status_history(status_change_id),
    FOREIGN KEY (reinstates_change_id)
        REFERENCES relation_status_history(status_change_id),
    CONSTRAINT chk_no_self_causation CHECK (
        caused_by_event_id IS NULL
        OR caused_by_event_id <> status_change_id
    ),
    CONSTRAINT chk_no_self_reinstatement CHECK (
        reinstates_change_id IS NULL
        OR reinstates_change_id <> status_change_id
    ),
    CONSTRAINT chk_reinstatement_requires_target CHECK (
        (change_kind = 'reinstatement'
         AND reinstates_change_id IS NOT NULL
         AND caused_by_event_id IS NOT NULL
         AND new_status IN ('documented', 'verified'))
        OR (change_kind <> 'reinstatement'
            AND reinstates_change_id IS NULL)
    ),
    CONSTRAINT chk_decision_required CHECK (
        new_status NOT IN ('documented', 'verified', 'withdrawn', 'rejected')
        OR decision_id IS NOT NULL
    )
);

CREATE UNIQUE INDEX uq_rel_agg_ver
    ON relation_status_history(relation_id, aggregate_version);

CREATE INDEX idx_rsh_correlation
    ON relation_status_history(correlation_id);

-- reparation_id = FK vers relation_status_history.status_change_id
--   (l'evenement repair doit exister avant d'ajouter les details)
-- repairs_event_id = la revocation reparee (status_change_id du retrait)
CREATE TABLE reparation_actions (
    reparation_id TEXT PRIMARY KEY,
    relation_id TEXT NOT NULL,
    repairs_event_id TEXT NOT NULL,
    repair_kind TEXT NOT NULL CHECK (repair_kind IN (
        'fact_correction', 'evidence_replacement',
        'procedure_correction', 'acknowledgment',
        'withdrawal_of_error', 'safeguard_added',
        'reinstatement_basis'
    )),
    description TEXT NOT NULL,
    performed_at TIMESTAMPTZ NOT NULL,
    performed_by TEXT NOT NULL,
    evidence_file_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN (
        'proposed', 'completed', 'verified', 'rejected'
    )),
    correlation_id TEXT NOT NULL,
    FOREIGN KEY (reparation_id)
        REFERENCES relation_status_history(status_change_id),
    FOREIGN KEY (repairs_event_id)
        REFERENCES relation_status_history(status_change_id),
    FOREIGN KEY (evidence_file_id)
        REFERENCES file_manifest(file_id)
);

CREATE INDEX idx_rep_repairs_event
    ON reparation_actions(repairs_event_id);

CREATE TABLE invariants (
    invariant_id TEXT PRIMARY KEY,
    description TEXT NOT NULL
);

INSERT INTO invariants VALUES
    ('inv_12', 'Toute restauration declare quelle revocation elle traite, quelle decision l autorise, et quelles preuves la soutiennent.');
'''


# =================================================================
# FONCTION D'ECRITURE UNIQUE (OCC)
# =================================================================

def write_transition(con, *, relation_id, old_status, new_status,
                     change_kind, reason, changed_at, changed_by,
                     decision_id, correlation_id,
                     caused_by_event_id=None,
                     reinstates_change_id=None, expected_version=0):
    '''Seul point d'entree pour ecrire dans relation_status_history.

    OCC : expected_version doit egaler current_version dans relation_streams.
    Aucun autre chemin de code ne doit inserer dans relation_status_history.
    '''
    con.execute('BEGIN TRANSACTION')
    try:
        # 1. OCC : lire la version courante
        row = con.execute(
            'SELECT current_version FROM relation_streams WHERE relation_id = ?',
            [relation_id]
        ).fetchone()

        if row is None:
            con.execute(
                'INSERT INTO relation_streams (relation_id, current_version) VALUES (?, 0)',
                [relation_id]
            )
            current_version = 0
        else:
            current_version = row[0]

        if expected_version != current_version:
            raise RuntimeError(
                f'OCC : attendu {expected_version}, courant {current_version}'
            )

        new_version = current_version + 1
        eid = f'evt_{change_kind}_{new_version}_{uuid.uuid4().hex[:8]}'

        # 2. Verification explicite des FK (DuckDB peut ne pas les enforce)
        if caused_by_event_id is not None:
            fk = con.execute(
                'SELECT 1 FROM relation_status_history WHERE status_change_id = ?',
                [caused_by_event_id]
            ).fetchone()
            if not fk:
                raise ValueError(
                    f'caused_by_event_id {caused_by_event_id} introuvable'
                )

        if reinstates_change_id is not None:
            fk = con.execute(
                'SELECT 1 FROM relation_status_history WHERE status_change_id = ?',
                [reinstates_change_id]
            ).fetchone()
            if not fk:
                raise ValueError(
                    f'reinstates_change_id {reinstates_change_id} introuvable'
                )

        # 3. Garde causale pour les reinstatements
        if change_kind == 'reinstatement':
            if not reinstates_change_id or not caused_by_event_id:
                raise ValueError(
                    'Une rehabilitation exige reinstates_change_id et caused_by_event_id'
                )

            target = con.execute(
                '''SELECT changed_at, new_status, correlation_id, change_kind
                   FROM relation_status_history
                   WHERE status_change_id = ? AND relation_id = ?
                     AND change_kind IN ('withdrawal', 'rejection', 'dispute')''',
                [reinstates_change_id, relation_id]
            ).fetchone()

            if not target:
                raise ValueError(
                    f'Revocation cible {reinstates_change_id} introuvable ou invalide'
                )

            t_at, t_new, t_corr, t_kind = target

            if t_at >= changed_at:
                raise ValueError('Paradoxe temporel : cible posterieure')
            if t_corr != correlation_id:
                raise ValueError(
                    f'Rupture correlation_id : {correlation_id} != {t_corr}'
                )

            repair_count = con.execute(
                '''SELECT COUNT(*) FROM reparation_actions
                   WHERE repairs_event_id = ? AND status = 'verified' ''',
                [reinstates_change_id]
            ).fetchone()[0]

            if repair_count == 0:
                raise ValueError('Aucune reparation verified pour la cible')

        # 4. Insertion dans l'historique (append-only)
        con.execute(
            '''INSERT INTO relation_status_history (
                status_change_id, relation_id, aggregate_version,
                old_status, new_status, change_kind, reason,
                changed_at, changed_by, decision_id,
                caused_by_event_id, correlation_id, reinstates_change_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            [eid, relation_id, new_version,
             old_status, new_status, change_kind, reason,
             changed_at, changed_by, decision_id,
             caused_by_event_id, correlation_id, reinstates_change_id]
        )

        # 5. Mise a jour OCC (WHERE current_version = expected)
        updated = con.execute(
            '''UPDATE relation_streams SET current_version = ?
               WHERE relation_id = ? AND current_version = ?
               RETURNING current_version''',
            [new_version, relation_id, current_version]
        ).fetchone()

        if updated is None:
            raise RuntimeError('OCC : conflit de version concurrent')

        # 6. Projection : relations.status reflete le dernier evenement
        con.execute(
            'UPDATE relations SET status = ? WHERE relation_id = ?',
            [new_status, relation_id]
        )

        con.execute('COMMIT')
        return eid
    except Exception:
        con.execute('ROLLBACK')
        raise


def add_reparation_detail(con, *, repair_event_id, relation_id,
                          repairs_event_id, repair_kind, description,
                          performed_at, performed_by, evidence_file_id,
                          status, correlation_id):
    '''Ajoute une ligne de detail dans reparation_actions.

    repair_event_id : status_change_id de l'evenement repair dans
                      relation_status_history (FK).
    repairs_event_id : status_change_id de la revocation reparee.
    '''
    con.execute(
        '''INSERT INTO reparation_actions (
            reparation_id, relation_id, repairs_event_id,
            repair_kind, description, performed_at, performed_by,
            evidence_file_id, status, correlation_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
        [repair_event_id, relation_id, repairs_event_id,
         repair_kind, description, performed_at, performed_by,
         evidence_file_id, status, correlation_id]
    )


# =================================================================
# AUDIT CAUSAL (inline, pas d'import externe)
# =================================================================

def verify_causal_graph(con, relation_id):
    '''Audit causal : verifie chaque reinstatement d'une relation.'''
    violations = []

    reinstatements = con.execute(
        '''SELECT status_change_id, changed_at, caused_by_event_id,
                  correlation_id, reinstates_change_id
           FROM relation_status_history
           WHERE relation_id = ? AND change_kind = 'reinstatement'
           ORDER BY changed_at''',
        [relation_id]
    ).fetchall()

    for row in reinstatements:
        eid, changed_at, caused_by, corr_id, reinstates_id = row

        if reinstates_id is None:
            violations.append({'event': eid, 'code': 'MISSING_REINSTATES_CHANGE_ID'})
            continue

        target = con.execute(
            '''SELECT changed_at, new_status, correlation_id, change_kind
               FROM relation_status_history WHERE status_change_id = ?''',
            [reinstates_id]
        ).fetchone()

        if target is None:
            violations.append({
                'event': eid, 'code': 'MISSING_TARGET',
                'detail': f'cible {reinstates_id} introuvable'
            })
            continue

        t_at, t_new, t_corr, t_kind = target

        if t_kind not in ('withdrawal', 'rejection', 'dispute'):
            violations.append({
                'event': eid, 'code': 'TARGET_NOT_REVOCATION',
                'detail': f'type {t_kind}'
            })
        if t_at >= changed_at:
            violations.append({'event': eid, 'code': 'NON_PRIOR_TARGET'})
        if t_corr != corr_id:
            violations.append({
                'event': eid, 'code': 'CORRELATION_MISMATCH',
                'detail': f'{corr_id} != {t_corr}'
            })

        if caused_by:
            caused_exists = con.execute(
                'SELECT 1 FROM relation_status_history WHERE status_change_id = ?',
                [caused_by]
            ).fetchone()
            if not caused_exists:
                violations.append({
                    'event': eid, 'code': 'CAUSED_BY_NOT_FOUND',
                    'detail': f'{caused_by} introuvable'
                })

        repair_count = con.execute(
            '''SELECT COUNT(*) FROM reparation_actions
               WHERE repairs_event_id = ? AND status = 'verified' ''',
            [reinstates_id]
        ).fetchone()[0]

        if repair_count == 0:
            violations.append({'event': eid, 'code': 'NO_VERIFIED_REPAIR'})

    return {
        'causal_verdict': 'ALIGNED' if not violations else 'MISALIGNED',
        'reinstatements_analyzed': len(reinstatements),
        'violations_count': len(violations),
        'violations': violations,
    }


# =================================================================
# AUDIT DE MEMOIRE DUALE (inline, pas d'import externe)
# =================================================================

def run_dual_reading_audit(con, relation_id):
    '''Double lecture du journal : chronologique + inverse.'''
    events = con.execute(
        '''SELECT status_change_id, old_status, new_status, change_kind,
                  changed_at, reinstates_change_id
           FROM relation_status_history
           WHERE relation_id = ?
           ORDER BY changed_at ASC''',
        [relation_id]
    ).fetchall()

    discontinuities = 0
    retrograde = 0

    # Lecture chronologique : continuite
    for i in range(1, len(events)):
        prev_new = events[i - 1][2]
        curr_old = events[i][1]
        curr_kind = events[i][3]
        curr_reinstates = events[i][5]

        if curr_kind == 'reinstatement':
            if curr_reinstates is None:
                discontinuities += 1
        elif prev_new != curr_old:
            discontinuities += 1

    # Lecture inverse : pas de retrograde non explique
    for i in range(len(events) - 2, -1, -1):
        later_old = events[i + 1][1]
        later_kind = events[i + 1][3]
        earlier_new = events[i][2]

        if later_kind == 'reinstatement':
            pass
        elif later_old != earlier_new:
            retrograde += 1

    return {
        'concordance_verdict': 'ALIGNED' if discontinuities == 0 and retrograde == 0 else 'MISALIGNED',
        'discontinuities_count': discontinuities,
        'retrograde_violations_count': retrograde,
        'events_analyzed': len(events),
    }


# =================================================================
# SEED : Cycle E1 -> E2 -> E_R -> R1 -> E3
# =================================================================

def seed_cycle(con):
    '''Deroule le cycle causal complet avec FK corrigee.'''
    now = datetime.now(timezone.utc)
    rel_id = 'rel_demo'
    corr_id = f'corr_{uuid.uuid4().hex[:12]}'

    # Relation de base
    con.execute(
        'INSERT INTO relations VALUES (?, ?, ?, ?, ?, ?)',
        [rel_id, 'ent_a', 'ent_b', 'related_to', 'candidate', now]
    )

    # Decisions
    d1 = 'dec_est_01'
    d2 = 'dec_wd_02'
    d3 = 'dec_repair_03'
    d4 = 'dec_reinst_04'

    for did, dt, reason in [
        (d1, now - timedelta(days=3), 'Etablissement initial'),
        (d2, now - timedelta(days=2), 'Retrait preventif'),
        (d3, now - timedelta(hours=12), 'Approbation reparation'),
        (d4, now, 'Approbation rehabilitation'),
    ]:
        con.execute(
            'INSERT INTO decisions VALUES (?, ?, ?, ?, ?, ?)',
            [did, rel_id, 'approved', reason, 'reviewer_1', dt]
        )

    # Fichier de preuve
    file_id = 'f_repair_01'
    con.execute(
        'INSERT INTO file_manifest VALUES (?, ?, ?, ?, ?, ?)',
        [file_id, 'Rapport de correction',
         hashlib.sha256(b'procedure reparatoire 2026').hexdigest(),
         'verified', 'mikael', now - timedelta(hours=6)]
    )

    # E1 : Etablissement (version 0 -> 1)
    e1 = write_transition(
        con, relation_id=rel_id, old_status='candidate',
        new_status='documented', change_kind='establishment',
        reason='Premiere documentation', changed_at=now - timedelta(days=3),
        changed_by='reviewer_1', decision_id=d1, correlation_id=corr_id,
        expected_version=0
    )
    print(f'  E1 establishment : {e1} (version 1)')

    # E2 : Revocation (version 1 -> 2)
    e2 = write_transition(
        con, relation_id=rel_id, old_status='documented',
        new_status='withdrawn', change_kind='withdrawal',
        reason='Contestation documentaire', changed_at=now - timedelta(days=2),
        changed_by='reviewer_1', decision_id=d2, correlation_id=corr_id,
        caused_by_event_id=e1, expected_version=1
    )
    print(f'  E2 withdrawal    : {e2} (version 2)')

    # E_R : Evenement repair (version 2 -> 3)
    # Cet evenement existe dans relation_status_history.
    # E3.caused_by_event_id pointera vers E_R, pas vers R1.
    e_r = write_transition(
        con, relation_id=rel_id, old_status='withdrawn',
        new_status='withdrawn', change_kind='repair',
        reason='Procedure de correction appliquee',
        changed_at=now - timedelta(hours=12),
        changed_by='repairer_1', decision_id=d3, correlation_id=corr_id,
        caused_by_event_id=e2, expected_version=2
    )
    print(f'  E_R repair event : {e_r} (version 3)')

    # R1 : Detail de reparation (dans reparation_actions)
    # reparation_id = E_R (FK vers relation_status_history)
    # repairs_event_id = E2 (la revocation reparee)
    add_reparation_detail(
        con, repair_event_id=e_r, relation_id=rel_id,
        repairs_event_id=e2, repair_kind='procedure_correction',
        description='Correction complete de la specification',
        performed_at=now - timedelta(hours=6),
        performed_by='repairer_1', evidence_file_id=file_id,
        status='verified', correlation_id=corr_id
    )
    print(f'  R1 reparation    : {e_r} -> repairs {e2}')

    # E3 : Rehabilitation (version 3 -> 4)
    # caused_by_event_id = E_R (existe dans relation_status_history)
    # reinstates_change_id = E2 (la revocation restauree)
    e3 = write_transition(
        con, relation_id=rel_id, old_status='withdrawn',
        new_status='documented', change_kind='reinstatement',
        reason='Retablissement apres reparation verifiee',
        changed_at=now, changed_by='reviewer_1',
        decision_id=d4, correlation_id=corr_id,
        caused_by_event_id=e_r, reinstates_change_id=e2,
        expected_version=3
    )
    print(f'  E3 reinstatement : {e3} (version 4)')

    return rel_id, corr_id, {'E1': e1, 'E2': e2, 'E_R': e_r, 'E3': e3}


# =================================================================
# MAIN
# =================================================================

def main():
    print('=== Registre de continuite gouverne (minimal) ===')
    print()

    con = duckdb.connect(':memory:')
    con.execute(SCHEMA_SQL)
    print('Schema cree.')

    print()
    print('--- Seed : cycle E1 -> E2 -> E_R -> R1 -> E3 ---')
    rel_id, corr_id, events = seed_cycle(con)
    print(f'  correlation_id : {corr_id}')

    # Verifier relations.status (projection via write_transition)
    status = con.execute(
        'SELECT status FROM relations WHERE relation_id = ?', [rel_id]
    ).fetchone()[0]
    print(f'  relations.status = {status} (attendu: documented)')

    version = con.execute(
        'SELECT current_version FROM relation_streams WHERE relation_id = ?',
        [rel_id]
    ).fetchone()[0]
    print(f'  current_version = {version} (attendu: 4)')

    print()
    print('--- Audit de memoire duale ---')
    dual = run_dual_reading_audit(con, rel_id)
    print(f"  Verdict        : {dual['concordance_verdict']}")
    print(f"  Discontinuites : {dual['discontinuities_count']}")
    print(f"  Retrograde     : {dual['retrograde_violations_count']}")
    print(f"  Evenements     : {dual['events_analyzed']}")

    print()
    print('--- Audit causal ---')
    causal = verify_causal_graph(con, rel_id)
    print(f"  Verdict         : {causal['causal_verdict']}")
    print(f"  Rehabilitations : {causal['reinstatements_analyzed']}")
    print(f"  Violations      : {causal['violations_count']}")
    if causal['violations']:
        for v in causal['violations']:
            print(f"    - {v['code']}: {v.get('detail', '')}")

    # Test OCC : version attendue incorrecte
    print()
    print('--- Test OCC : conflit de version ---')
    try:
        write_transition(
            con, relation_id=rel_id, old_status='documented',
            new_status='verified', change_kind='transition',
            reason='Test OCC', changed_at=datetime.now(timezone.utc),
            changed_by='test', decision_id='dec_test',
            correlation_id=corr_id, expected_version=99
        )
        print('  ECHEC : OCC non bloque')
    except RuntimeError as e:
        print(f'  OK : OCC bloque -> {e}')

    print()
    if (dual['concordance_verdict'] == 'ALIGNED'
            and causal['causal_verdict'] == 'ALIGNED'
            and status == 'documented'
            and version == 4):
        print('[SUCCES] Integrite totale : causalite + memoire duale + projection + OCC.')
    else:
        print('[ECHEC] Invariant rompu.')

    con.close()


if __name__ == '__main__':
    main()
