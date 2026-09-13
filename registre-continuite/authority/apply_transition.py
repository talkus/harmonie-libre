# authority/apply_transition.py
import json

from attest.verify import verify_against_registry
from attest.delegation import check_delegation_chain


def has_active_contradiction(con, relation_id: str, now: str) -> bool:
    row = con.execute(
        """
        SELECT 1 FROM contradictions
        WHERE relation_id = ? AND status = 'active'
    """,
        [relation_id],
    ).fetchone()
    return row is not None


def insert_attestation(con, record: dict, verify_result: dict, now: str):
    env = record["signed_envelope"]
    att = record["attestation"]

    # Persistance bit-a-bit de l'enveloppe canonique (archivage probatoire)
    # Le BLOB fige les octets exacts produits par JCS (RFC 8785).
    import hashlib
    envelope_json = json.dumps(env, ensure_ascii=False, sort_keys=True)
    envelope_bytes = envelope_json.encode('utf-8')
    envelope_sha = hashlib.sha256(envelope_bytes).hexdigest()

    con.execute(
        """
        INSERT INTO decision_attestations (
            attestation_id, decision_id,
            subject_type, subject_id,
            actor_id, actor_role,
            key_id, signature_algorithm, canonicalization_scheme, hash_algorithm,
            signed_envelope_jcs, signed_envelope_sha256,
            signed_payload_hash, signature_hex,
            attestation_method, issued_at,
            cryptographic_verification_at, cryptographic_verification_result,
            authorization_verification_at, authorization_verification_result,
            inserted_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            att["attestation_id"], env["decision_id"],
            env["subject_type"], env["subject_id"],
            env["actor_id"], env["actor_role"],
            env["key_id"], record["signature_algorithm"],
            record["canonicalization_scheme"], record["hash_algorithm"],
            envelope_bytes, envelope_sha,
            record["signed_payload_hash"], record["signature_hex"],
            att["attestation_method"], env["issued_at"],
            now, verify_result["cryptographic"],
            now, verify_result["authorization"],
            now, None,
        ],
    )


def apply_status_transition(con, record: dict, now: str, *,
                            check_delegation: bool = True):
    """Orchestre verification + permission + delegation + transition.

    Le seul endroit qui ecrit valid dans authorization_verification_result.

    Etapes :
    1. Verification cryptographique (4 etapes : integrite, cle, crypto, role)
    2. Verification de delegation (si reviewer_id different de actor_id)
    3. Verification de permission (transition_permissions)
    4. Verification de contradiction active
    5. Application de la transition (transaction)
    """
    verify_result = verify_against_registry(con, record, now)

    if verify_result["cryptographic"] != "valid":
        raise RuntimeError(
            f"Verification cryptographique echouee : {verify_result}"
        )
    if verify_result["authorization"] not in ("valid", "valid_with_compromise_warning"):
        raise RuntimeError(
            f"Autorisation refusee : {verify_result}"
        )

    env = record["signed_envelope"]
    payload = env["payload"]

    # Verification de delegation (si l'acteur signe au nom d'un reviewer)
    reviewer_id = payload.get("reviewer_id")
    if check_delegation and reviewer_id and reviewer_id != env["actor_id"]:
        del_result = check_delegation_chain(con,
            actor_id=env["actor_id"],
            reviewer_id=reviewer_id,
            delegated_role=env["actor_role"],
            relation_id=payload.get("relation_id", "*"),
            transition_kind=payload.get("transition_kind", "*"),
            now=now,
        )
        if not del_result["authorized"]:
            raise RuntimeError(
                f"Delegation refusee : {del_result['error"]}"
            )

    con.execute("BEGIN TRANSACTION")
    try:
        insert_attestation(con, record, verify_result, now)

        perm = con.execute(
            """
            SELECT requires_attestation, requires_explicit_review,
                   requires_direct_evidence, requires_no_active_contradiction,
                   required_review_kind, governing_policy_key
            FROM transition_permissions
            WHERE role_id = ? AND from_status = ? AND to_status = ?
        """,
            [env["actor_role"], payload["old_status"], payload["new_status"]],
        ).fetchone()

        if perm is None:
            raise RuntimeError("Aucune permission pour cette transition.")

        if perm[0] and record.get("signature_hex") is None:
            raise RuntimeError("Attestation requise.")

        if perm[3] and has_active_contradiction(con, payload["relation_id"], now):
            raise RuntimeError("Contradiction active bloque la transition.")

        con.execute(
            """
            UPDATE relations
            SET status = ?
            WHERE relation_id = ? AND status = ?
        """,
            [payload["new_status"], payload["relation_id"], payload["old_status"]],
        )

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise
