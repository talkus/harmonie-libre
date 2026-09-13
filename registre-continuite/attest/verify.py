# attest/verify.py
import hashlib
from datetime import datetime, timezone

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


def _canonicalize(obj) -> bytes:
    import rfc8785
    return rfc8785.dumps(obj)


def _parse_ts(ts):
    """Tolerant ISO-8601 / datetime parser for comparison."""
    if isinstance(ts, datetime):
        return ts
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def verify_against_registry(con, record: dict, now_iso: str) -> dict:
    """Verification en 4 etapes contre le registre de confiance.

    1. Integrite du fichier (hash recompose)
    2. Resolution de la cle dans actor_signing_keys
    3. Verification cryptographique (Ed25519)
    4. Autorisation : role actif a la date d'emission (issued_at)

    Gestion du compromised_since :
    - Une cle compromise ne peut plus autoriser de nouvelles decisions.
    - Une signature emise AVANT compromised_since reste historiquement valide.
    - Une signature emise APRES compromised_since est rejetee.
    """
    envelope = record["signed_envelope"]
    signature_hex = record["signature_hex"]
    issued_at = _parse_ts(envelope["issued_at"])

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
               valid_from, valid_until, status, compromised_since
        FROM actor_signing_keys
        WHERE key_id = ?
    """,
        [key_id],
    ).fetchone()

    if key_row is None:
        return {"cryptographic": "unknown_key", "authorization": "rejected"}

    (key_actor, algo, pub_hex, fp,
     valid_from, valid_until, status, compromised_since) = key_row

    valid_from_dt = _parse_ts(valid_from)
    valid_until_dt = _parse_ts(valid_until) if valid_until else None
    compromised_dt = _parse_ts(compromised_since) if compromised_since else None

    if algo != "Ed25519":
        return {"cryptographic": "unsupported_algorithm", "authorization": "rejected"}

    if status == "destroyed":
        return {"cryptographic": "key_destroyed", "authorization": "rejected"}

    if status == "revoked":
        # Une cle revoquee peut encore verifier des signatures historiques
        # si issued_at < compromised_since.
        if compromised_dt and issued_at < compromised_dt:
            pass  # Historiquement valide — continuer la verification
        else:
            return {"cryptographic": "revoked_key", "authorization": "rejected"}

    if status == "suspected_compromise":
        if compromised_dt and issued_at >= compromised_dt:
            return {"cryptographic": "compromised_key", "authorization": "rejected"}
        # Si issued_at < compromised_since, on continue mais on signale le risque
        # La verification cryptographique peut encore reussir.

    if status not in ("active", "retiring", "retired", "revoked", "suspected_compromise"):
        return {"cryptographic": f"key_status_{status}", "authorization": "rejected"}

    if key_actor != envelope["actor_id"]:
        return {"cryptographic": "key_actor_mismatch", "authorization": "rejected"}

    if valid_from_dt > issued_at:
        return {"cryptographic": "key_not_yet_valid", "authorization": "rejected"}

    if valid_until_dt and issued_at > valid_until_dt:
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

    # Verifier que le type de decision est autorise pour cette cle
    allowed = con.execute(
        "SELECT allowed_decision_types FROM actor_signing_keys WHERE key_id = ?",
        [key_id],
    ).fetchone()

    if allowed and allowed[0]:
        import json
        decision_types = json.loads(allowed[0])
        decision_type = envelope.get("decision_type")
        if decision_types and decision_type not in decision_types:
            return {"cryptographic": "valid", "authorization": "decision_type_not_allowed"}

    # Avertissement si la cle est suspectee mais signature historiquement valide
    if status == "suspected_compromise" and compromised_dt and issued_at < compromised_dt:
        return {
            "cryptographic": "valid",
            "authorization": "valid_with_compromise_warning",
            "warning": f"Cle suspectee de compromission depuis {compromised_since}. "
                       f"Signature emise avant la compromission — historiquement valide.",
        }

    return {"cryptographic": "valid", "authorization": "valid"}
