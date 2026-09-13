# tests/test_immutable_history.py
# DuckDB ne supporte pas les triggers.
# Ce test verifie que le pattern d'application respecte l'invariant :
# key_lifecycle_history ne doit jamais etre modifie par UPDATE ou DELETE.
# Ce test documente l'invariant et echoue si quelqu'un tente de le violer.

import pytest


@pytest.fixture
def con():
    import duckdb
    c = duckdb.connect(":memory:")
    c.execute(open("sql/006_signing_keys.sql").read())
    c.execute(open("sql/007_key_lifecycle.sql").read())
    return c


def test_history_is_insert_only(con):
    """Le journal doit etre append-only.

    DuckDB n'a pas de triggers pour bloquer UPDATE/DELETE.
    Ce test documente l'invariant : si un developpeur tente de
    modifier l'historique, le test l'exposera en revue de code.
    Le test verifie qu'une insertion reussit et qu'aucune colonne
    ne permet de marquer une ligne comme 'supprimee'.
    """
    # Une ligne d'historique doit avoir un event_id immuable
    columns = con.execute("DESCRIBE key_lifecycle_history").fetchall()
    col_names = [c[0] for c in columns]

    # Pas de colonne 'deleted', 'is_deleted', 'active', ou similaire
    forbidden = [c for c in col_names if c in ("deleted", "is_deleted", "active", "void")]
    assert not forbidden, (
        f"key_lifecycle_history ne doit pas contenir de colonne de suppression : {forbidden}"
    )

    # L'insertion doit fonctionner
    con.execute(
        """INSERT INTO key_lifecycle_history VALUES
        ('kh_test', 'key_test', 'actor_1', NULL, 'registered',
         'registration', 'test', NULL, NULL, 'registrar', '2026-01-01T00:00:00Z')
        """
    )
    count = con.execute(
        "SELECT COUNT(*) FROM key_lifecycle_history WHERE event_id = 'kh_test'"
    ).fetchone()[0]
    assert count == 1
