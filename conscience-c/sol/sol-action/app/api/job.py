"""Fixed CSV worker and capability-scoped RPC bridge. No arbitrary code or URLs."""
import csv
import hashlib
import io
import json
import os
import re
import urllib.error
import urllib.request
import uuid
from decimal import Decimal, localcontext
from http.server import BaseHTTPRequestHandler
from pathlib import Path
import sys

# Fixed application-local helper, included explicitly in the deployment bundle.
_BRIDGE_ROOT = Path(__file__).resolve().parents[1]
if str(_BRIDGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_BRIDGE_ROOT))
import bridge_runtime

WORKER_VERSION = "SOL-ACTION-PY/0.1.0"
PROJECT_URL = "https://jljelwrblfitvjbmrykx.supabase.co"
# Public anon credential only; embedded because CDN assets are absent from the Python bundle.
PUBLIC_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImpsamVsd3JibGZpdHZqYm1yeWt4Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODk1OTEyMTIsImV4cCI6MjEwNTE2NzIxMn0.SdG9TCcSOpXEPEVhZiXWwSPlZFxrXXnnxK6rLfSe3SQ'
MAX_BODY = 180000
MAX_SOURCE = 32768
ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,79}\Z", re.ASCII)
CURRENCY = re.compile(r"[A-Z]{3}\Z", re.ASCII)
AMOUNT = re.compile(r"[+-]?[0-9]{1,12}(?:\.[0-9]{1,2})?\Z", re.ASCII)
CAP = re.compile(r"[0-9a-f]{64}\Z", re.ASCII)


class InputError(ValueError):
    pass


class UncertainOutcome(Exception):
    pass


def unique_object(pairs):
    """Reject ambiguous JSON before choosing which occurrence to trust."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("DUPLICATE_JSON_KEY")
        result[key] = value
    return result


def correlated_response(response, action, data):
    """Check the original envelope; never invent an identity or an effect."""
    if type(response) is not dict or type(response.get("ok")) is not bool:
        raise UncertainOutcome("RPC_RESPONSE_SHAPE")
    claims_reference = response["ok"] or any(key in response for key in
        ("job_id", "request_id", "target_request_id", "receipt", "effect", "sqlstate", "durable_refusal", "terminal"))
    if not claims_reference:
        # An opaque denial grants no correlation or absence-of-effect claim.
        return response
    if response.get("job_id") != data["job_id"]:
        raise UncertainOutcome("RPC_JOB_CORRELATION_UNKNOWN")
    if action in {"receipt", "creation_receipt"}:
        if response.get("action") != "lookup_receipt" or response.get("target_request_id") != data["target_request_id"]:
            raise UncertainOutcome("RPC_RECEIPT_CORRELATION_UNKNOWN")
    elif action in {"create", "verify", "complete", "reconcile"}:
        if response.get("action") != action or response.get("request_id") != data["request_id"]:
            raise UncertainOutcome("RPC_COMMAND_CORRELATION_UNKNOWN")
    return response


def compute_csv(source):
    """Produce exact Decimal totals; the separate SQL implementation verifies them."""
    if type(source) is not str or not 1 <= len(source.encode("utf-8")) <= MAX_SOURCE:
        raise InputError("CSV_SIZE")
    if "\x00" in source or "\ufeff" in source:
        raise InputError("CSV_ENCODING")
    # csv.reader(strict=True) alone accepts unescaped quotes in unquoted fields.
    # Validate quote placement before using the standard RFC-style reader.
    state = "start"
    i = 0
    while i < len(source):
        char = source[i]
        if state == "quoted":
            if char == '"':
                state = "after_quote"
        elif state == "after_quote":
            if char == '"':
                state = "quoted"
            elif char == ',':
                state = "start"
            elif char in "\r\n":
                state = "start"
                if char == '\r':
                    if i + 1 >= len(source) or source[i + 1] != '\n':
                        raise InputError("CSV_LINE_ENDING")
                    i += 1
            else:
                raise InputError("CSV_QUOTING")
        elif char == '"':
            if state != "start":
                raise InputError("CSV_QUOTING")
            state = "quoted"
        elif char == ',':
            state = "start"
        elif char in "\r\n":
            state = "start"
            if char == '\r':
                if i + 1 >= len(source) or source[i + 1] != '\n':
                    raise InputError("CSV_LINE_ENDING")
                i += 1
        else:
            state = "unquoted"
        i += 1
    if state == "quoted":
        raise InputError("CSV_QUOTING")
    try:
        parsed = list(csv.reader(io.StringIO(source, newline=""), strict=True))
    except csv.Error as exc:
        raise InputError("CSV_QUOTING") from exc
    if not parsed or parsed[0] != ["id", "currency", "amount"]:
        raise InputError("CSV_HEADER")
    rows = parsed[1:]
    if not 1 <= len(rows) <= 500:
        raise InputError("CSV_ROWS")
    row_ids = []
    seen = set()
    totals = {}
    with localcontext() as context:
        context.prec = 40
        for row in rows:
            if len(row) != 3:
                raise InputError("CSV_COLUMNS")
            ident, currency, raw_amount = row
            if not ID.fullmatch(ident):
                raise InputError("CSV_ID")
            if ident in seen:
                raise InputError("CSV_DUPLICATE_ID")
            if not CURRENCY.fullmatch(currency):
                raise InputError("CSV_CURRENCY")
            if not AMOUNT.fullmatch(raw_amount):
                raise InputError("CSV_AMOUNT")
            seen.add(ident)
            row_ids.append(ident)
            totals[currency] = totals.get(currency, Decimal(0)) + Decimal(raw_amount)
        amounts = [{"currency": key, "amount": format(value if value else Decimal(0), ".2f")}
                   for key, value in sorted(totals.items())]
    return {"source_sha256": hashlib.sha256(source.encode("utf-8")).hexdigest(),
            "rows": len(rows), "row_ids": row_ids, "totals": amounts}


def exact_keys(value, allowed, required):
    if type(value) is not dict or set(value) - set(allowed) or set(required) - set(value):
        raise InputError("INVALID_FIELDS")


def valid_uuid(value):
    if type(value) is not str:
        raise InputError("INVALID_UUID")
    try:
        parsed = uuid.UUID(value)
    except (ValueError, AttributeError) as exc:
        raise InputError("INVALID_UUID") from exc
    if str(parsed) != value:
        raise InputError("INVALID_UUID")


def validate_request(body):
    exact_keys(body, ["action", "input"], ["action", "input"])
    action = body["action"]
    if type(action) is not str or action not in {"create", "status", "produce", "verify", "complete", "reconcile", "audit", "receipt", "creation_receipt"}:
        raise InputError("UNKNOWN_ACTION")
    data = body["input"]
    common = ["job_id", "capability"]
    extra = {
        "create": ["request_id", "mandate", "requirements", "source_csv", "source_origin", "parent_job_id", "parent_capability"],
        "produce": ["request_id", "result_request_id", "expected_step_id"],
        "verify": ["request_id", "expected_step_id"],
        "complete": ["request_id", "expected_step_id"],
        "reconcile": ["request_id", "production_request_id", "target_request_id"],
        "status": [], "audit": [], "receipt": ["target_request_id"], "creation_receipt": ["target_request_id"]
    }[action]
    required = common + ([] if action in {"status", "audit", "receipt", "creation_receipt"} else ["request_id"])
    exact_keys(data, common + extra, required)
    valid_uuid(data["job_id"])
    if type(data["capability"]) is not str or not CAP.fullmatch(data["capability"]):
        raise InputError("INVALID_CAPABILITY")
    for field in ["request_id", "result_request_id", "production_request_id", "target_request_id", "parent_job_id"]:
        if field in data:
            valid_uuid(data[field])
    if action in {"produce", "verify", "complete"}:
        if data.get("expected_step_id") != action:
            raise InputError("EXPECTED_STEP_REQUIRED")
    if action in {"receipt", "creation_receipt"} and "target_request_id" not in data:
        raise InputError("ORIGINAL_REQUEST_REQUIRED")
    if action == "produce" and "result_request_id" not in data:
        raise InputError("RESULT_REQUEST_REQUIRED")
    if action == "reconcile" and not ("production_request_id" in data or "target_request_id" in data):
        raise InputError("ORIGINAL_REQUEST_REQUIRED")
    if action == "create":
        if ("parent_job_id" in data) != ("parent_capability" in data):
            raise InputError("PARENT_ACCESS_REQUIRED")
        if "parent_capability" in data and (type(data["parent_capability"]) is not str or not CAP.fullmatch(data["parent_capability"]) or data["parent_capability"] == data["capability"]):
            raise InputError("INVALID_PARENT_CAPABILITY")
        if type(data.get("mandate")) is not str or not 1 <= len(data["mandate"].strip()) <= 10000:
            raise InputError("INVALID_MANDATE")
        requirements = data.get("requirements")
        if type(requirements) is not list or not 1 <= len(requirements) <= 32 or any(type(x) is not str or not 1 <= len(x) <= 2000 for x in requirements):
            raise InputError("INVALID_REQUIREMENTS")
        source = data.get("source_csv")
        if type(source) is not str or not 1 <= len(source.encode("utf-8")) <= MAX_SOURCE:
            raise InputError("CSV_SIZE")
        origin = data.get("source_origin")
        exact_keys(origin, ["kind", "provider", "reference"], ["kind"])
        if origin["kind"] != "declared":
            # Browser claims never acquire connector provenance.
            raise InputError("CONNECTOR_PROVENANCE_NOT_ACCEPTED_FROM_BROWSER")
        for key in ["provider", "reference"]:
            if key in origin and (type(origin[key]) is not str or not 1 <= len(origin[key]) <= 1000):
                raise InputError("INVALID_ORIGIN")
    return action, data


def public_configuration():
    path = Path(__file__).resolve().parents[1] / "public" / "config.json"
    try:
        config = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        config = {}
    url = os.environ.get("SUPABASE_URL") or config.get("supabase_url") or PROJECT_URL
    key = os.environ.get("SUPABASE_ANON_KEY") or config.get("supabase_anon_key") or PUBLIC_ANON_KEY
    if url != PROJECT_URL or type(key) is not str or not key or len(key) > 4096:
        raise InputError("SERVICE_NOT_CONFIGURED")
    # Even a configuration mistake must not load a service-role key.
    if key.startswith("eyJ"):
        import base64
        try:
            encoded = key.split(".")[1]
            claims = json.loads(base64.urlsafe_b64decode(encoded + "=" * (-len(encoded) % 4)))
        except (ValueError, IndexError) as exc:
            raise InputError("INVALID_PUBLIC_KEY") from exc
        if claims.get("role") != "anon":
            raise InputError("PRIVILEGED_KEY_FORBIDDEN")
    elif not key.startswith("sb_publishable_"):
        raise InputError("INVALID_PUBLIC_KEY")
    return url, key


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise UncertainOutcome("RPC_REDIRECT")


def rpc(action, data, api_name="sol_action_api"):
    if api_name not in {"sol_action_api", "sol_action_bridge_api", "sol_action_creation_api"}:
        raise InputError("RPC_NAME_FORBIDDEN")
    url, key = public_configuration()
    request = urllib.request.Request(url + "/rest/v1/rpc/" + api_name,
        data=json.dumps({"p_action": action, "p_input": data}, ensure_ascii=False, separators=(",", ":")).encode("utf-8"),
        headers={"Content-Type": "application/json", "apikey": key, "Authorization": "Bearer " + key}, method="POST")
    try:
        with urllib.request.build_opener(NoRedirect()).open(request, timeout=9) as response:
            raw = response.read(1048577)
        if len(raw) > 1048576:
            raise UncertainOutcome("RPC_RESPONSE_SIZE")
        result = json.loads(raw, object_pairs_hook=unique_object)
        if type(result) is not dict:
            raise UncertainOutcome("RPC_RESPONSE_SHAPE")
        return result
    except InputError:
        raise
    except Exception as exc:
        # HTTP/transport errors may occur after the transaction committed.
        raise UncertainOutcome("RPC_OUTCOME_UNKNOWN") from exc


def dispatch(body, call_rpc=rpc, worker=compute_csv, call_bridge=None,
             release_loader=bridge_runtime.load_release, token_loader=bridge_runtime.server_token,
             call_creation=None):
    action, data = validate_request(body)
    if call_bridge is None:
        call_bridge = lambda bridge_action, bridge_data: rpc(bridge_action, bridge_data, "sol_action_bridge_api")
    if call_creation is None:
        call_creation = lambda creation_action, creation_data: rpc(creation_action, creation_data, "sol_action_creation_api")
    if action == "creation_receipt":
        return correlated_response(call_creation("lookup_receipt", data), action, data)
    if action == "create":
        try:
            release = release_loader()
            token = token_loader()
        except Exception as exc:
            raise UncertainOutcome("RELEASE_OR_SERVER_CONFIGURATION_UNCONFIRMED") from exc
        response = call_creation("create_guarded", {
            "core_input": data, "bridge_token": token,
            "release_hash": release["release_hash"], "manifest_hash": release["manifest_hash"],
            "source_commit": release["source_commit"], "self_hash": release["self_hash"]})
        return correlated_response(response, action, data)
    if action == "receipt":
        return correlated_response(call_bridge("lookup_receipt", data), action, data)
    if action == "produce":
        try:
            release = release_loader()
            token = token_loader()
        except Exception as exc:
            raise UncertainOutcome("RELEASE_OR_SERVER_CONFIGURATION_UNCONFIRMED") from exc
        binding = call_bridge("bind", {
            "job_id": data["job_id"], "capability": data["capability"],
            "production_request_id": data["request_id"], "bridge_token": token,
            "release_hash": release["release_hash"], "manifest_hash": release["manifest_hash"],
            "source_commit": release["source_commit"], "self_hash": release["self_hash"]})
        # Bind and the unchanged core begin are committed in one bridge transaction.
        if (binding.get("ok") is not True or binding.get("status") != "BOUND_RELEASE"
                or binding.get("binding_granted") is not True or binding.get("deduplicated") is True
                or binding.get("job_id") != data["job_id"]
                or binding.get("production_request_id") != data["request_id"]
                or binding.get("release_hash") != release["release_hash"]
                or binding.get("self_hash") != release["self_hash"]
                or binding.get("binding_and_begin_atomic") is not True
                or type(binding.get("begin_receipt")) is not dict):
            return {"ok": False, "status": "OUTCOME_UNKNOWN", "action": "produce",
                    "job_id": data["job_id"], "request_id": data["request_id"],
                    "production_request_id": data["request_id"], "pending": True,
                    "error": "RELEASE_BINDING_NOT_NEWLY_GRANTED", "automatic_retry": False,
                    "current_reuse_authorized": False}
    if action != "produce":
        # The recovery boundary checks request collisions for every command.
        # Existing-job recovery remains in its pinned bridge. New creation uses
        # the additive, release-authorized boundary above, without a dummy job.
        if action in {"verify", "complete", "reconcile"}:
            response = call_bridge("execute", {"core_action": action, "core_input": data})
        else:
            response = call_rpc(action, data)
        return correlated_response(response, action, data)
    # Never issue a second begin: only the receipt returned by atomic bridge bind is used.
    begun = binding["begin_receipt"]
    if begun.get("ok") is False and begun.get("status") == "REJECTED" and type(begun.get("sqlstate")) is str:
        # Defensive response-shape guard: a conforming atomic bridge never grants this case.
        return {"ok": False, "status": "OUTCOME_UNKNOWN", "action": "produce",
                "job_id": data["job_id"], "request_id": data["request_id"],
                "production_request_id": data["request_id"], "pending": True,
                "error": "CORE_BEGIN_UNCONFIRMED_AFTER_RELEASE_BINDING",
                "automatic_retry": False, "current_reuse_authorized": False}
    # Deduplicated or ambiguous begin responses never run the worker again.
    if (begun.get("ok") is not True or begun.get("status") != "RECORDED"
            or begun.get("begin_granted") is not True or begun.get("deduplicated") is True):
        return begun
    if begun.get("production_request_id") != data["request_id"]:
        raise UncertainOutcome("BEGIN_CORRELATION_UNKNOWN")
    source = begun.get("source_csv")
    try:
        result = worker(source)
    except Exception as exc:
        # begin is already durable: a failed worker does not undo that intention.
        raise UncertainOutcome("WORKER_OUTCOME_UNKNOWN") from exc
    if result["source_sha256"] != begun.get("source_sha256"):
        raise UncertainOutcome("SOURCE_BINDING_UNKNOWN")
    committed = call_rpc("result", {
        "job_id": data["job_id"], "capability": data["capability"],
        "request_id": data["result_request_id"], "expected_step_id": "produce",
        "production_request_id": data["request_id"], "worker_version": WORKER_VERSION,
        "result": result})
    if committed.get("ok") is not True:
        # A rejected result transaction does not cancel the earlier durable begin.
        # Never forward its per-RPC no-effect marker as a composite no-effect claim.
        committed = {key: value for key, value in committed.items() if key not in {"effect", "effect_scope"}}
        committed.update({"ok": False, "status": "OUTCOME_UNKNOWN", "action": "result",
                          "job_id": data["job_id"], "request_id": data["result_request_id"],
                          "production_request_id": data["request_id"], "pending": True,
                          "production_started": True, "automatic_retry": False,
                          "current_reuse_authorized": False})
    return committed


class handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        # Never log CSV, capability, body, URL queries, or raw backend errors.
        pass

    def reply(self, code, value):
        payload = json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        if "?" in self.path:
            self.reply(400, {"ok": False, "status": "REJECTED", "error": "GET_JOB_DATA_FORBIDDEN"})
            return
        self.reply(200, {"ok": True, "status": "AVAILABLE", "worker_version": WORKER_VERSION,
                         "capabilities": ["bounded_csv_decimal", "capability_scoped_rpc"],
                         "semantic_truth": "UNKNOWN", "automatic_retry": False})

    def do_POST(self):
        try:
            if "?" in self.path:
                raise InputError("QUERY_FORBIDDEN")
            if self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
                raise InputError("JSON_REQUIRED")
            length = int(self.headers.get("Content-Length", "0"))
            if not 1 <= length <= MAX_BODY:
                raise InputError("BODY_SIZE")
            raw = self.rfile.read(length)
            if len(raw) != length:
                raise InputError("BODY_INCOMPLETE")
            body = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_object)
            result = dispatch(body)
            self.reply(200, result)
        except (InputError, UnicodeError, ValueError) as exc:
            code = str(exc) if isinstance(exc, InputError) else "INVALID_JSON"
            self.reply(400, {"ok": False, "status": "REJECTED", "error": code,
                             "automatic_retry": False, "current_reuse_authorized": False})
        except Exception:
            self.reply(503, {"ok": False, "status": "OUTCOME_UNKNOWN", "error": "OUTCOME_UNKNOWN",
                             "automatic_retry": False, "current_reuse_authorized": False})

    def do_OPTIONS(self):
        self.reply(405, {"ok": False, "status": "REJECTED", "error": "METHOD_NOT_ALLOWED"})

