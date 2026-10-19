#!/usr/bin/env python
"""PD の新しい型（dec_xattn、extra_q）の val 評価（非公式 T-2026-10-19-stage2-pilot-four-new-types、Task C-2・C-5・C-6、Task F）。

.venv-relation-detr で動かす。評価の経路は train_t1b.py と pd_eval.py と同じ（build_det_loader、CocoEvaluator、上位 300）。
一回の順伝播から、最終の検出（extra_q は元と追加の和集合）と、extra_q では元の出力だけの検出を両方取る。

    --cfg configs/stage2pilot/pd_{dec_xattn,extra_q}_d{9,18}.py
    --iface-state <best_t1b.pth>     学習した界面を読む（無ければ初期値のまま。学習前の恒等性）
    --signal-val npz / --zero-ctx    評価時の信号
    --perturb gate      dec_xattn の α を零でない値にする（陽性対照）
    --perturb score0    extra_q のスコアの定数を 0 にする（陽性対照）
    --perturb random    extra_q の界面の重みをすべて乱数にする（元の出力が変わらないことの検査）
    --perturb unmask    extra_q の自己注意の mask を外す（元の query も追加の query を参照する。陽性対照）
    --ref-preds         基準の予測（塔単独の出力）との差の最大値を、最終の検出と元の出力だけの両方で記録する

    EGO_BODY=<BODY> EGO_ANN_DIR=<折り A> CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/pd_four_eval.py --cfg ... --out <json>
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import numpy as np
import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402  (import 時に cwd を third_party/Relation-DETR へ移す)

from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402

TASK_ID = "T-2026-10-19-stage2-pilot-four-new-types"
TOPK = 300


def trainable_report(model):
    """--trainable film（名前に phase を含むパラメータだけ）で学習する名前の集合が、界面のパラメータの全部か（Task C-2）。"""
    t1b.set_trainable(model, "film")
    trainable = sorted(n for n, p in model.named_parameters() if p.requires_grad)
    iface = sorted(n for n, _ in model.named_parameters() if n.startswith("phase_iface."))
    other = next(n for n, _ in model.named_parameters() if not n.startswith("phase_iface."))
    for p in model.parameters():
        p.requires_grad_(False)
    return {"trainable_names": trainable, "iface_names": iface, "equal": trainable == iface,
            "n_trainable": int(sum(p.numel() for n, p in model.named_parameters() if n in set(trainable))),
            "equal_with_one_detector_param_mixed": sorted(set(trainable) | {other}) == iface}


def coco_results(outputs, targets):
    return {t["image_id"]: {k: v.to("cpu") for k, v in o.items()} for t, o in zip(targets, outputs)}


@torch.no_grad()
def evaluate(model, loader, imgid_to_ctx, device, zero_ctx, dim):
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset
    model.eval()
    coco = get_coco_api_from_dataset(loader.dataset)
    xq = model.interface == "extra_q"
    evs = {"final": CocoEvaluator(coco, ["bbox"])}
    if xq:
        evs["orig"] = CocoEvaluator(coco, ["bbox"])
    per_image = []
    for images, targets in loader:
        images = [img.to(device) for img in images]
        model.set_phase_context(t1b.ctx_for_targets(targets, imgid_to_ctx, device, zero_ctx, dim))
        outputs = model(images)
        evs["final"].update(coco_results(outputs, targets))
        if not xq:
            continue
        last = model.xq_last
        sizes = model.query_original_sizes(images)
        orig = model.postprocessor({"pred_logits": last["orig_logits"], "pred_boxes": last["orig_boxes"]}, sizes)
        evs["orig"].update(coco_results(orig, targets))
        n_orig, n_cls = last["orig_logits"].shape[1], last["orig_logits"].shape[2]
        for b, t in enumerate(targets):
            po = last["orig_logits"][b].sigmoid().flatten()
            pe = last["extra_logits"][b].sigmoid().flatten()
            union = torch.cat([po, pe])
            idx = union.topk(TOPK).indices
            from_extra = (idx // n_cls >= n_orig).cpu().tolist()
            per_image.append({"image_id": int(t["image_id"]), "orig_300th_score": float(po.topk(TOPK).values[-1]),
                              "extra_max_score": float(pe.max()), "n_extra_in_top300": int(sum(from_extra)),
                              "from_extra": from_extra if model.xq_output == "union" else None})
    out = {}
    for k, ev in evs.items():
        ev.synchronize_between_processes()
        ev.accumulate()
        import contextlib
        import io
        with contextlib.redirect_stdout(io.StringIO()):
            ev.summarize()
        out[k] = {"mAP": float(ev.coco_eval["bbox"].stats[0]), "results": ev.predictions["bbox"]}
    return out, per_image


def perturb(model, how, scale, seed=1234):
    g = torch.Generator().manual_seed(seed)
    iface = model.phase_iface
    with torch.no_grad():
        if how == "gate":
            iface.alpha.copy_(torch.randn(iface.alpha.shape, generator=g) * scale)
        elif how == "score0":
            iface.score.zero_()
        elif how == "random":
            for p in iface.parameters():
                p.copy_(torch.randn(p.shape, generator=g))
        elif how == "unmask":
            model.xq_unmasked = True
        else:
            raise ValueError(how)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--det-ckpt", default=str(C.DET_CKPT))
    ap.add_argument("--iface-state", default=None)
    ap.add_argument("--perturb", choices=["gate", "score0", "random", "unmask"], default=None)
    ap.add_argument("--perturb-scale", type=float, default=0.05)
    ap.add_argument("--signal-val", default=None)
    ap.add_argument("--zero-ctx", action="store_true")
    ap.add_argument("--dim", type=int, default=9)
    ap.add_argument("--ref-preds", default=None)
    ap.add_argument("--save-preds", default=None, help="最終の検出の予測（gz）。extra_q では各検出が追加の出力か（from_extra）も並べて書く")
    ap.add_argument("--limit-images", type=int, default=None, help="試しに先頭の何枚だけを評価する（記録には使わない）")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = torch.device("cuda")
    torch.manual_seed(0)
    det_val = t1b.build_det_loader(train=False)
    if a.limit_images:
        det_val.dataset.ids = det_val.dataset.ids[:a.limit_images]
    stems = [Path(det_val.dataset.coco.imgs[i]["file_name"]).stem for i in det_val.dataset.ids]
    videos = C.assert_no_test(stems, "pd_four_eval")
    cfg = str(Path(a.cfg) if Path(a.cfg).is_absolute() else PROJ / a.cfg)
    model = t1b.build_model(device, 42, cfg, ckpt_override=a.det_ckpt)
    t1b.register_classes(model, det_val)
    from util.utils import load_checkpoint
    ck = load_checkpoint(a.det_ckpt)
    ck = ck["model"] if isinstance(ck, dict) and "model" in ck else ck
    keys = set(model.state_dict())
    load_report = {"missing_from_ckpt": sorted(keys - set(ck)), "unexpected_in_ckpt": sorted(set(ck) - keys)}
    load_report["missing_are_interface_only"] = all(k.startswith("phase") for k in load_report["missing_from_ckpt"])
    trainable = trainable_report(model)
    gates_init = model.gate_values()
    if a.iface_state:
        st = torch.load(a.iface_state, map_location="cpu")["model"]
        missing, unexpected = model.load_state_dict(st, strict=False)
        assert not unexpected, unexpected
        assert all(not k.startswith("phase") for k in missing), missing
        load_report["iface_state_keys"] = sorted(st)
    if a.perturb:
        perturb(model, a.perturb, a.perturb_scale)
    if a.signal_val:
        sig = t1b.load_signal_npz(a.signal_val)
        dim = next(iter(sig.values())).shape[0]
    else:
        sig, dim = {}, a.dim
    imgid_to_ctx, miss = t1b.build_imgid_to_ctx(det_val.dataset.coco, sig, dim)
    if a.signal_val and miss:
        raise SystemExit(f"信号の無いフレーム {miss}")
    zero = a.zero_ctx or not a.signal_val
    res_by, per_image = evaluate(model, det_val, imgid_to_ctx, device, zero, dim)
    ann = Path(t1b.ANN_DIR) / "instances_val.json"
    img_ids = sorted(int(i) for i in det_val.dataset.ids)
    res = {"task_id": TASK_ID, "cfg": a.cfg, "interface": model.interface, "det_ckpt": a.det_ckpt,
           "det_ckpt_sha256": C.sha256(a.det_ckpt), "iface_state": a.iface_state, "perturb": a.perturb,
           "perturb_scale": a.perturb_scale if a.perturb == "gate" else None, "signal_val": a.signal_val,
           "signal_val_sha256": C.sha256(a.signal_val) if a.signal_val else None, "zero_ctx": bool(zero), "dim": dim,
           "videos": videos, "n_images": len(img_ids), "limit_images": a.limit_images, "load_report": load_report,
           "trainable": trainable, "gates_init": gates_init, "gates_eval": model.gate_values(),
           "interface_params": int(sum(p.numel() for n, p in model.named_parameters() if n.startswith("phase"))),
           "non_interface_digest": t1b.frozen_digest(model)}
    for k, r in res_by.items():
        res[k] = {"eval_detection_mAP": r["mAP"], "metrics": M.summary(ann, r["results"], img_ids)}
        if a.ref_preds:
            ref = [x for x in M.load_results(a.ref_preds) if x["image_id"] in set(img_ids)]
            res[k]["diff_vs_ref"] = M.max_output_diff(r["results"], ref)
    if per_image:
        margins = np.array([p["orig_300th_score"] - p["extra_max_score"] for p in per_image])
        res["extra_q"] = {"n_images": len(per_image),
                          "images_extra_max_ge_orig_300th": int((margins <= 0).sum()),
                          "min_margin": float(margins.min()), "median_margin": float(np.median(margins)),
                          "max_extra_score": float(max(p["extra_max_score"] for p in per_image)),
                          "min_orig_300th_score": float(min(p["orig_300th_score"] for p in per_image)),
                          "n_extra_in_top300_total": int(sum(p["n_extra_in_top300"] for p in per_image)),
                          "images_with_extra_in_top300": int(sum(p["n_extra_in_top300"] > 0 for p in per_image))}
    if a.save_preds:
        with gzip.open(a.save_preds, "wt") as f:
            json.dump(res_by["final"]["results"], f)
        res["saved_preds"] = a.save_preds
        if per_image and model.xq_output == "union":
            side = Path(str(a.save_preds).replace(".json.gz", "_from_extra.json.gz"))
            with gzip.open(side, "wt") as f:
                json.dump({str(p["image_id"]): p["from_extra"] for p in per_image}, f)
            res["saved_from_extra"] = str(side)
    C.write_json(a.out, res)
    brief = {k: res[k]["eval_detection_mAP"] for k in res_by} | {
        "diff": {k: res[k].get("diff_vs_ref") for k in res_by}, "extra_q": res.get("extra_q"),
        "trainable_equal": trainable["equal"], "n_trainable": trainable["n_trainable"]}
    print(json.dumps(brief, ensure_ascii=False))


if __name__ == "__main__":
    main()
