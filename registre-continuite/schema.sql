-- Registre de continuite gouverne — Schéma DuckDB complet
-- Validé contre l'Architecture de clôture (11 frontières)
-- 11 workflows · 11 invariants · 3 niveaux de sortie
-- 
-- Règle de continuité :
-- Les originaux ne sont pas réécrits.
-- Les inférences ne deviennent pas des faits par répétition.
-- Les corrections ne sont pas des effacements.
-- Les contradictions deviennent des objets de travail.
-- Les décisions ont un auteur, une raison et une date.
-- Les exports sont des instantanés vérifiables, non des vérités autonomes.
--
-- Règle unifiante (architecture de clôture) :
-- Celui qui détecte ne décide pas. Celui qui décide n'a pas détecté.
-- Aucun statut n'est acquis par défaut.
--
-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 1 — INGESTION (Frontières 1, 2)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS documents (
    document_id          TEXT PRIMARY KEY,
    title                 TEXT NOT NULL,
    source_type           TEXT NOT NULL,
    source_url            TEXT,
    source_locator        TEXT,
    content_hash          TEXT NOT NULL,
    original_format       TEXT NOT NULL,
    raw_content           TEXT,
    imported_at           TIMESTAMP NOT NULL DEFAULT current_timestamp,
    imported_by           TEXT NOT NULL,
    integrity_verified    BOOLEAN NOT NULL DEFAULT false
);

CREATE TABLE IF NOT EXISTS import_events (
    event_id              TEXT PRIMARY KEY,
    document_id           TEXT NOT NULL REFERENCES documents(document_id),
    event_type            TEXT NOT NULL,
    event_timestamp       TIMESTAMP NOT NULL DEFAULT current_timestamp,
    actor                 TEXT NOT NULL,
    detail                TEXT
);

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 2 — EXTRACTION (Frontières 5, 6)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS entities (
    entity_id             TEXT PRIMARY KEY,
    canonical_label       TEXT NOT NULL,
    entity_type           TEXT NOT NULL,
    aliases               TEXT[],
    source_document_id    TEXT REFERENCES documents(document_id),
    created_at            TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by            TEXT NOT NULL,
    status                TEXT NOT NULL DEFAULT 'candidate',
    notes                 TEXT
);

CREATE TABLE IF NOT EXISTS claims (
    claim_id              TEXT PRIMARY KEY,
    document_id           TEXT NOT NULL REFERENCES documents(document_id),
    event_id              TEXT REFERENCES import_events(event_id),
    extracted_text        TEXT NOT NULL,
    extraction_method     TEXT NOT NULL,
    extraction_model      TEXT,
    extraction_confidence REAL,
    extracted_at          TIMESTAMP NOT NULL DEFAULT current_timestamp,
    extracted_by          TEXT NOT NULL,
    notes                 TEXT
);

CREATE TABLE IF NOT EXISTS relations (
    relation_id           TEXT PRIMARY KEY,
    source_id             TEXT NOT NULL REFERENCES entities(entity_id),
    target_id             TEXT NOT NULL REFERENCES entities(entity_id),
    relation_type         TEXT NOT NULL,
    document_id           TEXT NOT NULL REFERENCES documents(document_id),
    event_id              TEXT REFERENCES import_events(event_id),
    claim_id              TEXT REFERENCES claims(claim_id),
    extraction_method     TEXT NOT NULL,
    extraction_model      TEXT,
    extraction_confidence REAL,
    derivation_method     TEXT,
    status                TEXT NOT NULL DEFAULT 'candidate',
    confidence            REAL DEFAULT 0.0,
    created_at            TIMESTAMP NOT NULL DEFAULT current_timestamp,
    created_by            TEXT NOT NULL,
    reviewed_at           TIMESTAMP,
    reviewer_id           TEXT,
    review_note           TEXT,
    contradiction_id      TEXT,
    CHECK (source_id != target_id),
    CHECK (extraction_confidence IS NULL OR (extraction_confidence >= 0.0 AND extraction_confidence <= 1.0))
);

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 3 — CORROBORATION (Frontière 5 : croisement = nouvel acte)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS relation_evidence (
    evidence_id           TEXT PRIMARY KEY,
    relation_id           TEXT NOT NULL REFERENCES relations(relation_id),
    document_id           TEXT NOT NULL REFERENCES documents(document_id),
    event_id              TEXT REFERENCES import_events(event_id),
    evidence_kind         TEXT NOT NULL,
    source_family         TEXT,
    independence_group    TEXT,
    source_quote          TEXT NOT NULL,
    cross_reference_note  TEXT,
    relevance_score       REAL,
    reliability_score     REAL,
    integrity_status      TEXT DEFAULT 'pending',
    verification_status   TEXT DEFAULT 'pending',
    created_at            TIMESTAMP NOT NULL DEFAULT current_timestamp
);

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 4 — CONTRADICTIONS (Frontière 8 : SMN)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS contradictions (
    contradiction_id       TEXT PRIMARY KEY,
    relation_id           TEXT NOT NULL REFERENCES relations(relation_id),
    opposing_relation_id  TEXT REFERENCES relations(relation_id),
    contradiction_type    TEXT NOT NULL,
    description           TEXT NOT NULL,
    detected_at           TIMESTAMP NOT NULL DEFAULT current_timestamp,
    detected_by           TEXT NOT NULL,
    status                TEXT NOT NULL DEFAULT 'active',
    resolution_note       TEXT,
    resolved_at           TIMESTAMP,
    resolved_by           TEXT
);

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 5 — GOUVERNANCE (Frontière 7)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS relation_status_history (
    status_change_id      TEXT PRIMARY KEY,
    relation_id           TEXT NOT NULL REFERENCES relations(relation_id),
    old_status            TEXT,
    new_status            TEXT NOT NULL,
    change_kind           TEXT NOT NULL,
    reason                TEXT NOT NULL,
    changed_at            TIMESTAMP NOT NULL DEFAULT current_timestamp,
    changed_by            TEXT NOT NULL,
    evidence_ref          TEXT,
    review_request_id     TEXT
);

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 6 — VÉRIFICATION (Frontière 11)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS review_requests (
    review_request_id     TEXT PRIMARY KEY,
    relation_id           TEXT NOT NULL REFERENCES relations(relation_id),
    requested_by          TEXT NOT NULL,
    review_kind           TEXT NOT NULL,
    priority              TEXT NOT NULL,
    request_reason        TEXT NOT NULL,
    requested_at          TIMESTAMP NOT NULL DEFAULT current_timestamp,
    assigned_to           TEXT,
    status                TEXT NOT NULL DEFAULT 'open',
    completed_at          TIMESTAMP,
    outcome               TEXT,
    review_method         TEXT,
    result_evidence_id    TEXT REFERENCES relation_evidence(evidence_id),
    result_note           TEXT
);

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 7 — HISTORIQUE (append-only, Frontière 9)
-- relation_status_history sert d'historique. Jamais de UPDATE/DELETE.
-- ═══════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 8 — PUBLICATION (Frontières 2, 4)
-- Trois niveaux : canonique, travail, audit
-- ═══════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW canonical_map AS
SELECT r.relation_id, src.canonical_label AS source_label, src.entity_type AS source_type,
       r.relation_type, dst.canonical_label AS target_label, dst.entity_type AS target_type,
       r.status, r.confidence, r.derivation_method, r.created_at, r.reviewed_at, r.reviewer_id
FROM relations r
JOIN entities src ON src.entity_id = r.source_id
JOIN entities dst ON dst.entity_id = r.target_id
WHERE r.status IN ('documented', 'verified')
  AND NOT EXISTS (SELECT 1 FROM contradictions c WHERE c.relation_id = r.relation_id AND c.status = 'active');

CREATE OR REPLACE VIEW work_map AS
SELECT r.relation_id, src.canonical_label AS source_label, src.entity_type AS source_type,
       r.relation_type, dst.canonical_label AS target_label, dst.entity_type AS target_type,
       r.status, r.confidence, r.derivation_method, r.created_at, r.reviewed_at, r.reviewer_id, r.review_note,
       e.evidence_id, e.evidence_kind, e.source_family, e.independence_group, e.source_quote, e.relevance_score, e.reliability_score
FROM relations r
JOIN entities src ON src.entity_id = r.source_id
JOIN entities dst ON dst.entity_id = r.target_id
LEFT JOIN relation_evidence e ON e.relation_id = r.relation_id
WHERE r.status IN ('candidate', 'documented', 'verified', 'disputed');

-- ═══════════════════════════════════════════════════════════════
-- VUE D'AUDIT CENTRALE (knowledge_audit)
-- Frontière 4 : Séparer le statut de l'entité de l'identité de la personne
-- ═══════════════════════════════════════════════════════════════

CREATE OR REPLACE VIEW knowledge_audit AS
SELECT r.relation_id, r.source_id, src.canonical_label AS source_label, src.entity_type AS source_type,
       r.relation_type, r.target_id, dst.canonical_label AS target_label, dst.entity_type AS target_type,
       r.status AS relation_status, r.confidence, r.derivation_method,
       r.document_id AS relation_document_id, r.event_id AS relation_event_id,
       r.created_at, r.reviewed_at, r.reviewer_id, r.review_note,
       src.status AS source_entity_status, dst.status AS target_entity_status,
       e.evidence_id, e.document_id AS evidence_document_id, e.event_id AS evidence_event_id,
       e.evidence_kind, e.source_family, e.independence_group, e.source_quote, e.cross_reference_note,
       e.relevance_score, e.reliability_score, e.integrity_status, e.verification_status,
       h.old_status, h.new_status, h.change_kind, h.reason AS status_change_reason, h.changed_at, h.changed_by,
       rr.review_request_id, rr.review_kind, rr.status AS review_status, rr.outcome AS review_outcome,
       rr.review_method, rr.assigned_to AS review_assigned_to,
       c.contradiction_id, c.status AS contradiction_status, c.description AS contradiction_description
FROM relations r
LEFT JOIN entities src ON src.entity_id = r.source_id
LEFT JOIN entities dst ON dst.entity_id = r.target_id
LEFT JOIN relation_evidence e ON e.relation_id = r.relation_id
LEFT JOIN relation_status_history h ON h.status_change_id = (
    SELECT h2.status_change_id FROM relation_status_history h2
    WHERE h2.relation_id = r.relation_id ORDER BY h2.changed_at DESC LIMIT 1)
LEFT JOIN review_requests rr ON rr.relation_id = r.relation_id
LEFT JOIN contradictions c ON c.relation_id = r.relation_id;

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 9 — EXPORT IA (Frontière 10)
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS export_manifests (
    export_id             TEXT PRIMARY KEY,
    created_at            TIMESTAMP NOT NULL DEFAULT current_timestamp,
    source_database       TEXT NOT NULL DEFAULT 'continuite.duckdb',
    included_statuses     TEXT[] NOT NULL,
    table_count           INTEGER NOT NULL,
    total_rows            BIGINT NOT NULL,
    manifest_sha256       TEXT NOT NULL,
    created_by            TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS export_tables (
    export_id             TEXT NOT NULL REFERENCES export_manifests(export_id),
    table_name            TEXT NOT NULL,
    file_name             TEXT NOT NULL,
    file_format           TEXT NOT NULL,
    row_count             BIGINT NOT NULL,
    sha256                TEXT NOT NULL,
    PRIMARY KEY (export_id, table_name)
);

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 10 — TRAÇABILITÉ
-- Assuré par knowledge_audit. Toute relation doit pouvoir être expliquée.
-- ═══════════════════════════════════════════════════════════════

-- ═══════════════════════════════════════════════════════════════
-- WORKFLOW 11 — RÉTENTION (ajouté par validation Frontière 3)
-- "Rien n'est supprimé silencieusement" : la trace reste, pas l'objet
-- ═══════════════════════════════════════════════════════════════

CREATE TABLE IF NOT EXISTS retention_events (
    retention_id          TEXT PRIMARY KEY,
    document_id           TEXT REFERENCES documents(document_id),
    relation_id           TEXT REFERENCES relations(relation_id),
    entity_id             TEXT REFERENCES entities(entity_id),
    action                TEXT NOT NULL,
    reason                TEXT NOT NULL,
    decided_by            TEXT NOT NULL,
    decided_at            TIMESTAMP NOT NULL DEFAULT current_timestamp,
    effective_at          TIMESTAMP NOT NULL,
    review_method         TEXT,
    affected_content_hash TEXT,
    metadata_preserved    TEXT NOT NULL,
    CHECK (document_id IS NOT NULL OR relation_id IS NOT NULL OR entity_id IS NOT NULL)
);

-- ═══════════════════════════════════════════════════════════════
-- TESTS D'INVARIANTS (0 ligne = OK, 1+ ligne = violation)
-- ═══════════════════════════════════════════════════════════════

-- I1: Aucun document sans document_id, origine et SHA-256
-- I2: Aucun événement d'import sans document source
-- I3: Aucune relation candidate sans source, méthode et citation
-- I4: Aucune preuve sans document_id
-- I5: Aucun statut "documented" sans raison enregistrée
-- I6: Aucun statut "verified" sans reviewer_id, reviewed_at, review_method et preuve
-- I7: Aucun changement de statut sans ligne dans relation_status_history
-- I8: Aucune relation "documented/verified" si contradiction active
-- I9: Aucun export canonique contenant candidate/disputed/withdrawn/rejected
-- I10: Aucun effacement physique sans retention_event documenté
-- I11: Aucune IA à la fois extracteur et décideur (règle unifiante)

-- (Voir les requêtes SQL complètes dans le canvas registre-continuite)

-- ═══════════════════════════════════════════════════════════════
-- PREMIER CAS RÉEL — Transcription du 12 septembre 2026
-- Source : Notion page 3d98d1e3591e816980dfd61d4d4e3044
-- SHA-256 : 94f838644a7b7af5df72759a7fafca5a3d3d2f30ddde9341ae14a67b92c95d17
-- ═══════════════════════════════════════════════════════════════

INSERT INTO documents (document_id, title, source_type, source_url, source_locator, content_hash, original_format, imported_by)
VALUES ('doc_notion_transcription_2026-09-12',
    'Conversation Mikael — 12 septembre 2026 — transcription complète récupérée',
    'notion',
    'https://flowery-boat-98d.notion.site/...',
    '3d98d1e3591e816980dfd61d4d4e3044',
    '94f838644a7b7af5df72759a7fafca5a3d3d2f30ddde9341ae14a67b92c95d17',
    'markdown', 'vibe');

INSERT INTO import_events (event_id, document_id, event_type, actor, detail)
VALUES ('imp_001', 'doc_notion_transcription_2026-09-12', 'imported', 'vibe',
    '4 interventions V1-V4 + messages 6-44 + 5 suivis');

INSERT INTO entities (entity_id, canonical_label, entity_type, source_document_id, created_by, notes) VALUES
    ('ent_mikael', 'Mikael Mireault', 'Person', 'doc_notion_transcription_2026-09-12', 'vibe', 'Utilisateur'),
    ('ent_forteresse', 'Forteresse (projet)', 'Project', 'doc_notion_transcription_2026-09-12', 'vibe', 'PWA contemplative'),
    ('ent_double_memoire', 'Double mémoire', 'Concept', 'doc_notion_transcription_2026-09-12', 'vibe', 'Deux lectures en sens opposés'),
    ('ent_amour_choisi', 'Amour choisi', 'Concept', 'doc_notion_transcription_2026-09-12', 'vibe', 'Noyau éthique'),
    ('ent_noyau', 'Noyau Forteresse', 'Document', 'doc_notion_transcription_2026-09-12', 'vibe', '3 pièces : projection, ancre, second lecteur');

INSERT INTO relations (relation_id, source_id, target_id, relation_type, document_id, event_id, extraction_method, extraction_model, extraction_confidence, derivation_method, status, created_by)
VALUES
    ('rel_001', 'ent_mikael', 'ent_forteresse', 'WORKS_ON', 'doc_notion_transcription_2026-09-12', 'imp_001', 'ia_extract', 'vibe', 0.95, 'direct_quote', 'candidate', 'vibe'),
    ('rel_002', 'ent_mikael', 'ent_double_memoire', 'MENTIONS', 'doc_notion_transcription_2026-09-12', 'imp_001', 'ia_extract', 'vibe', 0.90, 'direct_quote', 'candidate', 'vibe'),
    ('rel_003', 'ent_double_memoire', 'ent_forteresse', 'CONCERNS', 'doc_notion_transcription_2026-09-12', 'imp_001', 'ia_extract', 'vibe', 0.85, 'direct_quote', 'candidate', 'vibe'),
    ('rel_004', 'ent_mikael', 'ent_amour_choisi', 'MENTIONS', 'doc_notion_transcription_2026-09-12', 'imp_001', 'ia_extract', 'vibe', 0.80, 'direct_quote', 'candidate', 'vibe'),
    ('rel_005', 'ent_noyau', 'ent_forteresse', 'DERIVES_FROM', 'doc_notion_transcription_2026-09-12', 'imp_001', 'ia_extract', 'vibe', 0.90, 'direct_quote', 'candidate', 'vibe');
