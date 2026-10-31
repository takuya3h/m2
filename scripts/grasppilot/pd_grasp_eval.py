"""案 B の検出器の val 評価（非公式 T-2026-10-31-grasp-pilot-probe、Task D-4・D-5）。

.venv-relation-detr で動かす。train_t1b.py と同じ評価の経路（eval_detection）に、pd_grasp の val の読み込みを使う。

    --mode zero|gt          評価時の地図（pred・gt_pred と --pred-view・--cfg は契約 T-2026-11-01-grasp-pilot-g で足した）
    --iface-state <pth>     学習した界面（無ければ零初期化のまま）
    --perturb               界面の重みを N(0, scale²) にする（陽性対照）
    --ref-preds <json.gz>   基準の予測（塔単独）との出力の差の最大値を記録
    --trainable-check       学習する集合（--trainable film の選び方）が界面のパラメータの全部でそれ以外を含まないか。
                            陽性対照として界面の外のパラメータを一つ混ぜた集合で不一致になるか
"""
from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402

from grasppilot import grasp_signals as G  # noqa: E402
from grasppilot.pd_grasp import build_grasp_loader  # noqa: E402
from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402
from stage2pilot.pd_eval import digest_non_iface  # noqa: E402

CFG = PROJ / "configs/stage2pilot/pd_graspmap_d5.py"


def trainable_check(model):
    t1b.set_trainable(model, "film")
    trainable = sorted(n for n, p in model.named_parameters() if p.requires_grad)
    iface = sorted(f"phase_iface.{n}" for n, _ in model.phase_iface.named_parameters())
    outside = next(n for n, _ in model.named_parameters() if not n.startswith("phase_iface"))
    return {"trainable_names": trainable, "iface_names": iface, "equal": trainable == iface,
            "equal_with_one_outside_param_mixed": sorted(set(trainable) | {outside}) == iface, "mixed_name": outside,
            "n_trainable": int(sum(p.numel() for p in model.parameters() if p.requires_grad))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", required=True, choices=("zero", "gt", "pred", "gt_pred"))
    ap.add_argument("--pred-view", default=None, help="pred・gt_pred の val の見取り（json）")
    ap.add_argument("--cfg", default=str(CFG), help="検出器の設定（既定は 5 チャネルの正解の型）")
    ap.add_argument("--iface-state", default=None)
    ap.add_argument("--perturb", action="store_true")
    ap.add_argument("--perturb-scale", type=float, default=0.05)
    ap.add_argument("--ref-preds", default=None)
    ap.add_argument("--save-preds", default=None)
    ap.add_argument("--trainable-check", action="store_true")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = torch.device("cuda")
    torch.manual_seed(0)
    index = G.HTSIndex(("train", "val"))
    det_val = build_grasp_loader(t1b.EGO_ROOT, t1b.ANN_DIR, False, a.mode, index, pred_view=a.pred_view)
    stems = [Path(im["file_name"]).stem for im in det_val.dataset.coco.imgs.values()]
    videos = C.assert_no_test(stems, "pd_grasp_eval")
    model = t1b.build_model(device, 42, str(a.cfg), ckpt_override=str(C.DET_CKPT))
    t1b.register_classes(model, det_val)
    from util.utils import load_checkpoint
    ck = load_checkpoint(str(C.DET_CKPT))
    ck = ck["model"] if isinstance(ck, dict) and "model" in ck else ck
    keys = set(model.state_dict())
    load_report = {"missing_from_ckpt": sorted(keys - set(ck)), "unexpected_in_ckpt": sorted(set(ck) - keys)}
    res = {"task_id": "T-2026-10-31-grasp-pilot-probe", "unofficial": True, "cfg": str(CFG),
           "cfg": str(a.cfg), "cfg_sha256": C.sha256(Path(a.cfg)), "pred_view": a.pred_view, "det_ckpt_sha256": C.sha256(C.DET_CKPT), "mode": a.mode,
           "iface_state": a.iface_state, "perturb": a.perturb, "perturb_scale": a.perturb_scale, "videos": videos,
           "load_report": load_report}
    if a.trainable_check:
        res["trainable"] = trainable_check(model)
    if a.iface_state:
        st = torch.load(a.iface_state, map_location="cpu")["model"]
        _, unexpected = model.load_state_dict(st, strict=False)
        assert not unexpected, unexpected
        res["iface_state_keys"] = sorted(st)
        res["iface_state_sha256"] = C.sha256(a.iface_state)
    if a.perturb:
        g = torch.Generator().manual_seed(1234)
        with torch.no_grad():
            model.phase_iface.weight.copy_((torch.randn(model.phase_iface.weight.shape, generator=g)
                                            * a.perturb_scale).to(device))
    res["non_interface_digest"] = digest_non_iface(model)
    res["iface_weight"] = model.gate_values()
    m_ap, _, preds = t1b.eval_detection(model, det_val, {}, device, True, collect_predictions=True, dim=1)
    res["eval_detection_mAP"] = m_ap
    res["metrics"] = M.summary(Path(t1b.ANN_DIR) / "instances_val.json", preds["results"])
    if a.ref_preds:
        res["diff_vs_ref"] = M.max_output_diff(preds["results"], M.load_results(a.ref_preds))
    if a.save_preds:
        Path(a.save_preds).parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(a.save_preds, "wt") as f:
            json.dump(preds["results"], f)
        res["saved_preds"] = a.save_preds
    C.write_json(a.out, res)
    print(json.dumps({"mode": a.mode, "perturb": a.perturb, "AP": res["metrics"]["AP"],
                      "target": res["metrics"]["target_AP"], "diff": res.get("diff_vs_ref"),
                      "trainable_equal": res.get("trainable", {}).get("equal"),
                      "missing": load_report["missing_from_ckpt"]}, ensure_ascii=False))


if __name__ == "__main__":
    main()
