"""Task A.3: GPU usage and compute-process owners, without partial matching.

    python gpu_owners.py                      # every GPU: memory, utilisation, processes and owners
    python gpu_owners.py --count-exe <path>   # how many compute processes run exactly that executable

A process is matched by resolving ``/proc/PID/exe`` and comparing the whole path, never a
substring. Processes outside this container are invisible here, so usage is judged from
both the owner count and each GPU's memory and utilisation.
"""
from __future__ import annotations

import argparse
import json
import os
import pwd
import subprocess


def query(fields, kind):
    out = subprocess.run(["nvidia-smi", f"--query-{kind}={','.join(fields)}",
                          "--format=csv,noheader,nounits"],
                         check=True, capture_output=True, text=True).stdout
    return [dict(zip(fields, (c.strip() for c in line.split(",")))) for line in out.splitlines() if line.strip()]


def processes():
    rows = []
    for app in query(["gpu_uuid", "pid", "used_memory"], "compute-apps"):
        pid = int(app["pid"])
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
            owner = pwd.getpwuid(os.stat(f"/proc/{pid}").st_uid).pw_name
        except (FileNotFoundError, PermissionError, KeyError):
            exe, owner = None, None
        rows.append({**app, "pid": pid, "exe": exe, "owner": owner})
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count-exe")
    args = ap.parse_args()
    procs = processes()
    if args.count_exe:
        print(json.dumps({"exe": args.count_exe,
                          "count": sum(p["exe"] == args.count_exe for p in procs)}))
        return
    gpus = query(["index", "uuid", "memory.used", "utilization.gpu"], "gpu")
    for gpu in gpus:
        mine = [p for p in procs if p["gpu_uuid"] == gpu["uuid"]]
        gpu["processes"] = mine
        gpu["owners"] = sorted({p["owner"] or "UNRESOLVED" for p in mine})
    print(json.dumps(gpus, ensure_ascii=False))


if __name__ == "__main__":
    main()
