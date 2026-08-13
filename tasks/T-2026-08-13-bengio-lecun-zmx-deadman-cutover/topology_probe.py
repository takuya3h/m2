#!/usr/bin/env python3
"""Classify the current transaction ancestry as direct SSH or verified zmx."""

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
    "known_cutover_check_failed",
    "lease_stalled",
    "owner_identity_changed",
    "transaction_owner_missing",
}
UNPROTECTED_FAILURES = {
    "guard_and_transaction_missing",
    "host_restarted",
    "host_stopped",
    "kernel_stopped",
    "storage_failed",
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
SECRET_FLAGS = {"--api-key", "--apikey", "--password", "--secret", "--token"}


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
    result: dict[str, Any] = {
        "path": str(path),
        "exists": True,
        "mode": f"{stat.S_IMODE(info.st_mode):03o}",
        "bytes": info.st_size,
        "device": info.st_dev,
        "inode": info.st_ino,
    }
    if path.is_file():
        try:
            result["sha256"] = sha256_file(path)
        except OSError:
            result["sha256"] = "UNKNOWN"
    return result


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
    parsed_pid, comm, ppid, start_tick = parse_stat(
        (root / "stat").read_text(encoding="utf-8")
    )
    raw = (root / "cmdline").read_bytes().split(b"\0")
    argv = [item.decode("utf-8", errors="replace") for item in raw if item]
    try:
        exe = (root / "exe").resolve(strict=True)
        exe_summary = file_summary(exe)
    except (OSError, RuntimeError):
        exe = None
        exe_summary = {"path": "UNKNOWN", "exists": False}
    return {
        "pid": parsed_pid,
        "ppid": ppid,
        "start_tick": start_tick,
        "comm": comm,
        "exe": str(exe) if exe is not None else "UNKNOWN",
        "exe_summary": exe_summary,
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
        except (FileNotFoundError, PermissionError, ProcessLookupError, ValueError):
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
            {"address_hex": address_hex, "port": port, "inode": int(fields[9])}
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


def valid_binary_identity(item: dict[str, Any]) -> bool:
    summary = item.get("exe_summary", {})
    digest = summary.get("sha256", "")
    return (
        item.get("pid", 0) > 0
        and item.get("start_tick", 0) > 0
        and item.get("exe", "UNKNOWN") != "UNKNOWN"
        and summary.get("exists") is True
        and summary.get("device", 0) > 0
        and summary.get("inode", 0) > 0
        and isinstance(digest, str)
        and len(digest) == 64
    )


def is_session_sshd(item: dict[str, Any]) -> bool:
    rendered = " ".join(item.get("cmdline", []))
    return (
        item.get("comm") == "sshd"
        and item.get("pid", 0) > 1
        and ("@" in rendered or "[priv]" in rendered)
    )


def is_pid1_listener(item: dict[str, Any]) -> bool:
    rendered = " ".join(item.get("cmdline", [])).lower()
    return (
        item.get("pid") == 1
        and item.get("comm") == "sshd"
        and "listener" in rendered
        and item.get("start_tick", 0) > 0
    )


def forbidden_ancestor(item: dict[str, Any]) -> bool:
    rendered = " ".join(item.get("cmdline", [])).lower()
    if "keeper.sh" in rendered or "/bin/syncthing" in rendered:
        return True
    if item.get("comm") == "ssh" or Path(item.get("exe", "")).name == "ssh":
        return any(flag in item.get("cmdline", []) for flag in ("-L", "-R", "-D"))
    return False


def identity_subset(item: dict[str, Any]) -> dict[str, Any]:
    summary = item.get("exe_summary", {})
    return {
        "pid": item.get("pid"),
        "ppid": item.get("ppid"),
        "start_tick": item.get("start_tick"),
        "comm": item.get("comm"),
        "exe": item.get("exe"),
        "exe_device": summary.get("device"),
        "exe_inode": summary.get("inode"),
        "exe_sha256": summary.get("sha256"),
    }


def identity_matches(expected: dict[str, Any], observed: dict[str, Any]) -> bool:
    return expected == observed and all(
        expected.get(key) not in (None, "", 0, "UNKNOWN")
        for key in ("pid", "start_tick", "exe", "exe_device", "exe_inode", "exe_sha256")
    )


def classify(
    chain: list[dict[str, Any]],
    all_items: list[dict[str, Any]],
    ssh_listeners: list[dict[str, Any]],
) -> tuple[str, dict[str, Any], list[str]]:
    failures: list[str] = []
    if any(forbidden_ancestor(item) for item in chain):
        failures.append("cutover_target_or_tunnel_is_ancestor")
    session_items = [item for item in chain if is_session_sshd(item)]
    chain_zmx = [item for item in chain if item.get("comm") == "zmx"]
    all_zmx = [item for item in all_items if item.get("comm") == "zmx"]
    pid1 = next((item for item in chain if item.get("pid") == 1), None)

    if len(chain_zmx) > 1:
        failures.append("multiple_zmx_in_ancestor_chain")
    if chain_zmx and len(all_zmx) != 1:
        failures.append(f"host_zmx_count_not_one:{len(all_zmx)}")

    direct = bool(session_items) and not chain_zmx
    verified_zmx = (
        not session_items
        and len(chain_zmx) == 1
        and len(all_zmx) == 1
        and chain_zmx[0].get("ppid") == 1
        and valid_binary_identity(chain_zmx[0])
        and pid1 is not None
        and is_pid1_listener(pid1)
        and bool(ssh_listeners)
    )
    if direct == verified_zmx:
        failures.append("topology_is_not_exactly_one_allowed_class")
        return "rejected", {}, failures
    if failures:
        return "rejected", {}, failures
    if direct:
        identity = {
            "classification": "direct_ssh",
            "session_sshd": [identity_subset(item) for item in session_items],
            "listener_inodes": sorted({item["inode"] for item in ssh_listeners}),
        }
        return "direct_ssh", identity, []
    identity = {
        "classification": "verified_zmx",
        "zmx": identity_subset(chain_zmx[0]),
        "pid1_sshd": identity_subset(pid1),
        "listener_inodes": sorted({item["inode"] for item in ssh_listeners}),
    }
    return "verified_zmx", identity, []


def residual_risks_valid(protected: set[str], unprotected: set[str]) -> bool:
    return protected == PROTECTED_FAILURES and unprotected == UNPROTECTED_FAILURES


def secret_hits(payload: Any, secrets: list[str]) -> int:
    rendered = json.dumps(payload, sort_keys=True)
    return sum(rendered.count(secret) for secret in secrets if secret)


def fixture_process(
    pid: int,
    ppid: int,
    comm: str,
    argv: list[str],
    *,
    tick: int | None = None,
    valid_binary: bool = True,
) -> dict[str, Any]:
    summary = {
        "path": f"/fixture/{comm}",
        "exists": valid_binary,
        "device": 10 if valid_binary else 0,
        "inode": pid + 100 if valid_binary else 0,
        "sha256": "a" * 64 if valid_binary else "UNKNOWN",
    }
    return {
        "pid": pid,
        "ppid": ppid,
        "start_tick": tick if tick is not None else pid * 10,
        "comm": comm,
        "exe": f"/fixture/{comm}" if valid_binary else "UNKNOWN",
        "exe_summary": summary,
        "cmdline": argv,
    }


def self_test() -> tuple[dict[str, Any], bool]:
    listener_fixture = """  sl  local_address rem_address st tx_queue rx_queue tr tm->when retrnsmt uid timeout inode
   0: 00000000:0016 00000000:0000 0A 0:0 00:0 0 0 0 111 1 0
   1: 0100007F:3039 00000000:0000 0A 0:0 00:0 0 0 0 222 1 0
"""
    listeners = parse_listeners(listener_fixture, SSH_PORT)
    pid1 = fixture_process(1, 0, "sshd", ["sshd: listener"])
    zmx = fixture_process(20, 1, "zmx", ["zmx", "a", "phone"])
    txn = fixture_process(30, 20, "python", ["python", "guarded_cutover.py"])
    verified_chain = [txn, zmx, pid1]
    classification, identity, failures = classify(verified_chain, verified_chain, listeners)

    session = fixture_process(40, 1, "sshd", ["sshd: ubuntu@pts/1"])
    direct_chain = [txn, session, pid1]
    direct_class, _direct_identity, direct_failures = classify(
        direct_chain, direct_chain, listeners
    )

    def rejected(chain: list[dict[str, Any]], all_items: list[dict[str, Any]], ls: list[dict[str, Any]]) -> bool:
        return classify(chain, all_items, ls)[0] == "rejected"

    name_only = fixture_process(
        20, 1, "zmx", ["zmx", "a", "phone"], valid_binary=False
    )
    second_zmx = fixture_process(21, 1, "zmx", ["zmx", "a", "other"])
    non_sshd_pid1 = fixture_process(1, 0, "init", ["init"])
    orphan = fixture_process(20, 1, "worker", ["worker"])
    keeper = fixture_process(25, 20, "bash", ["bash", str(HOME / "bin/keeper.sh")])
    syncthing = fixture_process(25, 20, "syncthing", [str(HOME / "bin/syncthing")])
    tunnel = fixture_process(25, 20, "ssh", ["ssh", "-L", "22001:localhost:22000"])
    changed_tick = json.loads(json.dumps(identity))
    changed_tick["zmx"]["start_tick"] += 1
    changed_binary = json.loads(json.dumps(identity))
    changed_binary["zmx"]["exe_sha256"] = "b" * 64
    decoy = "M2_TOPOLOGY_DECOY_SECRET_9f13"
    sanitized = sanitize_argv(["tool", f"token={decoy}", decoy], [decoy])

    checks = {
        "direct_ssh_fixture_passes": direct_class == "direct_ssh" and not direct_failures,
        "verified_zmx_fixture_passes": classification == "verified_zmx" and not failures,
        "listener_only_is_not_direct": rejected([txn, pid1], [txn, pid1], listeners),
        "name_only_zmx_rejected": rejected([txn, name_only, pid1], [txn, name_only, pid1], listeners),
        "multiple_zmx_rejected": rejected(
            verified_chain, verified_chain + [second_zmx], listeners
        ),
        "general_orphan_rejected": rejected([txn, orphan, pid1], [txn, orphan, pid1], listeners),
        "pid1_non_sshd_rejected": rejected(
            [txn, zmx, non_sshd_pid1], [txn, zmx, non_sshd_pid1], listeners
        ),
        "listener_missing_rejected": rejected(verified_chain, verified_chain, []),
        "keeper_ancestor_rejected": rejected(
            [txn, keeper, zmx, pid1], [txn, keeper, zmx, pid1], listeners
        ),
        "syncthing_ancestor_rejected": rejected(
            [txn, syncthing, zmx, pid1], [txn, syncthing, zmx, pid1], listeners
        ),
        "outbound_tunnel_ancestor_rejected": rejected(
            [txn, tunnel, zmx, pid1], [txn, tunnel, zmx, pid1], listeners
        ),
        "identity_exact_match": identity_matches(identity["zmx"], identity["zmx"]),
        "tick_change_rejected": not identity_matches(identity["zmx"], changed_tick["zmx"]),
        "binary_change_rejected": not identity_matches(identity["zmx"], changed_binary["zmx"]),
        "existing_listener_detected": len(listeners) == 1,
        "absent_listener_distinguished": len(parse_listeners(listener_fixture, ABSENT_PORT)) == 0,
        "listener_inode_reported": listeners[0]["inode"] == 111,
        "decoy_secret_positive_control": secret_hits([decoy], [decoy]) == 1,
        "secret_redacted": secret_hits(sanitized, [decoy]) == 0,
        "residual_risks_exact": residual_risks_valid(PROTECTED_FAILURES, UNPROTECTED_FAILURES),
        "host_stop_cannot_be_protected": not residual_risks_valid(
            PROTECTED_FAILURES | {"host_stopped"},
            UNPROTECTED_FAILURES - {"host_stopped"},
        ),
    }
    passed = all(checks.values())
    return {"checks": checks, "result": "PASS" if passed else "FAIL"}, passed


def live_snapshot(label: str) -> tuple[dict[str, Any], bool]:
    secrets = secret_values()
    chain = ancestor_chain(os.getpid(), secrets)
    processes = all_processes(secrets)
    ssh_listeners = listeners_for(SSH_PORT)
    absent_listeners = listeners_for(ABSENT_PORT)
    classification, identity, failures = classify(chain, processes, ssh_listeners)
    chain_pids = {item["pid"] for item in chain}
    session_sshd_outside = [
        identity_subset(item)
        for item in processes
        if is_session_sshd(item) and item["pid"] not in chain_pids
    ]
    zmx_processes = [identity_subset(item) for item in processes if item["comm"] == "zmx"]
    infrastructure_paths = {
        item["exe"]
        for item in chain
        if item.get("comm") in {"zmx", "sshd"} and item.get("exe") != "UNKNOWN"
    } | {"/etc/ssh/sshd_config"}
    checks = {
        "classification_allowed": classification in {"direct_ssh", "verified_zmx"},
        "classification_unique": not failures,
        "cutover_targets_not_ancestors": not any(forbidden_ancestor(item) for item in chain),
        "infrastructure_paths_disjoint": not (infrastructure_paths & CHANGE_PATHS),
        "ssh_listener_present": bool(ssh_listeners),
        "absent_listener_closed": not absent_listeners,
    }
    payload: dict[str, Any] = {
        "label": label,
        "classification": classification,
        "classification_identity": identity,
        "classification_failures": failures,
        "self": identity_subset(chain[0]) if chain else "UNKNOWN",
        "ancestor_chain": chain,
        "session_sshd_outside_chain": session_sshd_outside,
        "zmx_processes": zmx_processes,
        "listeners": {str(SSH_PORT): ssh_listeners, str(ABSENT_PORT): absent_listeners},
        "infrastructure_files": {
            "zmx": file_summary(Path(identity.get("zmx", {}).get("exe", "/nonexistent"))),
            "sshd": file_summary(Path("/usr/sbin/sshd")),
            "sshd_config": file_summary(Path("/etc/ssh/sshd_config")),
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
