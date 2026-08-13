#!/usr/bin/env python3
"""Read-only state probe for the lecun hub keeper cutover."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import os
import socket
import stat
import tempfile
from pathlib import Path
from typing import Any

HOME = Path("/home/ubuntu")
REPO = HOME / "slocal2/m2"
PORTS = (22000, 22001, 50072, 8384)
ABSENT_PROCESS = "m2_probe_process_that_does_not_exist_7d6c"
ABSENT_MARKER = HOME / ".tunnel_to_m2_probe_that_does_not_exist_7d6c"


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stat_fields(pid: int) -> tuple[int, int]:
    raw = (Path("/proc") / str(pid) / "stat").read_text()
    fields = raw[raw.rfind(")") + 2 :].split()
    return int(fields[1]), int(fields[19])


def ancestor_pids() -> set[int]:
    ancestors: set[int] = set()
    pid = os.getpid()
    while pid > 0 and pid not in ancestors:
        ancestors.add(pid)
        try:
            pid, _ = stat_fields(pid)
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            break
    return ancestors


def process_matches(argv: list[str], comm: str) -> dict[str, bool]:
    basenames = {Path(arg).name for arg in argv if arg}
    joined = " ".join(argv)
    return {
        "keeper": "keeper.sh" in basenames,
        "m2_sync": "m2-sync.sh" in basenames,
        "syncthing": comm == "syncthing" or "syncthing" in basenames,
        "ssh_local_forward": (
            (comm == "ssh" or "ssh" in basenames)
            and "22001:127.0.0.1:22000" in joined
        ),
        "absent_control": ABSENT_PROCESS in joined,
    }


def open_fds_for_path(target: Path) -> list[dict[str, int]]:
    holders: list[dict[str, int]] = []
    for proc_dir in Path("/proc").iterdir():
        if not proc_dir.name.isdigit():
            continue
        fd_dir = proc_dir / "fd"
        try:
            descriptors = list(fd_dir.iterdir())
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
        for descriptor in descriptors:
            try:
                if os.readlink(descriptor) == str(target):
                    holders.append({"pid": int(proc_dir.name), "fd": int(descriptor.name)})
            except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, ValueError):
                continue
    return sorted(holders, key=lambda item: (item["pid"], item["fd"]))


def fd_details(pid: int, fd: int) -> dict[str, Any]:
    path = Path("/proc") / str(pid) / "fd" / str(fd)
    try:
        details: dict[str, Any] = {
            "exists": True,
            "target": os.readlink(path),
            "inode": path.stat().st_ino,
        }
        if fd == 255:
            details["sha256"] = sha256_path(path)
        if fd == 9:
            lock_path = HOME / ".keeper.lock"
            holders = open_fds_for_path(lock_path)
            details["lock_probe_available"] = lock_available(lock_path)
            details["open_fds_for_lock"] = holders
            details["write_flock_held"] = (
                details["target"] == str(lock_path)
                and details["lock_probe_available"] is False
                and holders == [{"pid": pid, "fd": 9}]
            )
        return details
    except (FileNotFoundError, PermissionError, ProcessLookupError, OSError) as exc:
        return {"exists": False, "error": type(exc).__name__}


def processes() -> dict[str, list[dict[str, Any]]]:
    result: dict[str, list[dict[str, Any]]] = {
        "keeper": [],
        "m2_sync": [],
        "syncthing": [],
        "ssh_local_forward": [],
        "absent_control": [],
    }
    excluded = ancestor_pids()
    for proc_dir in sorted(Path("/proc").iterdir(), key=lambda item: item.name):
        if not proc_dir.name.isdigit():
            continue
        pid = int(proc_dir.name)
        if pid in excluded:
            continue
        try:
            argv = [
                value.decode("utf-8", errors="replace")
                for value in (proc_dir / "cmdline").read_bytes().split(b"\0")
                if value
            ]
            if not argv:
                continue
            comm = (proc_dir / "comm").read_text().strip()
            ppid, start_tick = stat_fields(pid)
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, ValueError):
            continue
        for category, matched in process_matches(argv, comm).items():
            if not matched:
                continue
            item: dict[str, Any] = {
                "pid": pid,
                "ppid": ppid,
                "start_tick": start_tick,
                "cmdline": argv,
            }
            if category == "keeper":
                item["fd9"] = fd_details(pid, 9)
                item["fd255"] = fd_details(pid, 255)
            result[category].append(item)
    return result


def decode_address(raw: str, ipv6: bool) -> str:
    packed = bytes.fromhex(raw)
    if ipv6:
        packed = b"".join(packed[index : index + 4][::-1] for index in range(0, 16, 4))
        return socket.inet_ntop(socket.AF_INET6, packed)
    return socket.inet_ntop(socket.AF_INET, packed[::-1])


def listeners() -> dict[str, list[dict[str, Any]]]:
    result = {str(port): [] for port in PORTS}
    for table_name, ipv6 in (("tcp", False), ("tcp6", True)):
        table = Path("/proc/net") / table_name
        try:
            lines = table.read_text().splitlines()[1:]
        except (FileNotFoundError, PermissionError):
            continue
        for line in lines:
            fields = line.split()
            if len(fields) < 10 or fields[3] != "0A":
                continue
            raw_address, raw_port = fields[1].split(":")
            port = int(raw_port, 16)
            if port not in PORTS:
                continue
            result[str(port)].append(
                {
                    "family": table_name,
                    "address": decode_address(raw_address, ipv6),
                    "port": port,
                    "inode": int(fields[9]),
                }
            )
    return result


def file_summary(path: Path) -> dict[str, Any]:
    try:
        data = path.read_bytes()
        mode = stat.S_IMODE(path.stat().st_mode)
        return {
            "path": str(path),
            "exists": True,
            "mode": f"{mode:03o}",
            "line_count": len(data.splitlines()),
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return {"path": str(path), "exists": False, "error": type(exc).__name__}


def markers() -> list[dict[str, Any]]:
    return [file_summary(path) for path in sorted(HOME.glob(".tunnel_to_*")) if path.is_file()]


def lock_available(path: Path) -> bool | None:
    try:
        descriptor = os.open(path, os.O_RDWR)
    except (FileNotFoundError, PermissionError, OSError):
        return None
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return False
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        return True
    finally:
        os.close(descriptor)


def snapshot(label: str) -> dict[str, Any]:
    process_state = processes()
    listen_state = listeners()
    marker_state = markers()
    return {
        "label": label,
        "processes": {
            name: {"count": len(items), "items": items}
            for name, items in process_state.items()
        },
        "listeners": {
            port: {"count": len(items), "items": items}
            for port, items in listen_state.items()
        },
        "markers": {"count": len(marker_state), "items": marker_state},
        "keeper_lock_available": lock_available(HOME / ".keeper.lock"),
        "files": {
            "authorized_keys": file_summary(HOME / ".ssh/authorized_keys"),
            "stignore": file_summary(REPO / ".stignore"),
            "known_hosts": file_summary(HOME / ".ssh/known_hosts"),
        },
    }


def temporary_lock_control() -> bool:
    with tempfile.NamedTemporaryFile(prefix="m2-hub-lock-control-") as first:
        with open(first.name, "rb") as second:
            fcntl.flock(first.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                try:
                    fcntl.flock(second.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    return True
                return False
            finally:
                fcntl.flock(first.fileno(), fcntl.LOCK_UN)


def self_test() -> tuple[dict[str, Any], bool]:
    state = snapshot("self_test_state")
    keeper_items = state["processes"]["keeper"]["items"]
    checks = {
        "listener_open_22000": state["listeners"]["22000"]["count"] > 0,
        "listener_open_8384": state["listeners"]["8384"]["count"] > 0,
        "listener_closed_22001": state["listeners"]["22001"]["count"] == 0,
        "process_keeper_present": state["processes"]["keeper"]["count"] == 1,
        "process_syncthing_present": state["processes"]["syncthing"]["count"] > 0,
        "process_absent_control": state["processes"]["absent_control"]["count"] == 0,
        "marker_expected_present": (
            state["markers"]["count"] == 1
            and state["markers"]["items"][0]["path"] == str(HOME / ".tunnel_to_philip")
        ),
        "marker_absent_control": not ABSENT_MARKER.exists(),
        "temporary_lock_contention_detected": temporary_lock_control(),
        "keeper_lock_held": state["keeper_lock_available"] is False,
        "keeper_fd9_lock_reported": (
            len(keeper_items) == 1 and keeper_items[0]["fd9"].get("write_flock_held") is True
        ),
    }
    passed = all(checks.values())
    return {"self_test": checks, "result": "PASS" if passed else "FAIL", "state": state}, passed


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--label")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test == bool(args.label):
        parser.error("exactly one of --self-test or --label is required")
    if args.self_test:
        result, passed = self_test()
        print(json.dumps(result, indent=2, sort_keys=True))
        return 0 if passed else 1
    print(json.dumps(snapshot(args.label), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
