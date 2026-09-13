-- 007_key_lifecycle.sql
-- Cycle de vie des cles — aligne sur NIST SP 800-57 Part 1 Rev 5
-- 8 phases : generated, registered, active, suspected_compromise, retiring, retired, revoked, destroyed
-- compromised_since : distingue validite historique et acceptation actuelle
--
-- IMPORTANT : DuckDB ne supporte pas les triggers.
-- key_lifecycle_history est immuable par convention d'application :
--   Aucun code ne doit emettre UPDATE ou DELETE contre cette table.
--   L'invariant est verifie par revue de code et par test d'integration.

-- Extension de actor_signing_keys (ALTER si la table existe deja)
ALTER TABLE actor_signing_keys ADD COLUMN IF NOT EXISTS compromised_since TIMESTAMP;
ALTER TABLE actor_signing_keys ADD COLUMN IF NOT EXISTS destroyed_at TIMESTAMP;
ALTER TABLE actor_signing_keys ADD COLUMN IF NOT EXISTS destroyed_by TEXT;
ALTER TABLE actor_signing_keys ADD COLUMN IF NOT EXISTS metadata_json JSON;
ALTER TABLE actor_signing_keys ADD COLUMN IF NOT EXISTS allowed_decision_types JSON;

-- Le statut passe de TEXT a une enum documantee :
-- generated | registered | active | suspected_compromise | retiring | retired | revoked | destroyed
-- (DuckDB : pas d'enum natif ; la contrainte est applicative + CHECK optionnel)

ALTER TABLE actor_signing_keys ADD CONSTRAINT IF NOT EXISTS chk_key_status
    CHECK (status IN (
        'generated', 'registered', 'active', 'suspected_compromise',
        'retiring', 'retired', 'revoked', 'destroyed'
    ));

-- Journal append-only du cycle de vie des cles
CREATE TABLE IF NOT EXISTS key_lifecycle_history (
    event_id          TEXT PRIMARY KEY,
    key_id            TEXT NOT NULL,
    actor_id          TEXT NOT NULL,
    from_status       TEXT,
    to_status          TEXT NOT NULL,
    event_type        TEXT NOT NULL,    -- registration, activation, rotation_start, rotation_complete,
                                        -- compromise_suspected, revoke, retire, destroy
    reason            TEXT,
    compromised_since TIMESTAMP,         -- non-NULL uniquement pour revoke / compromise_suspected
    decision_attestation_id TEXT,        -- lien vers decision_attestations si gouverne
    recorded_by       TEXT NOT NULL,
    recorded_at       TIMESTAMP NOT NULL,

    FOREIGN KEY (key_id) REFERENCES actor_signing_keys (key_id)
);

CREATE INDEX IF NOT EXISTS idx_lifecycle_key
    ON key_lifecycle_history (key_id, recorded_at);
CREATE INDEX IF NOT EXISTS idx_lifecycle_event
    ON key_lifecycle_history (event_type, recorded_at);

-- Vue : cles actives et acceptables a un instant donne
-- Une cle est acceptable pour une attestation emise a T si :
--   status = 'active' ET valid_from <= T ET (valid_until IS NULL OR T <= valid_until)
--   ET (compromised_since IS NULL OR T < compromised_since)
CREATE VIEW IF NOT EXISTS v_keys_acceptable_at AS
SELECT
    k.key_id,
    k.actor_id,
    k.algorithm,
    k.public_key_hex,
    k.fingerprint_sha256,
    k.status,
    k.valid_from,
    k.valid_until,
    k.compromised_since,
    CASE
        WHEN k.status = 'active'
         AND k.valid_from IS NOT NULL
         AND (k.valid_until IS NULL OR k.valid_until >= CURRENT_TIMESTAMP)
         AND (k.compromised_since IS NULL)
        THEN TRUE
        ELSE FALSE
    END AS currently_acceptable,
    CASE
        WHEN k.status IN ('active', 'retired', 'revoked')
         AND k.valid_from IS NOT NULL
         AND (k.compromised_since IS NULL OR k.valid_from < k.compromised_since)
        THEN TRUE
        ELSE FALSE
    END AS historically_valid
FROM actor_signing_keys k;

-- Vue : journal chronologique par cle
CREATE VIEW IF NOT EXISTS v_key_timeline AS
SELECT
    key_id,
    to_status,
    event_type,
    reason,
    recorded_at,
    recorded_by
FROM key_lifecycle_history
ORDER BY key_id, recorded_at;
