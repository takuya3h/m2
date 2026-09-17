#!/usr/bin/env python
"""T1b（P→D 界面）の 1 step を、数値精度と計算グラフの最適化の条件ごとに測る。

契約 T-2026-09-17-amp-compile-timing。**処方は変えない**（同じ config・同じ loader・
同じ最適化器群・同じ seed・同じバッチ）。変えるのは数値精度と計算グラフの最適化だけである。

条件:

    fp32           現行のまま（単精度）。基準
    bf16           bfloat16 の自動混合精度（尺度調整は不要）
    fp16           float16 の自動混合精度（GradScaler による勾配の尺度調整を伴う）
    compile        torch.compile のみ（精度は単精度）
    compile_bf16   torch.compile と bfloat16 の併用
    compile_fp16   torch.compile と float16 の併用

測り方:

- **暖機を入れる。** 最初の `--warmup` step は捨てる。compile は初回に時間がかかるため
  **初回 step の所要時間を別行に記録する**。
- **装置の同期を取ってから計時する。** 取らない計測も併せて行い、両方を出す
  （取らないと非同期実行のぶん速く見える）。
- バッチは最初に一度だけ取り出して実装のメモリに保持し、全条件へ同じ列を与える。
  形の列から要約値を作り、条件間で同一であることを示す。
- 記憶領域は `torch.cuda.max_memory_allocated` を条件ごとに取り直して記録する。
- 損失は全 step を記録し、非数・無限大・跳ねの有無を数える。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_t1b as T  # noqa: E402  (chdir/sys.path を伴うため後置 import)

AMP_DTYPE = {"bf16": torch.bfloat16, "fp16": torch.float16,
             "compile_bf16": torch.bfloat16, "compile_fp16": torch.float16}
COMPILED = {"compile", "compile_bf16", "compile_fp16", "compile_tf32"}
# TF32 は行列積の演算精度を下げる設定で、torch の既定は
# matmul 側が False・cudnn 側が True である（A6000 は Ampere で TF32 演算器を持つ）。
# **過程ごとに一度立てると残る**ため、条件ごとに明示して戻す。
TF32 = {"tf32", "compile_tf32"}


def sync() -> None:
    torch.cuda.synchronize()


def collect_batches(n: int, seed: int, trainable: str):
    """バッチを一度だけ取り出して保持する。seed を固定するため列は条件間で同じになる。"""
    torch.manual_seed(seed)
    det_train = T.build_det_loader(train=True)
    raw = T.build_model(torch.device("cuda"), seed, T.MODEL_CFG)
    T.register_classes(raw, det_train)
    T.set_trainable(raw, trainable)
    ctx_tr, _ = T.build_imgid_to_ctx(det_train.dataset.coco, T.load_phase_ctx("train"))

    from util.collate_fn import DataPrefetcher
    raw.train()
    pref = DataPrefetcher(det_train, torch.device("cuda"))
    batches = []
    for _ in range(n):
        b = pref.next()
        if b is None:
            break
        batches.append(b)
    shapes = [[list(im.shape) for im in imgs] for imgs, _ in batches]
    digest = hashlib.sha256(json.dumps(shapes).encode()).hexdigest()
    return raw, det_train, ctx_tr, batches, digest, len(det_train)


def make_optimizer(raw, lr, film_lr):
    from optimizer import param_dict
    groups = param_dict.finetune_t1b(raw, lr=lr, film_lr=film_lr)
    return torch.optim.AdamW(groups, lr=lr, weight_decay=1e-4, betas=(0.9, 0.999))


def run_condition(cond, raw, ctx_tr, batches, args):
    device = torch.device("cuda")
    opt = make_optimizer(raw, 1e-4, 5e-4)
    torch.backends.cuda.matmul.allow_tf32 = cond in TF32
    amp_dtype = AMP_DTYPE.get(cond)
    scaler = torch.cuda.amp.GradScaler() if cond in ("fp16", "compile_fp16") else None
    model = torch.compile(raw) if cond in COMPILED else raw

    def one_step(images, targets):
        raw.set_phase_context(T.ctx_for_targets(targets, ctx_tr, device, False))
        if amp_dtype is not None:
            with torch.autocast("cuda", dtype=amp_dtype):
                loss_dict = model(images, targets)
                loss = sum(loss_dict.values())
        else:
            loss_dict = model(images, targets)
            loss = sum(loss_dict.values())
        opt.zero_grad()
        if scaler is not None:
            scaler.scale(loss).backward()
            scaler.unscale_(opt)
            torch.nn.utils.clip_grad_norm_(
                [q for q in raw.parameters() if q.requires_grad], 0.1)
            scaler.step(opt)
            scaler.update()
        else:
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [q for q in raw.parameters() if q.requires_grad], 0.1)
            opt.step()
        return float(loss.detach())

    losses = []
    nb = len(batches)

    # 暖機。**初回の 1 step は別に計る**（compile の構築時間がここに入る）。
    sync()
    t0 = time.perf_counter()
    losses.append(one_step(*batches[0]))
    sync()
    first_step = time.perf_counter() - t0
    for i in range(1, args.warmup):
        losses.append(one_step(*batches[i % nb]))
    sync()
    torch.cuda.reset_peak_memory_stats()

    # 同期を取って計る
    per_step = []
    for i in range(args.steps):
        images, targets = batches[(args.warmup + i) % nb]
        sync()
        s0 = time.perf_counter()
        losses.append(one_step(images, targets))
        sync()
        per_step.append(time.perf_counter() - s0)
    peak_bytes = torch.cuda.max_memory_allocated()

    # 同期を取らずに計る（対照。取らないと速く見えることを示すため）
    sync()
    n0 = time.perf_counter()
    nosync = []
    for i in range(args.steps):
        images, targets = batches[(args.warmup + i) % nb]
        a = time.perf_counter()
        losses.append(one_step(images, targets))
        nosync.append(time.perf_counter() - a)
    sync()
    nosync_wall = (time.perf_counter() - n0) / args.steps

    finite = [x for x in losses if math.isfinite(x)]
    base = sorted(finite)[len(finite) // 2] if finite else float("nan")
    return {
        "condition": cond,
        "matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
        "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
        "first_step_seconds": first_step,
        "steps": args.steps,
        "warmup": args.warmup,
        "mean_seconds": sum(per_step) / len(per_step),
        "median_seconds": sorted(per_step)[len(per_step) // 2],
        "min_seconds": min(per_step),
        "max_seconds": max(per_step),
        "nosync_mean_seconds": sum(nosync) / len(nosync),
        "nosync_wall_per_step": nosync_wall,
        "peak_memory_bytes": peak_bytes,
        "loss": {
            "n": len(losses),
            "n_nonfinite": len(losses) - len(finite),
            "median": base,
            "max": max(finite) if finite else None,
            "min": min(finite) if finite else None,
            "n_spike_over_5x_median": sum(1 for x in finite if base > 0 and x > 5 * base),
            "first5": losses[:5],
            "last5": losses[-5:],
        },
    }


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--trainable", default="film", choices=("film", "all"))
    p.add_argument("--conditions", default="fp32,bf16,fp16,compile,compile_bf16")
    p.add_argument("--warmup", type=int, default=10)
    p.add_argument("--steps", type=int, default=40)
    p.add_argument("--batches", type=int, default=0,
                   help="保持するバッチ数。0 なら warmup + steps * 2")
    p.add_argument("--dynamo-suppress-errors", action="store_true",
                   help="dynamo が追跡に失敗した部分を例外にせず eager へ退避させる。"
                        "**実装は改変しない**回避手段。torch 2.1 では set_criterion.py の "
                        "F.one_hot が動的な形を扱えず TorchRuntimeError で止まるため要る")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    if args.dynamo_suppress_errors:
        # `import torch._dynamo` と書くと torch がこの関数の局所名になり、
        # module 側の torch を隠して以降が UnboundLocalError になる（実測）。
        from torch import _dynamo
        _dynamo.config.suppress_errors = True

    conds = [c for c in args.conditions.split(",") if c]
    nbatch = args.batches or (args.warmup + args.steps * 2)
    raw, det_train, ctx_tr, batches, digest, steps_per_epoch = collect_batches(
        nbatch, args.seed, args.trainable)

    results = []
    for cond in conds:
        # 条件ごとに重みを初期状態へ戻す。計時に影響しないが、損失の比較を公平にする。
        from util.utils import load_checkpoint, load_state_dict
        ck = load_checkpoint(str(T.RELDETR / f"checkpoints/incoming/seed{args.seed}/best_ap.pth"))
        load_state_dict(raw, ck["model"] if isinstance(ck, dict) and "model" in ck else ck)
        raw.train()
        try:
            results.append(run_condition(cond, raw, ctx_tr, batches, args))
            print(f"[bench] {cond}: {results[-1]['mean_seconds']:.4f}s "
                  f"(first {results[-1]['first_step_seconds']:.2f}s)", flush=True)
        except Exception as exc:  # noqa: BLE001  条件ごとの失敗を握って記録し、他条件は続ける
            results.append({"condition": cond, "failed": True,
                            "error": f"{type(exc).__name__}: {exc}"[:2000]})
            print(f"[bench] {cond}: 失敗 {type(exc).__name__}", flush=True)
        torch.cuda.empty_cache()

    base = next((r for r in results if r["condition"] == "fp32" and not r.get("failed")), None)
    for r in results:
        if base and not r.get("failed"):
            r["speedup_vs_fp32"] = base["mean_seconds"] / r["mean_seconds"]

    out = {
        "dynamo_suppress_errors": bool(args.dynamo_suppress_errors),
        "trainable": args.trainable,
        "seed": args.seed,
        "batch_shapes_sha256": digest,
        "n_batches_held": len(batches),
        "steps_per_epoch": steps_per_epoch,
        "gpu": torch.cuda.get_device_name(0),
        "torch": torch.__version__,
        "n_trainable_params": sum(q.numel() for q in raw.parameters() if q.requires_grad),
        "results": results,
    }
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps({"digest": digest,
                      "speedups": {r["condition"]: r.get("speedup_vs_fp32")
                                   for r in results}}, ensure_ascii=False))


if __name__ == "__main__":
    main()
