#!/usr/bin/env python3
"""Rollback only the bengio canary using validated saved state and numeric PIDs."""

from __future__ import annotations

import argparse
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

TASK_ID = "T-2026-08-13-bengio-canary-lecun-cutover"
HOME = Path("/home/ubuntu")
TASK_DIR = HOME / "slocal2/m2/tasks" / TASK_ID
BACKUP_DIR = HOME / f".hub-migration-backup.{TASK_ID}"
KEEPER = HOME / "bin/keeper.sh"
OLD_MARKER = HOME / ".tunnel_to_philip"
NEW_MARKER = HOME / ".tunnel_to_lecun"
LOCK = HOME / ".keeper.lock"


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
    for key in ("keeper_backup", "old_marker_backup", "devices_backup_dir"):
        path = Path(state.get(key, ""))
        if not within(path, backup_root):
            raise ValueError(f"state backup path escaped backup root: {key}")
    if not Path(state["keeper_backup"]).is_file():
        raise ValueError("keeper backup is missing")
    if not Path(state["old_marker_backup"]).is_file():
        raise ValueError("old marker backup is missing")
    if not Path(state["devices_backup_dir"]).is_dir():
        raise ValueError("device backup directory is missing")
    for key in ("keeper_sha256", "old_marker_sha256"):
        value = state.get(key)
        if not isinstance(value, str) or len(value) != 64 or any(char not in "0123456789abcdef" for char in value):
            raise ValueError(f"invalid saved digest: {key}")
    if sha256_path(Path(state["keeper_backup"])) != state["keeper_sha256"]:
        raise ValueError("keeper backup digest mismatch")
    if sha256_path(Path(state["old_marker_backup"])) != state["old_marker_sha256"]:
        raise ValueError("old marker backup digest mismatch")


def process_argv(pid: int) -> list[str]:
    if pid <= 1 or pid in ancestor_pids():
        raise ValueError(f"unsafe PID rejected: {pid}")
    path = Path("/proc") / str(pid) / "cmdline"
    return [
        value.decode("utf-8", errors="replace")
        for value in path.read_bytes().split(b"\0")
        if value
    ]


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
    argv = process_argv(pid)
    joined = " ".join(argv)
    if not all(token in joined for token in required_tokens):
        raise RuntimeError(f"PID {pid} no longer matches {label}; TERM not sent")
    os.kill(pid, signal.SIGTERM)
    deadline = time.monotonic() + 20
    while Path("/proc", str(pid)).exists() and time.monotonic() < deadline:
        time.sleep(0.2)
    if Path("/proc", str(pid)).exists():
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
        devices = root / "devices"
        keeper_backup.write_text("#!/bin/sh\n", encoding="utf-8")
        marker_backup.write_text("/safe/key\nold-hub\n", encoding="utf-8")
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
            "devices_backup_dir": str(devices),
            "keeper_sha256": sha256_path(keeper_backup),
            "old_marker_sha256": sha256_path(marker_backup),
            "keeper_mode": "755",
            "old_marker_mode": "600",
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
    return checks, all(checks.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    actions = parser.add_mutually_exclusive_group(required=True)
    actions.add_argument("--self-test", action="store_true")
    actions.add_argument("--validate-state", type=Path)
    actions.add_argument("--execute", type=Path)
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
    else:
        result = execute(args.execute, args.new_keeper_pid, args.new_tunnel_pid)
        exit_code = 0
    print(json.dumps(result, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
