#!/usr/bin/env python
"""凍結検出塔（ResNet-50 backbone）の出力キャッシュ。生成・決定性検査・経路比較。

契約 T-2026-09-17-frozen-feature-cache-timing。T1b（P→D 界面・W1）では
`freeze_indices=(0,1,2,3)` により backbone は全段凍結で、FiLM は C5 に当たる。
よって界面の重みに依存しない＝キャッシュ可能な範囲は **backbone の C3/C4/C5 出力まで**である。

三つの副命令を持つ。

  build  : 決定的な前処理（val は transforms=None）で backbone 出力を生成し、
           生の float32 として 1 画像 1 ファイルに保存する。鍵と要約値を index.json に書く。
  bench  : 同一の学習バッチ集合について、**塔を計算する経路**と
           **キャッシュを読む経路**の 1 step 所要時間を同一過程内で比較する。
           読み出しは posix_fadvise(DONTNEED) で頁キャッシュを落としてから測る
           （実寸のキャッシュは実装のメモリに収まらないため、温まった頁キャッシュの
           値を代表値として扱ってはならない）。

鍵（cache key）は塔の識別子を含む。塔を変えれば鍵も要約値も変わる（陰性対照）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import train_t1b as T  # noqa: E402  (chdir/sys.path を伴うため後置 import)

BODY = T.BODY


def sync() -> None:
    if torch.cuda.is_available():
        torch.cuda.synchronize()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tower_ckpt(seed: int) -> Path:
    return T.RELDETR / f"checkpoints/incoming/seed{seed}/best_ap.pth"


def cache_key(seed: int, model_cfg: str, split: str) -> dict:
    """鍵は塔の識別子・凍結源の要約値・前処理・分割から作る。塔を変えれば鍵が変わる。"""
    ck = tower_ckpt(seed)
    ck_sha = sha256_file(ck)
    material = json.dumps({
        "tower_id": f"relation_detr_seed{seed}",
        "tower_ckpt_sha256": ck_sha,
        "tower_ckpt_bytes": ck.stat().st_size,
        "model_cfg": model_cfg,
        "backbone": "ResNetBackbone(resnet50, return_indices=(1,2,3), freeze_indices=(0,1,2,3))",
        "preprocess": "presets.basic 相当（val: transforms=None・原解像度 1920x1080）",
        "split": split,
        "dtype": "float32",
    }, sort_keys=True, ensure_ascii=False)
    return {"material": json.loads(material), "key": hashlib.sha256(material.encode()).hexdigest()}


def feats_to_list(out):
    if isinstance(out, dict):
        return list(out.values()), list(out.keys())
    if isinstance(out, (list, tuple)):
        return list(out), None
    return [out], None


def cmd_build(args) -> None:
    device = torch.device("cuda")
    torch.manual_seed(args.seed)
    loader = T.build_det_loader(train=False)
    model = T.build_model(device, args.seed, T.MODEL_CFG)
    T.register_classes(model, loader)
    model.eval()

    key = cache_key(args.seed, T.MODEL_CFG, args.split)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    # 前処理（正規化・詰め物・mask 生成）は検出器の forward の内側にある。
    # backbone を直接呼ぶと入力が uint8 のままになるため、**実経路を走らせて
    # backbone の出力を hook で受け取る**。処方を変えずに同じ値を得る唯一の経路である。
    cap = {}
    h = model.backbone.register_forward_hook(
        lambda _m, _i, out: cap.__setitem__("out", out))

    entries = []
    t_start = time.perf_counter()
    with torch.no_grad():
        for i, (images, targets) in enumerate(loader):
            if i >= args.limit:
                break
            image_id = int(targets[0]["image_id"])
            images = [im.to(device) for im in images]
            model.set_phase_context(torch.zeros(len(images), T.NUM_PHASES, device=device))
            sync()
            model(images)
            sync()
            feats, keys = feats_to_list(cap["out"])
            arrs = [f.detach().to("cpu").numpy().astype(np.float32) for f in feats]
            path = out_dir / f"{image_id}.bin"
            with open(path, "wb") as fh:
                for a in arrs:
                    fh.write(np.ascontiguousarray(a).tobytes())
            entries.append({
                "image_id": image_id,
                "shapes": [list(a.shape) for a in arrs],
                "bytes": path.stat().st_size,
                "sha256": sha256_file(path),
            })
    elapsed = time.perf_counter() - t_start
    h.remove()

    agg = hashlib.sha256(
        "".join(e["sha256"] for e in sorted(entries, key=lambda e: e["image_id"])).encode()
    ).hexdigest()
    index = {
        "cache_key": key["key"],
        "key_material": key["material"],
        "feat_keys": keys,
        "n_entries": len(entries),
        "total_bytes": sum(e["bytes"] for e in entries),
        "aggregate_sha256": agg,
        "build_seconds": elapsed,
        "entries": entries,
    }
    (out_dir / "index.json").write_text(json.dumps(index, indent=2, ensure_ascii=False))
    print(json.dumps({k: v for k, v in index.items() if k != "entries"},
                     indent=2, ensure_ascii=False))


def cmd_bench(args) -> None:
    device = torch.device("cuda")
    torch.manual_seed(args.seed)
    det_train = T.build_det_loader(train=True)
    model = T.build_model(device, args.seed, T.MODEL_CFG)
    T.register_classes(model, det_train)
    T.set_trainable(model, args.trainable)
    ctx_tr, _ = T.build_imgid_to_ctx(det_train.dataset.coco, T.load_phase_ctx("train"))

    from optimizer import param_dict
    groups = param_dict.finetune_t1b(model, lr=1e-4, film_lr=5e-4)
    opt = torch.optim.AdamW(groups, lr=1e-4, weight_decay=1e-4, betas=(0.9, 0.999))

    from util.collate_fn import DataPrefetcher
    model.train()
    prefetcher = DataPrefetcher(det_train, device)

    # 同じバッチ集合を両経路へ与える。データ供給の時間は両経路から等しく除かれる。
    batches = []
    for _ in range(args.warmup + args.batches):
        b = prefetcher.next()
        if b is None:
            break
        batches.append(b)

    bench_dir = Path(args.cache_dir)
    bench_dir.mkdir(parents=True, exist_ok=True)

    # --- 1. 塔の出力をこのバッチ集合について保存する（＝ 1 epoch 分のキャッシュの縮小版） ---
    cap = {}
    hook = model.backbone.register_forward_hook(
        lambda _m, _i, out: cap.__setitem__("out", out))
    meta = []
    with torch.no_grad():
        for bi, (images, targets) in enumerate(batches):
            model.set_phase_context(T.ctx_for_targets(targets, ctx_tr, device, False))
            model(images, targets)  # 学習形の forward。backbone 出力は hook で受ける
            feats, feat_keys = feats_to_list(cap["out"])
            arrs = [f.detach().to("cpu").numpy().astype(np.float32) for f in feats]
            path = bench_dir / f"b{bi:05d}.bin"
            with open(path, "wb") as fh:
                for a in arrs:
                    fh.write(np.ascontiguousarray(a).tobytes())
            meta.append({"path": str(path), "shapes": [list(a.shape) for a in arrs],
                         "bytes": path.stat().st_size})
    hook.remove()
    # backbone は OrderedDict を返す（neck が .values() を呼ぶ）。読み戻しでも同じ型へ戻す。

    def load_cached(bi):
        # 逐次連結は再コピーを生むため、確保済みの緩衝へ直接読む（キャッシュ経路に公平にする）。
        m = meta[bi]
        size = m["bytes"]
        buf = bytearray(size)
        mv = memoryview(buf)
        with open(m["path"], "rb", buffering=0) as fh:
            os.posix_fadvise(fh.fileno(), 0, 0, os.POSIX_FADV_DONTNEED)  # 頁キャッシュを落とす
            off = 0
            while off < size:
                n = fh.readinto(mv[off:])
                if not n:
                    break
                off += n
        arr = np.frombuffer(buf, dtype=np.float32)
        out, off = [], 0
        for shp in m["shapes"]:
            n = int(np.prod(shp))
            out.append(torch.from_numpy(arr[off:off + n].reshape(shp)).to(device))
            off += n
        if feat_keys is not None:
            from collections import OrderedDict
            return OrderedDict(zip(feat_keys, out))
        return out

    def one_step(images, targets, cached_feats=None):
        model.set_phase_context(T.ctx_for_targets(targets, ctx_tr, device, False))
        if cached_feats is not None:
            orig = model.backbone.forward
            model.backbone.forward = lambda _x, _f=cached_feats: _f
        try:
            loss_dict = model(images, targets)
            loss = sum(loss_dict.values())
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(
                [q for q in model.parameters() if q.requires_grad], 0.1)
            opt.step()
        finally:
            if cached_feats is not None:
                model.backbone.forward = orig

    def run_compute(bi, images, targets):
        sync()
        a0 = time.perf_counter()
        one_step(images, targets)
        sync()
        return time.perf_counter() - a0

    def run_cache(bi, images, targets):
        sync()
        b0 = time.perf_counter()
        feats = load_cached(bi)
        sync()
        b1 = time.perf_counter()
        one_step(images, targets, cached_feats=feats)
        sync()
        b2 = time.perf_counter()
        return b1 - b0, b2 - b1

    rec = {"compute": [], "cache_read": [], "cache_step": [], "cache_total": []}
    for bi, (images, targets) in enumerate(batches):
        # 順序の偏りを見るため --swap で先後を入れ替えられるようにする（対照は両方向）。
        if args.swap:
            r, st = run_cache(bi, images, targets)
            c = run_compute(bi, images, targets)
        else:
            c = run_compute(bi, images, targets)
            r, st = run_cache(bi, images, targets)
        if bi >= args.warmup:
            rec["compute"].append(c)
            rec["cache_read"].append(r)
            rec["cache_step"].append(st)
            rec["cache_total"].append(r + st)

    def stat(xs):
        xs = sorted(xs)
        n = len(xs)
        return {"n": n, "mean": sum(xs) / n, "median": xs[n // 2],
                "min": xs[0], "max": xs[-1]}

    out = {
        "batches_measured": len(rec["compute"]),
        "warmup": args.warmup,
        "order": "cache_first" if args.swap else "compute_first",
        "trainable": args.trainable,
        "n_trainable_params": sum(q.numel() for q in model.parameters() if q.requires_grad),
        "cache_bytes_per_batch": {
            "mean": sum(m["bytes"] for m in meta) / len(meta),
            "min": min(m["bytes"] for m in meta),
            "max": max(m["bytes"] for m in meta),
        },
        "seconds": {k: stat(v) for k, v in rec.items()},
    }
    out["speedup_total"] = out["seconds"]["compute"]["mean"] / out["seconds"]["cache_total"]["mean"]
    Path(args.out).write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(json.dumps(out, indent=2, ensure_ascii=False))


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("build")
    b.add_argument("--seed", type=int, default=42)
    b.add_argument("--split", default="val")
    b.add_argument("--limit", type=int, default=32)
    b.add_argument("--out", required=True)
    b.set_defaults(func=cmd_build)

    n = sub.add_parser("bench")
    n.add_argument("--seed", type=int, default=42)
    n.add_argument("--batches", type=int, default=40)
    n.add_argument("--warmup", type=int, default=5)
    n.add_argument("--cache-dir", required=True)
    n.add_argument("--trainable", default="film", choices=("film", "all"),
                   help="film=W1（入力適合層のみ）/ all=末端まで学習（backbone は config で凍結のまま）")
    n.add_argument("--swap", action="store_true",
                   help="キャッシュ経路を先に回す（順序の偏りを両方向で見る）")
    n.add_argument("--out", required=True)
    n.set_defaults(func=cmd_bench)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
