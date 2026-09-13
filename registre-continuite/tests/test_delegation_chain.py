# tests/test_delegation_chain.py
# Tests des chaines de delegation : profondeur 1, profondeur 2,
# revocation, scope, anti-cycle, role incoherent.

import pytest
from attest.delegation import check_delegation_chain, insert_delegation, revoke_delegation


@pytest.fixture
def con():
    import duckdb
    c = duckdb.connect(":memory:")
    c.execute(open("sql/006_signing_keys.sql").read())
    c.execute(open("sql/007_key_lifecycle.sql").read())
    c.execute(open("sql/008_chain_integrity.sql").read())
    c.execute(open("sql/010_governance_hardening.sql").read())
    # Roles de base
    c.execute("INSERT INTO actor_roles VALUES ('root_actor', 'lead_auditor', '2020-01-01T00:00:00Z', NULL)")
    c.execute("INSERT INTO actor_roles VALUES ('mid_actor', 'lead_auditor', '2020-01-01T00:00:00Z', NULL)")
    return c


NOW = "2026-09-13T01:00:00Z"


def test_delegation_depth_1_direct(con):
    """Delegation directe : root_actor -> signer_d1, profondeur 1."""
    insert_delegation(con,
        delegation_id="del_root_d1",
        grantor_id="root_actor",
        grantee_id="signer_d1",
        delegated_role="lead_auditor",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="root_actor",
    )

    result = check_delegation_chain(con,
        actor_id="signer_d1",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
    )
    assert result["authorized"] is True
    assert result["depth"] == 1


def test_delegation_depth_2_chain(con):
    """Chaine a 2 sauts : root_actor -> mid_actor -> signer_d2.

    Le cas de base ancre sur signer_d2 (grantee_id = actor_id).
    Le pas recursif remonte vers mid_actor, puis vers root_actor.
    Le SELECT terminal verifie que root_actor a le role dans actor_roles.
    """
    insert_delegation(con,
        delegation_id="del_root_mid",
        grantor_id="root_actor",
        grantee_id="mid_actor",
        delegated_role="lead_auditor",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="root_actor",
    )
    insert_delegation(con,
        delegation_id="del_mid_signer",
        grantor_id="mid_actor",
        grantee_id="signer_d2",
        delegated_role="lead_auditor",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="mid_actor",
    )

    result = check_delegation_chain(con,
        actor_id="signer_d2",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
    )
    assert result["authorized"] is True
    assert result["depth"] == 2
    assert result["chain"] == ["signer_d2", "mid_actor", "root_actor"]


def test_no_delegation_returns_not_found(con):
    """Aucune delegation : ACTIVE_DELEGATION_NOT_FOUND."""
    result = check_delegation_chain(con,
        actor_id="unknown_actor",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
    )
    assert result["authorized"] is False
    assert result["error"] == "ACTIVE_DELEGATION_NOT_FOUND"


def test_revoked_delegation_not_accepted(con):
    """Une delegation revoquee ne doit pas etre acceptee."""
    insert_delegation(con,
        delegation_id="del_revoked",
        grantor_id="root_actor",
        grantee_id="signer_rev",
        delegated_role="lead_auditor",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="root_actor",
    )
    revoke_delegation(con,
        delegation_id="del_revoked",
        revoked_by="root_actor",
        reason="Compromission suspectee",
        now="2026-09-10T00:00:00Z",
    )

    result = check_delegation_chain(con,
        actor_id="signer_rev",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
    )
    assert result["authorized"] is False


def test_wrong_role_not_accepted(con):
    """Une delegation pour un role different ne doit pas etre acceptee."""
    insert_delegation(con,
        delegation_id="del_wrong_role",
        grantor_id="root_actor",
        grantee_id="signer_wrong",
        delegated_role="reviewer",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="root_actor",
    )

    result = check_delegation_chain(con,
        actor_id="signer_wrong",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
    )
    assert result["authorized"] is False


def test_scope_relation_filter(con):
    """Une delegation scopee a une relation specifique ne marche pas pour une autre."""
    insert_delegation(con,
        delegation_id="del_scoped",
        grantor_id="root_actor",
        grantee_id="signer_scoped",
        delegated_role="lead_auditor",
        scope_relation_id="rel_specific_001",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="root_actor",
    )

    # Bon scope : OK
    result_ok = check_delegation_chain(con,
        actor_id="signer_scoped",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        relation_id="rel_specific_001",
        now=NOW,
    )
    assert result_ok["authorized"] is True

    # Mauvais scope : refuse
    result_no = check_delegation_chain(con,
        actor_id="signer_scoped",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        relation_id="rel_other_999",
        now=NOW,
    )
    assert result_no["authorized"] is False


def test_expired_delegation_not_accepted(con):
    """Une delegation expiree ne doit pas etre acceptee."""
    insert_delegation(con,
        delegation_id="del_expired",
        grantor_id="root_actor",
        grantee_id="signer_exp",
        delegated_role="lead_auditor",
        valid_from="2020-01-01T00:00:00Z",
        valid_until="2026-01-01T00:00:00Z",  # expire avant NOW
        delegated_by="root_actor",
    )

    result = check_delegation_chain(con,
        actor_id="signer_exp",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
    )
    assert result["authorized"] is False


def test_cycle_protection(con):
    """Un cycle dans les delegations ne doit pas boucler indefiniment."""
    # Creer un cycle : A -> B -> A
    insert_delegation(con,
        delegation_id="del_a_b",
        grantor_id="actor_a",
        grantee_id="actor_b",
        delegated_role="lead_auditor",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="actor_a",
    )
    insert_delegation(con,
        delegation_id="del_b_a",
        grantor_id="actor_b",
        grantee_id="actor_a",
        delegated_role="lead_auditor",
        valid_from="2020-01-01T00:00:00Z",
        delegated_by="actor_b",
    )
    # actor_a a le role
    con.execute("INSERT INTO actor_roles VALUES ('actor_a', 'lead_auditor', '2020-01-01T00:00:00Z', NULL)")

    # La recherche depuis actor_b vers actor_a doit trouver la chaine
    # sans boucler grace a NOT list_contains(child.path, parent.grantee_id)
    result = check_delegation_chain(con,
        actor_id="actor_b",
        reviewer_id="actor_a",
        delegated_role="lead_auditor",
        now=NOW,
        max_depth=5,
    )
    assert result["authorized"] is True
    assert result["depth"] == 1  # chemin direct B -> A, pas par le cycle


def test_max_depth_limit(con):
    """La profondeur max est respectee."""
    # Chaine de 3 sauts
    insert_delegation(con,
        delegation_id="d1", grantor_id="root_actor", grantee_id="m1",
        delegated_role="lead_auditor", valid_from="2020-01-01T00:00:00Z", delegated_by="root_actor")
    insert_delegation(con,
        delegation_id="d2", grantor_id="m1", grantee_id="m2",
        delegated_role="lead_auditor", valid_from="2020-01-01T00:00:00Z", delegated_by="m1")
    insert_delegation(con,
        delegation_id="d3", grantor_id="m2", grantee_id="m3",
        delegated_role="lead_auditor", valid_from="2020-01-01T00:00:00Z", delegated_by="m2")

    # max_depth=2 : ne devrait pas atteindre root_actor (3 sauts)
    result = check_delegation_chain(con,
        actor_id="m3",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
        max_depth=2,
    )
    assert result["authorized"] is False

    # max_depth=3 : devrait atteindre root_actor
    result_ok = check_delegation_chain(con,
        actor_id="m3",
        reviewer_id="root_actor",
        delegated_role="lead_auditor",
        now=NOW,
        max_depth=3,
    )
    assert result_ok["authorized"] is True
    assert result_ok["depth"] == 3
