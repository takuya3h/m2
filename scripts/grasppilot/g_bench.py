"""G の構造（Mask2Former）の候補の計測（非公式 T-2026-10-31-grasp-pilot-probe、Task E-1）。本体の .venv を変えずに使う。

候補:
    mmdet   mmdet 3.3.0 の Mask2Former（R50、COCO instance、lsj 50e）。MultiScaleDeformableAttention は mmcv 2.1.0 の独自演算
    hf      transformers 4.44.2 の Mask2FormerForUniversalSegmentation（Swin-T、COCO instance）。変形注意は PyTorch の実装

    check   COCO の重みを読み（要約値をファイル名・記録と照合）、折り A の val の 1 枚で推論が通るか
    bench   学習の一歩（ラベルの集合は把持関係 5 クラス = E-2 の候補の一つ）を 10 歩の立ち上がりの後 60 歩測り、
            推論の速さ（val 50 枚）を測る。batch 2、入力は短辺 800（長辺 1333 まで）。単精度

    python scripts/grasppilot/g_bench.py check|bench --cand mmdet|hf --out <json>
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from grasppilot import grasp_signals as G  # noqa: E402
from stage2pilot import common as C  # noqa: E402

S = Path("/home/ubuntu/slocal2/stage2pilot_store/T-2026-10-31-grasp-pilot-probe/e")
W = S / "weights"
MMDET_CFG = "mask2former/mask2former_r50_8xb2-lsj-50e_coco.py"
MMDET_W = W / "mmdet/mask2former_r50_8xb2-lsj-50e_coco_20220506_191028-41b088b6.pth"
HF_DIR = next((W / "hf/hub/models--facebook--mask2former-swin-tiny-coco-instance/snapshots").glob("*"), None)
RAW = C.ROOT / "data/raw/ego"
MEAN, STD = np.array([123.675, 116.28, 103.53]), np.array([58.395, 57.12, 57.375])


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def verify_weight(path, expected_prefix):
    """重みの要約値がファイル名に埋め込まれた値（mmdet の慣習）か記録の値で始まるか。違えば拒む。"""
    d = sha(path)
    return {"path": str(path), "sha256": d, "expected_prefix": expected_prefix, "ok": d.startswith(expected_prefix)}


def image_path(stem, part):
    v = stem.split("_")[0]
    return RAW / part / v / f"{stem}.jpg"


def load_image(stem, part, short=800, long=1333):
    from PIL import Image
    im = Image.open(image_path(stem, part)).convert("RGB")
    w, h = im.size
    r = min(short / min(h, w), long / max(h, w))
    nw, nh = int(round(w * r)), int(round(h * r))
    return np.asarray(im.resize((nw, nh))), (h, w), (nh, nw)


def five_class_targets(index, stem, size):
    """把持関係 5 クラスのインスタンスのマスク（入力の大きさ）とクラス（0〜4）。"""
    out_m, out_c = [], []
    hh, ww = index.size[stem]
    for a in index.anns["hand_tool_seg"].get(stem, []):
        m = G.decode(a["segmentation"], hh, ww).astype(np.float32)
        m = F.interpolate(torch.from_numpy(m)[None, None], size=size, mode="nearest")[0, 0]
        out_m.append(m)
        out_c.append(a["category_id"] - 1)
    return torch.stack(out_m) if out_m else torch.zeros((0,) + size), torch.tensor(out_c, dtype=torch.long)


def val_stems(n, seed=42):
    fold = C.fold_a()
    stems = [f for v, fr, _ in C.phase_sequences(fold["val"]) for f in fr]
    return sorted(np.random.default_rng(seed).choice(stems, n, replace=False).tolist())


def train_stems(index, n, seed=42):
    fold = C.fold_a()
    stems = [f for v, fr, _ in C.phase_sequences(fold["train"]) for f in fr if index.annotated(f)]
    return np.random.default_rng(seed).choice(stems, n, replace=False).tolist()


# ---------------- mmdet ----------------
def mmdet_model(num_classes=None):
    import os

    import mmdet
    from mmdet.apis import init_detector
    from mmengine.config import Config
    cfg = Config.fromfile(os.path.join(os.path.dirname(mmdet.__file__), ".mim/configs", MMDET_CFG))
    if num_classes:
        cfg.model.panoptic_head.num_things_classes = num_classes
        cfg.model.panoptic_head.loss_cls.class_weight = [1.0] * num_classes + [0.1]
        cfg.model.panoptic_fusion_head.num_things_classes = num_classes
        cfg.num_things_classes = num_classes
        # LSJ の 1024×1024 への詰め物（batch_augments）を外し、hf と同じ入力（短辺 800、32 の倍数へ詰める）で測る
        cfg.model.data_preprocessor.batch_augments = None
    return init_detector(cfg, None, device="cuda"), cfg


def mmdet_load(model, strict_head=True):
    st = torch.load(MMDET_W, map_location="cpu")["state_dict"]
    own = model.state_dict()
    keep = {k: v for k, v in st.items() if k in own and own[k].shape == v.shape}
    missing, unexpected = model.load_state_dict(keep, strict=False)
    return {"loaded": len(keep), "skipped_shape": len([k for k in st if k in own and own[k].shape != st[k].shape]),
            "missing": len(missing)}


def mmdet_inputs(model, imgs, targets=None):
    from mmdet.structures import DetDataSample
    from mmengine.structures import InstanceData
    samples, tens = [], []
    for i, (arr, orig, size) in enumerate(imgs):
        tens.append(torch.from_numpy(arr).permute(2, 0, 1).contiguous())
        ds = DetDataSample(metainfo={"img_shape": size, "ori_shape": size, "pad_shape": size, "scale_factor": (1.0, 1.0),
                                     "batch_input_shape": size})
        if targets is not None:
            from mmdet.structures.mask import BitmapMasks
            m, c = targets[i]
            gi = InstanceData()
            gi.labels = c
            gi.masks = BitmapMasks(m.numpy().astype(np.uint8), size[0], size[1])
            boxes = []
            for mm in m.numpy():
                yy, xx = np.nonzero(mm)
                boxes.append([xx.min(), yy.min(), xx.max() + 1, yy.max() + 1] if len(xx) else [0, 0, 1, 1])
            gi.bboxes = torch.tensor(boxes, dtype=torch.float32).reshape(-1, 4)
            ds.gt_instances = gi
        samples.append(ds)
    data = model.data_preprocessor({"inputs": tens, "data_samples": samples}, training=targets is not None)
    return data["inputs"], data["data_samples"]


# ---------------- hf ----------------
def hf_model(num_labels=None):
    from transformers import Mask2FormerForUniversalSegmentation
    kw = {"num_labels": num_labels, "ignore_mismatched_sizes": True} if num_labels else {}
    return Mask2FormerForUniversalSegmentation.from_pretrained(str(HF_DIR), **kw).cuda()


def hf_pixels(imgs):
    hs = max(i[2][0] for i in imgs)
    ws = max(i[2][1] for i in imgs)
    hs, ws = (hs + 31) // 32 * 32, (ws + 31) // 32 * 32
    x = torch.zeros(len(imgs), 3, hs, ws)
    pm = torch.zeros(len(imgs), hs, ws, dtype=torch.long)
    for k, (arr, _, (h, w)) in enumerate(imgs):
        x[k, :, :h, :w] = torch.from_numpy(((arr - MEAN) / STD).transpose(2, 0, 1).astype(np.float32))
        pm[k, :h, :w] = 1
    return x.cuda(), pm.cuda()


def cmd_check(a):
    stem = val_stems(1)[0]
    img = load_image(stem, "val")
    res = {"cand": a.cand, "val_image": stem, "videos": C.assert_no_test([stem], "g_bench/check")}
    if a.cand == "mmdet":
        import mmcv
        import mmdet
        res.update(source=f"mmdet {mmdet.__version__} / mmcv {mmcv.__version__}（既存の .venv）", config=MMDET_CFG,
                   weight=verify_weight(MMDET_W, "41b088b6"),
                   weight_tampered_copy_rejected=not verify_weight(MMDET_W, "41b088b7")["ok"])
        model, _ = mmdet_model()
        res["load"] = mmdet_load(model)
        model.eval()
        x, ds = mmdet_inputs(model, [img])
        with torch.no_grad():
            out = model.predict(x, ds)[0]
        sc = out.pred_instances.scores.cpu().numpy()
        res.update(n_pred=int(len(sc)), n_score_ge_0_5=int((sc >= 0.5).sum()), top_labels=out.pred_instances.labels[:10].tolist(),
                   mask_shape=list(out.pred_instances.masks.shape))
    else:
        import transformers
        res.update(source=f"transformers {transformers.__version__}（既存の .venv）", hf_dir=str(HF_DIR),
                   weight=verify_weight(HF_DIR / "model.safetensors", "3550e8b2"),
                   weight_tampered_copy_rejected=not verify_weight(HF_DIR / "model.safetensors", "3550e8b3")["ok"])
        model = hf_model().eval()
        x, pm = hf_pixels([img])
        with torch.no_grad():
            out = model(pixel_values=x, pixel_mask=pm)
        prob = out.class_queries_logits.softmax(-1)[0, :, :-1]
        sc, lab = prob.max(-1)
        res.update(n_queries=int(prob.shape[0]), n_score_ge_0_5=int((sc >= 0.5).sum()),
                   top_labels=[model.config.id2label[int(k)] for k in lab[sc.argsort(descending=True)[:10]]],
                   mask_logits_shape=list(out.masks_queries_logits.shape))
    C.write_json(a.out, res)
    print(json.dumps(res, ensure_ascii=False))


def cmd_bench(a):
    index = G.HTSIndex(("train", "val"))
    stems = train_stems(index, 2 * (a.warmup + a.steps))
    videos = C.assert_no_test(stems, "g_bench/train")
    torch.manual_seed(42)
    if a.cand == "mmdet":
        model, _ = mmdet_model(num_classes=5)
        load = mmdet_load(model)
    else:
        model = hf_model(num_labels=5)
        load = {"note": "from_pretrained(num_labels=5, ignore_mismatched_sizes=True)"}
    model.train()
    opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4, weight_decay=0.05)
    times, shapes = [], []
    for g in range(torch.cuda.device_count()):
        torch.cuda.reset_peak_memory_stats(g)
    for step in range(a.warmup + a.steps):
        batch = [load_image(s, "train") for s in stems[2 * step:2 * step + 2]]
        tg = [five_class_targets(index, s, b[2]) for s, b in zip(stems[2 * step:2 * step + 2], batch)]
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        if a.cand == "mmdet":
            x, ds = mmdet_inputs(model, batch, tg)
            losses = model.loss(x, ds)
            loss = sum(v for k, v in losses.items() if "loss" in k)
        else:
            x, pm = hf_pixels(batch)
            out = model(pixel_values=x, pixel_mask=pm, mask_labels=[F.pad(m, (0, x.shape[-1] - m.shape[-1], 0, x.shape[-2] - m.shape[-2])).cuda() for m, _ in tg],
                        class_labels=[c.cuda() for _, c in tg])
            loss = out.loss
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        torch.cuda.synchronize()
        if step >= a.warmup:
            times.append(time.perf_counter() - t0)
            shapes.append(list(x.shape))
    peak = {g: int(torch.cuda.max_memory_allocated(g)) for g in range(torch.cuda.device_count())}
    # 推論の速さ
    model.eval()
    vs = val_stems(a.n_infer)
    C.assert_no_test(vs, "g_bench/infer")
    imgs = [load_image(s, "val") for s in vs]
    torch.cuda.synchronize()
    t0 = time.perf_counter()
    with torch.no_grad():
        for im in imgs:
            if a.cand == "mmdet":
                x, ds = mmdet_inputs(model, [im])
                model.predict(x, ds)
            else:
                x, pm = hf_pixels([im])
                model(pixel_values=x, pixel_mask=pm)
    torch.cuda.synchronize()
    infer = len(imgs) / (time.perf_counter() - t0)
    gpu = torch.cuda.get_device_name(0)
    res = {"cand": a.cand, "load": load, "label_set": "把持関係 5 クラス（E-2 の候補 1）", "batch": 2,
           "input": "短辺 800・長辺 1333 まで（画像の縮小は PIL の既定）", "precision": "fp32", "optimizer": "AdamW lr 1e-4 wd 0.05",
           "warmup_steps": a.warmup, "steps": a.steps, "step_seconds_mean": float(np.mean(times)),
           "step_seconds_median": float(np.median(times)), "step_seconds_p90": float(np.quantile(times, 0.9)),
           "input_shapes_seen": sorted({tuple(s) for s in map(tuple, shapes)})[:5], "peak_alloc_bytes_by_gpu": peak,
           "infer_images_per_sec_batch1": infer, "n_infer": len(imgs), "train_videos": videos, "gpu": gpu,
           "gpu_shared_with_other_runs": a.shared}
    C.write_json(a.out, res)
    print(json.dumps({k: res[k] for k in ("cand", "step_seconds_mean", "step_seconds_median", "peak_alloc_bytes_by_gpu",
                                          "infer_images_per_sec_batch1")}, ensure_ascii=False))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("check", "bench"))
    ap.add_argument("--cand", required=True, choices=("mmdet", "hf"))
    ap.add_argument("--out", required=True)
    ap.add_argument("--warmup", type=int, default=10)
    ap.add_argument("--steps", type=int, default=60)
    ap.add_argument("--n-infer", type=int, default=50)
    ap.add_argument("--shared", action="store_true", help="他の run と GPU を分けて測った印")
    a = ap.parse_args()
    {"check": cmd_check, "bench": cmd_bench}[a.cmd](a)


if __name__ == "__main__":
    main()
