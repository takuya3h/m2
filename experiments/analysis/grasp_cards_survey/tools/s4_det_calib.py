"""S4 検出塔の出力の形と較正（T-2026-11-08-grasp-cards-survey、SPEC §2 S4-2〜4）。.venv-relation-detr。学習しない。

extract_det_signals.py と同じ読み方（Config(MODEL_CFG).model → load_checkpoint → load_state_dict → eval、fp32、batch 1、
画像は data/raw/ego/<file_name> を ImageReadMode.RGB で読み、モデルの中の前処理に任せる）で、後処理後の出力
（scores・labels・boxes）を取る。評価の経路と同じかは、val の出力の COCO mAP が記録の値と一致するかで確かめる。

較正: 各フレームで得点の高い順に、同じクラスのまだ対応していない正解のうち IoU が最大のものと IoU 0.5 以上で対応させ、
対応したら 1、しなければ 0。得点を [0, 0.1), …, [0.9, 1.0] の 10 区間に分け、ECE = Σ (n_b / N) |正解率_b − 平均得点_b|。
対照: 得点をすべて 1 にした写し（ECE が大きくなるはず）、得点を対応の 0/1 にした写し（ECE が 0 になるはず）。

学習エンジン（util.engine）は使わない。作業ディレクトリと RELDETR_EVIDENCE_DIR は本契約の置き場に向ける。

    python s4_det_calib.py --part val --out-dir <STORE/c/s4>
    python s4_det_calib.py --part train --sample 1000 --seed 42 --out-dir <STORE/c/s4>
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
import time
from pathlib import Path

import numpy as np
import torch
from torchvision.io import ImageReadMode, read_image

PROJ = Path(__file__).resolve().parents[4]
REPO = PROJ / "third_party" / "Relation-DETR"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(PROJ / "scripts"))

from util.lazy_load import Config  # noqa: E402
from util.utils import load_checkpoint, load_state_dict  # noqa: E402

from stage2pilot import common as C  # noqa: E402

MODEL_CFG = str(REPO / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")
BINS = np.linspace(0, 1, 11)


def iou(a, b):
    """a (n,4) xyxy, b (m,4) xyxy → (n,m)。"""
    x0 = np.maximum(a[:, None, 0], b[None, :, 0])
    y0 = np.maximum(a[:, None, 1], b[None, :, 1])
    x1 = np.minimum(a[:, None, 2], b[None, :, 2])
    y1 = np.minimum(a[:, None, 3], b[None, :, 3])
    inter = np.clip(x1 - x0, 0, None) * np.clip(y1 - y0, 0, None)
    area = lambda z: (z[:, 2] - z[:, 0]) * (z[:, 3] - z[:, 1])  # noqa: E731
    return inter / (area(a)[:, None] + area(b)[None, :] - inter + 1e-12)


def match(scores, labels, boxes, gts):
    tp = np.zeros(len(scores), np.float32)
    used = set()
    g_box = np.array([[x["bbox"][0], x["bbox"][1], x["bbox"][0] + x["bbox"][2], x["bbox"][1] + x["bbox"][3]] for x in gts],
                     np.float64).reshape(-1, 4)
    g_cls = np.array([x["category_id"] for x in gts])
    ious = iou(boxes.astype(np.float64), g_box) if len(gts) else np.zeros((len(scores), 0))
    for i in np.argsort(-scores, kind="stable"):
        cand = [j for j in range(len(gts)) if g_cls[j] == labels[i] and j not in used and ious[i, j] >= 0.5]
        if cand:
            j = max(cand, key=lambda j: ious[i, j])
            used.add(j)
            tp[i] = 1.0
    return tp


def ece(conf, hit):
    idx = np.clip(np.digitize(conf, BINS[1:-1], right=False), 0, 9)
    rows, e = [], 0.0
    for b in range(10):
        m = idx == b
        n = int(m.sum())
        if n:
            acc, cf = float(hit[m].mean()), float(conf[m].mean())
            e += n / len(conf) * abs(acc - cf)
            rows.append({"bin": [float(BINS[b]), float(BINS[b + 1])], "n": n, "acc": acc, "conf": cf})
        else:
            rows.append({"bin": [float(BINS[b]), float(BINS[b + 1])], "n": 0})
    return float(e), rows


def q(x):
    x = np.asarray(x, np.float64)
    ps = [0, 1, 5, 25, 50, 75, 95, 99, 100]
    return {f"p{p}": float(np.percentile(x, p)) for p in ps} | {"n": int(len(x)), "mean": float(x.mean())}


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", required=True, choices=["train", "val"])
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    out = Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("RELDETR_EVIDENCE_DIR", str(out / "evidence"))
    os.chdir(out)
    ann = json.loads((C.DET_ANN_A / f"instances_{a.part}.json").read_text())
    images = sorted(ann["images"], key=lambda im: im["id"])
    if a.sample:
        rng = np.random.default_rng(a.seed)
        pick = sorted(rng.choice(len(images), a.sample, replace=False).tolist())
        images = [images[i] for i in pick]
    read_videos = C.assert_no_test([Path(im["file_name"]).stem for im in images], "s4_det_calib")
    by_img = {}
    for x in ann["annotations"]:
        by_img.setdefault(x["image_id"], []).append(x)
    ck_path = str(C.DET_CKPT)
    assert C.sha256(ck_path) == C.DET_SHA256
    model = Config(MODEL_CFG).model.eval()
    ck = load_checkpoint(ck_path)
    if isinstance(ck, dict) and "model" in ck:
        ck = ck["model"]
    load_state_dict(model, ck)
    model.to("cuda")
    for p in model.parameters():
        p.requires_grad_(False)
    import models.bricks.ms_deform_attn as msda
    if msda._C is None:
        raise RuntimeError("MultiScaleDeformableAttention の拡張が読み込まれていない（conventions#env_p0）")
    def digest():
        import hashlib
        h = hashlib.sha256()
        for k, v in sorted(model.state_dict().items()):
            h.update(k.encode())
            h.update(v.detach().cpu().contiguous().numpy().tobytes())
        return h.hexdigest()
    before = digest()
    post = model.postprocessor
    print(f"[s4] part={a.part} frames={len(images)} videos={read_videos} ms_deform_attn_ext={msda._C is not None} "
          f"select={post.select_box_nums_for_evaluation} nms={post.nms_iou_threshold} "
          f"conf={post.confidence_score}", flush=True)
    logits_q = {}
    model.transformer.decoder.class_head[-1].register_forward_hook(
        lambda m, i, o: logits_q.__setitem__("shape", list(o.shape)))
    all_s, all_l, all_tp, top1, coco, fwd = [], [], [], [], [], []
    n_out = set()
    for k, im in enumerate(images):
        img = read_image(str(PROJ / "data/raw/ego" / im["file_name"]), ImageReadMode.RGB).to("cuda")
        torch.cuda.synchronize()
        t0 = time.perf_counter()
        pred = model([img])[0]
        torch.cuda.synchronize()
        fwd.append(time.perf_counter() - t0)
        s = pred["scores"].float().cpu().numpy()
        lb = pred["labels"].cpu().numpy().astype(int)
        bx = pred["boxes"].float().cpu().numpy()
        n_out.add((len(s), tuple(pred["boxes"].shape)))
        tp = match(s, lb, bx, by_img.get(im["id"], []))
        all_s.append(s)
        all_l.append(lb)
        all_tp.append(tp)
        top1.append(float(s.max()))
        if a.part == "val":
            for b, sc, c in zip(bx, s, lb):
                coco.append({"image_id": im["id"], "category_id": int(c),
                             "bbox": [float(b[0]), float(b[1]), float(b[2] - b[0]), float(b[3] - b[1])], "score": float(sc)})
        if (k + 1) % 250 == 0:
            print(f"[s4] {k + 1}/{len(images)}", flush=True)
    after = digest()
    S, L, T = np.concatenate(all_s), np.concatenate(all_l), np.concatenate(all_tp)
    e, rows = ece(S, T)
    hi = S >= 0.05
    e05, rows05 = ece(S[hi], T[hi])
    e_one, _ = ece(np.ones_like(S), T)
    e_hit, _ = ece(T.astype(np.float64), T)
    rec = {"task_id": "T-2026-11-08-grasp-cards-survey", "part": a.part, "frames": len(images),
           "sample": a.sample, "seed": a.seed, "read_videos": read_videos,
           "ckpt": str(C.DET_CKPT.relative_to(PROJ)), "ckpt_sha256": C.DET_SHA256,
           "weights_digest_before": before, "weights_digest_after": after, "weights_unchanged": before == after,
           "ms_deform_attn_ext": msda._C is not None, "num_queries_from_class_head": (logits_q.get("shape") or [None, None])[1],
           "class_head_logits_shape": logits_q.get("shape"),
           "postprocess": {"select_box_nums_for_evaluation": post.select_box_nums_for_evaluation,
                           "nms_iou_threshold": post.nms_iou_threshold, "confidence_score": post.confidence_score},
           "outputs_per_frame": sorted([[n, list(sh)] for n, sh in n_out]),
           "score_quantiles_all": q(S), "score_quantiles_top1_per_frame": q(top1),
           "n_outputs": int(len(S)), "n_tp_iou50": int(T.sum()), "gt_boxes": int(sum(len(by_img.get(im["id"], [])) for im in images)),
           "ece_all_10bins": e, "reliability_all": rows,
           "ece_score_ge_0.05_10bins": e05, "reliability_score_ge_0.05": rows05, "n_score_ge_0.05": int(hi.sum()),
           "control_ece_scores_all_1": e_one, "control_ece_scores_eq_hit": e_hit,
           "forward_seconds_per_frame_batch1": q(fwd[1:]),
           "evidence_dir": os.environ["RELDETR_EVIDENCE_DIR"], "cwd": os.getcwd()}
    if coco:
        from pycocotools.coco import COCO
        from pycocotools.cocoeval import COCOeval as CocoEvaluatorAlias
        with contextlib.redirect_stdout(io.StringIO()):
            gt = COCO(str(C.DET_ANN_A / "instances_val.json"))
            dt = gt.loadRes(coco)
            ev = CocoEvaluatorAlias(gt, dt, "bbox")
            ev.params.imgIds = [im["id"] for im in images]
            ev.evaluate()
            ev.accumulate()
            ev.summarize()
        rec["check_map_AP"] = float(ev.stats[0])
        rec["record_AP"] = C.DET_RECORD["AP"]
    np.savez(out / f"s4_outputs_{a.part}.npz", scores=S, labels=L, tp=T,
             frame_of=np.repeat(np.arange(len(images)), [len(x) for x in all_s]),
             frame_names=np.asarray([Path(im["file_name"]).stem for im in images]))
    (out / f"s4_record_{a.part}.json").write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({k: v for k, v in rec.items() if not k.startswith("reliability")}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
