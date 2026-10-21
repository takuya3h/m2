"""List compute processes per GPU with their owner, for T-2026-10-19-dlsta-tower-feasibility.

The owner comes from the uid of /proc/PID (exact), the executable from resolving
/proc/PID/exe. A PID that nvidia-smi reports but /proc cannot see (another PID
namespace) is reported as owner UNKNOWN rather than guessed.

    python gpu_procs.py            # table of every GPU
    python gpu_procs.py --pid N    # 1 if PID N is alive in /proc, else 0
"""
from __future__ import annotations

import argparse
import os
import pwd
import subprocess


def gpus():
    out = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,uuid,name,memory.total,memory.used",
         "--format=csv,noheader,nounits"], capture_output=True, text=True, check=True).stdout
    return [dict(zip(("index", "uuid", "name", "total_mib", "used_mib"),
                     (c.strip() for c in line.split(",")))) for line in out.strip().splitlines()]


def compute_apps():
    out = subprocess.run(
        ["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
         "--format=csv,noheader,nounits"], capture_output=True, text=True, check=True).stdout
    return [dict(zip(("uuid", "pid", "used_mib"), (c.strip() for c in line.split(","))))
            for line in out.strip().splitlines() if line.strip()]


def owner(pid):
    try:
        uid = os.stat(f"/proc/{pid}").st_uid
    except FileNotFoundError:
        return "UNKNOWN(not in /proc)", ""
    try:
        exe = os.readlink(f"/proc/{pid}/exe")
    except OSError:
        exe = "UNREADABLE"
    return pwd.getpwuid(uid).pw_name, exe


def alive(pid):
    return int(os.path.isdir(f"/proc/{pid}"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pid", type=int)
    args = parser.parse_args()
    if args.pid is not None:
        print(alive(args.pid))
        return
    apps = compute_apps()
    for g in gpus():
        mine = [a for a in apps if a["uuid"] == g["uuid"]]
        print(f"GPU{g['index']} {g['name']} total={g['total_mib']}MiB used={g['used_mib']}MiB "
              f"compute_procs={len(mine)}")
        for a in mine:
            user, exe = owner(a["pid"])
            print(f"  pid={a['pid']} used={a['used_mib']}MiB owner={user} exe={exe}")


if __name__ == "__main__":
    main()
