# Validation du registre contre l'Architecture de cloture (11 frontieres)

> Document de conformite. Chaque frontiere est validee par un invariant,
> un workflow, et une preuve dans le schema.

## Frontiere 1 — Gravite par objet

**Principe :** Chaque document a sa propre provenance, sa propre gravite.

**Invariant :** Les originaux ne sont pas reecrits.

**Workflow 1 (Ingestion) :** La table documents stocke source_type, source_url,
content_hash_sha256. Un document deja vu n'est pas recalcule.

**Preuve :**
    SELECT document_id, source_type, content_hash_sha256
    FROM documents
    WHERE document_id = 'doc_notion_transcription_2026-09-12';

Valide.

## Frontiere 2 — Contenant distinct de contenus

**Principe :** Le document ne determine pas le statut de ses contenus.

**Invariant :** Aucun statut n'est acquis par defaut.

**Workflow 2 (Extraction) :** Les entites sont candidate a l'extraction.
Le statut documented n'est atteint que par une decision explicite.

**Preuve :**
    SELECT status, COUNT(*) FROM entities GROUP BY status;
    -- candidate = extrait, pas encore valide

Valide.

## Frontiere 3 — Conservation

**Principe :** Rien n'est perdu. Rien n'est supprime silencieusement.

**Invariant :** Rien n'est supprime silencieusement (Workflow 11 — Retention).

**Workflow 11 (Retention) :** La table relation_status_history est append-only.
Une correction ajoute une ligne, n'en supprime aucune.

**Preuve :**
    SELECT * FROM relation_status_history
    WHERE relation_id = 'rel_XXX'
    ORDER BY created_at;

Valide.

## Frontiere 4 — Acces

**Principe :** Les exports sont des instantanes verificables.

**Invariant :** Les exports sont des instantanes verificables, non des verites autonomes.

**Workflow 9 (Export) :** COPY ... TO 'entities.parquet' (FORMAT PARQUET)
produit un instantane horodate. L'export porte le hash du contenu.

Valide.

## Frontiere 5 — Execution

**Principe :** Les decisions ont un auteur, une raison et une date.

**Invariant :** Les decisions ont un auteur, une raison et une date.

**Workflow 5 (Validation) :** La table decision_attestations stocke
actor_id, actor_role, issued_at, signed_envelope_jcs.

**Preuve :**
    SELECT attestation_id, actor_id, actor_role, issued_at
    FROM decision_attestations
    WHERE decision_id = 'dec_001';

Valide.

## Frontiere 6 — Decouverte

**Principe :** Les inférences ne deviennent pas des faits par repetition.

**Invariant :** Les inférences ne deviennent pas des faits par repetition.

**Workflow 2 (Extraction) :** Le champ extraction_method distingue
ia_extract (inférence) de human_verified (fait). Le statut candidate
ne passe a documented que par validation explicite.

Valide.

## Frontiere 7 — Instance

**Principe :** Chaque relation a un cycle de vie.

**Invariant :** Chaque relation a un statut, un historique, une tracabilite.

**Workflow 4 (Cycle de vie) :** relations.status dans
{candidate, documented, corrected, rejected, superseded}.
relation_status_history trace chaque transition.

Valide.

## Frontiere 8 — Suspension

**Principe :** Les contradictions deviennent des objets de travail.

**Invariant :** Les contradictions deviennent des objets de travail.

**Workflow 6 (Contradiction) :** La table contradictions stocke les
conflits avec un statut (active, resolved, superseded).
transition_permissions peut exiger requires_no_active_contradiction.

Valide.

## Frontiere 9 — Arbitrage

**Principe :** Celui qui detecte ne decide pas.

**Invariant 11 :** Aucun IA ne peut etre a la fois extracteur et decideur.

**Workflow 7 (Separation) :** actor_roles distingue extractor de
lead_auditor. transition_permissions verifie le role a issued_at.
Le CLI ne decide rien — seul apply_status_transition ecrit valid.

Valide.

## Frontiere 10 — Interoperabilite

**Principe :** Les exports sont verifies, pas autonomes.

**Invariant :** Les exports sont des instantanes verificables.

**Workflow 9 (Export) :** Export Parquet + export Cypher + export JSON.
Chaque export porte un hash. L'audit de chaine valide l'integrite.

Valide.

## Frontiere 11 — Confiance verifiable

**Principe :** Les attestations sont cryptographiquement verificables.

**Invariant :** La cle publique vient du registre, jamais du payload.

**Workflow 8 (Attestation) :** actor_signing_keys precharge les cles.
verify_against_registry verifie en 4 etapes. audit_chain audite la chaine.
tip_anchors ancre le tip externement.

Valide.

---

## Resume

| Frontiere | Invariant | Workflow | Statut |
|---|---|---|---|
| 1 Gravite par objet | Originaux non reecrits | 1 Ingestion | OK |
| 2 Contenant distinct | Aucun statut par defaut | 2 Extraction | OK |
| 3 Conservation | Rien supprime silencieusement | 11 Retention | OK |
| 4 Acces | Exports verificables | 9 Export | OK |
| 5 Execution | Auteur, raison, date | 5 Validation | OK |
| 6 Decouverte | Inférences distinctes | 2 Extraction | OK |
| 7 Instance | Cycle de vie par relation | 4 Cycle de vie | OK |
| 8 Suspension | Contradictions = objets | 6 Contradiction | OK |
| 9 Arbitrage | Detecte distinct de decide | 7 Separation | OK |
| 10 Interoperabilite | Exports verifies | 9 Export | OK |
| 11 Confiance verifiable | Cle du registre | 8 Attestation | OK |
