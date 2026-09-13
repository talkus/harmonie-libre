# attest/keys.py
import hashlib


def register_actor_key(
    con,
    *,
    key_id: str,
    actor_id: str,
    public_key_hex: str,
    valid_from: str,
    registered_by: str,
    registration_attestation_id: str,
    now: str,
):
    """Ceremonie d'enregistrement de cle. Operation de gouvernance.

    La cle publique vient du registrant, pas du payload.
    Refus si la meme cle est deja associee a un autre acteur.
    """
    public_bytes = bytes.fromhex(public_key_hex)
    if len(public_bytes) != 32:
        raise RuntimeError("Cle publique Ed25519 attendue : 32 octets.")

    fingerprint = hashlib.sha256(public_bytes).hexdigest()

    existing = con.execute(
        "SELECT actor_id FROM actor_signing_keys WHERE fingerprint_sha256 = ?",
        [fingerprint],
    ).fetchone()
    if existing and existing[0] != actor_id:
        raise RuntimeError(
            "Cette cle est deja associee a un autre acteur. Refus."
        )

    con.execute(
        """
        INSERT INTO actor_signing_keys (
            key_id, actor_id, algorithm, public_key_hex, fingerprint_sha256,
            valid_from, valid_until, status,
            registered_by, registration_attestation_id,
            revoked_at, revoked_by, revoke_reason
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            key_id,
            actor_id,
            "Ed25519",
            public_key_hex,
            fingerprint,
            valid_from,
            None,
            "active",
            registered_by,
            registration_attestation_id,
            None,
            None,
            None,
        ],
    )
