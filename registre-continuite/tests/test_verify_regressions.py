# tests/test_verify_regressions.py
# 6 tests de non-regression pour verify_against_registry.
# Chacun doit etre rejete. Aucun ne doit passer.

import hashlib
import json
from datetime import datetime, timezone

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from attest.envelope import build_envelope, sign_envelope
from attest.verify import verify_against_registry


def _make_key(con, key_id="key_test", actor_id="actor_1", status="active",
              valid_from=None, actor_override=None):
    private = Ed25519PrivateKey.generate()
    pub_bytes = private.public_key().public_bytes(
        raw=True, encoding=__import__("cryptography").hazmat.primitives.serialization.Encoding.Raw
    )
    pub_hex = pub_bytes.hex()
    fp = hashlib.sha256(pub_bytes).hexdigest()
    con.execute(
        """
        INSERT INTO actor_signing_keys VALUES
        (?, ?, 'Ed25519', ?, ?, ?, NULL, ?, 'registrar', NULL, NULL, NULL, NULL)
        """,
        [key_id, actor_override or actor_id, pub_hex, fp,
         valid_from or "2020-01-01T00:00:00Z", status],
    )
    con.execute(
        "INSERT INTO actor_roles VALUES (?, 'lead_auditor', '2020-01-01T00:00:00Z', NULL)",
        [actor_override or actor_id],
    )
    return private, pub_hex


def _make_record(private_key, envelope_overrides=None):
    envelope = build_envelope(
        key_id="key_test",
        actor_id="actor_1",
        actor_role="lead_auditor",
        decision_id="dec_test",
        decision_type="status_transition",
        subject_type="relation",
        subject_id="rel_test",
        payload={"relation_id": "rel_test", "old_status": "candidate", "new_status": "documented", "reason": "test"},
        policy_versions={"transition": "v1"},
    )
    if envelope_overrides:
        envelope.update(envelope_overrides)

    canonical, digest, sig_hex = sign_envelope(private_key, envelope)
    return {
        "protocol": envelope["protocol"],
        "attestation": {
            "attestation_id": envelope["attestation_id"],
            "key_id": envelope["key_id"],
            "actor_id": envelope["actor_id"],
            "actor_role": envelope["actor_role"],
            "attestation_method": "ed25519_jcs_rfc8785",
            "issued_at": envelope["issued_at"],
        },
        "signed_envelope": envelope,
        "signed_payload_hash": digest,
        "signature_hex": sig_hex,
        "signature_algorithm": "Ed25519",
        "canonicalization_scheme": "RFC8785-JCS",
        "hash_algorithm": "sha256",
    }


@pytest.fixture
def con():
    import duckdb
    c = duckdb.connect(":memory:")
    c.execute(open("sql/006_signing_keys.sql").read())
    return c


def test_unknown_key(con):
    private, _ = _make_key(con, key_id="key_other")
    record = _make_record(private, {"key_id": "key_nonexistent"})
    result = verify_against_registry(con, record, "2026-09-13T00:00:00Z")
    assert result["cryptographic"] == "unknown_key"


def test_revoked_key(con):
    private, _ = _make_key(con, status="revoked")
    record = _make_record(private)
    result = verify_against_registry(con, record, "2026-09-13T00:00:00Z")
    assert result["cryptographic"] == "revoked_key"


def test_actor_mismatch(con):
    private, _ = _make_key(con, actor_id="actor_1")
    record = _make_record(private, {"actor_id": "actor_impostor"})
    result = verify_against_registry(con, record, "2026-09-13T00:00:00Z")
    assert result["cryptographic"] == "key_actor_mismatch"


def test_fingerprint_mismatch(con):
    private, _ = _make_key(con)
    record = _make_record(private)
    # Corrompre l'empreinte dans le registre
    con.execute(
        "UPDATE actor_signing_keys SET fingerprint_sha256 = 'deadbeef' WHERE key_id = 'key_test'"
    )
    result = verify_against_registry(con, record, "2026-09-13T00:00:00Z")
    assert result["cryptographic"] == "fingerprint_mismatch"


def test_modified_signature(con):
    private, _ = _make_key(con)
    record = _make_record(private)
    # Modifier un octet de la signature
    sig = bytes.fromhex(record["signature_hex"])
    sig = bytearray(sig)
    sig[0] ^= 0x01
    record["signature_hex"] = sig.hex()
    result = verify_against_registry(con, record, "2026-09-13T00:00:00Z")
    assert result["cryptographic"] == "invalid_signature"


def test_key_not_yet_valid(con):
    private, _ = _make_key(con, valid_from="2027-01-01T00:00:00Z")
    record = _make_record(private)
    result = verify_against_registry(con, record, "2026-09-13T00:00:00Z")
    assert result["cryptographic"] == "key_not_yet_valid"
