# attest/envelope.py
import hashlib
import uuid
from datetime import datetime, timezone

PROTOCOL = "continuite-attestation-v1"
CANONICALIZATION_SCHEME = "RFC8785-JCS"
HASH_ALGORITHM = "sha256"
SIGNATURE_ALGORITHM = "Ed25519"


def _canonicalize(obj) -> bytes:
    try:
        import rfc8785
    except ImportError as exc:
        raise RuntimeError(
            "rfc8785 obligatoire pour toute enveloppe signee."
        ) from exc
    return rfc8785.dumps(obj)


def build_envelope(
    *,
    key_id: str,
    actor_id: str,
    actor_role: str,
    decision_id: str,
    decision_type: str,
    subject_type: str,
    subject_id: str,
    payload: dict,
    policy_versions: dict,
    issued_at: str | None = None,
    attestation_id: str | None = None,
) -> dict:
    return {
        "protocol": PROTOCOL,
        "attestation_id": attestation_id or f"att_{uuid.uuid4().hex}",
        "key_id": key_id,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "decision_id": decision_id,
        "decision_type": decision_type,
        "subject_type": subject_type,
        "subject_id": subject_id,
        "issued_at": issued_at or datetime.now(timezone.utc).isoformat(),
        "payload": payload,
        "policy_versions": policy_versions,
    }


def sign_envelope(private_key, envelope: dict) -> tuple[bytes, str, str]:
    canonical = _canonicalize(envelope)
    digest = hashlib.sha256(canonical).hexdigest()
    signature_hex = private_key.sign(canonical).hex()
    return canonical, digest, signature_hex
