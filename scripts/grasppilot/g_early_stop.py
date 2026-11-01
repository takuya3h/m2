"""G の 3 本の打ち切りの見張り（非公式 T-2026-11-01-grasp-pilot-g）。利用者の決定（2026-11-01 09:5x JST）:
「各実験について、val の数値が 4 エポックほど変わらなくなったら打ち切って良い」。

規則: val の 38 クラスの mask mAP の最良（厳密に上回ったら更新。g_train.py と同じ判定）が 4 epoch 続けて更新されなければ打ち切る
（SPEC §3.2 の「停滞 4 で学習率 × 0.1、再停滞で打ち切り」の二段目を待たない）。最良の epoch の重み（best.pth）を使う。

走っている g_train.py には差し込めないので、logs/history.json を外から見て、条件を満たした run の起動のシェルと学習を止め、
g_train.py の終わりと同じ記録（metrics.json・per_class_ap.json・notes.md・end.txt・exit_code.txt）を書く。

    .venv/bin/python scripts/grasppilot/g_early_stop.py [--patience 4] [--once]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import time
from pathlib import Path

PROJ = Path(__file__).resolve().parents[2]
TASK = "T-2026-11-01-grasp-pilot-g"
S = Path("/home/ubuntu/slocal2/stage2pilot_store") / TASK
RUNS = {g: PROJ / f"experiments/phase1/grasppilot2_G_{g}_seed42" for g in ("all", "H1", "H2")}


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def stale_since_best(history):
    best, best_epoch, stale = -1.0, None, 0
    for r in history[1:]:                          # epoch 0 は学習前
        if r["segm_mAP"] > best:
            best, best_epoch, stale = r["segm_mAP"], r["epoch"], 0
        else:
            stale += 1
    return best, best_epoch, stale


def pids_of(run_name):
    """その run の起動のシェル（run_g.sh）と学習（g_train.py とその worker）の PID。自分自身は含めない。"""
    out = subprocess.run(["ps", "-eo", "pid,args"], capture_output=True, text=True).stdout.splitlines()
    me = os.getpid()
    g = run_name.split("_")[2]
    shells, trains = [], []
    for line in out[1:]:
        pid, _, args = line.strip().partition(" ")
        pid = int(pid)
        if pid == me:
            continue
        a = args.split()
        if len(a) >= 3 and a[0] == "bash" and a[1].endswith("run_g.sh") and a[2] == g:
            shells.append(pid)
        elif "g_train.py" in args and f"experiments/phase1/{run_name}" in args and a[0].endswith("python"):
            trains.append(pid)
    return shells, trains


def finalize(g, run, history, best, best_epoch, stale, patience):
    name = run.name
    shells, trains = pids_of(name)
    for p in shells + trains:                      # 先にシェルを止める（exit_code を書かせない）
        try:
            os.kill(p, signal.SIGKILL)
        except ProcessLookupError:
            pass
    time.sleep(3)
    ckpt = S / "g/ckpt" / name / "best.pth"
    best_rec = next(h for h in history if h["epoch"] == best_epoch)
    cfg = json.loads((run / "config.json").read_text())
    last = history[-1]["epoch"]
    lowered = next((h["epoch"] for h in history if h.get("action") == "lower"), None)
    started = time.mktime(time.strptime((run / "start.txt").read_text().strip(), "%Y-%m-%d %H:%M:%S %Z"))
    metrics = {"task_id": TASK, "unofficial": True, "run": name, "videos": cfg["videos"], "best_epoch": best_epoch,
               "best_segm_mAP": best, "best_grasp5_mAP": best_rec["grasp5_mAP"], "pre_segm_mAP": history[0]["segm_mAP"],
               "pre_grasp5_mAP": history[0]["grasp5_mAP"], "epochs_completed": last, "lr_lowered_epoch": lowered,
               "early_stopped_epoch": last, "reached_epoch_cap": False,
               "stop_rule": f"利用者の決定: 最良が {patience} epoch 更新されなければ打ち切り（g_early_stop.py）",
               "stale_epochs_at_stop": stale, "killed_pids": shells + trains,
               "elapsed_seconds": time.time() - started, "peak_alloc_bytes": max(h.get("peak_alloc_bytes", 0) for h in history),
               "best_ckpt": str(ckpt), "best_ckpt_sha256": sha(ckpt), "last_ckpt_sha256": None}
    (run / "metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2) + "\n")
    (run / "per_class_ap.json").write_text(json.dumps(best_rec["per_class_ap"], ensure_ascii=False, indent=2) + "\n")
    (run / "notes.md").write_text(
        f"# {name}（非公式 {TASK}）\n\n把持塔 G（Mask2Former R50、38 クラス）、学ぶ動画 {cfg['train_videos']}、val {cfg['val_videos']}。\n"
        f"最良 epoch {best_epoch}: segm mAP {best:.4f}、把持関係 5 クラス {best_rec['grasp5_mAP']:.4f}。"
        f"学習前 {history[0]['segm_mAP']:.4f} / {history[0]['grasp5_mAP']:.4f}。\n"
        f"評価を終えた epoch {last}（学習率を下げた epoch {lowered}）。利用者の決定により、最良が {patience} epoch 更新されなかった時点で打ち切った"
        f"（走っていた epoch {last + 1} の途中の学習は捨てた）。\n")
    (run / "end.txt").write_text(time.strftime("%Y-%m-%d %H:%M:%S %Z") + "\n")
    (run / "exit_code.txt").write_text("0\n")
    print(f"[stop] {name} best_epoch={best_epoch} best={best:.4f} stale={stale} last={last} killed={shells + trains}", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--patience", type=int, default=4)
    ap.add_argument("--once", action="store_true")
    a = ap.parse_args()
    done = set()
    while True:
        for g, run in RUNS.items():
            if g in done or (run / "exit_code.txt").exists():
                done.add(g)
                continue
            hp = run / "logs/history.json"
            if not hp.exists():
                continue
            history = json.loads(hp.read_text())
            best, best_epoch, stale = stale_since_best(history)
            if best_epoch is not None and stale >= a.patience:
                finalize(g, run, history, best, best_epoch, stale, a.patience)
                done.add(g)
        if a.once or len(done) == len(RUNS):
            break
        time.sleep(30)


if __name__ == "__main__":
    main()
