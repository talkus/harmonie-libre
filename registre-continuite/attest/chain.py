# attest/chain.py
# Append d'evenements dans key_lifecycle_history avec chaine de hachage.
#
# Correctifs revue :
# 1. Transaction explicite + chain_lock (anti-course)
# 2. Timestamp normalise : strftime("%Y-%m-%dT%H:%M:%S.%fZ")
# 3. Round-trip payload : check de coherence
# 4. Validation format hash

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone

HASH_RE = re.compile(r"^[0-9a-f]{64}$")


def _normalize_ts(dt: datetime) -> str:
    """Figera le format timestamp des deux cotes (insert + audit)."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _canonicalize_event(event: dict) -> bytes:
    """Canonicalisation JCS (RFC 8785) de l'evenement pour le hash."""
    try:
        import rfc8785
    except ImportError as exc:
        raise RuntimeError(
            "rfc8785 obligatoire pour la chaine de hachage."
        ) from exc
    return rfc8785.dumps(event)


def _hash_event(event: dict) -> str:
    canonical = _canonicalize_event(event)
    return hashlib.sha256(canonical).hexdigest()


def _build_hashable_event(
    *,
    key_id, actor_id, from_status, to_status,
    event_type, reason, compromised_since,
    decision_attestation_id, recorded_by, recorded_at_normalized,
    previous_event_hash,
) -> dict:
    """Construit le dict canonique qui sera hashé.

    L'ordre des cles est determine par JCS (RFC 8785), pas par l'ordre
    d'insertion. Le timestamp est deja normalise.
    """
    event = {
        "key_id": key_id,
        "actor_id": actor_id,
        "from_status": from_status,
        "to_status": to_status,
        "event_type": event_type,
        "reason": reason,
        "compromised_since": compromised_since,
        "decision_attestation_id": decision_attestation_id,
        "recorded_by": recorded_by,
        "recorded_at": recorded_at_normalized,
        "previous_event_hash": previous_event_hash,
    }
    # Retirer les cles None pour un hash stable
    return {k: v for k, v in event.items() if v is not None}


def _check_payload_roundtrip(payload_obj: dict) -> None:
    """Verifie que le payload survive a un round-trip JSON sans perte.

    Detecte les flottants non round-trippables et les normalisations
    Unicode qui produiraient un hash divergent sans alteration reelle.
    """
    serialized = json.dumps(payload_obj, ensure_ascii=False, sort_keys=True)
    reparsed = json.loads(serialized)
    reserialized = json.dumps(reparsed, ensure_ascii=False, sort_keys=True)
    if serialized != reserialized:
        raise RuntimeError(
            "Round-trip JSON non lossless pour le payload. "
            "Le hash d'audit divergerait sans alteration reelle. "
            "Causes probables : flottant non round-trippable, "
            "normalisation Unicode, ou tri de cles instable."
        )


def append_key_lifecycle_event(
    con,
    *,
    key_id: str,
    actor_id: str,
    from_status: str | None,
    to_status: str,
    event_type: str,
    reason: str | None = None,
    compromised_since: str | None = None,
    decision_attestation_id: str | None = None,
    recorded_by: str,
    recorded_at: datetime | None = None,
    now_iso: str | None = None,
    payload_obj: dict | None = None,
):
    """Ajoute un evenement dans la chaine avec hachage et verrou.

    Transaction + chain_lock pour eviter la course critique.
    UNIQUE(previous_event_hash) rejette les fourches au niveau schema.

    Args:
        payload_obj: dict optionnel a verifier en round-trip avant insertion.
        now_iso: fallback si recorded_at est None (compat ascendante).
    """
    # Normaliser le timestamp
    if recorded_at is not None:
        recorded_at_normalized = _normalize_ts(recorded_at)
    elif now_iso is not None:
        # Compat ascendante : normaliser aussi le fallback
        recorded_at_normalized = now_iso
    else:
        recorded_at_normalized = _normalize_ts(datetime.now(timezone.utc))

    # Verifier le round-trip du payload si fourni
    if payload_obj is not None:
        _check_payload_roundtrip(payload_obj)

    event_id = f"kh_{uuid.uuid4().hex}"

    con.execute("BEGIN TRANSACTION")
    try:
        # Acquerir le verrou applicatif
        con.execute(
            "UPDATE chain_lock SET holder = ?, acquired_at = ? WHERE lock_id = 1",
            [event_id, recorded_at_normalized],
        )

        # Trouver le tip (dernier bloc de la chaine)
        last = con.execute(
            """
            SELECT current_event_hash, event_id
            FROM key_lifecycle_history
            WHERE current_event_hash IS NOT NULL
            ORDER BY recorded_at DESC, event_id DESC
            LIMIT 1
            """,
        ).fetchone()

        if last is None:
            previous_event_hash = None  # bloc de genese
        else:
            previous_event_hash = last[0]
            if not HASH_RE.match(previous_event_hash):
                raise RuntimeError(
                    f"Tip corrompu : current_event_hash invalide = {previous_event_hash}"
                )

        # Construire l'evenement canonique et le hasher
        hashable = _build_hashable_event(
            key_id=key_id,
            actor_id=actor_id,
            from_status=from_status,
            to_status=to_status,
            event_type=event_type,
            reason=reason,
            compromised_since=compromised_since,
            decision_attestation_id=decision_attestation_id,
            recorded_by=recorded_by,
            recorded_at_normalized=recorded_at_normalized,
            previous_event_hash=previous_event_hash,
        )

        current_event_hash = _hash_event(hashable)

        if not HASH_RE.match(current_event_hash):
            raise RuntimeError(
                f"Hash calcule invalide : {current_event_hash}"
            )

        # Inserer (UNIQUE sur previous_event_hash rejette les fourches)
        con.execute(
            """
            INSERT INTO key_lifecycle_history (
                event_id, key_id, actor_id, from_status, to_status,
                event_type, reason, compromised_since,
                decision_attestation_id, recorded_by, recorded_at,
                current_event_hash, previous_event_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                event_id, key_id, actor_id, from_status, to_status,
                event_type, reason, compromised_since,
                decision_attestation_id, recorded_by, recorded_at_normalized,
                current_event_hash, previous_event_hash,
            ],
        )

        # Liberer le verrou
        con.execute(
            "UPDATE chain_lock SET holder = NULL, acquired_at = NULL WHERE lock_id = 1",
        )

        con.execute("COMMIT")
    except Exception:
        con.execute("ROLLBACK")
        raise

    return {
        "event_id": event_id,
        "current_event_hash": current_event_hash,
        "previous_event_hash": previous_event_hash,
    }


def publish_tip_anchor(
    con,
    *,
    tip_hash: str,
    tip_event_id: str,
    published_by: str,
    source: str = "manual",
    external_ref: str | None = None,
    notes: str | None = None,
):
    """Publie le tip_hash dans un journal d'ancrage externe.

    L'audit comparera le tip observe au dernier tip publie pour
    detecter une troncature de la fin de chaine.
    """
    if not HASH_RE.match(tip_hash):
        raise RuntimeError(f"tip_hash invalide : {tip_hash}")

    anchor_id = f"ta_{uuid.uuid4().hex}"
    now = _normalize_ts(datetime.now(timezone.utc))

    con.execute(
        """
        INSERT INTO tip_anchors (
            anchor_id, tip_hash, tip_event_id,
            published_by, published_at, source, external_ref, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [anchor_id, tip_hash, tip_event_id, published_by, now,
         source, external_ref, notes],
    )
    return {"anchor_id": anchor_id, "tip_hash": tip_hash}
