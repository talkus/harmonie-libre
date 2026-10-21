"""Local release-file checks. These checks are not machine attestation."""
import hashlib
import json
import os
import re
from pathlib import Path

HEX64 = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)
COMMIT = re.compile(r"[0-9a-f]{40}\Z", re.ASCII)
RELATIVE = re.compile(r"[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*\Z", re.ASCII)


class ReleaseCheckError(ValueError):
    pass


def no_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ReleaseCheckError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def read_json(path, limit):
    try:
        raw = path.read_bytes()
        if not 1 <= len(raw) <= limit:
            raise ReleaseCheckError("RELEASE_METADATA_SIZE")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=no_duplicate_keys)
    except (OSError, UnicodeError, ValueError) as exc:
        raise ReleaseCheckError("RELEASE_METADATA_UNAVAILABLE_OR_INVALID") from exc
    if type(value) is not dict:
        raise ReleaseCheckError("RELEASE_METADATA_SHAPE")
    return raw, value


def load_release(root=None):
    root = Path(root).resolve() if root is not None else Path(__file__).resolve().parent
    raw, manifest = read_json(root / "release-source.json", 100000)
    _, info = read_json(root / "build-info.json", 4096)
    if set(manifest) != {"schema", "files"} or manifest["schema"] != "SOL_ACTION_RELEASE_SOURCE/v1":
        raise ReleaseCheckError("RELEASE_MANIFEST_SCHEMA")
    if set(info) != {"schema", "source_commit"} or info["schema"] != "SOL_ACTION_BUILD_INFO/v1" or type(info["source_commit"]) is not str or not COMMIT.fullmatch(info["source_commit"]):
        raise ReleaseCheckError("BUILD_INFO_SCHEMA")
    files = manifest["files"]
    if type(files) is not dict or not 1 <= len(files) <= 128 or not {"api/job.py", "bridge_runtime.py"}.issubset(files):
        raise ReleaseCheckError("RELEASE_FILES_SHAPE")
    actual = {}
    for relative, expected in files.items():
        if type(relative) is not str or len(relative) > 180 or not RELATIVE.fullmatch(relative) or any(part in {".", ".."} for part in relative.split("/")) or relative in {"release-source.json", "build-info.json"}:
            raise ReleaseCheckError("RELEASE_PATH")
        if type(expected) is not str or not HEX64.fullmatch(expected):
            raise ReleaseCheckError("RELEASE_HASH_SHAPE")
        path = (root / relative).resolve()
        if root not in path.parents or not path.is_file():
            raise ReleaseCheckError("RELEASE_FILE_MISSING_OR_OUTSIDE_ROOT")
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise ReleaseCheckError("RELEASE_FILE_UNREADABLE") from exc
        if len(content) > 1048576:
            raise ReleaseCheckError("RELEASE_FILE_SIZE")
        actual[relative] = hashlib.sha256(content).hexdigest()
        if actual[relative] != expected:
            raise ReleaseCheckError("RELEASE_FILE_HASH_MISMATCH")
    manifest_hash = hashlib.sha256(raw).hexdigest()
    commit = info["source_commit"]
    return {"manifest_hash": manifest_hash, "source_commit": commit,
            "release_hash": hashlib.sha256((manifest_hash + ":" + commit).encode("ascii")).hexdigest(),
            "self_hash": actual["api/job.py"], "files": actual}


def server_token():
    token = os.environ.get("SOL_BRIDGE_TOKEN", "")
    if not HEX64.fullmatch(token):
        raise ReleaseCheckError("BRIDGE_SERVER_TOKEN_UNAVAILABLE")
    return token
