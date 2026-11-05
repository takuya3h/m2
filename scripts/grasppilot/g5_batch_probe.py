"""G の batch と数値精度の計測（非公式 T-2026-11-05-grasp-tower-rebuild、SPEC §3.0・Task B0）。本体の .venv。

一つの水準（GPU ごとの batch × 数値精度）を GPU 1 枚で数十歩だけ学び、記憶と一歩の時間を測る。重みは保存しない。
学習の部品は `g5_train.py`（構造・COCO の重み・反転でラベルを入れ替える取り出し）と `g_train.py`（入力の組み立て）をそのまま使う。
fp16 は `g_train.py --amp fp16` と同じ形（optim_wrapper を AmpOptimWrapper、loss_scale dynamic）。学習率は変えない。
bf16（利用者の追加の指示 2026-11-06）は同じ AmpOptimWrapper・loss_scale dynamic で dtype だけ bfloat16 にする。

一歩の時間 = 前の歩の更新の終わりから、この歩の更新の終わりまで（読み込みの待ちを含む。cuda の同期の後に測る）。
最初の --warmup 歩を除いた --measure 歩の平均と標準偏差。溢れた（CUDA の記憶の不足）ら、その歩と記憶を記録して終わる。
nvidia-smi の記憶・使用率・電力は別の糸で 0.5 秒ごとに読む。

    .venv/bin/python scripts/grasppilot/g5_batch_probe.py --batch 2 --amp none|fp16|bf16 --ann-dir <S/g/ann> --out <json> [--no-weights]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

import numpy as np
import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
sys.path.insert(0, str(PROJ / "src"))
from grasppilot import g5_train as G5  # noqa: E402
from grasppilot import g_bench as B  # noqa: E402
from grasppilot import g_train as T  # noqa: E402
from stage2pilot import common as C  # noqa: E402


class SmiPoller(threading.Thread):
    """nvidia-smi で一つの GPU の記憶（MiB）・使用率（%）・電力（W）を周期的に読む。"""

    def __init__(self, index, period=0.5):
        super().__init__(daemon=True)
        self.index, self.period, self.rows, self.stop = index, period, [], threading.Event()

    def run(self):
        while not self.stop.is_set():
            r = subprocess.run(["nvidia-smi", "-i", str(self.index), "--query-gpu=memory.used,utilization.gpu,power.draw",
                                "--format=csv,noheader,nounits"], capture_output=True, text=True)
            try:
                m, u, p = (float(x) for x in r.stdout.strip().split(","))
                self.rows.append((time.monotonic(), m, u, p))
            except ValueError:
                pass
            self.stop.wait(self.period)


def physical_gpu():
    vis = os.environ.get("CUDA_VISIBLE_DEVICES", "0").split(",")[0]
    return int(vis)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--batch", type=int, required=True)
    ap.add_argument("--amp", choices=("none", "fp16", "bf16"), required=True)
    ap.add_argument("--ann-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--measure", type=int, default=50)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--no-weights", action="store_true", help="対照: COCO の重みを読まない写し")
    a = ap.parse_args()
    os.environ["WANDB_MODE"] = "offline"
    torch.manual_seed(a.seed)
    np.random.seed(a.seed)
    from mmengine.optim import build_optim_wrapper

    tr = json.loads((Path(a.ann_dir) / "g5_train.json").read_text())
    C.assert_no_test([im["stem"] for im in tr["images"]], "batch probe")
    if a.no_weights:
        model, cfg = B.mmdet_model(num_classes=G5.NUM_CLASSES)
        load = {"loaded": 0, "n_checkpoint": None, "note": "対照: COCO の重みを読まない"}
    else:
        model, cfg, load = G5.build_model()
    if a.amp in ("fp16", "bf16"):
        cfg.optim_wrapper.type = "AmpOptimWrapper"
        cfg.optim_wrapper.loss_scale = "dynamic"
        if a.amp == "bf16":
            cfg.optim_wrapper.dtype = "bfloat16"
    optim = build_optim_wrapper(model, cfg.optim_wrapper)
    g = torch.Generator()
    g.manual_seed(a.seed)
    loader = torch.utils.data.DataLoader(G5.G5Flip(tr, True), batch_size=a.batch, shuffle=True, num_workers=a.workers,
                                         collate_fn=T.collate, generator=g, pin_memory=False, drop_last=True)  # nosemgrep
    gpu = physical_gpu()
    smi = SmiPoller(gpu)
    torch.cuda.reset_peak_memory_stats()
    model.train()
    total = a.warmup + a.measure
    rec = {"task_id": G5.TASK, "unofficial": True, "batch": a.batch, "amp": a.amp, "no_weights": a.no_weights,
           "gpu_index": gpu, "gpu_name": torch.cuda.get_device_name(0), "train_frames": len(tr["images"]),
           "steps_per_epoch": len(loader), "warmup": a.warmup, "measure": a.measure, "init": load,
           "lr_max": max(gr["lr"] for gr in optim.optimizer.param_groups), "accumulation": 1,
           "optim_wrapper": json.loads(json.dumps(cfg.optim_wrapper.to_dict(), default=str)),
           "expandable_segments": os.environ.get("PYTORCH_CUDA_ALLOC_CONF"), "host": os.uname().nodename,
           "code_sha256": T.sha(Path(__file__)), "git_commit": T.git("rev-parse", "HEAD")}
    times, images, nonfinite, losses = [], [], [], []
    status, oom = "ok", None
    smi.start()
    t_prev = time.monotonic()
    t_smi0 = None
    try:
        for step, batch in enumerate(loader, start=1):
            images.append(len(batch))
            inputs, samples = T.to_inputs(model, batch, training=True)
            with optim.optim_context(model):
                ls = model.loss(inputs, samples)
            loss, _ = model.parse_losses(ls)
            if not torch.isfinite(loss):
                nonfinite.append(step)
            optim.update_params(loss)
            torch.cuda.synchronize()
            now = time.monotonic()
            times.append(now - t_prev)
            t_prev = now
            losses.append(float(loss))
            if step == a.warmup:
                t_smi0 = now
            if step >= total:
                break
    except (torch.cuda.OutOfMemoryError, RuntimeError) as e:
        # cuDNN の初期化の失敗（CUDNN_STATUS_NOT_INITIALIZED）も記憶の不足で起きうるので、同じ形で記録して区別する
        if not isinstance(e, torch.cuda.OutOfMemoryError) and "CUDNN_STATUS_NOT_INITIALIZED" not in str(e):
            raise
        status = "oom" if isinstance(e, torch.cuda.OutOfMemoryError) else "cudnn_not_initialized"
        oom = {"step": len(images), "message": str(e).splitlines()[0][:300],
               "max_allocated_bytes": int(torch.cuda.max_memory_allocated()),
               "max_reserved_bytes": int(torch.cuda.max_memory_reserved())}
    smi.stop.set()
    smi.join()
    meas = times[a.warmup:total]
    rows = smi.rows
    steady = [r for r in rows if t_smi0 is not None and r[0] >= t_smi0]
    rec.update({
        "status": status, "oom": oom, "steps_done": len(times), "images_per_step": sorted(set(images)),
        "images_loaded": int(sum(images)), "images_equal_batch": all(n == a.batch for n in images),
        "max_allocated_bytes": int(torch.cuda.max_memory_allocated()), "max_reserved_bytes": int(torch.cuda.max_memory_reserved()),
        "smi_max_memory_mib": max((r[1] for r in rows), default=None),
        "step_seconds_mean": float(np.mean(meas)) if len(meas) == a.measure else None,
        "step_seconds_std": float(np.std(meas, ddof=1)) if len(meas) == a.measure else None,
        "epoch_seconds_estimate": float(np.mean(meas) * len(loader)) if len(meas) == a.measure else None,
        "smi_util_mean_steady": float(np.mean([r[2] for r in steady])) if steady else None,
        "smi_power_mean_steady_w": float(np.mean([r[3] for r in steady])) if steady else None,
        "nonfinite_loss_steps": nonfinite, "loss_first": losses[0] if losses else None, "loss_last": losses[-1] if losses else None})
    C.write_json(a.out, rec)
    print("[probe]", json.dumps({k: rec[k] for k in ("batch", "amp", "no_weights", "status", "steps_done", "images_per_step",
                                                      "max_allocated_bytes", "max_reserved_bytes", "smi_max_memory_mib",
                                                      "step_seconds_mean", "step_seconds_std", "steps_per_epoch",
                                                      "epoch_seconds_estimate", "nonfinite_loss_steps")}), flush=True)


if __name__ == "__main__":
    main()
