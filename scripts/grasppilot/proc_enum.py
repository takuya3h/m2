"""andrew の compute プロセスの列挙（非公式 T-2026-10-31-grasp-pilot-probe、Task A-3）。

各 PID の ``/proc/PID/exe`` を解決し、実行ファイルの basename と引数の要素で分類する。
compute とみなすもの:
  - 実行ファイルの basename が python で始まる
  - 引数の要素のどれかが、既知の compute の入口（下の COMPUTE_ARGS）と完全一致する
  - nvidia-smi が GPU の compute として挙げる PID

    python scripts/grasppilot/proc_enum.py                 一覧と compute の件数（JSON）
    python scripts/grasppilot/proc_enum.py --match-exe P   exe の解決先が P と完全一致する PID の件数（自己検査）
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

COMPUTE_ARGS = {"torchrun", "accelerate", "deepspeed"}


def processes():
    out = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit():
            continue
        try:
            exe = os.readlink(d / "exe")
            argv = (d / "cmdline").read_bytes().split(b"\0")
            argv = [a.decode(errors="replace") for a in argv if a]
        except (FileNotFoundError, PermissionError, ProcessLookupError, OSError):
            continue
        out.append({"pid": int(d.name), "exe": exe, "argv": argv})
    return out


def gpu_pids():
    try:
        r = subprocess.run(["nvidia-smi", "--query-compute-apps=pid", "--format=csv,noheader"],
                           capture_output=True, text=True, check=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        return set()
    return {int(x) for x in r.stdout.split() if x.strip().isdigit()}


def is_compute(p, gpus):
    base = os.path.basename(p["exe"])
    return base.startswith("python") or any(a in COMPUTE_ARGS for a in p["argv"]) or p["pid"] in gpus


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--match-exe")
    ap.add_argument("--exclude-pid", type=int, action="append", default=[])
    args = ap.parse_args()
    procs = processes()
    if args.match_exe:
        hits = [p["pid"] for p in procs if p["exe"] == args.match_exe]
        print(json.dumps({"match_exe": args.match_exe, "count": len(hits), "pids": hits}))
        return
    gpus = gpu_pids()
    me = {os.getpid(), *args.exclude_pid}
    compute = [p for p in procs if p["pid"] not in me and is_compute(p, gpus)]
    bases = {}
    for p in procs:
        b = os.path.basename(p["exe"])
        bases[b] = bases.get(b, 0) + 1
    print(json.dumps({"n_processes": len(procs), "gpu_pids": sorted(gpus), "n_compute": len(compute),
                      "compute": compute, "exe_basenames": dict(sorted(bases.items()))},
                     ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
