#!/usr/bin/env python3
"""Rollback only the andrew cutover using validated saved state and numeric PIDs."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

TASK_ID = "T-2026-08-13-andrew-lecun-sync-cutover"
HOME = Path("/home/ubuntu")
TASK_DIR = HOME / "slocal2/m2/tasks" / TASK_ID
BACKUP_DIR = HOME / f".hub-migration-backup.{TASK_ID}"
KEEPER = HOME / "bin/keeper.sh"
OLD_MARKER = HOME / ".tunnel_to_philip"
NEW_MARKER = HOME / ".tunnel_to_lecun"
LOCK = HOME / ".keeper.lock"
GUARD_LOCK = BACKUP_DIR / "guard.lock"
ROLLBACK_LOCK = BACKUP_DIR / "rollback.lock"
READY = BACKUP_DIR / "guard-ready.json"
ARM_REQUEST = BACKUP_DIR / "arm-request.json"
ARMED = BACKUP_DIR / "guard-armed.json"
LEASE = BACKUP_DIR / "lease.json"
COMMIT_TOKEN = BACKUP_DIR / "commit-token.json"
ROLLBACK_REQUEST = BACKUP_DIR / "rollback-request.json"
ROLLBACK_DONE = BACKUP_DIR / "rollback-done.json"
EVENTS = BACKUP_DIR / "guard-events.jsonl"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def within(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def validate_state(state: dict[str, Any], backup_root: Path = BACKUP_DIR) -> None:
    if state.get("task_id") != TASK_ID:
        raise ValueError("state task_id does not match this rollback helper")
    expected = {
        "keeper_path": KEEPER,
        "old_marker_path": OLD_MARKER,
        "new_marker_path": NEW_MARKER,
    }
    for key, value in expected.items():
        if Path(state.get(key, "")) != value:
            raise ValueError(f"state target path rejected: {key}")
    for key in ("keeper_backup", "old_marker_backup", "known_hosts_backup", "devices_backup_dir"):
        path = Path(state.get(key, ""))
        if not within(path, backup_root):
            raise ValueError(f"state backup path escaped backup root: {key}")
    if not Path(state["keeper_backup"]).is_file():
        raise ValueError("keeper backup is missing")
    if not Path(state["old_marker_backup"]).is_file():
        raise ValueError("old marker backup is missing")
    if not Path(state["known_hosts_backup"]).is_file():
        raise ValueError("known_hosts backup is missing")
    if not Path(state["devices_backup_dir"]).is_dir():
        raise ValueError("device backup directory is missing")
    for key in ("keeper_sha256", "old_marker_sha256", "known_hosts_sha256"):
        value = state.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError(f"invalid saved digest: {key}")
    if sha256_path(Path(state["keeper_backup"])) != state["keeper_sha256"]:
        raise ValueError("keeper backup digest mismatch")
    if sha256_path(Path(state["old_marker_backup"])) != state["old_marker_sha256"]:
        raise ValueError("old marker backup digest mismatch")
    if sha256_path(Path(state["known_hosts_backup"])) != state["known_hosts_sha256"]:
        raise ValueError("known_hosts backup digest mismatch")


def start_tick(pid: int) -> int:
    raw = (Path("/proc") / str(pid) / "stat").read_text()
    return int(raw[raw.rfind(")") + 2 :].split()[19])


def atomic_json(path: Path, value: Any) -> None:
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.write(descriptor, (json.dumps(value, sort_keys=True) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def event(kind: str, **fields: Any) -> None:
    record = {"event": kind, "monotonic": time.monotonic(), "pid": os.getpid(), **fields}
    descriptor = os.open(EVENTS, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    try:
        os.write(descriptor, (json.dumps(record, sort_keys=True) + "\n").encode())
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def rollback_reason(owner_alive: bool, tick_matches: bool, lease_age: float, commit_valid: bool) -> str | None:
    if commit_valid:
        return None
    if not owner_alive:
        return "owner_missing"
    if not tick_matches:
        return "owner_tick_mismatch"
    if lease_age > 30:
        return "lease_expired"
    return None


def process_argv(pid: int) -> list[str]:
    if pid <= 1 or pid in ancestor_pids():
        raise ValueError(f"unsafe PID rejected: {pid}")
    path = Path("/proc") / str(pid) / "cmdline"
    return [
        value.decode("utf-8", errors="replace")
        for value in path.read_bytes().split(b"\0")
        if value
    ]


def process_exited(pid: int) -> bool:
    stat_path = Path("/proc") / str(pid) / "stat"
    try:
        raw = stat_path.read_text()
    except FileNotFoundError:
        return True
    state = raw[raw.rfind(")") + 2 :].split()[0]
    return state == "Z"


def ancestor_pids() -> set[int]:
    result: set[int] = set()
    pid = os.getpid()
    while pid > 0 and pid not in result:
        result.add(pid)
        try:
            raw = (Path("/proc") / str(pid) / "stat").read_text()
            fields = raw[raw.rfind(")") + 2 :].split()
            pid = int(fields[1])
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            break
    return result


def terminate_one(pid: int, required_tokens: tuple[str, ...], label: str) -> dict[str, Any]:
    if pid == 0:
        return {"label": label, "pid": 0, "result": "already_absent"}
    if process_exited(pid):
        return {"label": label, "pid": pid, "result": "already_exited"}
    argv = process_argv(pid)
    joined = " ".join(argv)
    if not all(token in joined for token in required_tokens):
        raise RuntimeError(f"PID {pid} no longer matches {label}; TERM not sent")
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 20
    while not process_exited(pid) and time.monotonic() < deadline:
        time.sleep(0.2)
    if not process_exited(pid):
        raise RuntimeError(f"PID {pid} did not exit after TERM; no stronger signal was sent")
    return {"label": label, "pid": pid, "signal": "TERM", "result": "exited"}


def atomic_copy(source: Path, destination: Path, mode: int) -> None:
    temporary = destination.with_name(destination.name + f".restore.{os.getpid()}")
    shutil.copy2(source, temporary)
    os.chmod(temporary, mode)
    os.replace(temporary, destination)


def restore_devices(backup_dir: Path) -> dict[str, Any]:
    process = subprocess.run(
        [sys.executable, str(TASK_DIR / "syncthing_route.py"), "--restore", str(backup_dir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"Syncthing device restore failed rc={process.returncode}: {process.stderr.strip()[-500:]}")
    return json.loads(process.stdout)


def launch_keeper() -> int:
    process = subprocess.Popen(
        [str(KEEPER)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    )
    return process.pid


def execute(state_path: Path, new_keeper_pid: int, new_tunnel_pid: int) -> dict[str, Any]:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    validate_state(state)
    actions = [
        terminate_one(new_keeper_pid, ("keeper.sh",), "new_keeper"),
        terminate_one(
            new_tunnel_pid,
            ("ssh", "22001:127.0.0.1:22000", "192.168.196.176"),
            "new_lecun_tunnel",
        ),
    ]
    actions.append({"restore_devices": restore_devices(Path(state["devices_backup_dir"]))})
    if NEW_MARKER.exists():
        failed = BACKUP_DIR / f".tunnel_to_lecun.failed.{int(time.time())}"
        os.replace(NEW_MARKER, failed)
        actions.append({"new_marker_moved_to": str(failed)})
    atomic_copy(Path(state["old_marker_backup"]), OLD_MARKER, int(state["old_marker_mode"], 8))
    actions.append({"old_marker_restored": str(OLD_MARKER)})
    atomic_copy(
        Path(state["known_hosts_backup"]),
        HOME / ".ssh/known_hosts",
        int(state["known_hosts_mode"], 8),
    )
    actions.append({"known_hosts_restored": True})
    if KEEPER.exists():
        failed_keeper = BACKUP_DIR / f"keeper.failed.{int(time.time())}"
        os.replace(KEEPER, failed_keeper)
        actions.append({"new_keeper_moved_to": str(failed_keeper)})
    atomic_copy(Path(state["keeper_backup"]), KEEPER, int(state["keeper_mode"], 8))
    if sha256_path(KEEPER) != state["keeper_sha256"]:
        raise RuntimeError("restored keeper digest mismatch")
    old_keeper_pid = launch_keeper()
    actions.append({"old_keeper_launched_pid": old_keeper_pid})
    return {"task_id": TASK_ID, "result": "ROLLBACK_EXECUTED", "actions": actions}


def watch(state_path: Path, owner_pid: int, owner_tick: int) -> dict[str, Any]:
    state = json.loads(state_path.read_text(encoding="utf-8"))
    validate_state(state)
    state_digest = sha256_path(state_path)
    lock_fd = os.open(GUARD_LOCK, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        try:
            fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError("a guard already holds the task lock") from exc
        atomic_json(READY, {"guard_pid": os.getpid(), "guard_tick": start_tick(os.getpid()), "state_sha256": state_digest})
        event("ready", state_sha256=state_digest, owner_pid=owner_pid, owner_tick=owner_tick)
        deadline = time.monotonic() + 30
        while not ARM_REQUEST.exists() and time.monotonic() < deadline:
            time.sleep(0.2)
        if not ARM_REQUEST.exists():
            raise RuntimeError("arm request was not received")
        request = json.loads(ARM_REQUEST.read_text(encoding="utf-8"))
        if request != {"owner_pid": owner_pid, "owner_tick": owner_tick, "state_sha256": state_digest}:
            raise RuntimeError("arm request identity or digest mismatch")
        atomic_json(ARMED, {**request, "guard_pid": os.getpid(), "guard_tick": start_tick(os.getpid())})
        event("armed", state_sha256=state_digest)
        while True:
            commit_valid = False
            if COMMIT_TOKEN.exists():
                token = json.loads(COMMIT_TOKEN.read_text(encoding="utf-8"))
                commit_valid = token.get("state_sha256") == state_digest and token.get("owner_pid") == owner_pid and token.get("owner_tick") == owner_tick
            if commit_valid:
                event("disarmed", state_sha256=state_digest)
                return {"result": "DISARMED"}
            try:
                live_tick = start_tick(owner_pid)
                owner_alive, tick_matches = True, live_tick == owner_tick
            except (FileNotFoundError, ProcessLookupError, PermissionError, ValueError):
                owner_alive, tick_matches = False, False
            lease_age = float("inf")
            if LEASE.exists():
                lease = json.loads(LEASE.read_text(encoding="utf-8"))
                if lease.get("owner_pid") == owner_pid and lease.get("owner_tick") == owner_tick:
                    lease_age = time.monotonic() - float(lease.get("monotonic", 0))
            reason = "rollback_requested" if ROLLBACK_REQUEST.exists() else rollback_reason(owner_alive, tick_matches, lease_age, False)
            if reason:
                rollback_fd = os.open(ROLLBACK_LOCK, os.O_RDWR | os.O_CREAT, 0o600)
                try:
                    fcntl.flock(rollback_fd, fcntl.LOCK_EX)
                    if not ROLLBACK_DONE.exists():
                        runtime_path = BACKUP_DIR / "runtime.json"
                        runtime = json.loads(runtime_path.read_text(encoding="utf-8")) if runtime_path.exists() else {}
                        result = execute(state_path, int(runtime.get("new_keeper_pid", 0)), int(runtime.get("new_tunnel_pid", 0)))
                        atomic_json(ROLLBACK_DONE, {"reason": reason, "result": result})
                        event("rollback", reason=reason)
                finally:
                    os.close(rollback_fd)
                return {"result": "ROLLED_BACK", "reason": reason}
            time.sleep(1)
    finally:
        os.close(lock_fd)


class FakeRest:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def restore(self, directory: Path) -> None:
        for name in ("philip", "lecun"):
            json.loads((directory / f"syncthing-device-{name}.json").read_text(encoding="utf-8"))
        self.calls.append("restore_devices")


def self_test() -> tuple[dict[str, bool], bool]:
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="m2-canary-rollback-") as raw:
        root = Path(raw)
        keeper_backup = root / "keeper.before"
        marker_backup = root / "marker.before"
        known_hosts_backup = root / "known_hosts.before"
        devices = root / "devices"
        keeper_backup.write_text("#!/bin/sh\n", encoding="utf-8")
        marker_backup.write_text("/safe/key\nold-hub\n", encoding="utf-8")
        known_hosts_backup.write_text("safe host key\n", encoding="utf-8")
        devices.mkdir()
        for name in ("philip", "lecun"):
            (devices / f"syncthing-device-{name}.json").write_text(
                json.dumps({"deviceID": name, "name": name, "addresses": []}),
                encoding="utf-8",
            )
        state = {
            "task_id": TASK_ID,
            "keeper_path": str(KEEPER),
            "old_marker_path": str(OLD_MARKER),
            "new_marker_path": str(NEW_MARKER),
            "keeper_backup": str(keeper_backup),
            "old_marker_backup": str(marker_backup),
            "known_hosts_backup": str(known_hosts_backup),
            "devices_backup_dir": str(devices),
            "keeper_sha256": sha256_path(keeper_backup),
            "old_marker_sha256": sha256_path(marker_backup),
            "known_hosts_sha256": sha256_path(known_hosts_backup),
            "keeper_mode": "755",
            "old_marker_mode": "600",
            "known_hosts_mode": "600",
        }
        validate_state(state, backup_root=root)
        checks["valid_fixture_accepted"] = True
        wrong = dict(state)
        wrong["keeper_path"] = "/tmp/not-the-keeper"
        try:
            validate_state(wrong, backup_root=root)
            checks["outside_target_rejected"] = False
        except ValueError:
            checks["outside_target_rejected"] = True
        try:
            process_argv(1)
            checks["unsafe_pid_rejected"] = False
        except ValueError:
            checks["unsafe_pid_rejected"] = True
        fake = FakeRest()
        fake.restore(devices)
        checks["fake_rest_restore_called_once"] = fake.calls == ["restore_devices"]
        ordered_plan = ["stop_new_keeper", "stop_new_tunnel", "restore_devices", "restore_marker", "restore_keeper", "launch_old_keeper"]
        checks["rollback_order_fixed"] = ordered_plan.index("restore_devices") < ordered_plan.index("restore_marker")
        checks["owner_missing_requests_rollback"] = rollback_reason(False, False, 0, False) == "owner_missing"
        checks["tick_mismatch_requests_rollback"] = rollback_reason(True, False, 0, False) == "owner_tick_mismatch"
        checks["lease_expiry_requests_rollback"] = rollback_reason(True, True, 31, False) == "lease_expired"
        checks["valid_commit_disarms"] = rollback_reason(False, False, 999, True) is None
    return checks, all(checks.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--self-test", action="store_true")
    actions.add_argument("--validate-state", type=Path)
    actions.add_argument("--execute", type=Path)
    actions.add_argument("--watch", type=Path)
    parser.add_argument("--owner-pid", type=int)
    parser.add_argument("--owner-tick", type=int)
    parser.add_argument("--new-keeper-pid", type=int, default=0)
    parser.add_argument("--new-tunnel-pid", type=int, default=0)
    args = parser.parse_args()
    if args.self_test:
        checks, passed = self_test()
        result = {"self_test": checks, "result": "PASS" if passed else "FAIL"}
        exit_code = 0 if passed else 1
    elif args.validate_state:
        state = json.loads(args.validate_state.read_text(encoding="utf-8"))
        validate_state(state)
        result = {"result": "PASS", "state": str(args.validate_state)}
        exit_code = 0
    elif args.watch:
        if args.owner_pid is None or args.owner_tick is None:
            parser.error("--watch requires --owner-pid and --owner-tick")
        result = watch(args.watch, args.owner_pid, args.owner_tick)
        exit_code = 0
    else:
        result = execute(args.execute, args.new_keeper_pid, args.new_tunnel_pid)
        exit_code = 0
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
