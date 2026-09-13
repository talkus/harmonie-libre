# attest/keys_lifecycle.py
# Transitions de cycle de vie des cles, alignees sur NIST SP 800-57.
# Toute transition ecrit une ligne dans key_lifecycle_history (append-only).

import uuid
from datetime import datetime, timezone


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def _record_event(con, *, key_id, actor_id, from_status, to_status,
                  event_type, reason, compromised_since, attestation_id,
                  recorded_by):
    con.execute(
        """
        INSERT INTO key_lifecycle_history (
            event_id, key_id, actor_id, from_status, to_status,
            event_type, reason, compromised_since,
            decision_attestation_id, recorded_by, recorded_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """,
        [
            f"kh_{uuid.uuid4().hex}",
            key_id, actor_id,
            from_status, to_status,
            event_type, reason, compromised_since,
            attestation_id, recorded_by, _now_iso(),
        ],
    )


def activate_key(con, *, key_id, recorded_by, attestation_id=None):
    row = con.execute(
        "SELECT actor_id, status FROM actor_signing_keys WHERE key_id = ?",
        [key_id],
    ).fetchone()
    if row is None:
        raise RuntimeError("Cle inconnue.")
    actor_id, current_status = row
    if current_status not in ("registered", "generated"):
        raise RuntimeError(
            f"Activation refusee : statut actuel = {current_status}. "
            "Seules les cles 'generated' ou 'registered' peuvent etre activees."
        )
    con.execute(
        "UPDATE actor_signing_keys SET status = 'active' WHERE key_id = ?",
        [key_id],
    )
    _record_event(con,
        key_id=key_id, actor_id=actor_id,
        from_status=current_status, to_status="active",
        event_type="activation", reason="Cle activée",
        compromised_since=None, attestation_id=attestation_id,
        recorded_by=recorded_by,
    )


def rotate_key(con, *, old_key_id, new_key_id, actor_id, public_key_hex,
               valid_from, registered_by, attestation_id=None):
    """Rotation additive : ajouter la nouvelle cle, basculer, marquer l'ancienne retiring.

    1. Enregistrer la nouvelle cle (status = registered)
    2. Activer la nouvelle cle (status = active)
    3. Marquer l'ancienne cle 'retiring' (fenetre de chevauchement)
    L'ancienne cle reste acceptable pour les artefacts signes avant sa
    date de fin. Elle passera a 'retired' apres expiration.
    """
    import hashlib
    from attest.keys import register_actor_key

    con.execute("BEGIN TRANSACTION")
    try:
        # 1. Enregistrer la nouvelle cle
        register_actor_key(
            con,
            key_id=new_key_id,
            actor_id=actor_id,
            public_key_hex=public_key_hex,
            valid_from=valid_from,
            registered_by=registered_by,
            registration_attestation_id=attestation_id or "",
            now=_now_iso(),
        )
        con.execute(
            "UPDATE actor_signing_keys SET status = 'registered' WHERE key_id = ?",
            [new_key_id],
        )

        # 2. Activer la nouvelle cle
        activate_key(con, key_id=new_key_id, recorded_by=registered_by,
                     attestation_id=attestation_id)

        # 3. Marquer l'ancienne cle 'retiring'
        old_row = con.execute(
            "SELECT status FROM actor_signing_keys WHERE key_id = ?",
            [old_key_id],
        ).fetchone()
        if old_row is None:
            raise RuntimeError("Ancienne cle introuvable.")
        old_status = old_row[0]
        if old_status != "active":
            raise RuntimeError(
                f"Rotation refusee : l'ancienne cle n'est pas active (statut = {old_status})."
            )
        con.execute(
            "UPDATE actor_signing_keys SET status = 'retiring' WHERE key_id = ?",
            [old_key_id],
        )
        _record_event(con,
            key_id=old_key_id, actor_id=actor_id,
            from_status="active", to_status="retiring",
            event_type="rotation_start",
            reason=f"Rotation additive vers {new_key_id}",
            compromised_since=None, attestation_id=attestation_id,
            recorded_by=registered_by,
        )

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise


def complete_rotation(con, *, old_key_id, recorded_by, attestation_id=None):
    """Marquer une cle 'retiring' comme 'retired' (apres expiration des artefacts)."""
    row = con.execute(
        "SELECT actor_id, status, valid_until FROM actor_signing_keys WHERE key_id = ?",
        [old_key_id],
    ).fetchone()
    if row is None:
        raise RuntimeError("Cle inconnue.")
    actor_id, status, valid_until = row
    if status != "retiring":
        raise RuntimeError(
            f"Fin de rotation refusee : statut = {status}, 'retiring' attendu."
        )
    if valid_until is not None and valid_until > _now_iso():
        raise RuntimeError(
            "La cle n'a pas encore expire. Attendre valid_until ou le forcer."
        )
    con.execute(
        "UPDATE actor_signing_keys SET status = 'retired' WHERE key_id = ?",
        [old_key_id],
    )
    _record_event(con,
        key_id=old_key_id, actor_id=actor_id,
        from_status="retiring", to_status="retired",
        event_type="rotation_complete",
        reason="Rotation terminee : cle retiree apres expiration",
        compromised_since=None, attestation_id=attestation_id,
        recorded_by=recorded_by,
    )


def suspect_compromise(con, *, key_id, compromised_since, reason, recorded_by,
                      attestation_id=None):
    """Marquer une cle comme suspectee de compromission.

    compromised_since est la date estimee du debut de la compromission.
    Les signatures emises AVANT compromised_since restent historiquement valides.
    Les signatures emises APRES ne sont plus acceptees.
    """
    row = con.execute(
        "SELECT actor_id, status FROM actor_signing_keys WHERE key_id = ?",
        [key_id],
    ).fetchone()
    if row is None:
        raise RuntimeError("Cle inconnue.")
    actor_id, current_status = row
    if current_status not in ("active", "retiring"):
        raise RuntimeError(
            f"Compromission suspectee refusee : statut = {current_status}. "
            "Seules les cles 'active' ou 'retiring' peuvent etre marquees."
        )
    con.execute(
        """
        UPDATE actor_signing_keys
        SET status = 'suspected_compromise', compromised_since = ?
        WHERE key_id = ?
        """,
        [compromised_since, key_id],
    )
    _record_event(con,
        key_id=key_id, actor_id=actor_id,
        from_status=current_status, to_status="suspected_compromise",
        event_type="compromise_suspected",
        reason=reason,
        compromised_since=compromised_since,
        attestation_id=attestation_id,
        recorded_by=recorded_by,
    )


def revoke_key(con, *, key_id, reason, revoked_by, compromised_since=None,
               attestation_id=None):
    """Revocation formelle. Arrete la capacite de la cle a autoriser l'avenir.

    Si compromised_since est fourni, les signatures emises avant restent valides.
    Si compromised_since est NULL, toutes les signatures sont considerees suspectes.
    """
    row = con.execute(
        "SELECT actor_id, status FROM actor_signing_keys WHERE key_id = ?",
        [key_id],
    ).fetchone()
    if row is None:
        raise RuntimeError("Cle inconnue.")
    actor_id, current_status = row
    if current_status == "destroyed":
        raise RuntimeError("Cle deja detruite. La revocation n'a plus d'effet.")

    now = _now_iso()
    con.execute(
        """
        UPDATE actor_signing_keys
        SET status = 'revoked',
            revoked_at = ?,
            revoked_by = ?,
            revoke_reason = ?,
            compromised_since = COALESCE(?, compromised_since)
        WHERE key_id = ?
        """,
        [now, revoked_by, reason, compromised_since, key_id],
    )
    _record_event(con,
        key_id=key_id, actor_id=actor_id,
        from_status=current_status, to_status="revoked",
        event_type="revoke",
        reason=reason,
        compromised_since=compromised_since,
        attestation_id=attestation_id,
        recorded_by=revoked_by,
    )


def destroy_key(con, *, key_id, reason, destroyed_by, attestation_id=None):
    """Destruction de la cle. Les metadonnees restent (NIST : on conserve la trace).

    La cle publique est conservée pour la verification des artefacts historiques.
    La cle privee doit etre detruite cote operateur (hors de ce registre).
    """
    row = con.execute(
        "SELECT actor_id, status FROM actor_signing_keys WHERE key_id = ?",
        [key_id],
    ).fetchone()
    if row is None:
        raise RuntimeError("Cle inconnue.")
    actor_id, current_status = row
    if current_status not in ("retired", "revoked"):
        raise RuntimeError(
            f"Destruction refusee : statut = {current_status}. "
            "La cle doit etre 'retired' ou 'revoked' avant destruction."
        )

    now = _now_iso()
    con.execute(
        """
        UPDATE actor_signing_keys
        SET status = 'destroyed', destroyed_at = ?, destroyed_by = ?
        WHERE key_id = ?
        """,
        [now, destroyed_by, key_id],
    )
    _record_event(con,
        key_id=key_id, actor_id=actor_id,
        from_status=current_status, to_status="destroyed",
        event_type="destroy",
        reason=reason,
        compromised_since=None,
        attestation_id=attestation_id,
        recorded_by=destroyed_by,
    )
