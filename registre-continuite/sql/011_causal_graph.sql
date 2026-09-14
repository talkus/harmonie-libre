-- 011_causal_graph.sql -- Graphe causal append-only (v2)
-- Relation_status_history + reparation_actions + decisions + file_manifest
-- Principe : une restauration ne modifie jamais la revocation qu'elle traite.

-- 1. TABLES DE SUPPORT
CREATE TABLE IF NOT EXISTS decisions (
    decision_id TEXT PRIMARY KEY,
    subject_id TEXT NOT NULL,
    outcome TEXT NOT NULL CHECK (outcome IN ('approved', 'rejected', 'pending')),
    reasoning TEXT,
    decided_by TEXT NOT NULL,
    decided_at TIMESTAMPTZ NOT NULL,
    decision_attestation_id TEXT
);

CREATE TABLE IF NOT EXISTS file_manifest (
    file_id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    system_role TEXT,
    storage_provider TEXT,
    external_uri TEXT,
    sha256_hash TEXT NOT NULL,
    version_label TEXT,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'verified', 'rejected', 'archived')),
    verified_by TEXT,
    verified_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS invariants (
    invariant_id TEXT PRIMARY KEY,
    description TEXT NOT NULL,
    check_sql TEXT
);

-- 2. ALTER relation_status_history : 8 colonnes causales
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS caused_by_event_id TEXT;
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS correlation_id TEXT;
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS reinstates_change_id TEXT;
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS decision_id TEXT;
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS exec_id TEXT;
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS policy_key TEXT;
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS policy_version INTEGER;
ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS policy_hash TEXT;

-- 3. CONTRAINTES CHECK
ALTER TABLE relation_status_history ADD CONSTRAINT chk_no_self_causation CHECK (caused_by_event_id IS NULL OR caused_by_event_id <> status_change_id);
ALTER TABLE relation_status_history ADD CONSTRAINT chk_no_self_reinstatement CHECK (reinstates_change_id IS NULL OR reinstates_change_id <> status_change_id);
ALTER TABLE relation_status_history ADD CONSTRAINT chk_reinstatement_requires_target CHECK ((change_kind = 'reinstatement' AND reinstates_change_id IS NOT NULL AND caused_by_event_id IS NOT NULL AND new_status IN ('documented', 'verified')) OR (change_kind <> 'reinstatement' AND reinstates_change_id IS NULL));
ALTER TABLE relation_status_history ADD CONSTRAINT chk_decision_required CHECK (new_status NOT IN ('documented', 'verified', 'withdrawn', 'rejected') OR decision_id IS NOT NULL);

-- Index
CREATE INDEX IF NOT EXISTS idx_rsh_correlation ON relation_status_history(correlation_id);
CREATE INDEX IF NOT EXISTS idx_rsh_reinstates ON relation_status_history(reinstates_change_id) WHERE reinstates_change_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rsh_caused_by ON relation_status_history(caused_by_event_id) WHERE caused_by_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rsh_relation_changed ON relation_status_history(relation_id, changed_at);

-- 4. TABLE reparation_actions
CREATE TABLE IF NOT EXISTS reparation_actions (
    reparation_id TEXT PRIMARY KEY,
    relation_id TEXT NOT NULL,
    repairs_event_id TEXT NOT NULL,
    repair_kind TEXT NOT NULL CHECK (repair_kind IN ('fact_correction', 'evidence_replacement', 'procedure_correction', 'acknowledgment', 'withdrawal_of_error', 'safeguard_added', 'reinstatement_basis')),
    description TEXT NOT NULL,
    performed_at TIMESTAMPTZ NOT NULL,
    performed_by TEXT NOT NULL,
    decision_id TEXT,
    evidence_file_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('proposed', 'completed', 'verified', 'rejected')),
    correlation_id TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rep_repairs_event ON reparation_actions(repairs_event_id);
CREATE INDEX IF NOT EXISTS idx_rep_correlation ON reparation_actions(correlation_id);
CREATE INDEX IF NOT EXISTS idx_rep_status ON reparation_actions(status);

-- 5. Invariant 12
INSERT INTO invariants (invariant_id, description, check_sql) VALUES ('inv_12', 'Toute restauration (reinstatement) declare explicitement quelle revocation elle traite (reinstates_change_id), quelle decision l autorise, et quelles preuves la soutiennent.', 'SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM relation_status_history WHERE change_kind = ''reinstatement'' AND reinstates_change_id IS NULL)') ON CONFLICT (invariant_id) DO NOTHING;
