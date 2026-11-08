"""S1 工程塔の空間特徴（T-2026-11-08-grasp-cards-survey、SPEC §2 S1-2〜4）。本体の .venv。学習しない。

確定の工程塔の fine-tune の checkpoint を、キャッシュを作った経路（stage1_ptower_r3.extract）と同じ手順で読み
（build_backbone → load_state_dict → fc = Identity → eval）、val の 1 動画を評価時の前処理（EVAL_TRANSFORM）で通し、
layer4 の出力（空間の地図）を forward hook で取る。決定性の設定もキャッシュを作ったとき（stage1_ptower.deterministic）と同じ。

  - 地図の形・1 フレームの時間（batch 16 と batch 1）・保存の大きさ（fp32 と fp16 の .npy を保存先に書いて測る）
  - 対照: 地図の空間平均が同じフレームのキャッシュの特徴と相対 1e-3 で一致し、別のフレーム（1 つずらす）とは一致しない
  - 縮小率: 入力の画素と地図の画素の比

    .venv/bin/python s1_pmap.py --video 09 --out-dir <STORE/c/s1>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
CKPT = ROOT / "experiments/phase1/stage1_ptower_20_005_ft_coco_lr0.0001_foldA_seed42/checkpoints/best.pth"
CKPT_SHA = "79c2c4782458c981b347e424a7b27dd81166e9721317d6dc569e8d92241acf6b"


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def state_digest(model):
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        h.update(k.encode())
        h.update(v.detach().cpu().contiguous().numpy().tobytes())
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", default="09")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--batch", type=int, default=16)
    a = ap.parse_args()
    import stage1_ptower as base
    base.deterministic(42)
    import torch
    from torch import nn
    from torch.utils.data import DataLoader

    import stage1_ptower_r3 as r3
    from stage2pilot import common as C

    assert a.video in C.fold_a()["val"]
    C.assert_no_test([a.video], "s1_pmap")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assert sha(CKPT) == CKPT_SHA
    clips = json.loads((C.MANIFEST_DIR / "val.json").read_text())["clips"]      # test の目録は開かない
    names = list(json.loads((C.MANIFEST_DIR / "phase_vocab.json").read_text()))
    ds = r3.FoldFrames(clips, [a.video], train=False)
    frames = [f["frame"] for f in ds.frames]
    read_videos = sorted({C.video_of(f) for f in frames})
    C.assert_no_test(frames, "s1_pmap")
    state = torch.load(CKPT, map_location="cpu", weights_only=True)
    model, source, _ = r3.build_backbone(len(names), "cuda:0", "coco")
    model.load_state_dict(state["model"])
    model.fc = nn.Identity()
    model.eval().requires_grad_(False)
    before = state_digest(model)
    grab = {}
    model.layer4.register_forward_hook(lambda m, i, o: grab.__setitem__("map", o))
    loader = DataLoader(ds, batch_size=a.batch, shuffle=False, num_workers=4)
    n = len(ds)
    shape = None
    f32 = f16 = None
    gap = np.zeros((n, 2048), np.float32)
    k = 0
    fwd, total_t0 = [], time.monotonic()
    in_shape = None
    with torch.no_grad():
        for images, _, ids in loader:
            assert list(ids) == frames[k:k + len(ids)]
            x = images.to("cuda:0")
            in_shape = list(x.shape[1:])
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            y = model(x)
            torch.cuda.synchronize()
            fwd.append((time.perf_counter() - t0, len(ids)))
            m = grab["map"].float().cpu().numpy()
            if f32 is None:
                shape = list(m.shape[1:])
                f32 = np.lib.format.open_memmap(str(out / f"p_layer4_{a.video}_fp32.npy"), "w+", np.float32, (n, *shape))
                f16 = np.lib.format.open_memmap(str(out / f"p_layer4_{a.video}_fp16.npy"), "w+", np.float16, (n, *shape))
            f32[k:k + len(ids)] = m
            f16[k:k + len(ids)] = m.astype(np.float16)
            gap[k:k + len(ids)] = y.float().cpu().numpy()
            k += len(ids)
    total_s = time.monotonic() - total_t0
    f32.flush()
    f16.flush()
    # batch 1 の時間（先頭 20 フレーム。最初の 1 回は温め）
    one = []
    with torch.no_grad():
        for i in range(21):
            x = ds[i][0][None].to("cuda:0")
            torch.cuda.synchronize()
            t0 = time.perf_counter()
            model(x)
            torch.cuda.synchronize()
            if i:
                one.append(time.perf_counter() - t0)
    after = state_digest(model)
    # 対照
    cache = C.load_features()
    ref = np.stack([cache[f] for f in frames]).astype(np.float64)
    mean_map = np.asarray(f32, np.float64).mean(axis=(2, 3))
    def rel(a_, b_):
        return np.linalg.norm(a_ - b_, axis=1) / np.linalg.norm(b_, axis=1)
    rel_same = rel(mean_map, ref)
    rel_shift = rel(mean_map[1:], ref[:-1])
    rel_gap = rel(gap.astype(np.float64), ref)
    mean16 = np.asarray(f16, np.float64).mean(axis=(2, 3))
    rel16 = rel(mean16, ref)
    fwd_s = sum(t for t, _ in fwd[1:])
    fwd_n = sum(c for _, c in fwd[1:])
    rec = {
        "task_id": "T-2026-11-08-grasp-cards-survey", "video": a.video, "frames": n, "read_videos": read_videos,
        "ckpt": str(CKPT.relative_to(ROOT)), "ckpt_sha256": CKPT_SHA, "best_epoch": int(state["epoch"]),
        "weights_digest_before": before, "weights_digest_after": after, "weights_unchanged": before == after,
        "layer": "torchvision ResNet-50 layer4 の出力（avgpool の前）", "transform": str(r3.EVAL_TRANSFORM),
        "input_chw": in_shape, "map_chw": shape,
        "stride_input_px_per_map_px": [in_shape[1] / shape[1], in_shape[2] / shape[2]],
        "stride_original_px_per_map_px": [1080 / shape[1], 1920 / shape[2]],
        "batch": a.batch, "forward_seconds_per_frame_batch": fwd_s / fwd_n,
        "forward_seconds_per_frame_batch1": {"n": len(one), "median": float(np.median(one)), "min": float(min(one)),
                                             "max": float(max(one))},
        "total_seconds_incl_loading": total_s, "total_seconds_per_frame_incl_loading": total_s / n,
        "bytes_fp32_file": (out / f"p_layer4_{a.video}_fp32.npy").stat().st_size,
        "bytes_fp16_file": (out / f"p_layer4_{a.video}_fp16.npy").stat().st_size,
        "bytes_fp32_per_frame": int(np.prod(shape)) * 4, "bytes_fp16_per_frame": int(np.prod(shape)) * 2,
        "control_same_frame_rel_l2": {"max": float(rel_same.max()), "median": float(np.median(rel_same)), "n_over_1e-3": int((rel_same > 1e-3).sum())},
        "control_fp16_same_frame_rel_l2": {"max": float(rel16.max()), "n_over_1e-3": int((rel16 > 1e-3).sum())},
        "control_avgpool_vs_cache_rel_l2_max": float(rel_gap.max()),
        "control_avgpool_vs_mapmean_max_abs": float(np.abs(gap - mean_map).max()),
        "control_shift1_rel_l2": {"min": float(rel_shift.min()), "median": float(np.median(rel_shift)),
                                  "n_under_1e-3": int((rel_shift <= 1e-3).sum())},
        "deterministic": "stage1_ptower.deterministic(42)（キャッシュを作ったときと同じ）",
        "gpu": torch.cuda.get_device_name(0), "torch": torch.__version__,
    }
    (out / f"s1_record_{a.video}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
