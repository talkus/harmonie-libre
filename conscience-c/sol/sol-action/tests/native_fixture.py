"""Local-only native-browser fixture. Serves pinned app bytes; no provider calls.

The response transport is synthetic. The browser's Web Locks, origin storage,
events and tab concurrency are native and are the only properties under test.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

JOB = "10000000-0000-4000-8000-000000000001"
MISSION = "20000000-0000-4000-8000-000000000001"
FOREIGN = "90000000-0000-4000-8000-000000000009"
JOB_KEY = "sol-action-session-v1"
MISSION_KEY = "sol-action-mission-session-v1"
CAP = "b" * 64  # Deliberately public synthetic capability; never a real credential.
SOURCE = "id,currency,amount\none,EUR,0.10\n"
HASH = hashlib.sha256(SOURCE.encode()).hexdigest()


def stamp(value=None):
    return (value or datetime.now(timezone.utc)).isoformat().replace("+00:00", "Z")


def result():
    return {"source_sha256": HASH, "rows": 1, "row_ids": ["one"], "totals": [{"currency": "EUR", "amount": "0.10"}]}


def seed_job():
    return {"version": 1, "job_id": JOB, "capability": CAP, "mandate": "LOCAL NATIVE-BROWSER FIXTURE ONLY", "requirements": ["One synthetic CSV row, no provider proof"], "source_csv": SOURCE, "source_sha256": HASH, "next_step_id": "verify", "result": result(), "history": [], "pending": None}


def matrix():
    return [{"compound_id": f"{JOB}:r{i}", "task_id": JOB, "anchor_task_id": JOB, "role": "ROOT" if i < 16 else "COMPANION", "requirement": {"id": f"r{i}", "text": f"Synthetic exact requirement {i}", "contract": {"kind": "semantic_claim", "target": {"claim": "UNKNOWN"}}}, "mapping_basis": "OPERATOR_DECLARED", "validation": "UNKNOWN"} for i in range(32)]


def definition():
    return {"mission_id": MISSION, "definition_hash": "a" * 64, "definition": {"job_id": JOB, "job": {"job_id": JOB, "mandate": seed_job()["mandate"], "requirements": seed_job()["requirements"], "source_sha256": HASH}, "requirements_matrix": matrix()}, "last_report": None}


def verify_response(route, data):
    if route == "/api/job":
        return {"ok": True, "action": "verify", "job_id": data["job_id"], "request_id": data["request_id"], "status": "PASS", "next_step_id": "complete", "source_sha256": HASH, "verification": {"status": "PASS", "scope": "SYNTHETIC_LOCAL_FIXTURE_ONLY"}, "current_reuse_authorized": False}
    now = datetime.now(timezone.utc)
    checks = [{"name": name, "verdict": "PASS", "reason": "SYNTHETIC_LOCAL_FIXTURE_NOT_PROVIDER_PROOF", "evidence": {"synthetic_fixture": True}} for name in ["runtime_dependencies", "mission_integrity", "job_and_source_identity", "bundle_current_resolution", "job_journal", "pending_intents", "production_release_binding", "independent_sql_oracle", "runtime_file_observation"]]
    report = {"status": "TECHNICAL_RESULT_VERIFIED", "technical_verdict": "PASS", "general_mandate": "UNKNOWN", "all_original_requirements_satisfied": False, "verified_at": stamp(now), "expires_at": stamp(now + timedelta(seconds=59)), "requirements": matrix(), "checks": checks, "fixture_scope": "SYNTHETIC_TRANSPORT_ONLY"}
    return {"ok": True, "action": "verify", "job_id": data["job_id"], "mission_id": data["mission_id"], "request_id": data["request_id"], "report_id": "40000000-0000-4000-8000-000000000001", "status": "TECHNICAL_RESULT_VERIFIED", "technical_verdict": "PASS", "report": report, "current_reuse_authorized": True, "general_mandate": "UNKNOWN"}


class Fixture:
    def __init__(self, app_dir, evidence_path):
        public = app_dir.resolve() / "public"
        self.files = {}
        for name in ["intent-slot.js", "app.js", "missions.js", "styles.css", "index.html"]:
            source = public / name
            if source.exists():
                self.files["/" + name] = source.read_bytes()
        for required in ["/app.js", "/missions.js", "/index.html"]:
            if required not in self.files:
                raise ValueError(f"Missing app file: {required}")
        self.hashes = {name: hashlib.sha256(value).hexdigest() for name, value in self.files.items()}
        self.app_dir = str(app_dir.resolve())
        self.evidence_path = evidence_path.resolve()
        self.mutex = threading.Lock()
        self.release = threading.Event()
        self.calls = []
        self.committed = {}
        self.started_at = stamp()
        self.save()

    def snapshot(self):
        return {"schema": "SOL_NATIVE_BROWSER_LOCAL_FIXTURE_STATE/v1", "started_at": self.started_at, "observed_at": stamp(), "app_dir": self.app_dir, "pinned_public_file_sha256": self.hashes, "scope": "Native browser locks/storage/tabs; synthetic HTTP responses, no provider calls or business proof", "held_responses": not self.release.is_set(), "calls": self.calls, "counts": {"verify": sum(x["action"] == "verify" for x in self.calls), "receipt": sum(x["action"] == "receipt" for x in self.calls), "status": sum(x["action"] == "status" for x in self.calls)}, "committed_request_ids": list(self.committed)}

    def save(self):
        self.evidence_path.parent.mkdir(parents=True, exist_ok=True)
        self.evidence_path.write_text(json.dumps(self.snapshot(), ensure_ascii=False, indent=2) + "\n")

    def html(self):
        html = self.files["/index.html"].decode()
        html = html.replace("<head>", '<head><script src="/fixture-bootstrap.js"></script>', 1)
        controls = '''<aside style="padding:12px;background:#fff3b0;border:3px solid #8b3900;font:16px sans-serif">
<strong>LOCAL TEST FIXTURE — synthetic service, no Supabase/Vercel call</strong>
<p id="fixture-native-locks"></p><button id="fixture-ready">1. Load and select synthetic Mission</button>
<button id="fixture-arm">Hold verify responses</button><button id="fixture-release">Release verify responses</button>
<button id="fixture-foreign">Insert foreign test pending UUID</button><button id="fixture-inspect">Inspect counters and local pending</button>
<button id="fixture-reset">Reset this fixture origin</button><pre id="fixture-state" style="white-space:pre-wrap;max-height:250px;overflow:auto"></pre></aside>'''
        return html.replace("<body>", "<body>" + controls, 1).encode()

    def bootstrap(self):
        seed = json.dumps(seed_job(), ensure_ascii=False)
        return f'''(function(){{
const JK={json.dumps(JOB_KEY)}, MK={json.dumps(MISSION_KEY)}, MID={json.dumps(MISSION)}, FOREIGN={json.dumps(FOREIGN)};
if(localStorage.getItem(JK)===null) localStorage.setItem(JK,JSON.stringify({seed}));
document.addEventListener('DOMContentLoaded',()=>{{
const $=id=>document.getElementById(id);
$('fixture-native-locks').textContent='Native Web Locks: '+Boolean(navigator.locks&&navigator.locks.request)+'; origin '+location.origin+'; tab '+location.pathname;
async function control(action){{await fetch('/fixture/control',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify({{action}})}});}}
async function inspect(){{const server=await fetch('/fixture/state').then(r=>r.json());let pending;try{{pending=JSON.parse(localStorage.getItem(MK)||'null')?.pending||null;}}catch(_){{pending='CORRUPT';}}$('fixture-state').textContent=JSON.stringify({{counts:server.counts,committed_request_ids:server.committed_request_ids,pending,source_hashes:server.pinned_public_file_sha256}},null,2);}}
$('fixture-ready').onclick=()=>{{$('mission-load').click();let attempts=0;const timer=setInterval(()=>{{if([...$('mission-select').options].some(x=>x.value===MID)){{$('mission-select').value=MID;$('mission-select').dispatchEvent(new Event('change',{{bubbles:true}}));clearInterval(timer);}}else if(++attempts>100)clearInterval(timer);}},20);}};
$('fixture-arm').onclick=async()=>{{await control('hold');await inspect();}};
$('fixture-release').onclick=async()=>{{await control('release');await inspect();}};
$('fixture-foreign').onclick=async()=>{{const pending={{action:'verify',input:{{job_id:{json.dumps(JOB)},mission_id:MID,request_id:FOREIGN}},prepared_at:new Date().toISOString()}};localStorage.setItem(MK,JSON.stringify({{version:1,job_id:{json.dumps(JOB)},mission_id:MID,pending}}));await inspect();}};
$('fixture-inspect').onclick=inspect;
$('fixture-reset').onclick=async()=>{{await control('reset');localStorage.removeItem(JK);localStorage.removeItem(MK);location.reload();}};
inspect();
}});
}})();'''.encode()


def handler_for(fixture):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass

        def send(self, code, value, content_type="application/json; charset=utf-8"):
            raw = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False).encode()
            self.send_response(code)
            for key, val in {"Content-Type": content_type, "Content-Length": str(len(raw)), "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}.items():
                self.send_header(key, val)
            self.end_headers()
            try:
                self.wfile.write(raw)
            except (BrokenPipeError, ConnectionResetError):
                pass

        def do_GET(self):
            route = urlsplit(self.path).path
            if route in ("/", "/A", "/B", "/index.html"):
                self.send(200, fixture.html(), "text/html; charset=utf-8")
            elif route == "/fixture-bootstrap.js":
                self.send(200, fixture.bootstrap(), "application/javascript; charset=utf-8")
            elif route == "/fixture/state":
                with fixture.mutex:
                    self.send(200, fixture.snapshot())
            elif route == "/provider-observation.json":
                self.send(200, {"fixture": True})
            elif route in fixture.files:
                content_type = "text/css; charset=utf-8" if route.endswith(".css") else "application/javascript; charset=utf-8"
                self.send(200, fixture.files[route], content_type)
            else:
                self.send(404, {"error": "FIXTURE_ROUTE_ONLY"})

        def do_POST(self):
            route = urlsplit(self.path).path
            try:
                size = int(self.headers.get("Content-Length", "0"))
                if not 0 < size <= 16384:
                    raise ValueError("size")
                body = json.loads(self.rfile.read(size))
                if route == "/fixture/control":
                    action = body["action"]
                    with fixture.mutex:
                        if action == "hold":
                            fixture.release.clear()
                        elif action == "release":
                            fixture.release.set()
                        elif action == "reset":
                            fixture.release.set()
                            fixture.calls = []
                            fixture.committed = {}
                        else:
                            raise ValueError("control")
                        fixture.save()
                    self.send(200, {"ok": True, "fixture_control": action})
                    return
                if route not in ("/api/mission", "/api/job"):
                    self.send(404, {"error": "FIXTURE_ROUTE_ONLY"})
                    return
                action, data = body["action"], body["input"]
                if data.get("capability") != CAP or data.get("job_id") != JOB:
                    raise ValueError("synthetic identity required")
                with fixture.mutex:
                    fixture.calls.append({"at": stamp(), "route": route, "action": action, "job_id": data.get("job_id"), "mission_id": data.get("mission_id"), "request_id": data.get("request_id"), "target_request_id": data.get("target_request_id")})
                    fixture.save()
                if action == "verify":
                    value = verify_response(route, data)
                    with fixture.mutex:
                        fixture.committed[data["request_id"]] = value
                        fixture.save()
                    # A browser may time out first. That is intentionally not
                    # a production network failure or a fresh provider proof.
                    fixture.release.wait(timeout=45)
                    self.send(200, value)
                elif action == "receipt" and route == "/api/mission":
                    with fixture.mutex:
                        original = fixture.committed.get(data["target_request_id"])
                        receipt = json.loads(json.dumps(original)) if original else None
                    if receipt:
                        receipt["current_reuse_authorized"] = False
                        receipt["report"]["current_reuse_authorized"] = False
                    self.send(200, {"ok": True, "action": "receipt", "job_id": JOB, "mission_id": data["mission_id"], "target_request_id": data["target_request_id"], "found": bool(receipt), "status": "HISTORICAL_NOT_CURRENT" if receipt else "UNKNOWN", "current_reuse_authorized": False, "receipt": receipt})
                elif action == "status":
                    if route == "/api/mission":
                        self.send(200, {"ok": True, "action": "status", "job_id": JOB, "status": "HISTORICAL_NOT_CURRENT", "current_reuse_authorized": False, "missions": [definition()]})
                    else:
                        self.send(200, {"ok": True, "action": "status", "job_id": JOB, "next_step_id": "verify", "result": result(), "source_sha256": HASH, "current_reuse_authorized": False})
                else:
                    self.send(400, {"ok": False, "status": "REJECTED", "error": "ONLY_SYNTHETIC_STATUS_VERIFY_RECEIPT_SUPPORTED", "current_reuse_authorized": False})
            except (ValueError, KeyError, TypeError):
                self.send(400, {"ok": False, "error": "INVALID_LOCAL_FIXTURE_INPUT"})
    return Handler


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--app-dir", type=Path, required=True)
    parser.add_argument("--state-file", type=Path, required=True)
    parser.add_argument("--port", type=int, default=8783)
    args = parser.parse_args()
    fixture = Fixture(args.app_dir, args.state_file)
    server = ThreadingHTTPServer(("127.0.0.1", args.port), handler_for(fixture))
    print(json.dumps({"url_A": f"http://127.0.0.1:{args.port}/A", "url_B": f"http://127.0.0.1:{args.port}/B", "state_file": str(fixture.evidence_path), "pinned_file_sha256": fixture.hashes, "scope": "LOCAL_SYNTHETIC_TRANSPORT_NATIVE_BROWSER_LOCKS_ONLY"}), flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
