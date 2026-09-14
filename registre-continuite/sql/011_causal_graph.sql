-- ═══════════════════════════════════════════════════════════════════
-- MIGRATION 011 — GRAPHE CAUSAL APPEND-ONLY
-- Relation_status_history + reparation_actions
-- Principe : une restauration ne modifie jamais la revocation
-- qu'elle traite. Elle cree un nouvel evenement, lie a cette
-- revocation, autorise par une nouvelle decision et soutenu
-- par des preuves verifiables.
-- ═══════════════════════════════════════════════════════════════════

-- ───────────────────────────────────────────────────────────────
-- 1.ALTER relation_status_history : ajout des colonnes causales
-- ───────────────────────────────────────────────────────────────

-- Surchage de la table : on recree avec les colonnes supplementaires
-- si la table existe deja, on utilise ALTER TABLE ADD COLUMN

ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS
    status_change_id TEXT;

ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS
    change_kind TEXT;

ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS
    caused_by_event_id TEXT;

ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS
    correlation_id TEXT;

ALTER TABLE relation_status_history ADD COLUMN IF NOT EXISTS
    reinstates_change_id TEXT;

-- Si la table n'existe pas encore, on la cree complete
CREATE TABLE IF NOT EXISTS relation_status_history (
    status_change_id TEXT PRIMARY KEY,
    relation_id TEXT NOT NULL,
    old_status TEXT,
    new_status TEXT NOT NULL,
    change_kind TEXT NOT NULL CHECK (
        change_kind IN (
            'establishment',
            'transition',
            'withdrawal',
            'rejection',
            'dispute',
            'repair',
            'reinstatement'
        )
    ),
    reason TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL,
    changed_by TEXT NOT NULL,
    decision_id TEXT NOT NULL,
    caused_by_event_id TEXT,
    correlation_id TEXT NOT NULL,
    reinstates_change_id TEXT,

    FOREIGN KEY (decision_id)
        REFERENCES decisions(decision_id),
    FOREIGN KEY (caused_by_event_id)
        REFERENCES relation_status_history(status_change_id),
    FOREIGN KEY (reinstates_change_id)
        REFERENCES relation_status_history(status_change_id),

    CONSTRAINT chk_no_self_causation CHECK (
        caused_by_event_id IS NULL
        OR caused_by_event_id <> status_change_id
    ),
    CONSTRAINT chk_no_self_reinstatement CHECK (
        reinstates_change_id IS NULL
        OR reinstates_change_id <> status_change_id
    ),
    CONSTRAINT chk_reinstatement_requires_target CHECK (
        (
            change_kind = 'reinstatement'
            AND reinstates_change_id IS NOT NULL
            AND caused_by_event_id IS NOT NULL
            AND new_status IN ('documented', 'verified')
        )
        OR (
            change_kind <> 'reinstatement'
            AND reinstates_change_id IS NULL
        )
    ),
    CONSTRAINT chk_decision_required CHECK (
        new_status NOT IN (
            'documented',
            'verified',
            'withdrawn',
            'rejected'
        )
        OR decision_id IS NOT NULL
    )
);

-- Index pour le graphe causal
CREATE INDEX IF NOT EXISTS idx_rsh_correlation
    ON relation_status_history(correlation_id);

CREATE INDEX IF NOT EXISTS idx_rsh_reinstates
    ON relation_status_history(reinstates_change_id)
    WHERE reinstates_change_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_rsh_caused_by
    ON relation_status_history(caused_by_event_id)
    WHERE caused_by_event_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_rsh_relation_changed
    ON relation_status_history(relation_id, changed_at);

-- ───────────────────────────────────────────────────────────────
-- 2. TABLE reparation_actions
-- ───────────────────────────────────────────────────────────────

CREATE TABLE IF NOT EXISTS reparation_actions (
    reparation_id TEXT PRIMARY KEY,
    relation_id TEXT NOT NULL,
    repairs_event_id TEXT NOT NULL,
    repair_kind TEXT NOT NULL CHECK (
        repair_kind IN (
            'fact_correction',
            'evidence_replacement',
            'procedure_correction',
            'acknowledgment',
            'withdrawal_of_error',
            'safeguard_added',
            'reinstatement_basis'
        )
    ),
    description TEXT NOT NULL,
    performed_at TIMESTAMPTZ NOT NULL,
    performed_by TEXT NOT NULL,
    decision_id TEXT,
    evidence_file_id TEXT NOT NULL,
    status TEXT NOT NULL CHECK (
        status IN (
            'proposed',
            'completed',
            'verified',
            'rejected'
        )
    ),
    correlation_id TEXT NOT NULL,

    FOREIGN KEY (relation_id)
        REFERENCES relations(relation_id),
    FOREIGN KEY (repairs_event_id)
        REFERENCES relation_status_history(status_change_id),
    FOREIGN KEY (decision_id)
        REFERENCES decisions(decision_id),
    FOREIGN KEY (evidence_file_id)
        REFERENCES file_manifest(file_id)
);

CREATE INDEX IF NOT EXISTS idx_rep_repairs_event
    ON reparation_actions(repairs_event_id);

CREATE INDEX IF NOT EXISTS idx_rep_correlation
    ON reparation_actions(correlation_id);

CREATE INDEX IF NOT EXISTS idx_rep_status
    ON reparation_actions(status);

-- ───────────────────────────────────────────────────────────────
-- 3. Invariant 12 : trace causale
-- ───────────────────────────────────────────────────────────────

INSERT INTO invariants (invariant_id, description, check_sql) VALUES (
    'inv_12',
    'Toute restauration (reinstatement) declare explicitement quelle revocation elle traite (reinstates_change_id), quelle decision l autorise, et quelles preuves la soutiennent. Une restauration ne modifie jamais l evenement qu elle restaure.',
    'SELECT 1 WHERE NOT EXISTS (SELECT 1 FROM relation_status_history WHERE change_kind = ''reinstatement'' AND reinstates_change_id IS NULL)'
) ON CONFLICT (invariant_id) DO NOTHING;
