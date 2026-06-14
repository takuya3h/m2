#!/usr/bin/env python3
"""学習プロセスの生死を「一意に」判定する診断器。誤診防止の唯一の正規ルート。

背景: 2026-05-30 に2度の誤診をした。
  (1)「ゾンビGPUメモリ→要リセット」: nvidia-smi --compute-apps の PID を /proc で
     DEAD 判定し、実際は稼働中の2学習を「死んだメモリ」と誤認。リセットしていたら
     稼働中の計算を破壊していた。
  (2)「seed42クラッシュ」: metrics.json が iter で凍結(eval中) + ps に出ない、で
     クラッシュと誤認。実際は eval フェーズで training metrics が一時停止しただけ。

根本原因: **単一の曖昧な信号(compute-apps PID / metrics mtime / ps grep)で生死を
判断した**こと。本スクリプトは時間差2サンプルで以下を一意分類する:

  COMPLETED  : model_final.pth が存在
  TRAINING   : metrics.json の iteration が T0→T1 で増加 (健全)
  EVALUATING : iteration は不変だが log.txt が更新中 (健全。eval を死と誤認しない)
  STALLED    : iteration も log.txt も不変だがプロセス生存 (ハング疑い、要調査)
  DEAD       : iteration も log.txt も不変 + プロセス不在 + 一定時間 log 凍結
  NOT_STARTED: metrics.json も log.txt も無い
  QUIESCENT  : 判定保留 (更新間隔内かもしれない。再サンプル推奨)

プロセス検出は ps/grep ではなく **/proc 全 cmdline を workdir 文字列で走査**する
(seed42 が ps grep に出なかった失敗の再発防止。ワーカー子プロセスも捕捉)。

使い方:
  python scripts/train_status.py <workdir> [--interval 20]
  python scripts/train_status.py --scan                 # 既知の学習dirを一括判定
  python scripts/train_status.py --can-i-reset          # 破壊操作の事前ゲート
      → 稼働中(TRAINING/EVALUATING/STALLED)が1つでもあれば exit 3 + 一覧。
        全て DEAD/COMPLETED/NOT_STARTED のときのみ exit 0 (=リセット/kill 許可)。
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
import time
from pathlib import Path

# 稼働中とみなす状態 (破壊操作を絶対にブロックすべき状態)
LIVE_STATES = {"TRAINING", "EVALUATING", "STALLED"}
# log.txt がこの秒数以上凍結 かつ プロセス不在 なら DEAD と確定
DEAD_STALL_SEC = 720
# STALLED(プロセスは居るが何も動かない)と判定する凍結秒数
STALL_SEC = 300


def _read_last_iter(metrics: Path) -> int | None:
    """metrics.json (detectron2 JSONL or 単一JSON) の最終 iteration。"""
    if not metrics.exists():
        return None
    try:
        lines = [l for l in metrics.read_text(errors="ignore").splitlines() if l.strip()]
    except OSError:
        return None
    for line in reversed(lines):
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        for key in ("iteration", "iter", "epoch"):
            if key in obj and isinstance(obj[key], (int, float)):
                return int(obj[key])
    return None


def _mtime(p: Path) -> float:
    try:
        return p.stat().st_mtime
    except OSError:
        return 0.0


def _proc_alive_for(workdir: str) -> list[int]:
    """/proc 全 cmdline を走査し workdir 文字列を含む生 PID を返す (ps grep より堅牢)。"""
    hits: list[int] = []
    wd = os.path.abspath(workdir)
    for entry in glob.glob("/proc/[0-9]*/cmdline"):
        try:
            raw = Path(entry).read_bytes().replace(b"\x00", b" ").decode("utf-8", "ignore")
        except OSError:
            continue
        if wd in raw or workdir in raw:
            try:
                hits.append(int(entry.split("/")[2]))
            except (IndexError, ValueError):
                pass
    return hits


def classify(workdir: str, interval: float) -> dict:
    """時間差2サンプルで状態を一意分類。"""
    wd = Path(workdir)
    metrics = wd / "metrics.json"
    log = wd / "log.txt"
    final = wd / "model_final.pth"

    if final.exists():
        return {"workdir": workdir, "state": "COMPLETED", "iter": _read_last_iter(metrics),
                "evidence": "model_final.pth 存在"}
    if not metrics.exists() and not log.exists():
        return {"workdir": workdir, "state": "NOT_STARTED", "iter": None,
                "evidence": "metrics.json も log.txt も無い"}

    # サンプル T0
    iter0 = _read_last_iter(metrics)
    logm0 = _mtime(log)
    time.sleep(interval)
    # サンプル T1
    iter1 = _read_last_iter(metrics)
    logm1 = _mtime(log)
    procs = _proc_alive_for(workdir)
    now = time.time()
    log_age = now - logm1 if logm1 else 1e9

    if iter0 is not None and iter1 is not None and iter1 > iter0:
        state, ev = "TRAINING", f"iter {iter0}→{iter1} (+{iter1 - iter0}/{interval:.0f}s)"
    elif logm1 > logm0:
        state, ev = "EVALUATING", f"iter不変({iter1}) だが log.txt 更新中 (eval中、死ではない)"
    elif procs:
        if log_age > STALL_SEC:
            state, ev = "STALLED", f"iter/log 共に不変かつ log {log_age:.0f}s 凍結、proc {procs} 生存=ハング疑い"
        else:
            state, ev = "QUIESCENT", f"更新間隔内かも (log_age {log_age:.0f}s)。再サンプル推奨。proc {procs}"
    else:
        if log_age > DEAD_STALL_SEC:
            state, ev = "DEAD", f"iter/log 不変 + プロセス不在 + log {log_age:.0f}s 凍結"
        else:
            state, ev = "QUIESCENT", f"プロセス不在だが log_age {log_age:.0f}s<{DEAD_STALL_SEC}s。再サンプルで確定を"
    return {"workdir": workdir, "state": state, "iter": iter1, "procs": procs,
            "log_age_sec": round(log_age), "evidence": ev}


def _default_scan_dirs() -> list[str]:
    pats = ["/tmp/dimaskdino_work_*", "/tmp/*_work_*", "/tmp/reldetr_work_*",
            "/tmp/sensex_*work*", "/tmp/stabledino_work_*"]
    found: list[str] = []
    for p in pats:
        found.extend(d for d in glob.glob(p) if os.path.isdir(d))
    return sorted(set(found))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workdir", nargs="?", help="判定する学習 work dir")
    ap.add_argument("--interval", type=float, default=20.0, help="2サンプル間隔秒 (既定20)")
    ap.add_argument("--scan", action="store_true", help="既知の学習dirを一括判定")
    ap.add_argument("--can-i-reset", action="store_true",
                    help="破壊操作の事前ゲート。稼働中があれば exit 3")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    if args.workdir and not args.scan and not args.can_i_reset:
        r = classify(args.workdir, args.interval)
        print(json.dumps(r, ensure_ascii=False, indent=2) if args.json
              else f"[{r['state']}] {r['workdir']}\n  {r['evidence']}")
        return 0

    dirs = _default_scan_dirs()
    if not dirs:
        print("学習 work dir が見つかりません (NOT_STARTED 扱い)")
        return 0
    results = [classify(d, args.interval) for d in dirs]
    if args.json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
    else:
        print("=== 学習状態スキャン (時間差サンプルで一意判定) ===")
        for r in results:
            print(f"  [{r['state']:<11}] {r['workdir']}  iter={r.get('iter')}  {r['evidence']}")

    live = [r for r in results if r["state"] in LIVE_STATES]
    if args.can_i_reset:
        if live:
            print("\n❌ 破壊操作 不可: 稼働中の学習があります →")
            for r in live:
                print(f"   - {r['workdir']} [{r['state']}] (procs={r.get('procs')})")
            print("これらを止めずに GPU リセット/kill は禁止。")
            return 3
        print("\n✅ 稼働中の学習なし。GPU リセット/kill は安全。")
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
