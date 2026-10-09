"""Install a verified release on the existing Linux host; never create memory.

Run as root with a previously verified archive SHA-256 and source commit.
This script is specific to the existing mem account and systemd deployment.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import pwd
import re
import shutil
import subprocess
import tarfile
import tempfile


BASE = Path("/opt/conscience-c")
DATA = Path("/var/lib/conscience-c")
CONFIG = Path("/etc/conscience-c")
DEPLOYMENT = "conscience-c/brain/deployment"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def command(args, *, cwd=None, logfile=None):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True,
                            timeout=600, check=False)
    if logfile is not None:
        logfile.write_text(result.stdout + result.stderr, encoding="utf-8")
    if result.returncode:
        # Full logs stay on the host; report only the command category and code.
        raise RuntimeError(f"{Path(args[0]).name} failed with code {result.returncode}")
    return result.stdout + result.stderr


def verify_files(release, manifest):
    for name, item in manifest["files"].items():
        path = release / name
        if path.is_symlink() or not path.is_file() or digest(path) != item["sha256"]:
            raise ValueError(f"release file differs: {name}")
        if item.get("git_blob"):
            data = path.read_bytes()
            actual = hashlib.sha1(b"blob " + str(len(data)).encode() + b"\0" + data).hexdigest()
            if actual != item["git_blob"]:
                raise ValueError(f"Git blob differs: {name}")


def registry_snapshot():
    root = Path("/var/lib/registre-mem/journal")
    files = {str(p.relative_to(root)): digest(p) for p in root.rglob("*") if p.is_file()}
    state = {}
    for unit in ("registre-mem.service", "registre-mem-caddy.service"):
        value = command(["systemctl", "show", unit, "-p", "ActiveState", "-p", "MainPID"])
        state[unit] = dict(line.split("=", 1) for line in value.splitlines() if "=" in line)
    return {"files": files, "services": state}


def install(args):
    if os.geteuid() != 0:
        raise PermissionError("installation requires root through the existing host management channel")
    # SSM bootstrap uses umask 077. Public program files must remain traversable
    # by the unprivileged execution account; memory/config modes stay explicit.
    os.umask(0o022)
    if not re.fullmatch(r"[0-9a-f]{40}", args.source_commit):
        raise ValueError("invalid source commit")
    if not re.fullmatch(r"[0-9a-f]{64}", args.sha256) or digest(args.archive) != args.sha256:
        raise ValueError("archive SHA-256 does not match the reviewed artifact")
    account = pwd.getpwnam("mem")
    before = registry_snapshot()
    # This initial installation must not replace an unexamined deployment.
    if (BASE / "current").exists() or (BASE / "current").is_symlink():
        raise FileExistsError("current release already exists; inspect before replacing it")
    for unit in ("conscience-c-work.service", "conscience-c-work.timer"):
        if (Path("/etc/systemd/system") / unit).exists():
            raise FileExistsError(f"existing unit must be inspected: {unit}")
    if (CONFIG / "work.env").exists():
        raise FileExistsError("existing work.env must be inspected")

    releases = BASE / "releases"
    releases.mkdir(parents=True, exist_ok=True)
    BASE.chmod(0o755)
    releases.chmod(0o755)
    incoming = Path(tempfile.mkdtemp(prefix=".incoming-", dir=BASE))
    incoming.chmod(0o755)
    with tarfile.open(args.archive, "r:gz") as archive:
        members = archive.getmembers()
        names = [m.name for m in members]
        if len(set(names)) != len(names):
            raise ValueError("duplicate archive members")
        for member in members:
            name = PurePosixPath(member.name)
            if not member.isfile() or name.is_absolute() or ".." in name.parts:
                raise ValueError("archive must contain only safe relative regular files")
        manifest = json.load(archive.extractfile("DEPLOYMENT_MANIFEST.json"))
        if manifest["source_commit"] != args.source_commit or manifest["creates_brain_memory"] is not False:
            raise ValueError("unexpected manifest provenance or memory creation")
        if set(names) != set(manifest["files"]) | {"DEPLOYMENT_MANIFEST.json"}:
            raise ValueError("manifest and archive members differ")
        for member in members:
            target = incoming / member.name
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as output:
                shutil.copyfileobj(archive.extractfile(member), output)
            target.chmod(0o644)
    verify_files(incoming, manifest)
    release = releases / args.source_commit
    if release.exists():
        raise FileExistsError("release already exists; inspect before reinstalling")
    incoming.rename(release)
    python = release / ".venv/bin/python"
    command(["/usr/bin/python3.11", "-m", "venv", str(release / ".venv")],
            logfile=release / "venv-install.log")
    command([str(python), "-m", "pip", "install", "--no-input", "--disable-pip-version-check",
             str(release / "conscience-c/brain") + "[simulation]"],
            logfile=release / "package-install.log")
    brain = release / "conscience-c/brain"
    checks = {}
    for name, argv, expected in (
        ("brain", ["-m", "unittest", "discover", "-s", "tests", "-v"], 481),
        ("continuity", [str(release / "conscience-c/verify_reprise.py")], 11),
    ):
        output = command(["runuser", "-u", "mem", "--", str(python), *argv], cwd=brain,
                         logfile=release / f"{name}-tests.log")
        count = re.search(r"Ran (\d+) tests?", output)
        if count is None or int(count.group(1)) != expected or "skipped=" in output:
            raise RuntimeError(f"unexpected {name} test count or skipped test")
        checks[name] = {"tests": expected, "result": "passed", "log_sha256": digest(release / f"{name}-tests.log")}
    verify_files(release, manifest)
    runtime = json.loads(command([str(python), "-c",
        "import importlib.metadata,json,sys; print(json.dumps({'python':sys.version.split()[0],"
        "'brain':importlib.metadata.version('conscience-c-brain'),"
        "'cryptography':importlib.metadata.version('cryptography')}))"]))
    if runtime["brain"] != manifest["package_version"]:
        raise RuntimeError("installed package version differs")
    for path in (DATA, DATA / "brain"):
        if path.is_symlink():
            raise ValueError("data directories must not be symlinks")
        path.mkdir(exist_ok=True)
        os.chown(path, account.pw_uid, account.pw_gid)
        path.chmod(0o700)
    receipts = DATA / "deployment"
    receipts.mkdir(exist_ok=True)
    receipts.chmod(0o750)
    os.chown(receipts, 0, account.pw_gid)
    CONFIG.mkdir(exist_ok=True)
    CONFIG.chmod(0o750)
    os.chown(CONFIG, 0, account.pw_gid)
    sample = CONFIG / "work.env.example"
    shutil.copyfile(release / DEPLOYMENT / "work.env.example", sample)
    os.chown(sample, 0, account.pw_gid)
    sample.chmod(0o640)
    pointer = BASE / ".current-next"
    pointer.symlink_to(release)
    pointer.replace(BASE / "current")
    units = [release / DEPLOYMENT / "systemd" / name
             for name in ("conscience-c-work.service", "conscience-c-work.timer")]
    command(["systemd-analyze", "verify", *[str(p) for p in units]], logfile=release / "systemd-verify.log")
    for path in units:
        shutil.copyfile(path, Path("/etc/systemd/system") / path.name)
    command(["systemctl", "daemon-reload"])
    command(["systemctl", "enable", "--now", "conscience-c-work.timer"])
    command(["systemctl", "start", "conscience-c-work.service"])
    timer = command(["systemctl", "show", "conscience-c-work.timer", "-p", "ActiveState", "-p", "SubState", "-p", "UnitFileState"])
    service = command(["systemctl", "show", "conscience-c-work.service", "-p", "ActiveState", "-p", "Result", "-p", "ConditionResult"])
    after = registry_snapshot()
    original_files_unchanged = all(after["files"].get(p) == h for p, h in before["files"].items())
    processes_unchanged = before["services"] == after["services"]
    if not original_files_unchanged or not processes_unchanged:
        command(["systemctl", "stop", "conscience-c-work.timer", "conscience-c-work.service"])
        raise RuntimeError("registry baseline differs; stop and inspect deployment")
    record = {
        "schema": "CC-DEPLOYMENT-RECEIPT-1", "examined_at": datetime.now(timezone.utc).isoformat(),
        "source_commit": args.source_commit, "archive_sha256": args.sha256,
        "manifest_sha256": digest(release / "DEPLOYMENT_MANIFEST.json"), "runtime": runtime,
        "tests": checks, "release": str(release), "timer": timer.strip(), "service": service.strip(),
        "registry_original_files_unchanged": original_files_unchanged,
        "registry_processes_unchanged": processes_unchanged,
        "registry_file_count_before": len(before["files"]), "registry_file_count_after": len(after["files"]),
        "brain_memory_present": (DATA / "brain/state.json").is_file() and (DATA / "brain/events.jsonl").is_file(),
        "active_plan_config_present": (CONFIG / "work.env").is_file(),
        "operational_examination_observed": False, "continuous_service_observed": False,
    }
    receipt = receipts / ("release-" + args.source_commit + ".json")
    with receipt.open("x", encoding="utf-8") as output:
        json.dump(record, output, ensure_ascii=False, indent=2)
        output.write("\n")
    receipt.chmod(0o640)
    print(json.dumps(record, ensure_ascii=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    parser.add_argument("--source-commit", required=True)
    install(parser.parse_args())
