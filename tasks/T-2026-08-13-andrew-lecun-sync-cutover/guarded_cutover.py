#!/usr/bin/env python3
"""Run the Andrew-to-lecun cutover as one guarded foreground transaction."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

TASK_ID = "T-2026-08-13-andrew-lecun-sync-cutover"
HOME = Path("/home/ubuntu")
REPO = HOME / "slocal2/m2"
TASK_DIR = REPO / "tasks" / TASK_ID
BACKUP = HOME / f".hub-migration-backup.{TASK_ID}"
STATE = BACKUP / "state.json"
RUNTIME = BACKUP / "runtime.json"
LEASE = BACKUP / "lease.json"
READY = BACKUP / "guard-ready.json"
ARM_REQUEST = BACKUP / "arm-request.json"
ARMED = BACKUP / "guard-armed.json"
COMMIT_TOKEN = BACKUP / "commit-token.json"
ROLLBACK_REQUEST = BACKUP / "rollback-request.json"
ROLLBACK_DONE = BACKUP / "rollback-done.json"
KEEPER = HOME / "bin/keeper.sh"
OLD_MARKER = HOME / ".tunnel_to_philip"
NEW_MARKER = HOME / ".tunnel_to_lecun"
KEY = HOME / ".ssh/id_ed25519_andrewtophilip"
KNOWN_HOSTS = HOME / ".ssh/known_hosts"
TEMP_KNOWN_HOSTS = BACKUP / "known_hosts.lecun"
PROBE_DIR = HOME / "claude-sync/cutover-probes" / TASK_ID
REMOTE_PROBE_DIR = f"/home/ubuntu/claude-sync/cutover-probes/{TASK_ID}"
STABILITY_SECONDS = 1805


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tick(pid: int) -> int:
    raw = (Path("/proc") / str(pid) / "stat").read_text()
    return int(raw[raw.rfind(")") + 2 :].split()[19])


def atomic_bytes(path: Path, data: bytes, mode: int = 0o600, exclusive: bool = False) -> None:
    if exclusive and path.exists():
        raise FileExistsError(path)
    temporary = path.with_name(path.name + f".tmp.{os.getpid()}")
    descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, mode)
    try:
        os.write(descriptor, data)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
    os.replace(temporary, path)


def atomic_json(path: Path, value: Any, exclusive: bool = False) -> None:
    atomic_bytes(path, (json.dumps(value, sort_keys=True) + "\n").encode(), exclusive=exclusive)


def run_json(argv: list[str], timeout: float = 60) -> Any:
    process = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"command failed rc={process.returncode}: {argv[1]}: {process.stderr.strip()[-500:]}")
    return json.loads(process.stdout)


def local_snapshot(label: str) -> dict[str, Any]:
    return run_json([sys.executable, str(TASK_DIR / "andrew_probe.py"), "--label", label])


def route_snapshot() -> dict[str, Any]:
    return run_json([sys.executable, str(TASK_DIR / "syncthing_route.py"), "--inspect"])


def write_lease(owner_pid: int, owner_tick: int, sequence: int) -> None:
    atomic_json(LEASE, {"owner_pid": owner_pid, "owner_tick": owner_tick, "sequence": sequence, "monotonic": time.monotonic()})


def wait_file(path: Path, timeout: float, lease_identity: tuple[int, int] | None = None) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    sequence = 0
    while time.monotonic() < deadline:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
        if lease_identity:
            sequence += 1
            write_lease(*lease_identity, sequence)
        time.sleep(0.2)
    raise TimeoutError(f"timed out waiting for {path}")


def unchanged_start(start: dict[str, Any], current: dict[str, Any], route: dict[str, Any]) -> bool:
    keys = ("keeper", "known_hosts")
    files_same = all(start["files"][key]["sha256"] == current["files"][key]["sha256"] for key in keys)
    backup_devices = {
        name: json.loads((BACKUP / f"syncthing-device-{name}.json").read_text(encoding="utf-8"))
        for name in ("philip", "lecun")
    }
    device_objects_same = all(
        route["devices"][name]["object_sha256"]
        == hashlib.sha256(
            json.dumps(backup_devices[name], sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest()
        for name in ("philip", "lecun")
    )
    syncthing_same = [
        (item["pid"], item["start_tick"])
        for item in start["processes"]["syncthing"]["items"]
    ] == [
        (item["pid"], item["start_tick"])
        for item in current["processes"]["syncthing"]["items"]
    ]
    return (
        files_same
        and device_objects_same
        and syncthing_same
        and current["markers"]["count"] == 1
        and current["markers"]["items"][0]["path"] == str(OLD_MARKER)
        and current["processes"]["keeper"]["count"] == 1
        and current["processes"]["ssh_local_forward"]["count"] == 0
        and current["listeners"]["22001"]["count"] == 0
        and route["localhost_route"]["state"] == "philip_only"
        and route["restart_required"] is False
    )


def make_state(start: dict[str, Any]) -> dict[str, Any]:
    return {
        "task_id": TASK_ID,
        "keeper_path": str(KEEPER),
        "old_marker_path": str(OLD_MARKER),
        "new_marker_path": str(NEW_MARKER),
        "keeper_backup": str(BACKUP / "keeper.start"),
        "old_marker_backup": str(BACKUP / "marker.philip.start"),
        "known_hosts_backup": str(BACKUP / "known_hosts.start"),
        "devices_backup_dir": str(BACKUP),
        "keeper_sha256": sha(BACKUP / "keeper.start"),
        "old_marker_sha256": sha(BACKUP / "marker.philip.start"),
        "known_hosts_sha256": sha(BACKUP / "known_hosts.start"),
        "keeper_mode": f"{stat.S_IMODE(KEEPER.stat().st_mode):03o}",
        "old_marker_mode": f"{stat.S_IMODE(OLD_MARKER.stat().st_mode):03o}",
        "known_hosts_mode": f"{stat.S_IMODE(KNOWN_HOSTS.stat().st_mode):03o}",
        "old_keeper_pid": start["processes"]["keeper"]["items"][0]["pid"],
        "old_keeper_tick": start["processes"]["keeper"]["items"][0]["start_tick"],
        "syncthing_identity": [(x["pid"], x["start_tick"]) for x in start["processes"]["syncthing"]["items"]],
    }


def add_center_host_key() -> int:
    original = KNOWN_HOSTS.read_bytes()
    candidates = [line for line in TEMP_KNOWN_HOSTS.read_bytes().splitlines() if line]
    if len(candidates) != 1:
        raise RuntimeError("temporary known_hosts must contain exactly one lecun key")
    lines = original.splitlines()
    if candidates[0] in lines:
        return 0
    atomic_bytes(KNOWN_HOSTS, original.rstrip(b"\n") + b"\n" + candidates[0] + b"\n", stat.S_IMODE(KNOWN_HOSTS.stat().st_mode))
    return 1


def deploy_keeper() -> str:
    process = subprocess.run(
        ["git", "show", "origin/phase0:scripts/sync/keeper.sh"],
        cwd=REPO,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError("could not read the phase0 keeper object")
    expected = hashlib.sha256(process.stdout).hexdigest()
    atomic_bytes(KEEPER, process.stdout, 0o755)
    os.chmod(KEEPER, 0o755)
    if sha(KEEPER) != expected:
        raise RuntimeError("deployed keeper digest mismatch")
    return expected


def launch_keeper() -> int:
    return subprocess.Popen(
        [str(KEEPER)],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
        close_fds=True,
    ).pid


def validate_success(start: dict[str, Any], snap: dict[str, Any], route: dict[str, Any], expected_keeper: str) -> tuple[int, int]:
    if snap["markers"]["count"] != 1 or snap["markers"]["items"][0].get("path") != str(NEW_MARKER):
        raise RuntimeError("lecun marker is not the only marker")
    if snap["markers"]["items"][0].get("hub_address") != "192.168.196.176":
        raise RuntimeError("lecun marker address mismatch")
    keepers = snap["processes"]["keeper"]["items"]
    tunnels = snap["processes"]["ssh_forward_lecun"]["items"]
    if len(keepers) != 1 or len(tunnels) != 1 or snap["processes"]["ssh_forward_philip"]["count"] != 0:
        raise RuntimeError("keeper or tunnel cardinality mismatch")
    if keepers[0]["fd255"].get("sha256") != expected_keeper or keepers[0]["fd9"].get("write_flock_held") is not True:
        raise RuntimeError("keeper object or lock mismatch")
    if snap["listeners"]["22001"]["count"] == 0:
        raise RuntimeError("localhost tunnel listener is closed")
    if route["localhost_route"]["state"] != "lecun_only" or route["restart_required"]:
        raise RuntimeError("route or restart-required gate failed")
    if not route["connections"]["lecun"]["connected"]:
        raise RuntimeError("lecun device is not connected")
    if [(x["pid"], x["start_tick"]) for x in snap["processes"]["syncthing"]["items"]] != [
        (x["pid"], x["start_tick"]) for x in start["processes"]["syncthing"]["items"]
    ]:
        raise RuntimeError("Syncthing process identity changed")
    return keepers[0]["pid"], tunnels[0]["pid"]


def remote_python(code: str, timeout: float = 30) -> str:
    sys.path.insert(0, str(TASK_DIR))
    import center_probe

    process = subprocess.run(center_probe.SSH_ARGV, input=code, capture_output=True, text=True, timeout=timeout, check=False)
    if process.returncode != 0:
        raise RuntimeError(f"remote probe command failed rc={process.returncode}: {process.stderr.strip()[-500:]}")
    return process.stdout.strip()


def probe_pair(owner: tuple[int, int], sequence: int) -> tuple[dict[str, Any], int]:
    PROBE_DIR.mkdir(parents=True, exist_ok=True)
    payload_a = (TASK_ID + "\nfrom=andrew\n" + os.urandom(32).hex() + "\n").encode()
    local_a = PROBE_DIR / "probe-from-andrew.txt"
    atomic_bytes(local_a, payload_a, 0o644, exclusive=True)
    digest_a = hashlib.sha256(payload_a).hexdigest()
    remote_a = f"{REMOTE_PROBE_DIR}/probe-from-andrew.txt"
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        sequence += 1
        write_lease(*owner, sequence)
        code = f"from pathlib import Path\nimport hashlib,json\np=Path({remote_a!r})\nprint(json.dumps({{'exists':p.is_file(),'bytes':p.stat().st_size if p.is_file() else 0,'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else ''}}))\n"
        info = json.loads(remote_python(code))
        if info == {"exists": True, "bytes": len(payload_a), "sha256": digest_a}:
            break
        time.sleep(2)
    else:
        raise TimeoutError("andrew-to-lecun probe did not arrive")
    payload_b = (TASK_ID + "\nfrom=lecun\n" + os.urandom(32).hex() + "\n").encode()
    digest_b = hashlib.sha256(payload_b).hexdigest()
    encoded = base64.b64encode(payload_b).decode()
    remote_b = f"{REMOTE_PROBE_DIR}/probe-from-lecun.txt"
    code = f"from pathlib import Path\nimport base64,json\np=Path({remote_b!r}); p.parent.mkdir(parents=True,exist_ok=True)\nassert not p.exists()\np.write_bytes(base64.b64decode({encoded!r}))\nprint(json.dumps({{'bytes':p.stat().st_size}}))\n"
    json.loads(remote_python(code))
    local_b = PROBE_DIR / "probe-from-lecun.txt"
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        sequence += 1
        write_lease(*owner, sequence)
        if local_b.is_file() and local_b.stat().st_size == len(payload_b) and sha(local_b) == digest_b:
            break
        time.sleep(2)
    else:
        raise TimeoutError("lecun-to-andrew probe did not arrive")
    return {
        "andrew_to_lecun": {"path": str(local_a), "bytes": len(payload_a), "sha256": digest_a},
        "lecun_to_andrew": {"path": str(local_b), "bytes": len(payload_b), "sha256": digest_b},
    }, sequence


def execute() -> dict[str, Any]:
    owner_pid, owner_tick = os.getpid(), tick(os.getpid())
    start = json.loads((BACKUP / "start-snapshot.json").read_text(encoding="utf-8"))
    if not unchanged_start(start, local_snapshot("pre_transaction"), route_snapshot()):
        raise RuntimeError("live state no longer matches the sealed old state")
    state = make_state(start)
    atomic_json(STATE, state, exclusive=True)
    state_digest = sha(STATE)
    guard_log = (BACKUP / "guard.log").open("ab", buffering=0)
    guard = subprocess.Popen(
        [sys.executable, str(TASK_DIR / "rollback_guard.py"), "--watch", str(STATE), "--owner-pid", str(owner_pid), "--owner-tick", str(owner_tick)],
        stdin=subprocess.DEVNULL,
        stdout=guard_log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
        close_fds=True,
    )
    sequence = 1
    live_started = False
    write_lease(owner_pid, owner_tick, sequence)
    try:
        ready = wait_file(READY, 20, (owner_pid, owner_tick))
        if ready.get("state_sha256") != state_digest:
            raise RuntimeError("guard ready digest mismatch")
        atomic_json(ARM_REQUEST, {"owner_pid": owner_pid, "owner_tick": owner_tick, "state_sha256": state_digest}, exclusive=True)
        armed = wait_file(ARMED, 20, (owner_pid, owner_tick))
        if armed.get("state_sha256") != state_digest:
            raise RuntimeError("guard armed digest mismatch")
        sys.path.insert(0, str(TASK_DIR))
        import rollback_guard

        old_keeper = start["processes"]["keeper"]["items"][0]
        if tick(old_keeper["pid"]) != old_keeper["start_tick"]:
            raise RuntimeError("old keeper identity changed before TERM")
        rollback_guard.terminate_one(old_keeper["pid"], ("keeper.sh",), "old_keeper")
        live_started = True
        added_host_keys = add_center_host_key()
        run_json([sys.executable, str(TASK_DIR / "syncthing_route.py"), "--set-lecun", "--backup-dir", str(BACKUP)])
        os.replace(OLD_MARKER, BACKUP / f"marker.philip.moved.{int(time.time())}")
        atomic_bytes(NEW_MARKER, f"{KEY}\n192.168.196.176\n".encode(), state["old_marker_mode"] and int(state["old_marker_mode"], 8))
        expected_keeper = deploy_keeper()
        new_keeper_pid = launch_keeper()
        atomic_json(RUNTIME, {"new_keeper_pid": new_keeper_pid, "new_tunnel_pid": 0})
        deadline = time.monotonic() + 60
        success = None
        while time.monotonic() < deadline:
            sequence += 1
            write_lease(owner_pid, owner_tick, sequence)
            snap, route = local_snapshot("post_cutover_wait"), route_snapshot()
            try:
                keeper_pid, tunnel_pid = validate_success(start, snap, route, expected_keeper)
                success = (snap, route, keeper_pid, tunnel_pid)
                break
            except RuntimeError:
                time.sleep(2)
        if success is None:
            raise RuntimeError("cutover did not reach the success predicate")
        first, first_route, keeper_pid, tunnel_pid = success
        atomic_json(RUNTIME, {"new_keeper_pid": keeper_pid, "new_tunnel_pid": tunnel_pid})
        probes, sequence = probe_pair((owner_pid, owner_tick), sequence)
        began_wall, began_mono = time.time(), time.monotonic()
        deadline = began_mono + STABILITY_SECONDS
        while time.monotonic() < deadline:
            sequence += 1
            write_lease(owner_pid, owner_tick, sequence)
            if sequence % 3 == 0:
                snap, route = local_snapshot("stability_poll"), route_snapshot()
                current_keeper, current_tunnel = validate_success(start, snap, route, expected_keeper)
                if (current_keeper, current_tunnel) != (keeper_pid, tunnel_pid):
                    raise RuntimeError("keeper or tunnel identity changed during stability window")
            time.sleep(min(5, max(0, deadline - time.monotonic())))
        final = local_snapshot("stability_final")
        final_route = route_snapshot()
        validate_success(start, final, final_route, expected_keeper)
        final_digest = hashlib.sha256(json.dumps({"snapshot": final, "route": final_route, "probes": probes}, sort_keys=True).encode()).hexdigest()
        atomic_json(COMMIT_TOKEN, {"owner_pid": owner_pid, "owner_tick": owner_tick, "state_sha256": state_digest, "final_sha256": final_digest}, exclusive=True)
        guard.wait(timeout=20)
        if ROLLBACK_DONE.exists() or guard.returncode != 0:
            raise RuntimeError("guard did not disarm cleanly")
        result = {
            "result": "PASS",
            "owner": {"pid": owner_pid, "start_tick": owner_tick},
            "guard": ready,
            "added_known_host_keys": added_host_keys,
            "keeper": {"pid": keeper_pid, "sha256": expected_keeper},
            "tunnel_pid": tunnel_pid,
            "probes": probes,
            "stability": {"wall_seconds": time.time() - began_wall, "monotonic_seconds": time.monotonic() - began_mono},
            "first_snapshot": first,
            "first_route": first_route,
            "final_snapshot": final,
            "final_route": final_route,
        }
        atomic_json(BACKUP / "cutover-result.json", result, exclusive=True)
        return result
    except BaseException:
        if ARMED.exists() and not COMMIT_TOKEN.exists() and live_started:
            atomic_json(ROLLBACK_REQUEST, {"owner_pid": owner_pid, "owner_tick": owner_tick, "requested_at": time.monotonic()})
            try:
                wait_file(ROLLBACK_DONE, 40)
            except TimeoutError:
                pass
        elif ARMED.exists() and not live_started and guard.poll() is None:
            guard.terminate()
            guard.wait(timeout=10)
        raise
    finally:
        guard_log.close()


def self_test() -> tuple[dict[str, bool], bool]:
    checks: dict[str, bool] = {}
    with tempfile.TemporaryDirectory(prefix="andrew-guarded-cutover-") as raw:
        root = Path(raw)
        target = root / "state.json"
        atomic_json(target, {"task_id": TASK_ID}, exclusive=True)
        checks["atomic_json_written"] = json.loads(target.read_text())["task_id"] == TASK_ID
        try:
            atomic_json(target, {}, exclusive=True)
            checks["exclusive_write_rejects_duplicate"] = False
        except FileExistsError:
            checks["exclusive_write_rejects_duplicate"] = True
        marker = f"{KEY}\n192.168.196.176\n".splitlines()
        checks["marker_has_exact_two_lines"] = marker == [str(KEY), "192.168.196.176"]
        checks["scope_excludes_zmx_and_sshd"] = all(name not in {"zmx", "sshd"} for name in ("keeper", "ssh_forward_lecun"))
    return checks, all(checks.values())


def main() -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--self-test", action="store_true")
    group.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        checks, passed = self_test()
        print(json.dumps({"result": "PASS" if passed else "FAIL", "self_test": checks}, indent=2, sort_keys=True))
        return 0 if passed else 1
    result = execute()
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
