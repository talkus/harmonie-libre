# authority/apply_transition.py
import json

from attest.verify import verify_against_registry


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

    con.execute(
        """
        INSERT INTO decision_attestations (
            attestation_id, decision_id,
            subject_type, subject_id,
            actor_id, actor_role,
            key_id, signature_algorithm, canonicalization_scheme, hash_algorithm,
            signed_envelope_jcs, signed_payload_hash, signature_hex,
            attestation_method, issued_at,
            cryptographic_verification_at, cryptographic_verification_result,
            authorization_verification_at, authorization_verification_result,
            inserted_at, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            att["attestation_id"], env["decision_id"],
            env["subject_type"], env["subject_id"],
            env["actor_id"], env["actor_role"],
            env["key_id"], record["signature_algorithm"],
            record["canonicalization_scheme"], record["hash_algorithm"],
            json.dumps(env, ensure_ascii=False),
            record["signed_payload_hash"], record["signature_hex"],
            att["attestation_method"], env["issued_at"],
            now, verify_result["cryptographic"],
            now, verify_result["authorization"],
            now, None,
        ],
    )


def apply_status_transition(con, record: dict, now: str):
    """Orchestre verification + permission + transition en une transaction.

    Le seul endroit qui ecrit 'valid' dans authorization_verification_result.
    """
    verify_result = verify_against_registry(con, record, now)

    if verify_result["cryptographic"] != "valid":
        raise RuntimeError(
            f"Verification cryptographique echouee : {verify_result}"
        )
    if verify_result["authorization"] != "valid":
        raise RuntimeError(
            f"Autorisation refusee : {verify_result}"
        )

    env = record["signed_envelope"]
    payload = env["payload"]

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
