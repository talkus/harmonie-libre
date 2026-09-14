#!/usr/bin/env python3
"""Amorcage de bout en bout et validation du cycle causal complet."""
from datetime import datetime, timedelta, timezone
import hashlib, os, pathlib, sys, uuid
import duckdb
from causal_memory_audit import verify_causal_graph
from dual_memory_audit import run_dual_reading_audit

DB_PATH = 'continuite.duckdb'
SCHEMA_PATH = pathlib.Path(__file__).parent / 'schema.sql'
SQL_DIR = pathlib.Path(__file__).parent / 'sql'

def apply_schema_and_migrations(con):
    con.execute('CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ)')
    if SCHEMA_PATH.exists():
        print('-> Application schema.sql...')
        con.execute(SCHEMA_PATH.read_text(encoding='utf-8'))
    else: print('  ATTENTION : schema.sql absent')
    for sql_file in sorted(SQL_DIR.glob('*.sql')):
        version = sql_file.stem.split('_')[0]
        applied = con.execute('SELECT 1 FROM schema_migrations WHERE version = ?', [version]).fetchone()
        if not applied:
            print(f'-> Application migration {sql_file.name}...')
            con.execute(sql_file.read_text(encoding='utf-8'))
            con.execute('INSERT INTO schema_migrations VALUES (?, CURRENT_TIMESTAMP)', [version])

def seed_demo_causal_cycle(db_path: str):
    con = duckdb.connect(db_path)
    now = datetime.now(timezone.utc)
    rel_id = 'rel_audit_40_semaines'
    corr_id = f'corr_{uuid.uuid4().hex[:12]}'
    doc_id = 'doc_bootstrap_causal'
    print(f'\nCycle causal de test sur : {rel_id}')
    con.execute('BEGIN TRANSACTION;')
    try:
        con.execute("INSERT INTO documents (document_id, title, source_type, content_hash, original_format, imported_by) VALUES (?, 'Document bootstrap causal', 'local', ?, 'text', 'bootstrap') ON CONFLICT (document_id) DO NOTHING;", [doc_id, hashlib.sha256(b'bootstrap').hexdigest()])
        con.execute("INSERT INTO relations (relation_id, source_id, target_id, relation_type, document_id, extraction_method, status, created_at, created_by) VALUES (?, 'ent_mikael', 'ent_forteresse', 'WORKS_ON', ?, 'manual', 'documented', ?, 'bootstrap') ON CONFLICT (relation_id) DO UPDATE SET status = 'documented';", [rel_id, doc_id, now - timedelta(days=2)])
        file_id = 'f_repair_spec_01'
        file_hash = hashlib.sha256(b'Contenu conforme procedure reparatoire 2026').hexdigest()
        con.execute("INSERT INTO file_manifest (file_id, title, system_role, storage_provider, external_uri, sha256_hash, version_label, status, verified_by, verified_at) VALUES (?, 'Rapport de correction', 'archives', 'local_fs', 'docs/repair.md', ?, 'v1.0', 'verified', 'mikael', ?) ON CONFLICT (file_id) DO NOTHING;", [file_id, file_hash, now - timedelta(hours=12)])
        d_est = f'dec_est_{uuid.uuid4().hex[:8]}'
        d_rev = f'dec_rev_{uuid.uuid4().hex[:8]}'
        d_reb = f'dec_reb_{uuid.uuid4().hex[:8]}'
        con.execute("INSERT INTO decisions VALUES (?, ?, 'approved', 'Etablissement initial', 'mikael', ?, NULL), (?, ?, 'approved', 'Retrait preventif', 'mikael', ?, NULL), (?, ?, 'approved', 'Approbation rehabilitation', 'mikael', ?, NULL);", [d_est, rel_id, now - timedelta(days=2), d_rev, rel_id, now - timedelta(days=1), d_reb, rel_id, now])
        e1_id = f'evt_e1_{uuid.uuid4().hex[:8]}'
        con.execute("INSERT INTO relation_status_history (status_change_id, relation_id, old_status, new_status, change_kind, reason, changed_at, changed_by, decision_id, caused_by_event_id, reinstates_change_id, correlation_id, exec_id, policy_key, policy_version, policy_hash) VALUES (?, ?, 'candidate', 'documented', 'establishment', 'Initialisation', ?, 'mikael', ?, NULL, NULL, ?, 'exec_1', 'pol_1', 1, 'hash_pol');", [e1_id, rel_id, now - timedelta(days=2), d_est, corr_id])
        e2_id = f'evt_e2_{uuid.uuid4().hex[:8]}'
        con.execute("INSERT INTO relation_status_history (status_change_id, relation_id, old_status, new_status, change_kind, reason, changed_at, changed_by, decision_id, caused_by_event_id, reinstates_change_id, correlation_id, exec_id, policy_key, policy_version, policy_hash) VALUES (?, ?, 'documented', 'withdrawn', 'withdrawal', 'Suspicion incoherence', ?, 'mikael', ?, ?, NULL, ?, 'exec_2', 'pol_1', 1, 'hash_pol');", [e2_id, rel_id, now - timedelta(days=1), d_rev, e1_id, corr_id])
        r1_id = f'rep_r1_{uuid.uuid4().hex[:8]}'
        con.execute("INSERT INTO reparation_actions VALUES (?, ?, ?, 'procedure_correction', 'Audit complet et correction', ?, 'mikael', ?, ?, 'verified', ?);", [r1_id, rel_id, e2_id, now - timedelta(hours=6), d_reb, file_id, corr_id])
        e3_id = f'evt_e3_{uuid.uuid4().hex[:8]}'
        con.execute("INSERT INTO relation_status_history (status_change_id, relation_id, old_status, new_status, change_kind, reason, changed_at, changed_by, decision_id, caused_by_event_id, reinstates_change_id, correlation_id, exec_id, policy_key, policy_version, policy_hash) VALUES (?, ?, 'withdrawn', 'documented', 'reinstatement', 'Retablissement acte', ?, 'mikael', ?, ?, ?, ?, 'exec_3', 'pol_1', 1, 'hash_pol');", [e3_id, rel_id, now, d_reb, r1_id, e2_id, corr_id])
        con.execute('COMMIT;')
        print(f'Cycle injecte: E1={e1_id} E2={e2_id} R1={r1_id} E3={e3_id} corr={corr_id}')
    except Exception:
        con.execute('ROLLBACK;')
        raise
    finally:
        con.close()
    print('\n--- 1. AUDIT DE MEMOIRE DUALE ---')
    dual = run_dual_reading_audit(db_path, rel_id)
    print(f"  Concordance: {dual['concordance_verdict']}  Discontinuites: {dual['discontinuities_count']}  Retrograde: {dual['retrograde_violations_count']}")
    print('\n--- 2. AUDIT DE CAUSALITE GRAPHE ---')
    causal = verify_causal_graph(db_path, rel_id)
    print(f"  Causalite: {causal['causal_verdict']}  Rehabilitations: {causal['reinstatements_analyzed']}  Violations: {causal['violations_count']}")
    if dual['concordance_verdict'] == 'ALIGNED' and causal['causal_verdict'] == 'ALIGNED':
        print('\n[SUCCES] Integrite totale : graphe causal et double lecture alignes.')
        return True
    else:
        print('\n[ECHEC] Invariant rompu.', file=sys.stderr)
        for v in causal.get('violations', []): print(f"  - {v['code']}: {v['detail']}", file=sys.stderr)
        return False

if __name__ == '__main__':
    if os.path.exists(DB_PATH): os.remove(DB_PATH)
    print(f'Creation base : {DB_PATH}')
    con_init = duckdb.connect(DB_PATH)
    apply_schema_and_migrations(con_init)
    con_init.close()
    success = seed_demo_causal_cycle(DB_PATH)
    sys.exit(0 if success else 1)
