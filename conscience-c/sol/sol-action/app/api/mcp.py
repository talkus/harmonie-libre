"""Public, read-only MCP surface. No job, capability, token, network call or mutation."""
import hashlib
import json
import re
from http.server import BaseHTTPRequestHandler
from pathlib import Path

VERSION = "0.3.0"
PROTOCOLS = {"2025-03-26", "2025-06-18", "2025-11-25"}
ORIGIN = "https://sol-action-verifiee.vercel.app"
LIMIT = 16384

TOOL = {
    "name": "release_manifest",
    "title": "Version publique du service SOL-Action",
    "description": "Read hashes of the listed bundled server files and the pinned GitHub commit. CDN assets are checked separately at deployment time. Read-only; no job data or correctness certificate.",
    "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    "outputSchema": {"type": "object", "properties": {"available": {"type": "boolean"}, "release_hash": {"type": "string"}, "source_commit": {"type": "string"}, "source_files": {"type": "object"}, "file_scope": {"type": "string", "const": "BUNDLED_SERVER_FILES_ONLY"}, "source_repository": {"type": "string"}, "source_directory": {"type": "string"}, "does_not_establish": {"type": "array", "items": {"type": "string"}}}, "required": ["available", "release_hash", "source_commit", "source_files", "file_scope", "source_repository", "source_directory", "does_not_establish"], "additionalProperties": False},
    "annotations": {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
}


def bundle_diagnostics(base=None):
    """Only public source filenames and hashes; no directory scan, env, CSV or secret."""
    root = Path(base) if base else Path(__file__).resolve().parents[1]
    checks = {}
    for name in ("release-source.json", "build-info.json", "api/job.py", "api/mcp.py", "bridge_runtime.py", "vercel.json"):
        try:
            content = (root / name).read_bytes()
            checks[name] = {"readable": True, "sha256": hashlib.sha256(content).hexdigest()}
        except OSError:
            checks[name] = {"readable": False}
    return checks


def release_manifest(base=None):
    root = Path(base) if base else Path(__file__).resolve().parents[1]
    raw = (root / "release-source.json").read_bytes()
    if len(raw) > 65536:
        raise ValueError("RELEASE_UNAVAILABLE")
    source = json.loads(raw)
    build = json.loads((root / "build-info.json").read_bytes())
    commit = build.get("source_commit")
    if not isinstance(commit, str) or not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("RELEASE_UNAVAILABLE")
    if source.get("schema") != "SOL_ACTION_RELEASE_SOURCE/v1" or not isinstance(source.get("files"), dict):
        raise ValueError("RELEASE_UNAVAILABLE")
    files = source["files"]
    if not files or len(files) > 40 or "api/mcp.py" not in files or "api/job.py" not in files:
        raise ValueError("RELEASE_UNAVAILABLE")
    for name, expected in files.items():
        if not isinstance(name, str) or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected):
            raise ValueError("RELEASE_UNAVAILABLE")
        path = root / name
        if name.startswith("/") or ".." in Path(name).parts or path.is_symlink() or root.resolve() not in path.resolve().parents:
            raise ValueError("RELEASE_UNAVAILABLE")
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise ValueError("RELEASE_UNAVAILABLE")
    digest = hashlib.sha256(raw).hexdigest()
    release_hash = hashlib.sha256((digest + ":" + commit).encode("ascii")).hexdigest()
    return {"available": True, "release_hash": release_hash, "source_commit": commit, "source_files": files, "file_scope": "BUNDLED_SERVER_FILES_ONLY", "source_repository": "https://github.com/talkus/harmonie-libre", "source_directory": "conscience-c/sol/sol-action",
            "does_not_establish": ["Correctness of CSV inputs or totals", "Semantic satisfaction of a general mandate", "Independent runtime or machine attestation", "Runtime reading of CDN assets; their HTTP checks are separate and dated", "Safety or conduct of unlisted tools", "Unchanging future deployment"]}


def dispatch(message, loader=release_manifest):
    if not isinstance(message, dict) or message.get("jsonrpc") != "2.0" or not isinstance(message.get("method"), str):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request"}}
    ident = message.get("id")
    if ident is not None and (type(ident) not in (str, int) or (type(ident) is int and abs(ident) > 9007199254740991)):
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32600, "message": "Invalid request identifier"}}
    method = message["method"]
    if "id" not in message:
        return None
    params = message.get("params", {})
    if not isinstance(params, dict):
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32602, "message": "Object params required"}}
    if method == "initialize":
        requested = params.get("protocolVersion")
        result = {"protocolVersion": requested if isinstance(requested, str) and requested in PROTOCOLS else "2025-11-25", "capabilities": {"tools": {}}, "serverInfo": {"name": "sol-action-release", "version": VERSION}, "instructions": "Public release metadata only. No job data or execution. Conformance is not correctness."}
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": [TOOL]}
    elif method == "tools/call":
        if params.get("name") != "release_manifest" or params.get("arguments", {}) != {}:
            result = {"isError": True, "content": [{"type": "text", "text": "Unsupported tool or arguments"}]}
        else:
            try:
                value = loader()
                result = {"isError": False, "structuredContent": value, "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))}]}
            except Exception:
                failure = {"available": False, "reason": "Release metadata unavailable or integrity mismatch. No verdict is established.", "public_source_file_diagnostics": bundle_diagnostics()}
                result = {"isError": True, "content": [{"type": "text", "text": json.dumps(failure, sort_keys=True, separators=(",", ":"))}]}
    else:
        return {"jsonrpc": "2.0", "id": ident, "error": {"code": -32601, "message": "Method not found"}}
    return {"jsonrpc": "2.0", "id": ident, "result": result}


class handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def reply(self, status, value=None):
        raw = b"" if value is None else json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Allow", "POST, GET, OPTIONS")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        if raw:
            self.wfile.write(raw)

    def allowed_origin(self):
        return self.headers.get("Origin") in (None, ORIGIN)

    def allowed_protocol(self):
        return self.headers.get("MCP-Protocol-Version", "2025-03-26") in PROTOCOLS

    def do_POST(self):
        if not self.allowed_origin():
            self.reply(403, {"error": "ORIGIN_NOT_ALLOWED"})
            return
        if not self.allowed_protocol():
            self.reply(400, {"error": "UNSUPPORTED_PROTOCOL_VERSION"})
            return
        try:
            if "?" in self.path or self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
                raise ValueError("Invalid request")
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= LIMIT:
                self.reply(413, {"error": "BODY_SIZE"})
                return
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise ValueError("Invalid body")
            message = json.loads(raw.decode("utf-8"))
            answer = dispatch(message)
            self.reply(202 if answer is None else 200, answer)
        except Exception:
            self.reply(400, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})

    def do_GET(self):
        self.reply(403 if not self.allowed_origin() else 405 if self.allowed_protocol() else 400)

    def do_OPTIONS(self):
        self.reply(403 if not self.allowed_origin() else 204 if self.allowed_protocol() else 400)
