-- 008_chain_integrity.sql
-- Chaine de hachage sur key_lifecycle_history + ancrage externe du tip.
--
-- Correctifs de la revue technique :
-- 1. Course critique : UNIQUE(previous_event_hash) + chain_lock (verrou applicatif)
-- 2. Normalisation du timestamp : format fige des deux cotes
-- 3. Propagation en cascade : audit utilise recalculated_curr_hash
-- 4. Round-trip payload : check de coherence a l'insert
-- 5. Ancrage externe du tip : table tip_anchors + validation audit
-- 6. Validation format hash : CHECK ^[0-9a-f]{64}$
--    Exception handling : elargi dans le code Python
--    UNIQUE event_id : deja PRIMARY KEY, renforce
--    KeyError journal vide : corrige dans audit_chain.py

-- Colonnes de chaine sur key_lifecycle_history
ALTER TABLE key_lifecycle_history ADD COLUMN IF NOT EXISTS current_event_hash TEXT;
ALTER TABLE key_lifecycle_history ADD COLUMN IF NOT EXISTS previous_event_hash TEXT;

-- Un bloc ne peut avoir qu'un seul successeur (anti-fourche)
-- NULL autorise uniquement pour le bloc de genese
CREATE UNIQUE INDEX IF NOT EXISTS uq_previous_event_hash
    ON key_lifecycle_history (previous_event_hash)
    WHERE previous_event_hash IS NOT NULL;

-- Validation du format des hashes (64 hex minuscules)
ALTER TABLE key_lifecycle_history ADD CONSTRAINT IF NOT EXISTS chk_current_hash_format
    CHECK (current_event_hash IS NULL OR current_event_hash ~ '^[0-9a-f]{64}$');
ALTER TABLE key_lifecycle_history ADD CONSTRAINT IF NOT EXISTS chk_previous_hash_format
    CHECK (previous_event_hash IS NULL OR previous_event_hash ~ '^[0-9a-f]{64}$');

-- Verrou applicatif mono-ligne pour serialiser les appends
-- DuckDB ne supporte pas FOR UPDATE sur tous les backends.
-- On acquire un verrou exclusif via cette table.
CREATE TABLE IF NOT EXISTS chain_lock (
    lock_id      INTEGER PRIMARY KEY DEFAULT 1,
    holder       TEXT,
    acquired_at  TIMESTAMP,
    CHECK (lock_id = 1)
);

INSERT INTO chain_lock (lock_id, holder, acquired_at)
SELECT 1, NULL, NULL
WHERE NOT EXISTS (SELECT 1 FROM chain_lock WHERE lock_id = 1);

-- Ancrage externe du tip
-- Chaque publication enregistre le tip_hash observe dans un journal
-- append-only. L'audit verifie que le tip observe est un descendant
-- du dernier tip publie (anti-troncature).
CREATE TABLE IF NOT EXISTS tip_anchors (
    anchor_id      TEXT PRIMARY KEY,
    tip_hash       TEXT NOT NULL,
    tip_event_id   TEXT NOT NULL,
    published_by   TEXT NOT NULL,
    published_at   TIMESTAMP NOT NULL,
    source         TEXT NOT NULL,    -- 's3_object_lock', 'public_chain', 'secondary_duckdb', 'manual'
    external_ref   TEXT,              -- URL ou identifiant externe
    notes          TEXT
);

CREATE INDEX IF NOT EXISTS idx_tip_anchors_published
    ON tip_anchors (published_at DESC);

-- Vue : dernier tip ancre publie
CREATE VIEW IF NOT EXISTS v_latest_tip_anchor AS
SELECT tip_hash, tip_event_id, published_at, source, external_ref
FROM tip_anchors
ORDER BY published_at DESC
LIMIT 1;
