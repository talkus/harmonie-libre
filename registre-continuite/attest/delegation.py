# attest/delegation.py
# Verification des chaines de delegation par CTE recursive.
#
# Correctif critique : le cas de base ancre uniquement sur le signataire
# physique (grantee_id = actor_id). La correspondance avec reviewer_id
# s'effectue au sommet de la chaine, dans le SELECT terminal.
# L'ancienne version filtrait grantor_id = reviewer_id des le pas 0,
# ce qui restreignait aux delegations directes (profondeur 1) et empechait
# la recursion de demarrer pour les chaines multi-sauts.

from typing import Optional


def check_delegation_chain(
    con,
    *,
    actor_id: str,
    reviewer_id: str,
    delegated_role: str,
    relation_id: str = '*',
    transition_kind: str = '*',
    now: str,
    max_depth: int = 10,
) -> dict:
    """Verifie qu il existe une chaine de delegation de actor_id vers reviewer_id.

    Structure de la CTE recursive (6 binds) :

    1. Cas de base : ancrage sur le signataire effectif (grantee_id = actor_id).
       Filtre sur scope_relation_id, scope_transition_kind, validite temporelle.
       Bind 1: actor_id, Bind 2: relation_id, Bind 3: transition_kind, Bind 4: now

    2. Pas recursif : remontee vers le delegant parent.
       Joint sur parent.grantee_id = child.grantor_id.
       Filtre : profondeur < max_depth, coherence du role et du scope,
       non-revocation, validite temporelle, anti-cycle.
       Bind 5: now

    3. Cloture : un maillon de la chaine doit etre le reviewer racine
       titulaire du role. Joint sur actor_roles pour verifier le role.
       Bind 6: reviewer_id

    Returns:
        {'authorized': bool, 'depth': int|None, 'chain': list|None, 'error': str|None}
    """
    sql = f"""
    WITH RECURSIVE chain AS (
        -- 1. Cas de base : ancrage sur le signataire effectif
        SELECT d.delegation_id, d.grantor_id, d.grantee_id, d.delegated_role,
               d.scope_relation_id, d.scope_transition_kind, 1 AS depth,
               [d.grantee_id] AS path
        FROM actor_delegations d
        WHERE d.grantee_id = ?
          AND d.delegated_role = ?
          AND d.scope_relation_id IN (?, '*')
          AND d.scope_transition_kind IN (?, '*')
          AND d.revoked = FALSE
          AND ?::TIMESTAMPTZ BETWEEN d.valid_from AND d.valid_until

        UNION ALL

        -- 2. Pas recursif : remontee vers le delegant parent
        SELECT parent.delegation_id, parent.grantor_id, parent.grantee_id,
               parent.delegated_role, parent.scope_relation_id,
               parent.scope_transition_kind, child.depth + 1,
               list_append(child.path, parent.grantee_id)
        FROM actor_delegations parent
        JOIN chain child ON parent.grantee_id = child.grantor_id
        WHERE child.depth < {max_depth}
          AND parent.delegated_role = child.delegated_role
          AND parent.scope_relation_id IN (child.scope_relation_id, '*')
          AND parent.scope_transition_kind IN (child.scope_transition_kind, '*')
          AND parent.revoked = FALSE
          AND ?::TIMESTAMPTZ BETWEEN parent.valid_from AND parent.valid_until
          AND NOT list_contains(child.path, parent.grantee_id)
    )
    -- 3. Cloture : un maillon doit etre le reviewer racine titulaire du role
    SELECT c.delegation_id, c.delegated_role, c.grantor_id, c.depth, c.path
    FROM chain c
    JOIN actor_roles ar ON ar.actor_id = c.grantor_id AND ar.role = c.delegated_role
    WHERE c.grantor_id = ?
    """

    params = [
        actor_id,       # bind 1
        delegated_role,  # filtre sur le role delegue
        relation_id,     # bind 2
        transition_kind, # bind 3
        now,             # bind 4
        now,             # bind 5 (pas recursif)
        reviewer_id,     # bind 6
    ]

    rows = con.execute(sql, params).fetchall()

    if not rows:
        return {
            'authorized': False,
            'depth': None,
            'chain': None,
            'error': 'ACTIVE_DELEGATION_NOT_FOUND',
        }

    # Prendre la chaine la plus courte
    best = min(rows, key=lambda r: r[3])
    return {
        'authorized': True,
        'depth': best[3],
        'chain': best[4],  # path
        'delegation_id': best[0],
        'root_grantor': best[2],
        'delegated_role': best[1],
        'error': None,
    }


def insert_delegation(
    con,
    *,
    delegation_id: str,
    grantor_id: str,
    grantee_id: str,
    delegated_role: str,
    valid_from: str,
    valid_until: str | None = None,
    scope_relation_id: str = '*',
    scope_transition_kind: str = '*',
    delegated_by: str,
    delegation_attestation_id: str | None = None,
):
    """Insere une delegation dans actor_delegations."""
    con.execute(
        """
        INSERT INTO actor_delegations (
            delegation_id, grantor_id, grantee_id, delegated_role,
            scope_relation_id, scope_transition_kind,
            valid_from, valid_until, revoked,
            delegated_by, delegation_attestation_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, FALSE, ?, ?)
        """,
        [delegation_id, grantor_id, grantee_id, delegated_role,
         scope_relation_id, scope_transition_kind,
         valid_from, valid_until, delegated_by, delegation_attestation_id],
    )


def revoke_delegation(con, *, delegation_id: str, revoked_by: str, reason: str, now: str):
    """Revoque une delegation."""
    con.execute(
        """
        UPDATE actor_delegations
        SET revoked = TRUE, revoked_at = ?, revoked_by = ?, revoke_reason = ?
        WHERE delegation_id = ?
        """,
        [now, revoked_by, reason, delegation_id],
    )
