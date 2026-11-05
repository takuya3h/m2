"""List compute processes on andrew for T-2026-11-06-tower-batch-probe.

A process is selected when ``/proc/PID/exe`` resolves exactly to one of the given
executables (default: the interpreters a training run can use) and, if ``--arg`` is given,
one element of its argv equals that string exactly. Substrings never match (a wrapper's
command line that merely mentions a token is not selected). nvidia-smi's compute
processes are listed as well, with the same resolution of their PID.

    python procs.py                                   # default interpreters + nvidia-smi
    python procs.py --exe /usr/bin/bash --arg TOKEN   # control: exact exe and argv element
"""
from __future__ import annotations

import argparse
import json
import os
import pwd
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
DEFAULT_EXES = [ROOT / ".venv/bin/python", ROOT / ".venv-relation-detr/bin/python",
                Path("/usr/bin/python3")]


def resolve(path):
    return os.path.realpath(path)


def processes():
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
            argv = Path(f"/proc/{pid}/cmdline").read_bytes().split(b"\0")[:-1]
            uid = os.stat(f"/proc/{pid}").st_uid
        except OSError:
            continue
        yield {"pid": pid, "exe": exe, "argv": [a.decode(errors="replace") for a in argv],
               "user": pwd.getpwuid(uid).pw_name}


def gpu_apps():
    out = subprocess.run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
                          "--format=csv,noheader,nounits"], capture_output=True, text=True,
                         check=True).stdout
    return [dict(zip(("uuid", "pid", "used_mib"), (c.strip() for c in line.split(","))))
            for line in out.strip().splitlines() if line.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", action="append")
    ap.add_argument("--arg")
    ap.add_argument("--exclude-pid", type=int, action="append", default=[])
    args = ap.parse_args()
    exes = sorted({resolve(p) for p in (args.exe or DEFAULT_EXES)})
    me = os.getpid()
    skip = {me, *args.exclude_pid}
    hits = [p for p in processes() if p["pid"] not in skip and p["exe"] in exes
            and (args.arg is None or args.arg in p["argv"])]
    apps = gpu_apps()
    print(json.dumps({"exes": exes, "arg": args.arg, "excluded_self_pid": me, "excluded_pids": args.exclude_pid,
                      "count": len(hits), "processes": hits,
                      "nvidia_smi_compute_apps": apps}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
