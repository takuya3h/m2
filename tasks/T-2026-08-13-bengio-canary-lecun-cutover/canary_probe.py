#!/usr/bin/env python3
"""Secret-safe local state probe for the bengio canary cutover."""

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
ABSENT_PROCESS = "m2_canary_process_that_does_not_exist_91d2"
ABSENT_MARKER = HOME / ".tunnel_to_m2_canary_that_does_not_exist_91d2"
PHILIP_ENDPOINTS = ("philip", "192.168.196.150")
LECUN_ENDPOINTS = ("lecun", "192.168.196.176")


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


def sanitize_argv(argv: list[str]) -> list[str]:
    result: list[str] = []
    redact_next = False
    for value in argv:
        lowered = value.lower()
        if redact_next:
            result.append("<redacted>")
            redact_next = False
        elif any(token in lowered for token in ("apikey=", "api-key=", "token=", "password=")):
            result.append(value.split("=", 1)[0] + "=<redacted>")
        else:
            result.append(value)
            redact_next = lowered in {"--apikey", "--api-key", "--token", "--password"}
    return result


def process_matches(argv: list[str], comm: str) -> dict[str, bool]:
    basenames = {Path(arg).name for arg in argv if arg}
    joined = " ".join(argv)
    is_forward = (
        (comm == "ssh" or "ssh" in basenames)
        and "22001:127.0.0.1:22000" in joined
    )
    return {
        "keeper": "keeper.sh" in basenames,
        "m2_sync": "m2-sync.sh" in basenames,
        "syncthing": comm == "syncthing" or "syncthing" in basenames,
        "ssh_local_forward": is_forward,
        "ssh_forward_philip": is_forward and any(value in joined for value in PHILIP_ENDPOINTS),
        "ssh_forward_lecun": is_forward and any(value in joined for value in LECUN_ENDPOINTS),
        "absent_control": ABSENT_PROCESS in joined,
    }


def open_fds_for_path(target: Path) -> list[dict[str, int]]:
    holders: list[dict[str, int]] = []
    for proc_dir in Path("/proc").iterdir():
        if not proc_dir.name.isdigit():
            continue
        try:
            descriptors = list((proc_dir / "fd").iterdir())
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
        for descriptor in descriptors:
            try:
                if os.readlink(descriptor) == str(target):
                    holders.append({"pid": int(proc_dir.name), "fd": int(descriptor.name)})
            except (FileNotFoundError, PermissionError, ProcessLookupError, OSError, ValueError):
                continue
    return sorted(holders, key=lambda item: (item["pid"], item["fd"]))


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
    categories = (
        "keeper",
        "m2_sync",
        "syncthing",
        "ssh_local_forward",
        "ssh_forward_philip",
        "ssh_forward_lecun",
        "absent_control",
    )
    result: dict[str, list[dict[str, Any]]] = {name: [] for name in categories}
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
                "cmdline": sanitize_argv(argv),
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
        try:
            lines = (Path("/proc/net") / table_name).read_text().splitlines()[1:]
        except (FileNotFoundError, PermissionError):
            continue
        for line in lines:
            fields = line.split()
            if len(fields) < 10 or fields[3] != "0A":
                continue
            raw_address, raw_port = fields[1].split(":")
            port = int(raw_port, 16)
            if port in PORTS:
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
        info = path.stat()
        return {
            "path": str(path),
            "exists": True,
            "mode": f"{stat.S_IMODE(info.st_mode):03o}",
            "bytes": len(data),
            "line_count": len(data.splitlines()),
            "mtime_ns": info.st_mtime_ns,
            "sha256": hashlib.sha256(data).hexdigest(),
        }
    except (FileNotFoundError, PermissionError, OSError) as exc:
        return {"path": str(path), "exists": False, "error": type(exc).__name__}


def syncthing_config_path() -> Path | None:
    candidates = (
        HOME / ".local/state/syncthing/config.xml",
        HOME / ".config/syncthing/config.xml",
    )
    return next((path for path in candidates if path.is_file()), None)


def marker_summary(path: Path) -> dict[str, Any]:
    result = file_summary(path)
    if not result.get("exists"):
        return result
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
        result["key_path"] = lines[0] if lines else ""
        result["hub_address"] = lines[1] if len(lines) > 1 else path.name.removeprefix(".tunnel_to_")
    except (UnicodeError, OSError):
        result["parse_error"] = True
    return result


def markers() -> list[dict[str, Any]]:
    return [marker_summary(path) for path in sorted(HOME.glob(".tunnel_to_*")) if path.is_file()]


def snapshot(label: str) -> dict[str, Any]:
    process_state = processes()
    listen_state = listeners()
    marker_state = markers()
    config_path = syncthing_config_path()
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
            "keeper": file_summary(HOME / "bin/keeper.sh"),
            "m2_sync": file_summary(HOME / "bin/m2-sync.sh"),
            "authorized_keys": file_summary(HOME / ".ssh/authorized_keys"),
            "known_hosts": file_summary(HOME / ".ssh/known_hosts"),
            "stignore": file_summary(REPO / ".stignore"),
            "sync_pause": file_summary(REPO / ".sync-pause"),
            "sync_alerts": file_summary(HOME / "claude-sync/sync-alerts.log"),
            "syncthing_config": (
                file_summary(config_path)
                if config_path is not None
                else {"exists": False, "error": "not_found"}
            ),
        },
    }


def route_state(philip_addresses: list[str], lecun_addresses: list[str]) -> str:
    localhost = "tcp://127.0.0.1:22001"
    count = philip_addresses.count(localhost) + lecun_addresses.count(localhost)
    if count == 0:
        return "missing"
    if count > 1:
        return "duplicate"
    if localhost in philip_addresses:
        return "philip_only"
    if localhost in lecun_addresses:
        return "lecun_only"
    return "unexpected"


def secret_hits(text: str, secret_values: list[str]) -> int:
    return sum(text.count(value) for value in secret_values if value)


def temporary_lock_control() -> dict[str, bool]:
    with tempfile.NamedTemporaryFile(prefix="m2-canary-lock-control-") as first:
        with open(first.name, "rb") as second:
            fcntl.flock(first.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                try:
                    fcntl.flock(second.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    contended = False
                except BlockingIOError:
                    contended = True
            finally:
                fcntl.flock(first.fileno(), fcntl.LOCK_UN)
            try:
                fcntl.flock(second.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                released = True
                fcntl.flock(second.fileno(), fcntl.LOCK_UN)
            except BlockingIOError:
                released = False
    return {"contention_detected": contended, "released_lock_available": released}


def self_test() -> tuple[dict[str, Any], bool]:
    state = snapshot("self_test_state")
    keeper_items = state["processes"]["keeper"]["items"]
    lock_control = temporary_lock_control()
    decoy = "M2_CANARY_DECOY_SECRET_b880f2"
    normal_json = json.dumps(state, sort_keys=True)
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
        "temporary_lock_contention_detected": lock_control["contention_detected"],
        "temporary_lock_release_detected": lock_control["released_lock_available"],
        "keeper_lock_held": state["keeper_lock_available"] is False,
        "keeper_fd9_lock_reported": (
            len(keeper_items) == 1 and keeper_items[0]["fd9"].get("write_flock_held") is True
        ),
        "route_old_distinguished": route_state(["tcp://127.0.0.1:22001"], []) == "philip_only",
        "route_new_distinguished": route_state([], ["tcp://127.0.0.1:22001"]) == "lecun_only",
        "route_duplicate_rejected": (
            route_state(["tcp://127.0.0.1:22001"], ["tcp://127.0.0.1:22001"])
            == "duplicate"
        ),
        "route_missing_rejected": route_state([], []) == "missing",
        "decoy_secret_positive_control": secret_hits(decoy, [decoy]) == 1,
        "normal_output_excludes_decoy": secret_hits(normal_json, [decoy]) == 0,
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
