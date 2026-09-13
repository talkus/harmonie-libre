# attest/audit_chain.py
# Audit de la chaine de hachage de key_lifecycle_history.
#
# Correctifs revue :
# 1. Propagation en cascade : prev_calculated_hash = recalculated_curr_hash
#    (forensiquement utile pour representer jusqu'ou la chaine est contaminee)
# 2. Normalisation du timestamp des deux cotes
# 3. Validation du format des hashes (^[0-9a-f]{64}$)
# 4. Ancrage externe : validation que le tip observe est descendant du
#    dernier tip publie dans tip_anchors
# 5. Exception handling : elargi (duckdb.IOException, etc.)
# 6. KeyError journal vide : toutes les cles presentes dans le retour

import hashlib
import json
import re
import sys
from datetime import datetime, timezone

HASH_RE = re.compile(r"^[0-9a-f]{64}$")

# Codes de retour
EXIT_PASSED = 0
EXIT_VIOLATIONS = 1
EXIT_ERROR = 2


def _normalize_ts(dt) -> str:
    """Figera le format timestamp pour la comparaison."""
    if isinstance(dt, str):
        # Si c'est deja une string, normaliser via parse
        dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")


def _canonicalize_event(event: dict) -> bytes:
    try:
        import rfc8785
    except ImportError as exc:
        raise RuntimeError("rfc8785 obligatoire pour l'audit.") from exc
    return rfc8785.dumps(event)


def _hash_event(event: dict) -> str:
    return hashlib.sha256(_canonicalize_event(event)).hexdigest()


def _build_hashable_event(row) -> dict:
    """Reconstruit le dict canonique a partir d'une ligne de la base.

    L'ordre des cles est determine par JCS. Le timestamp est renormalise.
    """
    (event_id, key_id, actor_id, from_status, to_status,
     event_type, reason, compromised_since,
     decision_attestation_id, recorded_by, recorded_at,
     current_event_hash, previous_event_hash) = row

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
        "recorded_at": _normalize_ts(recorded_at),
        "previous_event_hash": previous_event_hash,
    }
    return {k: v for k, v in event.items() if v is not None}


def _validate_hash_format(h: str | None, field_name: str) -> str | None:
    """Retourne un message de violation si le format est invalide, sinon None."""
    if h is None:
        return None
    if not HASH_RE.match(h):
        return f"{field_name} format invalide : {h!r} (attendu ^[0-9a-f]{{64}}$)"
    return None


def _is_descendant_of(con, tip_event_id: str, anchor_event_id: str) -> bool:
    """Verifie que tip_event_id est un descendant de anchor_event_id
    dans la chaine (en remontant les previous_event_hash)."""
    if tip_event_id == anchor_event_id:
        return True

    current = tip_event_id
    visited = set()
    while current is not None and current not in visited:
        visited.add(current)
        row = con.execute(
            """
            SELECT event_id, previous_event_hash
            FROM key_lifecycle_history
            WHERE event_id = ?
            """,
            [current],
        ).fetchone()
        if row is None:
            return False
        event_id, prev_hash = row
        if event_id == anchor_event_id:
            return True
        if prev_hash is None:
            return False  # on a atteint la genese sans trouver l'ancre
        # Trouver l'event_id correspondant au previous_event_hash
        prev_row = con.execute(
            "SELECT event_id FROM key_lifecycle_history WHERE current_event_hash = ?",
            [prev_hash],
        ).fetchone()
        if prev_row is None:
            return False
        current = prev_row[0]
    return False


def audit_chain(con, *, check_tip_anchor: bool = True) -> dict:
    """Audite la chaine de hachage de key_lifecycle_history.

    Retourne un dict avec toutes les cles presentes (meme en cas d'erreur
    ou de journal vide) pour eviter les KeyError cote appelant.

    Returns:
        {
            "status": "PASSED" | "VIOLATIONS" | "ERROR",
            "total_events": int,
            "violations_count": int,
            "violations": list[str],
            "tip_hash": str | None,
            "tip_event_id": str | None,
            "anchor_validated": bool | None,
        }
    """
    result = {
        "status": "PASSED",
        "total_events": 0,
        "violations_count": 0,
        "violations": [],
        "tip_hash": None,
        "tip_event_id": None,
        "anchor_validated": None,
    }

    try:
        rows = con.execute(
            """
            SELECT event_id, key_id, actor_id, from_status, to_status,
                   event_type, reason, compromised_since,
                   decision_attestation_id, recorded_by, recorded_at,
                   current_event_hash, previous_event_hash
            FROM key_lifecycle_history
            WHERE current_event_hash IS NOT NULL
            ORDER BY recorded_at ASC, event_id ASC
            """,
        ).fetchall()
    except Exception as exc:
        result["status"] = "ERROR"
        result["violations"].append(f"Erreur de lecture : {exc}")
        result["violations_count"] = 1
        return result

    result["total_events"] = len(rows)

    if len(rows) == 0:
        # Journal vide : PASSED, toutes les cles presentes
        return result

    violations = []
    prev_calculated_hash = None  # hash du bloc precedent, RECALCULE
    prev_event_id = None

    for i, row in enumerate(rows):
        event_id = row[0]
        stored_curr_hash = row[11]
        stored_prev_hash = row[12]

        # --- Validation du format des hashes ---
        fmt_err = _validate_hash_format(stored_curr_hash, "current_event_hash")
        if fmt_err:
            violations.append(f"Bloc {i} ({event_id}): {fmt_err}")

        fmt_err = _validate_hash_format(stored_prev_hash, "previous_event_hash")
        if fmt_err:
            violations.append(f"Bloc {i} ({event_id}): {fmt_err}")

        # --- Verification du lien (previous_event_hash) ---
        if i == 0:
            # Bloc de genese : previous_event_hash doit etre NULL
            if stored_prev_hash is not None:
                violations.append(
                    f"Bloc 0 ({event_id}): genese avec previous_event_hash non-NULL = {stored_prev_hash}"
                )
        else:
            # Le previous_event_hash stocke doit etre egal au hash RECALCULE
            # du bloc precedent (propagation en cascade)
            if stored_prev_hash != prev_calculated_hash:
                violations.append(
                    f"Bloc {i} ({event_id}): BROKEN_CHAIN_LINK "
                    f"previous_event_hash stocke = {stored_prev_hash}, "
                    f"hash recalcule du precedent = {prev_calculated_hash}"
                )

        # --- Recalcul du hash du bloc courant ---
        try:
            hashable = _build_hashable_event(row)
            recalculated_curr_hash = _hash_event(hashable)
        except Exception as exc:
            violations.append(
                f"Bloc {i} ({event_id}): echec de recalcul du hash : {exc}"
            )
            recalculated_curr_hash = None

        if recalculated_curr_hash is not None and stored_curr_hash != recalculated_curr_hash:
            violations.append(
                f"Bloc {i} ({event_id}): PAYLOAD_TAMPERING "
                f"hash stocke = {stored_curr_hash}, "
                f"hash recalcule = {recalculated_curr_hash}"
            )

        # --- Propagation en cascade ---
        # On utilise recalculated_curr_hash (pas stored_curr_hash) pour
        # que la contamination se propage forensiquement jusqu'au bout.
        prev_calculated_hash = recalculated_curr_hash
        prev_event_id = event_id

    # --- Tip ---
    last_row = rows[-1]
    result["tip_hash"] = last_row[11]
    result["tip_event_id"] = last_row[0]

    # --- Validation de l'ancrage externe du tip ---
    if check_tip_anchor:
        try:
            anchor_row = con.execute(
                """
                SELECT tip_hash, tip_event_id
                FROM tip_anchors
                ORDER BY published_at DESC
                LIMIT 1
                """,
            ).fetchone()

            if anchor_row is not None:
                anchor_tip_hash, anchor_event_id = anchor_row
                # Le tip observe doit etre un descendant du tip ancre
                is_descendant = _is_descendant_of(con, result["tip_event_id"], anchor_event_id)
                if not is_descendant:
                    violations.append(
                        f"TRUNCATION_DETECTED : tip observe ({result['tip_event_id']}) "
                        f"n'est pas un descendant du dernier tip ancre ({anchor_event_id}). "
                        f"Possible troncature de la fin de chaine."
                    )
                result["anchor_validated"] = is_descendant
            else:
                result["anchor_validated"] = None  # pas d'ancre publiee
        except Exception as exc:
            violations.append(
                f"Erreur lors de la validation de l'ancrage : {exc}"
            )
            result["anchor_validated"] = False

    result["violations"] = violations
    result["violations_count"] = len(violations)
    result["status"] = "VIOLATIONS" if violations else "PASSED"

    return result


def main():
    """CLI entry point pour l'audit.

    Codes de retour :
        0 = PASSED (chaine valide)
        1 = VIOLATIONS (alterations detectees)
        2 = ERROR (erreur d'execution)
    """
    import argparse
    import duckdb

    parser = argparse.ArgumentParser(
        description="Audit de la chaine de hachage du cycle de vie des cles"
    )
    parser.add_argument("--db", required=True, help="Chemin vers le fichier DuckDB")
    parser.add_argument("--json", action="store_true", help="Sortie JSON exploitable par n8n")
    parser.add_argument("--no-anchor-check", action="store_true",
                        help="Desactiver la validation de l'ancrage externe du tip")
    args = parser.parse_args()

    try:
        con = duckdb.connect(args.db, read_only=True)
    except Exception as exc:
        print(f"ERROR: Impossible d'ouvrir la base : {exc}", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    try:
        report = audit_chain(con, check_tip_anchor=not args.no_anchor_check)
    except Exception as exc:
        # Capturer TOUTES les exceptions, pas seulement CatalogException
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(EXIT_ERROR)
    finally:
        con.close()

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(f"Status: {report['status']}")
        print(f"Events: {report['total_events']}")
        print(f"Violations: {report['violations_count']}")
        if report["tip_hash"]:
            print(f"Tip hash: {report['tip_hash'][:16]}...")
        if report["anchor_validated"] is not None:
            print(f"Anchor validated: {report['anchor_validated']}")
        for v in report["violations"]:
            print(f"  - {v}")

    if report["status"] == "PASSED":
        sys.exit(EXIT_PASSED)
    elif report["status"] == "VIOLATIONS":
        sys.exit(EXIT_VIOLATIONS)
    else:
        sys.exit(EXIT_ERROR)


if __name__ == "__main__":
    main()
