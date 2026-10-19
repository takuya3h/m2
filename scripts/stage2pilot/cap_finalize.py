"""PD の上限を 8 から 4 epoch にした後（spec の amendments の 4 件目）、8 で起動済みの run を 5 epoch 目の始まりで
止めたときに結果を書く（非公式 T-2026-10-18-stage2-pilot-folda）。

止めた run には train_t1b.py の t1b_result.json ができない。代わりに、ログに残る各 epoch の val mAP と、
最良の重み（STORE/pd_ckpt/<run>/best_t1b.pth に記録された epoch）から cap_result.json を書く。
最良の予測（predictions/val_*_best.json.gz）は 4 epoch 目の評価までの最良のまま残っている
（train_t1b.py が次に保存するのは 5 epoch 目の評価の後）。上限 4 で起動した run と同じ値になる。

    python scripts/stage2pilot/cap_finalize.py <run の作業フォルダ>
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stage2pilot import common as C  # noqa: E402

CAP = 4


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("run_dir")
    d = Path(ap.parse_args().run_dir)
    log = (d / "train.log").read_text(errors="replace")
    if "[t1b] DONE" in log:
        raise SystemExit("学習が自分で終わっている。t1b_result.json を使う")
    if f"[t1b][ep{CAP} 0/" not in log:
        raise SystemExit(f"{CAP + 1} epoch 目が始まっていない")
    init = float(re.search(r"warm-start init mAP=([0-9.]+)", log).group(1))
    per_epoch = {int(e): float(m) for e, m in re.findall(r"\[t1b\]\[ep(\d+)\] val mAP=([0-9.]+)", log)}
    if sorted(per_epoch) != list(range(CAP)):
        raise SystemExit(f"epoch 0〜{CAP - 1} の評価が揃っていない: {sorted(per_epoch)}")
    # train_t1b.py と同じく「前の最良より大きいとき」だけ更新する（同値なら早い epoch）
    best_ep = max(range(CAP), key=lambda e: (per_epoch[e], -e))
    ck = torch.load(C.STORE / "pd_ckpt" / d.name / "best_t1b.pth", map_location="cpu")
    if ck["epoch"] != best_ep:
        raise SystemExit(f"最良の重みの epoch {ck['epoch']} がログの最良 {best_ep} と食い違う")
    res = {
        "task_id": C.TASK_ID, "source": "scripts/stage2pilot/cap_finalize.py（train_t1b.py の t1b_result.json の代わり）",
        "seed": int(re.search(r"_seed(\d+)$", d.name).group(1)),
        "zero_ctx": "--zero-ctx" in (d / "command.sh").read_text(),
        "epoch_cap": CAP, "init_mAP": init, "best_epoch": best_ep, "mAP": per_epoch[best_ep],
        "per_epoch_eval": [{"epoch": e, "mAP": per_epoch[e]} for e in range(CAP)],
        "early_stopped_epoch": None, "epochs_run": CAP, "reached_epoch_cap": True,
        "frozen_digest_before": None, "frozen_digest_after": None,
        "note": f"上限 8 で起動し、{CAP + 1} epoch 目の始まりで外から止めた。凍結部の要約値は学習の終わりに書かれるため UNKNOWN",
    }
    C.write_json(d / "cap_result.json", res)
    print(f"[cap_finalize] {d.name} best@ep{best_ep} mAP={per_epoch[best_ep]:.4f} (init {init:.4f})")


if __name__ == "__main__":
    main()
