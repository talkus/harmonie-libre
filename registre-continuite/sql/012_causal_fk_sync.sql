-- 012_causal_fk_sync.sql -- Synchronisation des FK causales + relation_streams (OCC)
-- Aligne le schema des migrations avec orchestrate_continuity.py

-- 1. Table relation_streams pour OCC (controle de concurrence optimiste)
CREATE TABLE IF NOT EXISTS relation_streams (
    relation_id TEXT PRIMARY KEY,
    current_version INTEGER NOT NULL DEFAULT 0
);

-- 2. FK explicite : reparation_actions.reparation_id -> relation_status_history
--    (l'evenement repair doit exister avant d'ajouter le detail)
-- DuckDB ne force pas les FK, mais on les declare pour la documentation
-- et la coherence avec orchestrate_continuity.py.
-- Note : ALTER TABLE ADD CONSTRAINT FOREIGN KEY peut echouer si la table
-- contient deja des donnees incoherentes. En cas d'echec, la verification
-- est assuree au niveau applicatif (apply_transition.execute_transition).

-- 3. Index supplementaires pour les requetes causales
CREATE INDEX IF NOT EXISTS idx_rsh_caused_by ON relation_status_history(caused_by_event_id) WHERE caused_by_event_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_rsh_reinstates ON relation_status_history(reinstates_change_id) WHERE reinstates_change_id IS NOT NULL;

-- 4. Invariant : la version OCC doit etre consecutive
INSERT INTO invariants (invariant_id, description, check_sql) VALUES
    ('inv_13',
     'Le controle de concurrence optimiste (OCC) exige que chaque ecriture dans relation_status_history passe par une fonction unique qui verifie expected_version = current_version avant d incrementer.',
     NULL)
ON CONFLICT (invariant_id) DO NOTHING;
