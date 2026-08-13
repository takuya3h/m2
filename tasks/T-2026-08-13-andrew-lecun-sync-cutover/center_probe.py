#!/usr/bin/env python3
"""Read-only lecun probe sent over one fixed, strict SSH command."""

from __future__ import annotations

import argparse
import json
import subprocess
import textwrap
from pathlib import Path
from typing import Any

KEY = Path("/home/ubuntu/.ssh/id_ed25519_andrewtophilip")
KNOWN_HOSTS = Path(
    "/home/ubuntu/.hub-migration-backup.T-2026-08-13-andrew-lecun-sync-cutover/known_hosts.lecun"
)
HOST = "192.168.196.176"
SSH_ARGV = [
    "ssh",
    "-p",
    "50072",
    "-i",
    str(KEY),
    "-o",
    "BatchMode=yes",
    "-o",
    "StrictHostKeyChecking=yes",
    "-o",
    f"UserKnownHostsFile={KNOWN_HOSTS}",
    "-o",
    "ClearAllForwardings=yes",
    "-o",
    "ConnectTimeout=10",
    f"ubuntu@{HOST}",
    "python3",
    "-",
]

REMOTE_CODE = textwrap.dedent(
    r"""
    import fcntl, hashlib, json, os, socket, stat
    from pathlib import Path

    HOME = Path('/home/ubuntu')
    PORTS = (22000, 22001, 8384)

    def sha(path):
        h = hashlib.sha256()
        with path.open('rb') as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b''):
                h.update(chunk)
        return h.hexdigest()

    def summary(path):
        try:
            data = path.read_bytes(); info = path.stat()
            return {'path': str(path), 'exists': True,
                    'mode': f'{stat.S_IMODE(info.st_mode):03o}', 'bytes': len(data),
                    'line_count': len(data.splitlines()), 'sha256': hashlib.sha256(data).hexdigest()}
        except Exception as exc:
            return {'path': str(path), 'exists': False, 'error': type(exc).__name__}

    def stat_fields(pid):
        raw = (Path('/proc') / str(pid) / 'stat').read_text()
        fields = raw[raw.rfind(')') + 2:].split()
        return int(fields[1]), int(fields[19])

    def lock_available(path):
        try: fd = os.open(path, os.O_RDWR)
        except Exception: return None
        try:
            try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError: return False
            fcntl.flock(fd, fcntl.LOCK_UN); return True
        finally: os.close(fd)

    def processes():
        result = {'keeper': [], 'syncthing': [], 'ssh_local_forward': []}
        for proc in Path('/proc').iterdir():
            if not proc.name.isdigit(): continue
            try:
                argv = [v.decode('utf-8', 'replace') for v in proc.joinpath('cmdline').read_bytes().split(b'\0') if v]
                if not argv: continue
                comm = proc.joinpath('comm').read_text().strip()
                ppid, tick = stat_fields(int(proc.name))
            except Exception: continue
            bases = {Path(v).name for v in argv}; joined = ' '.join(argv)
            categories = []
            if 'keeper.sh' in bases: categories.append('keeper')
            if comm == 'syncthing' or 'syncthing' in bases: categories.append('syncthing')
            if (comm == 'ssh' or 'ssh' in bases) and '22001:127.0.0.1:22000' in joined:
                categories.append('ssh_local_forward')
            for category in categories:
                item = {'pid': int(proc.name), 'ppid': ppid, 'start_tick': tick}
                if category == 'keeper':
                    for fd in (9, 255):
                        fdpath = proc / 'fd' / str(fd)
                        try:
                            detail = {'exists': True, 'target': os.readlink(fdpath), 'inode': fdpath.stat().st_ino}
                            if fd == 255: detail['sha256'] = sha(fdpath)
                        except Exception as exc: detail = {'exists': False, 'error': type(exc).__name__}
                        item[f'fd{fd}'] = detail
                result[category].append(item)
        return result

    def decode(raw, ipv6):
        packed = bytes.fromhex(raw)
        if ipv6:
            packed = b''.join(packed[i:i+4][::-1] for i in range(0, 16, 4))
            return socket.inet_ntop(socket.AF_INET6, packed)
        return socket.inet_ntop(socket.AF_INET, packed[::-1])

    def listeners():
        result = {str(port): [] for port in PORTS}
        for table_name, ipv6 in (('tcp', False), ('tcp6', True)):
            try: lines = (Path('/proc/net') / table_name).read_text().splitlines()[1:]
            except Exception: continue
            for line in lines:
                fields = line.split()
                if len(fields) < 10 or fields[3] != '0A': continue
                raw_address, raw_port = fields[1].split(':'); port = int(raw_port, 16)
                if port in PORTS:
                    result[str(port)].append({'family': table_name, 'address': decode(raw_address, ipv6),
                                              'port': port, 'inode': int(fields[9])})
        return result

    process_state = processes(); listener_state = listeners()
    marker_items = [summary(p) for p in sorted(HOME.glob('.tunnel_to_*')) if p.is_file()]
    state = {
        'processes': {name: {'count': len(items), 'items': items} for name, items in process_state.items()},
        'listeners': {port: {'count': len(items), 'items': items} for port, items in listener_state.items()},
        'markers': {'count': len(marker_items), 'items': marker_items},
        'keeper_lock_available': lock_available(HOME / '.keeper.lock'),
        'files': {
            'keeper': summary(HOME / 'bin/keeper.sh'),
            'authorized_keys': summary(HOME / '.ssh/authorized_keys'),
        },
    }
    print(json.dumps(state, sort_keys=True))
    """
)


def center_snapshot(label: str) -> dict[str, Any]:
    process = subprocess.run(
        SSH_ARGV,
        input=REMOTE_CODE,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(f"strict SSH probe failed rc={process.returncode}: {process.stderr.strip()[-500:]}")
    state = json.loads(process.stdout)
    return {"label": label, "ssh": {"host": HOST, "port": 50072, "returncode": 0}, "state": state}


def self_test() -> tuple[dict[str, Any], bool]:
    result = center_snapshot("center_self_test")
    state = result["state"]
    checks = {
        "fixed_batch_mode": "BatchMode=yes" in SSH_ARGV,
        "fixed_strict_host_key": "StrictHostKeyChecking=yes" in SSH_ARGV,
        "fixed_clear_forwardings": "ClearAllForwardings=yes" in SSH_ARGV,
        "fixed_port": SSH_ARGV[1:3] == ["-p", "50072"],
        "fixed_key": SSH_ARGV[3:5] == ["-i", str(KEY)],
        "center_marker_zero": state["markers"]["count"] == 0,
        "center_keeper_one": state["processes"]["keeper"]["count"] == 1,
        "center_keeper_lock_held": state["keeper_lock_available"] is False,
        "center_syncthing_present": state["processes"]["syncthing"]["count"] > 0,
        "center_22000_open": state["listeners"]["22000"]["count"] > 0,
        "center_22001_closed": state["listeners"]["22001"]["count"] == 0,
    }
    passed = all(checks.values())
    return {"self_test": checks, "result": "PASS" if passed else "FAIL", "probe": result}, passed


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
    print(json.dumps(center_snapshot(args.label), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
