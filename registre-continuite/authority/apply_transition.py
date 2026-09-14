# authority/apply_transition.py
import json
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, AwareDatetime

from attest.verify import verify_against_registry
from attest.delegation import check_delegation_chain

MAX_REASON_LEN = 2000
MAX_EVIDENCE_IDS = 50

class ErrorCode(str, Enum):
    RBAC_DENIED = 'rbac_denied'
    EVIDENCE_HASH_MISMATCH = 'evidence_hash_mismatch'
    CAUSAL_PARADOX = 'causal_paradox'
    CAUSAL_TARGET_MISSING = 'causal_target_missing'
    CORRELATION_MISMATCH = 'correlation_mismatch'
    REPAIR_NOT_VERIFIED = 'repair_not_verified'

class GovernanceSecurityError(Exception):
    def __init__(self, code: ErrorCode, message: str):
        self.code = code
        self.message = message
        super().__init__(f'[{code.value}] {message}')

class TransitionRequest(BaseModel):
    decision_id: str = Field(..., min_length=8, max_length=128)
    relation_id: str = Field(..., min_length=1, max_length=128)
    subject_id: str = Field(..., min_length=1, max_length=128)
    old_status: str = Field(..., min_length=1, max_length=32)
    new_status: str = Field(..., min_length=1, max_length=32)
    change_kind: str = Field(..., pattern=r'^(establishment|transition|withdrawal|rejection|dispute|repair|reinstatement)$')
    reviewer_id: str = Field(..., min_length=1, max_length=128)
    reason: str = Field(..., min_length=5, max_length=MAX_REASON_LEN)
    reviewed_at: AwareDatetime
    evidence_ids: List[str] = Field(..., min_length=1, max_length=MAX_EVIDENCE_IDS)
    correlation_id: str = Field(..., min_length=8, max_length=128)
    caused_by_event_id: Optional[str] = Field(None, max_length=128)
    reinstates_change_id: Optional[str] = Field(None, max_length=128)

def has_active_contradiction(con, relation_id: str, now: str) -> bool:
    row = con.execute("SELECT 1 FROM contradictions WHERE relation_id = ? AND status = 'active'", [relation_id]).fetchone()
    return row is not None

def insert_attestation(con, record: dict, verify_result: dict, now: str):
    env = record['signed_envelope']
    att = record['attestation']
    import hashlib
    envelope_json = json.dumps(env, ensure_ascii=False, sort_keys=True)
    envelope_bytes = envelope_json.encode('utf-8')
    envelope_sha = hashlib.sha256(envelope_bytes).hexdigest()
    con.execute("""
        INSERT INTO decision_attestations (attestation_id, decision_id, subject_type, subject_id,
            actor_id, actor_role, key_id, signature_algorithm, canonicalization_scheme, hash_algorithm,
            signed_envelope_jcs, signed_envelope_sha256, signed_payload_hash, signature_hex,
            attestation_method, issued_at,
            cryptographic_verification_at, cryptographic_verification_result,
            authorization_verification_at, authorization_verification_result,
            inserted_at, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [att['attestation_id'], env['decision_id'], env['subject_type'], env['subject_id'],
         env['actor_id'], env['actor_role'], env['key_id'], record['signature_algorithm'],
         record['canonicalization_scheme'], record['hash_algorithm'],
         envelope_bytes, envelope_sha,
         record['signed_payload_hash'], record['signature_hex'],
         att['attestation_method'], env['issued_at'],
         now, verify_result['cryptographic'], now, verify_result['authorization'], now, None])

def apply_status_transition(con, record: dict, now: str, *, check_delegation: bool = True):
    """Orchestre verification + permission + delegation + transition."""
    verify_result = verify_against_registry(con, record, now)
    if verify_result['cryptographic'] != 'valid':
        raise RuntimeError(f"Verification cryptographique echouee : {verify_result}")
    if verify_result['authorization'] not in ('valid', 'valid_with_compromise_warning'):
        raise RuntimeError(f"Autorisation refusee : {verify_result}")
    env = record['signed_envelope']
    payload = env['payload']
    reviewer_id = payload.get('reviewer_id')
    if check_delegation and reviewer_id and reviewer_id != env['actor_id']:
        del_result = check_delegation_chain(con, actor_id=env['actor_id'], reviewer_id=reviewer_id,
            delegated_role=env['actor_role'], relation_id=payload.get('relation_id', '*'),
            transition_kind=payload.get('transition_kind', '*'), now=now)
        if not del_result['authorized']:
            raise RuntimeError(f"Delegation refusee : {del_result['error']}")
    con.execute('BEGIN TRANSACTION')
    try:
        insert_attestation(con, record, verify_result, now)
        perm = con.execute("SELECT requires_attestation, requires_explicit_review, requires_direct_evidence, requires_no_active_contradiction, required_review_kind, governing_policy_key FROM transition_permissions WHERE role_id = ? AND from_status = ? AND to_status = ?", [env['actor_role'], payload['old_status'], payload['new_status']]).fetchone()
        if perm is None: raise RuntimeError('Aucune permission pour cette transition.')
        if perm[0] and record.get('signature_hex') is None: raise RuntimeError('Attestation requise.')
        if perm[3] and has_active_contradiction(con, payload['relation_id'], now): raise RuntimeError('Contradiction active bloque la transition.')
        con.execute("UPDATE relations SET status = ? WHERE relation_id = ? AND status = ?", [payload['new_status'], payload['relation_id'], payload['old_status']])
        con.execute('COMMIT')
    except Exception:
        con.execute('ROLLBACK')
        raise

def execute_transition(con, req: TransitionRequest):
    """Applique une transition avec garde causale pour les reinstatements."""
    received_at = req.reviewed_at
    con.execute('BEGIN TRANSACTION')
    try:
        perm = con.execute("SELECT requires_attestation, requires_explicit_review, requires_direct_evidence, requires_no_active_contradiction, required_review_kind, governing_policy_key FROM transition_permissions WHERE role_id = ? AND from_status = ? AND to_status = ?", [req.reviewer_id, req.old_status, req.new_status]).fetchone()
        if perm is None:
            raise GovernanceSecurityError(ErrorCode.RBAC_DENIED, f'Aucune permission pour {req.reviewer_id}: {req.old_status} -> {req.new_status}')
        if perm[3] and has_active_contradiction(con, req.relation_id, str(received_at)):
            raise GovernanceSecurityError(ErrorCode.RBAC_DENIED, 'Contradiction active bloque la transition.')
        # Garde causale pour les rehabilitations
        if req.change_kind == 'reinstatement':
            if not req.reinstates_change_id or not req.caused_by_event_id:
                raise GovernanceSecurityError(ErrorCode.RBAC_DENIED, "Une rehabilitation exige 'reinstates_change_id' et 'caused_by_event_id'.")
            causal_check = con.execute("""
                SELECT target.changed_at, target.new_status, target.correlation_id,
                       rep.status AS rep_status, fm.status AS file_status
                FROM relation_status_history target
                LEFT JOIN reparation_actions rep ON rep.repairs_event_id = target.status_change_id
                LEFT JOIN file_manifest fm ON rep.evidence_file_id = fm.file_id
                WHERE target.status_change_id = ? AND target.relation_id = ?
                  AND target.change_kind IN ('withdrawal', 'rejection', 'dispute')
            """, [req.reinstates_change_id, req.relation_id]).fetchone()
            if not causal_check:
                raise GovernanceSecurityError(ErrorCode.RBAC_DENIED, f"Revocation cible '{req.reinstates_change_id}' introuvable ou invalide.")
            t_at, t_status, t_corr, rep_st, fm_st = causal_check
            if t_at >= received_at:
                raise GovernanceSecurityError(ErrorCode.CAUSAL_PARADOX, 'Paradoxe temporel : la revocation ciblee est posterieure a la rehabilitation.')
            if t_corr != req.correlation_id:
                raise GovernanceSecurityError(ErrorCode.CORRELATION_MISMATCH, f"Rupture de dossier : correlation_id '{req.correlation_id}' != '{t_corr}'.")
            if rep_st != 'verified' or fm_st != 'verified':
                raise GovernanceSecurityError(ErrorCode.REPAIR_NOT_VERIFIED, f"Reparation non verifiee (reparation: {rep_st}, fichier: {fm_st}).")
        # Mise a jour de la relation
        con.execute("UPDATE relations SET status = ?, reviewed_at = ?, reviewer_id = ? WHERE relation_id = ? AND status = ?", [req.new_status, str(received_at), req.reviewer_id, req.relation_id, req.old_status])
        # Insertion dans l'historique append-only
        event_id = f'evt_{req.relation_id}_{req.change_kind}_{int(received_at.timestamp())}'
        con.execute("""
            INSERT INTO relation_status_history (status_change_id, relation_id, old_status, new_status,
                change_kind, reason, changed_at, changed_by,
                decision_id, caused_by_event_id, correlation_id, reinstates_change_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [event_id, req.relation_id, req.old_status, req.new_status, req.change_kind,
             req.reason, str(received_at), req.reviewer_id, req.decision_id,
             req.caused_by_event_id, req.correlation_id, req.reinstates_change_id])
        con.execute('COMMIT')
        return {'status': 'applied', 'event_id': event_id}
    except GovernanceSecurityError:
        con.execute('ROLLBACK')
        raise
    except Exception:
        con.execute('ROLLBACK')
        raise
