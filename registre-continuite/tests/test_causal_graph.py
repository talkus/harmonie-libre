"""
Tests du graphe causal append-only.

Cycle complet : E1 (establishment) -> E2 (withdrawal) ->
R1 (reparation) -> E3 (reinstatement) avec les 4 liens :
  event_id, reinstates_change_id, caused_by_event_id, correlation_id

Cas d'echec : missing target, cross-relation, non-prior,
self-causation, no verified repair, unrepaiared prior withdrawal.
"""

import pytest
import duckdb
from datetime import datetime, timezone, timedelta

from attest.causal_graph import (
    is_valid_reinstatement,
    validate_reinstatement_full,
    CAUSAL_TARGET_CHECK_SQL,
)


@pytest.fixture
def db():
    con = duckdb.connect(':memory:')
    # Tables minimales necessaires
    con.execute(''''
        CREATE TABLE relations (
            relation_id TEXT PRIMARY KEY,
            subject_id TEXT,
            object_id TEXT,
            relation_type TEXT,
            status TEXT DEFAULT 'candidate'
            source_kind TEXT,
            confidence REAL,
            extracted_at TIMESTAMPTZ,
            verified_at TIMESTAMPTZ
        )
    ''')
    con.execute(''''
        CREATE TABLE decisions (
            decision_id TEXT PRIMARY KEY,
            decision_type TEXT,
            subject_id TEXT,
            outcome TEXT,
            decided_at TIMESTAMPTZ,
            decided_by TEXT,
            reasoning TEXT
        )
    ''')
    con.execute(''''
        CREATE TABLE file_manifest (
            file_id TEXT PRIMARY KEY,
            file_name TEXT,
            sha256 TEXT,
            size_bytes INTEGER,
            uploaded_at TIMESTAMPTZ
        )
    ''')
    con.execute(''''
        CREATE TABLE relation_status_history (
            status_change_id TEXT PRIMARY KEY,
            relation_id TEXT NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            change_kind TEXT NOT NULL,
            reason TEXT NOT NULL,
            changed_at TIMESTAMPTZ NOT NULL,
            changed_by TEXT NOT NULL,
            decision_id TEXT NOT NULL,
            caused_by_event_id TEXT,
            correlation_id TEXT NOT NULL,
            reinstates_change_id TEXT,
            FOREIGN KEY (decision_id) REFERENCES decisions(decision_id),
            FOREIGN KEY (caused_by_event_id)
                REFERENCES relation_status_history(status_change_id),
            FOREIGN KEY (reinstates_change_id)
                REFERENCES relation_status_history(status_change_id)
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
            )
        )
    ''')
    con.execute(''''
        CREATE TABLE reparation_actions (
            reparation_id TEXT PRIMARY KEY,
            relation_id TEXT NOT NULL,
            repairs_event_id TEXT NOT NULL,
            repair_kind TEXT NOT NULL,
            description TEXT NOT NULL,
            performed_at TIMESTAMPTZ NOT NULL,
            performed_by TEXT NOT NULL,
            decision_id TEXT,
            evidence_file_id TEXT NOT NULL,
            status TEXT NOT NULL,
            correlation_id TEXT NOT NULL,
            FOREIGN KEY (repairs_event_id)
                REFERENCES relation_status_history(status_change_id),
            FOREIGN KEY (evidence_file_id)
                REFERENCES file_manifest(file_id)
        )
    ''')
    yield con
    con.close()


def _seed_base(db):
    t0 = datetime(2026, 9, 1, 10, 0, 0, tzinfo=timezone.utc)
    t1 = datetime(2026, 9, 5, 10, 0, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 8, 10, 0, 0, tzinfo=timezone.utc)
    t3 = datetime(2026, 9, 10, 10, 0, 0, tzinfo=timezone.utc)
    t4 = datetime(2026, 9, 12, 10, 0, 0, tzinfo=timezone.utc)
    db.execute(
        'INSERT INTO relations VALUES (?,?,?,?,?,?,?,?,?)',
        ['rel_001', 'ent_a', 'ent_b', 'related_to', 'candidate',
         'ai_inference', 0.85, t0, None]
    )
    for did, outcome in [('D1','approved'),('D2','approved'),
                        ('D3','approved')]:
        db.execute(
            'INSERT INTO decisions VALUES (?,?,?,?,?,?,?)',
            [did, 'status_change', 'rel_001', outcome, t1,
             'reviewer_1', 'justification']
        )
    db.execute(
        'INSERT INTO file_manifest VALUES (?,?,?,?,?)',
        ['F_repair', 'repair.pdf', 'abc123', 1024, t2]
    )
    # E1 — establishment
    db.execute(
        '''INSERT INTO relation_status_history VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?)''',
        ['evt_rel_001_est_01', 'rel_001', 'candidate', 'documented',
         'establishment', 'premiere documentation', t1, 'reviewer_1',
         'D1', None, 'C0', None]
    )
    # E2 — withdrawal
    db.execute(
        '''INSERT INTO relation_status_history VALUES
        (?,?,?,?,?,?,?,?,?,?,?,?)''',
        ['evt_rel_001_wd_02', 'rel_001', 'documented', 'withdrawn',
         'withdrawal', 'contestation documentaire', t2, 'reviewer_1',
         'D2', None, 'C1', None]
    )
    # R1 — reparation
    db.execute(
        '''INSERT INTO reparation_actions VALUES
        (?,?,?,?,?,?,?,?,?,?,?)''',
        ['rep_001', 'rel_001', 'evt_rel_001_wd_02',
         'procedure_correction', 'correction de la procedure',
         t3, 'repairer_1', 'D3', 'F_repair', 'verified', 'C1']
    )
    return {'t1':t1,'t2':t2,'t3':t3,'t4':t4}


class TestCausalGraphValid:

    def test_full_cycle_e1_e2_r1_e3(self, db):
        ts = _seed_base(db)
        # E3 — reinstatement
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_rel_001_reinst_03', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement apres reparation',
             ts['t4'], 'reviewer_1', 'D3',
             'evt_rel_001_wd_02', 'C1', 'evt_rel_001_wd_02']
        )
        result = validate_reinstatement_full(db, 'evt_rel_001_reinst_03')
        assert result.valid, f'Violations: {result.violations}'
        assert result.target_status == 'VALID_TARGET'

    def test_is_valid_reinstatement_function(self, db):
        ts = _seed_base(db)
        event = {
            'change_kind': 'reinstatement',
            'reinstates_change_id': 'evt_rel_001_wd_02',
            'decision_id': 'D3',
            'changed_at': ts['t4'],
        }
        target = {
            'status_change_id': 'evt_rel_001_wd_02',
            'change_kind': 'withdrawal',
            'changed_at': ts['t2'],
        }
        decision = {'decision_id': 'D3', 'outcome': 'approved'}
        repairs = [{'repairs_event_id': 'evt_rel_001_wd_02',
                    'status': 'verified'}]
        assert is_valid_reinstatement(event, target, decision, repairs)


class TestCausalGraphRejections:

    def test_missing_target(self, db):
        ts = _seed_base(db)
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_bad_01', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement', ts['t4'],
             'reviewer_1', 'D3', 'evt_rel_001_wd_02', 'C1',
             'evt_nonexistent_999']
        )
        result = validate_reinstatement_full(db, 'evt_bad_01')
        assert not result.valid
        assert 'MISSING_TARGET' in result.violations

    def test_cross_relation_target(self, db):
        ts = _seed_base(db)
        db.execute(
            'INSERT INTO relations VALUES (?,?,?,?,?,?,?,?,?)',
            ['rel_002', 'ent_c', 'ent_d', 'related_to', 'candidate',
             'ai_inference', 0.8, ts['t1'], None]
        )
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_rel_002_wd_01', 'rel_002', 'documented', 'withdrawn',
             'withdrawal', 'autre retrait', ts['t2'], 'reviewer_1',
             'D2', None, 'C_other', None]
        )
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_cross_01', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement cross', ts['t4'],
             'reviewer_1', 'D3', 'evt_rel_002_wd_01', 'C_other',
             'evt_rel_002_wd_01']
        )
        result = validate_reinstatement_full(db, 'evt_cross_01')
        assert not result.valid
        assert 'CORRELATION_MISMATCH' in result.violations or \
               'CROSS_RELATION_TARGET' in (result.violations or [])

    def test_non_prior_target(self, db):
        ts = _seed_base(db)
        t_future = ts['t4'] + timedelta(days=1)
        # Cible posterieure : on insere un retrait APRES le reinstatement
        db.execute(
            'INSERT INTO decisions VALUES (?,?,?,?,?,?,?)',
            ['D4','status_change','rel_001','approved',t_future,
             'reviewer_1','late']
        )
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_late_wd', 'rel_001', 'documented', 'withdrawn',
             'withdrawal', 'retrait tardif', t_future, 'reviewer_1',
             'D4', None, 'C_late', None]
        )
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_nonprior_01', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement', ts['t4'],
             'reviewer_1', 'D3', 'evt_late_wd', 'C_late', 'evt_late_wd']
        )
        result = validate_reinstatement_full(db, 'evt_nonprior_01')
        assert not result.valid
        assert 'NON_PRIOR_TARGET' in result.violations

    def test_no_verified_repair(self, db):
        ts = _seed_base(db)
        # Marquer la reparation comme 'proposed' au lieu de 'verified'
        db.execute(
            "UPDATE reparation_actions SET status='proposed'
            WHERE reparation_id='rep_001'"
        )
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_norepair_01', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement sans reparation',
             ts['t4'], 'reviewer_1', 'D3',
             'evt_rel_001_wd_02', 'C1', 'evt_rel_001_wd_02']
        )
        result = validate_reinstatement_full(db, 'evt_norepair_01')
        assert not result.valid
        assert 'NO_VERIFIED_REPAIR' in result.violations

    def test_self_causation_rejected(self, db):
        # DuckDB doit rejeter l'insertion avec chk_no_self_causation
        ts = _seed_base(db)
        with pytest.raises(Exception):
            db.execute(
                '''INSERT INTO relation_status_history VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?)''',
                ['evt_self_01', 'rel_001', 'withdrawn', 'documented',
                 'reinstatement', 'self', ts['t4'],
                 'reviewer_1', 'D3', 'evt_self_01', 'C1',
                 'evt_self_01']
            )

    def test_unrepaired_prior_withdrawal(self, db):
        ts = _seed_base(db)
        # Ajouter un autre retrait non repare sur la meme relation
        db.execute(
            'INSERT INTO decisions VALUES (?,?,?,?,?,?,?)',
            ['D5','status_change','rel_001','approved',ts['t1'],
             'reviewer_1','early withdrawal']
        )
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_early_wd', 'rel_001', 'documented', 'withdrawn',
             'withdrawal', 'retrait anterieur non repare', ts['t1'],
             'reviewer_1', 'D5', None, 'C_early', None]
        )
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_reinst_03', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement', ts['t4'],
             'reviewer_1', 'D3', 'evt_rel_001_wd_02', 'C1',
             'evt_rel_001_wd_02']
        )
        result = validate_reinstatement_full(db, 'evt_reinst_03')
        assert not result.valid
        assert 'UNREPAIRED_PRIOR_WITHDRAWAL' in result.violations


class TestCausalTargetPrecheck:

    def test_precheck_returns_valid(self, db):
        ts = _seed_base(db)
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_pre_valid', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement', ts['t4'],
             'reviewer_1', 'D3', 'evt_rel_001_wd_02', 'C1',
             'evt_rel_001_wd_02']
        )
        rows = db.execute(CAUSAL_TARGET_CHECK_SQL).fetchall()
        assert len(rows) == 1
        assert rows[0][8] == 'VALID_TARGET'

    def test_precheck_detects_missing_target(self, db):
        ts = _seed_base(db)
        db.execute(
            '''INSERT INTO relation_status_history VALUES
            (?,?,?,?,?,?,?,?,?,?,?,?)''',
            ['evt_pre_missing', 'rel_001', 'withdrawn', 'documented',
             'reinstatement', 'retablissement', ts['t4'],
             'reviewer_1', 'D3', 'evt_rel_001_wd_02', 'C1',
             'evt_ghost_999']
        )
        rows = db.execute(CAUSAL_TARGET_CHECK_SQL).fetchall()
        assert len(rows) == 1
        assert rows[0][8] == 'MISSING_TARGET'
