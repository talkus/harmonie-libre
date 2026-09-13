-- 006_signing_keys.sql
-- Registre de cles de signature + attestations de decision v2
-- Corrige le point le plus grave : la cle publique vient du registre,
-- jamais du payload ou des notes.

CREATE TABLE IF NOT EXISTS actor_signing_keys (
    key_id          TEXT PRIMARY KEY,
    actor_id        TEXT NOT NULL,
    algorithm       TEXT NOT NULL,           -- Ed25519
    public_key_hex  TEXT NOT NULL,           -- 32 octets en hex
    fingerprint_sha256 TEXT NOT NULL,        -- SHA-256 de public_key_hex
    valid_from      TIMESTAMP NOT NULL,
    valid_until     TIMESTAMP,               -- NULL = toujours valide
    status          TEXT NOT NULL,           -- active, rotated, revoked
    registered_by   TEXT NOT NULL,
    registration_attestation_id TEXT,
    revoked_at      TIMESTAMP,
    revoked_by      TEXT,
    revoke_reason   TEXT
);

CREATE INDEX IF NOT EXISTS idx_keys_actor_status
    ON actor_signing_keys (actor_id, status, valid_from, valid_until);

CREATE INDEX IF NOT EXISTS idx_keys_fingerprint
    ON actor_signing_keys (fingerprint_sha256);

-- Attestations de decision v2
-- decision_id UNIQUE => idempotence au niveau schema : un rejeu echoue a l'insertion

DROP TABLE IF EXISTS decision_attestations;

CREATE TABLE decision_attestations (
    attestation_id                  TEXT PRIMARY KEY,
    decision_id                     TEXT NOT NULL UNIQUE,

    subject_type                    TEXT NOT NULL,
    subject_id                      TEXT NOT NULL,

    actor_id                        TEXT NOT NULL,
    actor_role                      TEXT NOT NULL,

    key_id                          TEXT NOT NULL,
    signature_algorithm             TEXT NOT NULL,   -- Ed25519
    canonicalization_scheme         TEXT NOT NULL,   -- RFC8785-JCS
    hash_algorithm                  TEXT NOT NULL,   -- sha256

    signed_envelope_jcs             TEXT NOT NULL,
    signed_payload_hash             TEXT NOT NULL,
    signature_hex                    TEXT NOT NULL,

    attestation_method              TEXT NOT NULL,   -- ed25519_jcs_rfc8785
    issued_at                       TIMESTAMP NOT NULL,

    cryptographic_verification_at   TIMESTAMP,
    cryptographic_verification_result TEXT NOT NULL, -- valid | tampered | unknown_key | ...

    authorization_verification_at   TIMESTAMP,
    authorization_verification_result TEXT NOT NULL, -- valid | role_not_active | ...

    inserted_at                     TIMESTAMP NOT NULL,
    notes                           TEXT,

    FOREIGN KEY (key_id) REFERENCES actor_signing_keys (key_id)
);

-- Roles des acteurs avec validite temporelle
CREATE TABLE IF NOT EXISTS actor_roles (
    actor_id    TEXT NOT NULL,
    role_id     TEXT NOT NULL,     -- lead_auditor, extractor, reviewer, ...
    valid_from  TIMESTAMP NOT NULL,
    valid_until TIMESTAMP,
    PRIMARY KEY (actor_id, role_id, valid_from)
);

-- Permissions de transition par role
CREATE TABLE IF NOT EXISTS transition_permissions (
    role_id                        TEXT NOT NULL,
    from_status                    TEXT NOT NULL,
    to_status                      TEXT NOT NULL,
    requires_attestation           BOOLEAN NOT NULL DEFAULT TRUE,
    requires_explicit_review       BOOLEAN NOT NULL DEFAULT FALSE,
    requires_direct_evidence       BOOLEAN NOT NULL DEFAULT FALSE,
    requires_no_active_contradiction BOOLEAN NOT NULL DEFAULT FALSE,
    required_review_kind            TEXT,     -- human_source_check, technical_test, ...
    governing_policy_key            TEXT,
    PRIMARY KEY (role_id, from_status, to_status)
);
