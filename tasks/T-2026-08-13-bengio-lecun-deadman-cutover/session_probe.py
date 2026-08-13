#!/usr/bin/env python3
"""Measure whether the current execution session is independent of cutover targets."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
from pathlib import Path
from typing import Any

HOME = Path("/home/ubuntu")
PROC = Path("/proc")
SSH_PORT = 22
ABSENT_PORT = 65534
CHANGE_PATHS = {
    str(HOME / "bin/keeper.sh"),
    str(HOME / ".tunnel_to_philip"),
    str(HOME / ".tunnel_to_lecun"),
    str(HOME / ".local/state/syncthing/config.xml"),
}
PROTECTED_FAILURES = {
    "transaction_owner_missing",
    "lease_stalled",
    "known_cutover_check_failed",
}
UNPROTECTED_FAILURES = {
    "host_stopped",
    "host_restarted",
    "kernel_stopped",
    "storage_failed",
    "guard_and_transaction_missing",
}
SECRET_ENV_NAMES = {
    "NOTION_API_KEY",
    "WANDB_API_KEY",
    "SYNCTHING_API_KEY",
    "GITHUB_TOKEN",
    "GH_TOKEN",
}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)(api[_-]?key|token|secret|password)=([^\s]+)"
)
SECRET_FLAGS = {
    "--api-key",
    "--apikey",
    "--password",
    "--secret",
    "--token",
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def file_summary(path: Path) -> dict[str, Any]:
    try:
        info = path.stat()
    except OSError:
        return {"path": str(path), "exists": False}
    summary: dict[str, Any] = {
        "path": str(path),
        "exists": True,
        "mode": f"{stat.S_IMODE(info.st_mode):03o}",
        "bytes": info.st_size,
    }
    if path.is_file():
        try:
            summary["sha256"] = sha256_file(path)
        except OSError:
            summary["sha256"] = "UNKNOWN"
    return summary


def secret_values(extra: list[str] | None = None) -> list[str]:
    values = [os.environ.get(name, "") for name in SECRET_ENV_NAMES]
    values.extend(extra or [])
    return sorted({value for value in values if value}, key=len, reverse=True)


def sanitize_argv(argv: list[str], secrets: list[str]) -> list[str]:
    sanitized: list[str] = []
    redact_next = False
    for value in argv:
        if redact_next:
            sanitized.append("<redacted>")
            redact_next = False
            continue
        cleaned = value
        for secret in secrets:
            cleaned = cleaned.replace(secret, "<redacted>")
        cleaned = SECRET_ASSIGNMENT.sub(lambda match: f"{match.group(1)}=<redacted>", cleaned)
        sanitized.append(cleaned)
        redact_next = value.lower() in SECRET_FLAGS
    return sanitized


def parse_stat(text: str) -> tuple[int, str, int, int]:
    before, after = text.rstrip().rsplit(")", 1)
    pid_text, comm = before.split("(", 1)
    fields = after.split()
    return int(pid_text), comm, int(fields[1]), int(fields[19])


def process_info(pid: int, secrets: list[str]) -> dict[str, Any]:
    root = PROC / str(pid)
    stat_text = (root / "stat").read_text(encoding="utf-8")
    parsed_pid, comm, ppid, start_tick = parse_stat(stat_text)
    raw = (root / "cmdline").read_bytes().split(b"\0")
    argv = [item.decode("utf-8", errors="replace") for item in raw if item]
    try:
        exe = str((root / "exe").readlink())
    except OSError:
        exe = "UNKNOWN"
    return {
        "pid": parsed_pid,
        "ppid": ppid,
        "start_tick": start_tick,
        "comm": comm,
        "exe": exe,
        "cmdline": sanitize_argv(argv, secrets),
    }


def ancestor_chain(start_pid: int, secrets: list[str]) -> list[dict[str, Any]]:
    chain: list[dict[str, Any]] = []
    seen: set[int] = set()
    pid = start_pid
    while pid > 0 and pid not in seen:
        seen.add(pid)
        try:
            item = process_info(pid, secrets)
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            break
        chain.append(item)
        if item["ppid"] == pid:
            break
        pid = item["ppid"]
    return chain


def all_processes(secrets: list[str]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for entry in PROC.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            items.append(process_info(int(entry.name), secrets))
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
            continue
    return items


def parse_listeners(text: str, port: int) -> list[dict[str, Any]]:
    listeners: list[dict[str, Any]] = []
    for line in text.splitlines()[1:]:
        fields = line.split()
        if len(fields) < 10 or fields[3] != "0A":
            continue
        address_hex, port_hex = fields[1].split(":")
        if int(port_hex, 16) != port:
            continue
        listeners.append(
            {
                "address_hex": address_hex,
                "port": port,
                "inode": int(fields[9]),
            }
        )
    return listeners


def listeners_for(port: int) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    for name in ("net/tcp", "net/tcp6"):
        try:
            found.extend(parse_listeners((PROC / name).read_text(encoding="ascii"), port))
        except OSError:
            continue
    return found


def identity_matches(expected: dict[str, int], observed: dict[str, int]) -> bool:
    return (
        expected.get("pid", 0) > 1
        and expected.get("pid") == observed.get("pid")
        and expected.get("start_tick", 0) > 0
        and expected.get("start_tick") == observed.get("start_tick")
    )


def ancestors_are_independent(chain: list[dict[str, Any]]) -> bool:
    forbidden = ("keeper.sh", "syncthing", "ssh -n", "ssh -f", "ssh -l")
    for item in chain:
        rendered = " ".join(item.get("cmdline", [])).lower()
        if any(token in rendered for token in forbidden):
            return False
    return True


def is_session_sshd(item: dict[str, Any]) -> bool:
    rendered = " ".join(item.get("cmdline", []))
    return (
        item.get("comm") == "sshd"
        and item.get("pid", 0) > 1
        and ("@" in rendered or "[priv]" in rendered)
    )


def residual_risks_valid(protected: set[str], unprotected: set[str]) -> bool:
    return protected == PROTECTED_FAILURES and unprotected == UNPROTECTED_FAILURES


def secret_hits(payload: Any, secrets: list[str]) -> int:
    rendered = json.dumps(payload, sort_keys=True)
    return sum(rendered.count(secret) for secret in secrets if secret)


def self_test() -> tuple[dict[str, Any], bool]:
    fixture = """  sl  local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode
   0: 00000000:0016 00000000:0000 0A 0:0 00:0 0 0 0 111 1 0
   1: 0100007F:3039 00000000:0000 0A 0:0 00:0 0 0 0 222 1 0
"""
    safe_chain = [
        {
            "pid": 30,
            "ppid": 20,
            "start_tick": 300,
            "comm": "python",
            "cmdline": ["python", "transaction.py"],
        },
        {
            "pid": 20,
            "ppid": 10,
            "start_tick": 200,
            "comm": "sshd",
            "cmdline": ["sshd: ubuntu@pts/5"],
        },
    ]
    keeper_chain = safe_chain + [
        {
            "pid": 10,
            "ppid": 1,
            "start_tick": 100,
            "comm": "bash",
            "cmdline": ["/bin/bash", str(HOME / "bin/keeper.sh")],
        }
    ]
    listener_only_chain = [
        {
            "pid": 1,
            "ppid": 0,
            "start_tick": 1,
            "comm": "sshd",
            "cmdline": ["sshd: /usr/sbin/sshd -D [listener]"],
        }
    ]
    expected = {"pid": 30, "start_tick": 300}
    decoy = "M2_DEADMAN_DECOY_SECRET_74a6"
    sanitized = sanitize_argv(["tool", f"token={decoy}", decoy], [decoy])
    checks = {
        "ancestor_chain_safe": ancestors_are_independent(safe_chain),
        "keeper_ancestor_rejected": not ancestors_are_independent(keeper_chain),
        "session_sshd_detected": any(is_session_sshd(item) for item in safe_chain),
        "listener_only_not_session": not any(
            is_session_sshd(item) for item in listener_only_chain
        ),
        "owner_identity_accepted": identity_matches(expected, expected),
        "pid_reuse_tick_rejected": not identity_matches(expected, {"pid": 30, "start_tick": 301}),
        "existing_listener_detected": len(parse_listeners(fixture, SSH_PORT)) == 1,
        "absent_listener_distinguished": len(parse_listeners(fixture, ABSENT_PORT)) == 0,
        "listener_inode_reported": parse_listeners(fixture, SSH_PORT)[0]["inode"] == 111,
        "decoy_secret_positive_control": secret_hits([decoy], [decoy]) == 1,
        "secret_redacted": secret_hits(sanitized, [decoy]) == 0,
        "residual_risks_exact": residual_risks_valid(PROTECTED_FAILURES, UNPROTECTED_FAILURES),
        "host_stop_cannot_be_protected": not residual_risks_valid(
            PROTECTED_FAILURES | {"host_stopped"}, UNPROTECTED_FAILURES - {"host_stopped"}
        ),
    }
    passed = all(checks.values())
    return {"checks": checks, "result": "PASS" if passed else "FAIL"}, passed


def live_snapshot(label: str) -> tuple[dict[str, Any], bool]:
    secrets = secret_values()
    chain = ancestor_chain(os.getpid(), secrets)
    processes = all_processes(secrets)
    sshd = [item for item in processes if item["comm"] == "sshd"]
    ssh_listeners = listeners_for(SSH_PORT)
    absent_listeners = listeners_for(ABSENT_PORT)
    ancestor_pids = {item["pid"] for item in chain}
    sshd_ancestors = [item for item in chain if is_session_sshd(item)]
    target_ancestors = [
        item for item in chain if not ancestors_are_independent([item])
    ]
    sshd_paths = {
        item["exe"] for item in sshd if item.get("exe") not in {None, "UNKNOWN"}
    } | {"/etc/ssh/sshd_config"}
    checks = {
        "ancestor_chain_reaches_sshd": bool(sshd_ancestors),
        "cutover_target_not_ancestor": not target_ancestors,
        "sshd_process_present": bool(sshd),
        "ssh_listener_present": bool(ssh_listeners),
        "ssh_listener_inode_unique": len({item["inode"] for item in ssh_listeners}) == len(ssh_listeners),
        "absent_port_closed": not absent_listeners,
        "sshd_paths_disjoint_from_changes": not (sshd_paths & CHANGE_PATHS),
    }
    payload = {
        "label": label,
        "self": {"pid": os.getpid(), "start_tick": chain[0]["start_tick"] if chain else "UNKNOWN"},
        "ancestor_chain": chain,
        "ancestor_pids": sorted(ancestor_pids),
        "sshd_processes": sshd,
        "listeners": {str(SSH_PORT): ssh_listeners, str(ABSENT_PORT): absent_listeners},
        "sshd_files": {
            "binary": file_summary(Path("/usr/sbin/sshd")),
            "config": file_summary(Path("/etc/ssh/sshd_config")),
        },
        "change_paths": sorted(CHANGE_PATHS),
        "outer_port_mapping": "UNKNOWN",
        "protected_failures": sorted(PROTECTED_FAILURES),
        "unprotected_failures": sorted(UNPROTECTED_FAILURES),
        "checks": checks,
    }
    checks["output_contains_no_known_secret"] = secret_hits(payload, secrets) == 0
    passed = all(checks.values())
    payload["result"] = "PASS" if passed else "FAIL"
    return payload, passed


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--label")
    args = parser.parse_args()
    if args.self_test:
        payload, passed = self_test()
    else:
        payload, passed = live_snapshot(args.label)
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
