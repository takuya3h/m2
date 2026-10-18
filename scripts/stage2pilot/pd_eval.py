#!/usr/bin/env python
"""PD の界面つき検出塔の val 評価（非公式 T-2026-10-18-stage2-pilot-folda、Task D-4/D-5/F）。

.venv-relation-detr で動かす。train_t1b.py と同じ評価の経路（build_det_loader / eval_detection）を使う。

    --cfg plain                     塔単独（relation_detr_resnet50_egosurgery.py）。恒等性の基準の予測を作る
    --cfg configs/stage2pilot/...   界面つき。--iface-state で学習した界面を読む（無ければ零初期化のまま）
    --perturb                       界面の最後の層（P2F は表）を零でない値にする（陽性対照）
    --signal-val npz / --zero-ctx   評価時の信号
    --ref-preds                     基準の予測（plain の出力）との出力の差の最大値を記録

    EGO_ANN_DIR=<折り A> CUDA_VISIBLE_DEVICES=0 python scripts/stage2pilot/pd_eval.py --cfg ... --out <json>
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
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

PLAIN_CFG = str(t1b.RELDETR / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")


def iface_last_params(model):
    """界面の最後の層（零初期化した層）。P2F は表の buffer。"""
    if model.interface == "film":
        return [model.phase_iface.mlp[-1].weight, model.phase_iface.mlp[-1].bias]
    if model.interface in ("clsbias_lin", "query"):
        return [model.phase_iface.weight, model.phase_iface.bias]
    return [model.phase_iface_table]


def digest_non_iface(model) -> str:
    h = hashlib.sha256()
    for k, v in sorted(model.state_dict().items()):
        if not k.startswith("phase"):
            h.update(k.encode())
            h.update(v.detach().cpu().contiguous().float().numpy().tobytes())
    return h.hexdigest()


@torch.no_grad()
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--det-ckpt", default=str(C.DET_CKPT))
    ap.add_argument("--iface-state", default=None)
    ap.add_argument("--fixed-table", default=None)
    ap.add_argument("--perturb", action="store_true")
    ap.add_argument("--perturb-scale", type=float, default=0.05)
    ap.add_argument("--signal-val", default=None)
    ap.add_argument("--zero-ctx", action="store_true")
    ap.add_argument("--dim", type=int, default=9)
    ap.add_argument("--ref-preds", default=None)
    ap.add_argument("--save-preds", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = torch.device("cuda")
    torch.manual_seed(0)
    det_val = t1b.build_det_loader(train=False)
    stems = [Path(im["file_name"]).stem for im in det_val.dataset.coco.imgs.values()]
    videos = C.assert_no_test(stems, "pd_eval")
    # train_t1b の import で cwd が third_party/Relation-DETR に移っているので、相対経路は repo から解決する
    cfg = PLAIN_CFG if a.cfg == "plain" else str(Path(a.cfg) if Path(a.cfg).is_absolute() else PROJ / a.cfg)
    model = t1b.build_model(device, 42, cfg, ckpt_override=a.det_ckpt)
    t1b.register_classes(model, det_val)
    from util.utils import load_checkpoint
    ck = load_checkpoint(a.det_ckpt)
    ck = ck["model"] if isinstance(ck, dict) and "model" in ck else ck
    keys = set(model.state_dict())
    load_report = {"missing_from_ckpt": sorted(keys - set(ck)), "unexpected_in_ckpt": sorted(set(ck) - keys)}
    load_report["missing_are_interface_only"] = all(k.startswith("phase") for k in load_report["missing_from_ckpt"])
    if a.cfg == "plain":
        model.set_phase_context = lambda ctx: None
    else:
        if a.fixed_table:
            model.set_fixed_table(np.asarray(json.loads(Path(a.fixed_table).read_text())["B"], np.float32))
        if a.iface_state:
            st = torch.load(a.iface_state, map_location="cpu")["model"]
            missing, unexpected = model.load_state_dict(st, strict=False)
            assert not unexpected, unexpected
            load_report["iface_state_keys"] = sorted(st)
        if a.perturb:
            g = torch.Generator().manual_seed(1234)
            for p in iface_last_params(model):
                p.copy_(torch.randn(p.shape, generator=g) * a.perturb_scale)
    if a.signal_val:
        sig = t1b.load_signal_npz(a.signal_val)
        dim = next(iter(sig.values())).shape[0]
    else:
        sig, dim = {}, a.dim
    imgid_to_ctx, miss = t1b.build_imgid_to_ctx(det_val.dataset.coco, sig, dim)
    if a.signal_val and miss:
        raise SystemExit(f"信号の無いフレーム {miss}")
    m_ap, per_class, preds = t1b.eval_detection(model, det_val, imgid_to_ctx, device, a.zero_ctx or not a.signal_val,
                                                collect_predictions=True, dim=dim)
    res = {"task_id": C.TASK_ID, "cfg": a.cfg, "det_ckpt": a.det_ckpt, "det_ckpt_sha256": C.sha256(a.det_ckpt),
           "iface_state": a.iface_state, "fixed_table": a.fixed_table, "perturb": a.perturb,
           "signal_val": a.signal_val, "zero_ctx": bool(a.zero_ctx or not a.signal_val), "dim": dim,
           "videos": videos, "eval_detection_mAP": m_ap, "load_report": load_report,
           "non_interface_digest": digest_non_iface(model),
           "interface_params": int(sum(p.numel() for n, p in model.named_parameters() if n.startswith("phase"))),
           "metrics": M.summary(Path(t1b.ANN_DIR) / "instances_val.json", preds["results"])}
    if a.ref_preds:
        res["diff_vs_ref"] = M.max_output_diff(preds["results"], M.load_results(a.ref_preds))
    if a.save_preds:
        with gzip.open(a.save_preds, "wt") as f:
            json.dump(preds["results"], f)
        res["saved_preds"] = a.save_preds
    C.write_json(a.out, res)
    print(json.dumps({k: res[k] for k in ("cfg", "eval_detection_mAP", "dim", "zero_ctx", "perturb")}
                     | {"AP": res["metrics"]["AP"], "diff": res.get("diff_vs_ref"),
                        "missing": load_report["missing_from_ckpt"][:6]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
