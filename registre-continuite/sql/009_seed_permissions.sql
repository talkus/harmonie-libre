-- 009_seed_permissions.sql
-- Donnees de seed pour transition_permissions
-- Definit qui peut faire quelle transition, avec quelles contraintes.

-- lead_auditor : peut promouvoir candidate -> documented
INSERT INTO transition_permissions VALUES
('lead_auditor', 'candidate', 'documented', TRUE, TRUE, TRUE, FALSE, 'human_source_check', 'transition_v1');

-- lead_auditor : peut corriger documented -> corrected
INSERT INTO transition_permissions VALUES
('lead_auditor', 'documented', 'corrected', TRUE, TRUE, FALSE, TRUE, 'human_source_check', 'transition_v1');

-- lead_auditor : peut rejeter candidate -> rejected
INSERT INTO transition_permissions VALUES
('lead_auditor', 'candidate', 'rejected', TRUE, TRUE, TRUE, FALSE, 'human_source_check', 'transition_v1');

-- lead_auditor : peut superseder documented -> superseded
INSERT INTO transition_permissions VALUES
('lead_auditor', 'documented', 'superseded', TRUE, TRUE, FALSE, FALSE, NULL, 'transition_v1');

-- reviewer : peut promouvoir candidate -> documented avec revue explicite
INSERT INTO transition_permissions VALUES
('reviewer', 'candidate', 'documented', TRUE, TRUE, FALSE, FALSE, 'technical_test', 'transition_v1');

-- reviewer : peut corriger documented -> corrected
INSERT INTO transition_permissions VALUES
('reviewer', 'documented', 'corrected', TRUE, TRUE, FALSE, TRUE, 'human_source_check', 'transition_v1');

-- extractor : NE PEUT PAS DECIDER (Invariant 11)
-- Aucune ligne pour extractor -> apply_status_transition refusera
