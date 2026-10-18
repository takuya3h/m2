"""装置のプロセスを /proc/PID/exe の解決と引数の要素の完全一致で列挙する（非公式 T-2026-10-18-stage2-pilot-folda）。

    python proc_enum.py --summary                  # exe ごとの件数と、python 系の全件の引数
    python proc_enum.py --exe /usr/bin/bash --argv zzz_marker   # 条件に合う PID を数える

部分一致は使わない（conventions#issuer_cautions 注意 6）。
"""
import argparse
import os
from collections import Counter


def procs():
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        pid = int(d)
        try:
            exe = os.readlink(f"/proc/{pid}/exe")
        except OSError:
            exe = None
        try:
            with open(f"/proc/{pid}/cmdline", "rb") as f:
                argv = [a.decode("utf-8", "replace") for a in f.read().split(b"\0") if a]
        except OSError:
            argv = []
        yield pid, exe, argv


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--exe", help="解決後の実行ファイルの経路（完全一致）")
    ap.add_argument("--argv", action="append", default=[], help="引数の要素（完全一致。複数可）")
    ap.add_argument("--summary", action="store_true")
    a = ap.parse_args()
    me = os.getpid()
    rows = [(p, e, v) for p, e, v in procs() if p != me]
    if a.summary:
        c = Counter(e for _, e, _ in rows)
        for e, n in sorted(c.items(), key=lambda t: (-t[1], str(t[0]))):
            print(f"{n:5d} {e}")
        print("--- python 系（exe の basename が python で始まる）")
        for p, e, v in sorted(rows):
            if e and os.path.basename(e).startswith("python"):
                print(p, e, " ".join(v)[:300])
        return
    hit = [p for p, e, v in rows
           if (a.exe is None or e == a.exe) and all(x in v for x in a.argv)]
    for p in hit:
        print(p)
    print(f"count={len(hit)}")


if __name__ == "__main__":
    main()
