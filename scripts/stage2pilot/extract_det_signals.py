#!/usr/bin/env python
"""Task C / E-5: 検出塔の信号を作る（非公式 T-2026-10-18-stage2-pilot-folda、SPEC §4 Task C の表）。

.venv-relation-detr で動かす。検出塔を fp32・eval・batch 1 で順伝播し、フレームごとに次を作る。

    D0        後処理後の出力（上位 300）から、クラスごとの最大スコア                     (15)
    D-GT      術具の正解の在否                                                         (15)
    D0-RT     領域トークン（extract_t1a_regiontoken.region_vector と同じ作り方）         (3840)
    D0-INST   後処理後の出力のスコア上位 K 個。その query の 15 クラスのスコア、枠（中心と幅高を
              画像の大きさで割った 4 つ）、その query の埋め込み（decoder 最終層の class_head への入力）
                                                                                       (K, 15 + 4 + 256)
    D0-INST-UQ  D0-INST と同じ作り方で、後処理の順位をたどって重複しない query の上位 K 個（SPEC の読み (b)）
    D-GT-INST 正解の枠。クラスの one-hot と枠（同じ正規化）。最大 K 個、count で数を持つ   (K, 15 + 4)

フレームは折りの注釈（instances_<part>.json）の画像。test の注釈は開かない。
val の後処理後の出力は COCO の検出結果の形でも保存し、評価器の mAP が検出塔の値と一致するかで
経路の同一性を確かめる（--check-map）。

    python scripts/stage2pilot/extract_det_signals.py --ckpt <best_ap.pth> --ann-dir <折り> \\
        --part val --videos 09,10 --out-dir <STORE/signals/...> --k 11 [--check-map]
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torchvision.io import ImageReadMode, read_image

PROJ = Path(__file__).resolve().parents[2]
REPO = PROJ / "third_party" / "Relation-DETR"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PROJ / "scripts"))

from util.lazy_load import Config  # noqa: E402
from util.utils import load_checkpoint, load_state_dict  # noqa: E402

from stage2pilot import common as C  # noqa: E402

MODEL_CFG = str(REPO / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
NUM_TOOLS = 15
EMBED = 256


class Capture:
    """decoder.class_head[-1] の forward hook。最終層の (埋め込み, logits) を取る。"""

    def __init__(self):
        self.tokens = self.logits = None

    def __call__(self, module, inputs, output):
        self.tokens = inputs[0].detach()[0].float()     # (Q, 256)
        self.logits = output.detach()[0].float()        # (Q, 15)


def cxcywh_norm(xyxy: np.ndarray, w: float, h: float) -> np.ndarray:
    x0, y0, x1, y1 = xyxy[..., 0], xyxy[..., 1], xyxy[..., 2], xyxy[..., 3]
    return np.stack([(x0 + x1) / 2 / w, (y0 + y1) / 2 / h, (x1 - x0) / w, (y1 - y0) / h], -1)


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--ann-dir", required=True)
    ap.add_argument("--part", required=True, choices=["train", "val"])
    ap.add_argument("--videos", required=True, help="通す動画（カンマ区切り）。注釈のうちこの動画だけ")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--k", type=int, required=True)
    ap.add_argument("--check-map", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    videos = sorted(a.videos.split(","))
    C.assert_no_test(videos, "extract_det_signals")
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)

    ann = json.loads((Path(a.ann_dir) / f"instances_{a.part}.json").read_text())
    cats = sorted(ann["categories"], key=lambda c: c["id"])
    assert [c["id"] for c in cats] == list(range(NUM_TOOLS))
    images = [im for im in ann["images"] if C.video_of(Path(im["file_name"]).stem) in videos]
    passed = C.assert_no_test([Path(im["file_name"]).stem for im in images], "extract_det_signals")
    assert passed == videos, (passed, videos)
    by_img = {}
    for x in ann["annotations"]:
        by_img.setdefault(x["image_id"], []).append(x)
    if a.limit:
        images = images[:a.limit]

    model = Config(MODEL_CFG).model.eval()
    ck = load_checkpoint(a.ckpt)
    if isinstance(ck, dict) and "model" in ck:
        ck = ck["model"]
    load_state_dict(model, ck)
    model.to("cuda")
    for p in model.parameters():
        p.requires_grad_(False)
    head = model.transformer.decoder.class_head[-1]
    assert head.in_features == EMBED and head.out_features == NUM_TOOLS
    cap = Capture()
    head.register_forward_hook(cap)
    import models.bricks.ms_deform_attn as msda
    ext_loaded = msda._C is not None
    if not ext_loaded:
        raise RuntimeError("MultiScaleDeformableAttention の拡張が読み込まれていない（conventions#env_p0）")
    print(f"[det-signal] ckpt={a.ckpt} sha={C.sha256(a.ckpt)} part={a.part} videos={videos} "
          f"images={len(images)} ms_deform_attn_ext={ext_loaded}", flush=True)

    ids, d0, dgt, rt, inst, inst_uq, gti, gtn, coco_results = [], [], [], [], [], [], [], [], []
    dup_queries, top_mismatch = 0, 0
    started = time.monotonic()
    for i, im in enumerate(images):
        img = read_image(str(PROJ / "data/raw/ego" / im["file_name"]), ImageReadMode.RGB).to("cuda")
        h, w = int(img.shape[1]), int(img.shape[2])
        assert (w, h) == (im["width"], im["height"])
        cap.tokens = cap.logits = None
        pred = model([img])[0]
        assert cap.tokens is not None
        scores = pred["scores"].float().cpu().numpy()
        labels = pred["labels"].cpu().numpy().astype(int)
        boxes = pred["boxes"].float().cpu().numpy()                    # xyxy, 元の画素
        prob = torch.sigmoid(cap.logits)                                # (Q, 15)
        tv, ti = torch.topk(prob.reshape(-1), len(scores))
        q_of = (ti // NUM_TOOLS).cpu().numpy()
        if not (np.allclose(tv.cpu().numpy(), scores, atol=1e-6) and np.array_equal(ti.cpu().numpy() % NUM_TOOLS, labels)):
            top_mismatch += 1
        # D0
        s = np.zeros(NUM_TOOLS, np.float32)
        for c in range(NUM_TOOLS):
            m = labels == c
            if m.any():
                s[c] = scores[m].max()
        # D0-RT（region_vector と同じ。score[q*, c] × 埋め込み[q*]）
        qstar = prob.argmax(0)
        r = (prob[qstar, torch.arange(NUM_TOOLS)][:, None] * cap.tokens[qstar]).reshape(-1).cpu().numpy()
        # D0-INST（上位 K。後処理の順位のまま）
        k = a.k
        qk = q_of[:k]
        dup_queries += k - len(set(qk.tolist()))
        tok = np.concatenate([prob[qk].cpu().numpy(), cxcywh_norm(boxes[:k], w, h),
                              cap.tokens[qk].cpu().numpy()], 1).astype(np.float32)
        # 読み (b): 後処理の順位をたどり、重複しない query の上位 K 個（同じ作り方の別版。D0-INST-UQ）
        seen, rows = set(), []
        for j, q in enumerate(q_of):
            if q not in seen:
                seen.add(q)
                rows.append(j)
            if len(rows) == k:
                break
        rows = np.asarray(rows)
        tok_uq = np.concatenate([prob[q_of[rows]].cpu().numpy(), cxcywh_norm(boxes[rows], w, h),
                                 cap.tokens[q_of[rows]].cpu().numpy()], 1).astype(np.float32)
        # 正解
        gts = by_img.get(im["id"], [])
        g = np.zeros(NUM_TOOLS, np.float32)
        gt_tok = np.zeros((k, NUM_TOOLS + 4), np.float32)
        if len(gts) > k:
            raise RuntimeError(f"正解の枠が K を超える: {im['file_name']} {len(gts)} > {k}")
        for j, x in enumerate(gts):
            g[x["category_id"]] = 1.0
            bx, by, bw, bh = x["bbox"]
            gt_tok[j, x["category_id"]] = 1.0
            gt_tok[j, NUM_TOOLS:] = [(bx + bw / 2) / w, (by + bh / 2) / h, bw / w, bh / h]
        ids.append(Path(im["file_name"]).stem)
        d0.append(s)
        rt.append(r)
        inst.append(tok)
        inst_uq.append(tok_uq)
        dgt.append(g)
        gti.append(gt_tok)
        gtn.append(len(gts))
        if a.check_map:
            for b, sc, lb in zip(boxes, scores, labels):
                coco_results.append({"image_id": im["id"], "category_id": int(lb),
                                     "bbox": [float(b[0]), float(b[1]), float(b[2] - b[0]), float(b[3] - b[1])],
                                     "score": float(sc)})
        if (i + 1) % 500 == 0:
            print(f"[det-signal] {i + 1}/{len(images)} {time.monotonic() - started:.0f}s", flush=True)

    rec = {"task_id": C.TASK_ID, "ckpt": a.ckpt, "ckpt_sha256": C.sha256(a.ckpt), "ann_dir": a.ann_dir,
           "part": a.part, "videos": videos, "frames": len(ids), "k": a.k, "precision": "fp32",
           "class_order": [c["name"] for c in cats], "dup_query_tokens": int(dup_queries),
           "postprocess_topk_mismatch_frames": int(top_mismatch),
           "gt_boxes_total": int(sum(gtn)), "gt_present_total": int(np.sum(dgt)),
           "elapsed_seconds": time.monotonic() - started, "files": {}}
    for name, arr, extra in (("D0", d0, {}), ("D-GT", dgt, {}), ("D0-RT", rt, {}), ("D0-INST", inst, {}),
                             ("D0-INST-UQ", inst_uq, {}),
                             ("D-GT-INST", gti, {"count": np.asarray(gtn, np.int64)})):
        path = out / f"{name}_{a.part}.npz"
        rec["files"][name] = {"path": str(path), "shape": list(np.asarray(arr).shape),
                              "sha256": C.save_signal(path, ids, np.asarray(arr, np.float32), **extra)}
    if a.check_map:
        import contextlib
        import io

        from pycocotools.coco import COCO
        from pycocotools.cocoeval import COCOeval as CocoEvaluatorAlias
        with contextlib.redirect_stdout(io.StringIO()):
            gt = COCO(str(Path(a.ann_dir) / f"instances_{a.part}.json"))
            dt = gt.loadRes(coco_results)
            ev = CocoEvaluatorAlias(gt, dt, "bbox")
            ev.params.imgIds = [im["id"] for im in images]
            ev.evaluate()
            ev.accumulate()
            ev.summarize()
        rec["check_map_AP"] = float(ev.stats[0])
        (out / f"pred_{a.part}_top300.json").write_text(json.dumps(coco_results))
    C.write_json(out / f"record_{a.part}.json", rec)
    print(json.dumps({k: v for k, v in rec.items() if k != "files"}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
