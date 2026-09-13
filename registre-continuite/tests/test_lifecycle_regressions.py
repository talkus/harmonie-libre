# tests/test_lifecycle_regressions.py
# Tests du cycle de vie des cles (NIST SP 800-57).
# Rotation additive, compromission, revocation, destruction.

import pytest
from datetime import datetime, timezone, timedelta
from attest.keys import register_actor_key
from attest.keys_lifecycle import (
    activate_key, rotate_key, complete_rotation,
    suspect_compromise, revoke_key, destroy_key,
)
from attest.key_crypto import generate_keypair


@pytest.fixture
def con():
    import duckdb
    c = duckdb.connect(":memory:")
    c.execute(open("sql/006_signing_keys.sql").read())
    c.execute(open("sql/007_key_lifecycle.sql").read())
    return c


def _register_key(con, key_id="key_a", actor_id="actor_1"):
    private, pub_hex, fp = generate_keypair()
    register_actor_key(
        con,
        key_id=key_id,
        actor_id=actor_id,
        public_key_hex=pub_hex,
        valid_from="2020-01-01T00:00:00Z",
        registered_by="registrar",
        registration_attestation_id="",
        now="2020-01-01T00:00:00Z",
    )
    con.execute(
        "UPDATE actor_signing_keys SET status = 'registered' WHERE key_id = ?",
        [key_id],
    )
    return private, pub_hex


def test_activation(con):
    _register_key(con)
    activate_key(con, key_id="key_a", recorded_by="registrar")
    status = con.execute(
        "SELECT status FROM actor_signing_keys WHERE key_id = 'key_a'"
    ).fetchone()[0]
    assert status == "active"
    events = con.execute(
        "SELECT to_status, event_type FROM key_lifecycle_history WHERE key_id = 'key_a'"
    ).fetchall()
    assert ("active", "activation") in events


def test_rotation_additive(con):
    _register_key(con)
    activate_key(con, key_id="key_a", recorded_by="registrar")

    _, new_pub = generate_keypair()
    rotate_key(
        con,
        old_key_id="key_a",
        new_key_id="key_b",
        actor_id="actor_1",
        public_key_hex=new_pub,
        valid_from="2026-09-13T00:00:00Z",
        registered_by="registrar",
    )

    old_status = con.execute(
        "SELECT status FROM actor_signing_keys WHERE key_id = 'key_a'"
    ).fetchone()[0]
    new_status = con.execute(
        "SELECT status FROM actor_signing_keys WHERE key_id = 'key_b'"
    ).fetchone()[0]
    assert old_status == "retiring"
    assert new_status == "active"


def test_compromised_since(con):
    _register_key(con)
    activate_key(con, key_id="key_a", recorded_by="registrar")

    suspect_compromise(
        con,
        key_id="key_a",
        compromised_since="2026-09-10T00:00:00Z",
        reason="Fuite suspectee",
        recorded_by="security",
    )
    status = con.execute(
        "SELECT status, compromised_since FROM actor_signing_keys WHERE key_id = 'key_a'"
    ).fetchone()
    assert status[0] == "suspected_compromise"
    assert status[1] is not None


def test_revoke_preserves_history(con):
    _register_key(con)
    activate_key(con, key_id="key_a", recorded_by="registrar")

    revoke_key(
        con,
        key_id="key_a",
        reason="Cle perdue",
        revoked_by="security",
        compromised_since="2026-09-12T00:00:00Z",
    )
    status = con.execute(
        "SELECT status, revoked_at, revoke_reason FROM actor_signing_keys WHERE key_id = 'key_a'"
    ).fetchone()
    assert status[0] == "revoked"
    assert status[1] is not None
    assert status[2] == "Cle perdue"

    # L'historique contient l'evenement de revocation
    events = con.execute(
        "SELECT event_type FROM key_lifecycle_history WHERE key_id = 'key_a' AND event_type = 'revoke'"
    ).fetchall()
    assert len(events) == 1


def test_destroy_requires_retired_or_revoked(con):
    _register_key(con)
    activate_key(con, key_id="key_a", recorded_by="registrar")

    # Destruction refusee sur une cle active
    with pytest.raises(RuntimeError, match="retired.*revoked"):
        destroy_key(
            con, key_id="key_a", reason="Test",
            destroyed_by="security",
        )

    revoke_key(con, key_id="key_a", reason="Revoke pour test", revoked_by="security")
    destroy_key(con, key_id="key_a", reason="Destruction finale", destroyed_by="security")
    status = con.execute(
        "SELECT status FROM actor_signing_keys WHERE key_id = 'key_a'"
    ).fetchone()[0]
    assert status == "destroyed"


def test_complete_rotation_requires_expiry(con):
    _register_key(con)
    activate_key(con, key_id="key_a", recorded_by="registrar")
    con.execute(
        "UPDATE actor_signing_keys SET valid_until = '2030-01-01T00:00:00Z' WHERE key_id = 'key_a'"
    )

    _, new_pub = generate_keypair()
    rotate_key(
        con,
        old_key_id="key_a",
        new_key_id="key_b",
        actor_id="actor_1",
        public_key_hex=new_pub,
        valid_from="2026-09-13T00:00:00Z",
        registered_by="registrar",
    )

    # La cle n'a pas expire — la fin de rotation doit echouer
    with pytest.raises(RuntimeError, match="pas encore expire"):
        complete_rotation(con, old_key_id="key_a", recorded_by="registrar")

    # Forcer l'expiration
    con.execute(
        "UPDATE actor_signing_keys SET valid_until = '2020-01-01T00:00:00Z' WHERE key_id = 'key_a'"
    )
    complete_rotation(con, old_key_id="key_a", recorded_by="registrar")
    status = con.execute(
        "SELECT status FROM actor_signing_keys WHERE key_id = 'key_a'"
    ).fetchone()[0]
    assert status == "retired"
