"""Task B-3（T-2026-11-09-grasp-roitoken-transition-pilot）。工程塔の空間特徴（layer4 と layer3）を取り出す。本体の .venv。学習しない。

T-2026-11-08-grasp-cards-survey の s1_pmap.py と同じ読み方（build_backbone → load_state_dict → fc = Identity → eval、
EVAL_TRANSFORM、stage1_ptower.deterministic(42)）で、折り A の train と val の工程の目録の全フレーム（術具注釈と同じ集合、
画像のある行）を通し、layer3 と layer4 の出力を forward hook で取って fp16 の .npy に書く。並びは common.phase_sequences の順。

  - 形・大きさ・sha256
  - 対照: layer4 の地図の空間平均（fp16 の保存値から）がキャッシュの同じフレームと相対 L2 で 1e-3 以内、1 つずらしたフレームとは外れる

    .venv/bin/python b3_pmaps.py --part val --out-dir <S>/feat
"""
from __future__ import annotations

import argparse
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


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", choices=["train", "val"], required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--batch", type=int, default=16)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    import stage1_ptower as base
    base.deterministic(42)
    import torch
    from PIL import Image
    from torch import nn
    from torch.utils.data import DataLoader, Dataset

    import stage1_ptower_r3 as r3
    from stage2pilot import common as C

    split = C.fold_a()
    videos = C.assert_no_test(split[a.part], "b3_pmaps")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    assert C.sha256(CKPT) == CKPT_SHA
    clips = json.loads((C.MANIFEST_DIR / f"{a.part}.json").read_text())["clips"]     # test の目録は開かない
    entry = {f["frame"]: f for c in clips for f in c["frames"]}
    frames = [f for _, fs, _ in C.phase_sequences(videos) for f in fs]
    C.assert_no_test(frames, "b3_pmaps")

    class Frames(Dataset):
        def __len__(self):
            return len(frames)

        def __getitem__(self, i):
            with Image.open(ROOT / entry[frames[i]]["image_path"]) as im:
                return r3.EVAL_TRANSFORM(im.convert("RGB")), frames[i]

    names = list(json.loads((C.MANIFEST_DIR / "phase_vocab.json").read_text()))
    state = torch.load(CKPT, map_location="cpu", weights_only=True)
    model, _, _ = r3.build_backbone(len(names), "cuda:0", "coco")
    model.load_state_dict(state["model"])
    model.fc = nn.Identity()
    model.eval().requires_grad_(False)
    grab = {}
    model.layer3.register_forward_hook(lambda m, i, o: grab.__setitem__("l3", o))
    model.layer4.register_forward_hook(lambda m, i, o: grab.__setitem__("l4", o))
    loader = DataLoader(Frames(), batch_size=a.batch, shuffle=False, num_workers=a.workers)
    n = len(frames)
    mm = {}
    gap = np.zeros((n, 2048), np.float32)
    k, t0, in_shape = 0, time.monotonic(), None
    with torch.no_grad():
        for images, ids in loader:
            assert list(ids) == frames[k:k + len(ids)]
            x = images.to("cuda:0")
            in_shape = list(x.shape[1:])
            y = model(x)
            for key in ("l3", "l4"):
                m = grab[key].half().cpu().numpy()
                if key not in mm:
                    mm[key] = np.lib.format.open_memmap(str(out / f"p_{'layer3' if key == 'l3' else 'layer4'}_{a.part}.npy"),
                                                        "w+", np.float16, (n, *m.shape[1:]))
                mm[key][k:k + len(ids)] = m
            gap[k:k + len(ids)] = y.float().cpu().numpy()
            k += len(ids)
            if k % 1600 < a.batch:
                print(f"[b3] {a.part} {k}/{n} {(time.monotonic() - t0) / k:.4f}s/frame", flush=True)
    seconds = time.monotonic() - t0
    for v in mm.values():
        v.flush()
    np.save(out / f"frame_ids_{a.part}.npy", np.asarray(frames))
    cache = C.load_features()
    ref = np.stack([cache[f] for f in frames]).astype(np.float64)
    l4 = np.load(out / f"p_layer4_{a.part}.npy", mmap_mode="r")
    mean_map = np.zeros((n, 2048), np.float64)
    for s in range(0, n, 256):
        mean_map[s:s + 256] = np.asarray(l4[s:s + 256], np.float64).mean(axis=(2, 3))

    def rel(a_, b_):
        return np.linalg.norm(a_ - b_, axis=1) / np.linalg.norm(b_, axis=1)
    same = rel(mean_map, ref)
    shift = rel(mean_map[1:], ref[:-1])
    gap_rel = rel(gap.astype(np.float64), ref)
    files = {}
    for name in ("layer3", "layer4"):
        p = out / f"p_{name}_{a.part}.npy"
        arr = np.load(p, mmap_mode="r")
        files[name] = {"path": str(p), "shape": list(arr.shape), "dtype": str(arr.dtype), "bytes": p.stat().st_size,
                       "sha256": C.sha256(p)}
    ids_path = out / f"frame_ids_{a.part}.npy"
    rec = {"task_id": "T-2026-11-09-grasp-roitoken-transition-pilot", "part": a.part, "frames": n, "videos": videos,
           "read_videos": C.assert_no_test(frames, "b3_pmaps"), "ckpt": str(CKPT.relative_to(ROOT)), "ckpt_sha256": CKPT_SHA,
           "transform": str(r3.EVAL_TRANSFORM), "input_chw": in_shape, "files": files,
           "frame_ids": {"path": str(ids_path), "sha256": C.sha256(ids_path)},
           "seconds_total": seconds, "seconds_per_frame": seconds / n,
           "control_same_frame_rel_l2": {"max": float(same.max()), "median": float(np.median(same)),
                                         "n_over_1e-3": int((same > 1e-3).sum())},
           "control_shift1_rel_l2": {"min": float(shift.min()), "median": float(np.median(shift)),
                                     "n_under_1e-3": int((shift <= 1e-3).sum())},
           "control_avgpool_vs_cache_rel_l2_max": float(gap_rel.max()),
           "deterministic": "stage1_ptower.deterministic(42)", "gpu": torch.cuda.get_device_name(0)}
    (out / f"b3_record_{a.part}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(rec, ensure_ascii=False, indent=1), flush=True)


if __name__ == "__main__":
    main()
