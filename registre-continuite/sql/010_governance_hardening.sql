-- 010_governance_hardening.sql
-- Gouvernance : delegations + archivage probatoire des enveloppes

-- Table des delegations de role
CREATE TABLE IF NOT EXISTS actor_delegations (
    delegation_id          TEXT PRIMARY KEY,
    grantor_id            TEXT NOT NULL,    -- celui qui delegue son role
    grantee_id            TEXT NOT NULL,    -- celui qui recoit la delegation
    delegated_role        TEXT NOT NULL,    -- lead_auditor, reviewer, ...
    scope_relation_id    TEXT,              -- relation specifique, ou '*' pour global
    scope_transition_kind TEXT,              -- transition specifique, ou '*' pour tout
    valid_from            TIMESTAMPTZ NOT NULL,
    valid_until           TIMESTAMPTZ,
    revoked               BOOLEAN NOT NULL DEFAULT FALSE,
    revoked_at            TIMESTAMPTZ,
    revoked_by             TEXT,
    revoke_reason         TEXT,
    delegated_by           TEXT NOT NULL,
    delegation_attestation_id TEXT,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_deleg_grantee
    ON actor_delegations (grantee_id, revoked, valid_from, valid_until);
CREATE INDEX IF NOT EXISTS idx_deleg_grantor
    ON actor_delegations (grantor_id, revoked);
CREATE INDEX IF NOT EXISTS idx_deleg_scope
    ON actor_delegations (scope_relation_id, scope_transition_kind);

-- Archivage probatoire : persistance bit-à-bit de l'enveloppe canonique
-- L'auditabilite long terme ne depend d'aucun analyseur SQL ni convertisseur
-- de fuseau horaire. Le BLOB fige les octets exacts produits par JCS (RFC 8785).
ALTER TABLE decision_attestations ADD COLUMN IF NOT EXISTS signed_envelope_jcs BLOB;
ALTER TABLE decision_attestations ADD COLUMN IF NOT EXISTS signed_envelope_sha256 TEXT;

CREATE INDEX IF NOT EXISTS idx_attest_env_sha
    ON decision_attestations (signed_envelope_sha256);
