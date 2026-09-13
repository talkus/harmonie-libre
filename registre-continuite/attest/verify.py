# attest/verify.py
import hashlib
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def _canonicalize(obj) -> bytes:
    import rfc8785
    return rfc8785.dumps(obj)


def verify_against_registry(con, record: dict, now_iso: str) -> dict:
    """Verification en 4 etapes contre le registre de confiance.

    1. Integrite du fichier (hash recompose)
    2. Resolution de la cle dans actor_signing_keys
    3. Verification cryptographique (Ed25519)
    4. Autorisation : role actif a la date d'emission (issued_at)
    """
    envelope = record["signed_envelope"]
    signature_hex = record["signature_hex"]

    # --- 1. Integrite du fichier ---
    canonical = _canonicalize(envelope)
    recomputed_hash = hashlib.sha256(canonical).hexdigest()
    if recomputed_hash != record["signed_payload_hash"]:
        return {"cryptographic": "tampered", "authorization": "rejected"}

    # --- 2. Resolution de la cle dans le registre ---
    key_id = envelope["key_id"]
    key_row = con.execute(
        """
        SELECT actor_id, algorithm, public_key_hex, fingerprint_sha256,
               valid_from, valid_until, status
        FROM actor_signing_keys
        WHERE key_id = ?
    """,
        [key_id],
    ).fetchone()

    if key_row is None:
        return {"cryptographic": "unknown_key", "authorization": "rejected"}

    (key_actor, algo, pub_hex, fp, valid_from, valid_until, status) = key_row

    if algo != "Ed25519":
        return {"cryptographic": "unsupported_algorithm", "authorization": "rejected"}
    if status != "active":
        return {"cryptographic": "revoked_key", "authorization": "rejected"}
    if key_actor != envelope["actor_id"]:
        return {"cryptographic": "key_actor_mismatch", "authorization": "rejected"}
    if valid_from > envelope["issued_at"]:
        return {"cryptographic": "key_not_yet_valid", "authorization": "rejected"}
    if valid_until is not None and envelope["issued_at"] > valid_until:
        return {"cryptographic": "key_expired", "authorization": "rejected"}

    # Empreinte annoncee vs empreinte reelle
    pub_bytes = bytes.fromhex(pub_hex)
    if hashlib.sha256(pub_bytes).hexdigest() != fp:
        return {"cryptographic": "fingerprint_mismatch", "authorization": "rejected"}

    # --- 3. Verification cryptographique ---
    try:
        Ed25519PublicKey.from_public_bytes(pub_bytes).verify(
            bytes.fromhex(signature_hex), canonical
        )
    except Exception:
        return {"cryptographic": "invalid_signature", "authorization": "rejected"}

    # --- 4. Autorisation (role actif a la date d'emission) ---
    role_row = con.execute(
        """
        SELECT 1 FROM actor_roles
        WHERE actor_id = ? AND role_id = ?
          AND valid_from <= ?
          AND (valid_until IS NULL OR valid_until >= ?)
    """,
        [envelope["actor_id"], envelope["actor_role"],
         envelope["issued_at"], envelope["issued_at"]],
    ).fetchone()

    if role_row is None:
        return {"cryptographic": "valid", "authorization": "role_not_active_at_issued_at"}

    return {"cryptographic": "valid", "authorization": "valid"}
