"""一歩ごとの時刻の観測器（T-2026-11-02-hostdiff-andrew）。学習の更新と処方には触れない。

``TOWER_SEARCH_OBSERVER`` にこのファイルの経路を渡すと、``scripts/run_ptower_search.py`` と
``scripts/train_relation_detr_search.py`` が読み込む。記録は ``<work>/step_times_rank<R>.jsonl``。

工程塔（fine-tune だけ。DDP の経路 ``stage1_ptower_r3_dist``）:
- ``micro``: micro-step の入口と出口の時刻。入口の間隔が micro-step の秒数。
  ``micro_step`` は ``torch.isfinite(loss)`` の判定で GPU と同期するため、時刻は GPU の進みに従う
- ``opt``: optimizer step の呼び出しの時刻。間隔が optimizer step の秒数（累積 4 回分を含む）
- ``epoch_start`` と ``val_start``・``val_end``（rank 0）: 学習だけの秒数と val の秒数
- ``TOWER_SEARCH_LOSS_HEX=1`` のときだけ、各 micro-step の損失を float の 16 進で書く（決定性の確かめ用。
  値を取り出すために一歩ごとに同期が一つ増えるので、本測定の run では書かない）

検出塔: optimizer step の呼び出しの時刻（``clip_grad_norm_`` の ``float(norm)`` で同期した直後）、
epoch の始めと終わり、評価の始めと終わり。
"""
from __future__ import annotations

import json
import os
import time
import types
from pathlib import Path


def _writer(work):
    rank = int(os.environ.get("RANK", "0"))
    handle = (Path(work) / f"step_times_rank{rank}.jsonl").open("a", buffering=1 << 16)

    def write(**record):
        handle.write(json.dumps(record) + "\n")

    return rank, handle, write


def install_phase(cfg, work):
    if cfg.action != "finetune":
        return
    import stage1_ptower_r3 as r3
    import stage1_ptower_r3_dist as dist_path
    import torch

    rank, handle, write = _writer(work)
    loss_hex = os.environ.get("TOWER_SEARCH_LOSS_HEX") == "1"
    state = {"epoch": 0, "micro": 0}
    micro_step = dist_path.micro_step
    set_epoch = dist_path.ShardedBatches.set_epoch
    frame_predictions = r3.frame_predictions
    optimizer_class = torch.optim.AdamW  # run_ptower_search の RecordedAdamW
    optimizer_step = optimizer_class.step

    def timed_micro(*args, **kwargs):
        start = time.monotonic()
        result = micro_step(*args, **kwargs)
        state["micro"] += 1
        record = {"kind": "micro", "epoch": state["epoch"], "i": state["micro"],
                  "t0": start, "t1": time.monotonic()}
        if loss_hex:
            record["loss"] = float(result).hex()
        write(**record)
        return result

    def timed_set_epoch(self, epoch):
        state["epoch"] = epoch
        write(kind="epoch_start", epoch=epoch, t=time.monotonic())
        handle.flush()
        return set_epoch(self, epoch)

    def timed_predictions(*args, **kwargs):
        write(kind="val_start", epoch=state["epoch"], t=time.monotonic())
        result = frame_predictions(*args, **kwargs)
        write(kind="val_end", epoch=state["epoch"], t=time.monotonic())
        handle.flush()
        return result

    def timed_step(self, *args, **kwargs):
        write(kind="opt", epoch=state["epoch"], t=time.monotonic())
        return optimizer_step(self, *args, **kwargs)

    dist_path.micro_step = timed_micro
    dist_path.ShardedBatches.set_epoch = timed_set_epoch
    r3.frame_predictions = timed_predictions
    optimizer_class.step = timed_step
    import atexit
    atexit.register(handle.close)


def install_detector(detector, work):
    rank, handle, write = _writer(work)
    train_epoch = detector.train_one_epoch_acc
    evaluate = detector.evaluate_acc

    def timed_train(**kwargs):
        epoch = kwargs["epoch"]
        optimizer = kwargs["optimizer"]
        original = optimizer.step

        def step(self, *args, **kw):
            write(kind="opt", epoch=epoch, t=time.monotonic())
            return original(*args, **kw)

        # 束縛メソッドにする。学習率の scheduler が ``step.__self__`` と ``__func__`` で包み直すため
        optimizer.step = types.MethodType(step, optimizer)
        write(kind="epoch_start", epoch=epoch, t=time.monotonic())
        try:
            return train_epoch(**kwargs)
        finally:
            optimizer.step = original
            write(kind="epoch_end", epoch=epoch, t=time.monotonic())
            handle.flush()

    def timed_eval(model, data_loader, epoch, accelerator=None):
        write(kind="val_start", epoch=epoch, t=time.monotonic())
        try:
            return evaluate(model, data_loader, epoch, accelerator)
        finally:
            write(kind="val_end", epoch=epoch, t=time.monotonic())
            handle.flush()

    detector.train_one_epoch_acc = timed_train
    detector.evaluate_acc = timed_eval
    import atexit
    atexit.register(handle.close)
