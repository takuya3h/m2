"""Task C-2〜C-4: W2・W3 の学ぶ集合と、学習前の出力の恒等性（非公式 T-2026-11-01-stage2-w23-andrew）。

.venv-relation-detr で動かす。起動は scripts/w23/run_pd_w23_andrew.sh の identity・perturb・setcheck から（型・W・腕の対応を
台本と共有するため）。学習の経路と同じ関数（train_t1b の build_model・register_classes・set_trainable・eval_detection）を使う。

    学ぶ集合: train_t1b.set_trainable(model, <台本が渡す --trainable>) の後の requires_grad の名前の集合を、
              SPEC §3.1 の定義から別に組んだ集合と比べる（陽性対照: 定義の外のパラメータを一つ混ぜると不一致）
                W1 = phase_iface.*
                W2 = phase_iface.* ＋ decoder の最終層・その層のクラスと box の頭
                W3 = phase_iface.* ＋ 設定の凍結（backbone の stem の conv1 と layer1。freeze_indices=(0,)）以外の全体
    恒等性:   界面は零から（P1 は FiLM の最後の層、DX は層ごとの α、案 B は 1×1 の畳み込み）。val を評価し、
              塔単独の予測（Task B-2 で保存）との出力の差の最大値を記録する
    陽性対照: --perturb で、零から始まる界面の重みを N(0, 0.05²) にする（P1 は pd_eval と、DX は pd_four_eval の gate と、
              案 B は pd_grasp_eval と同じ当て方）

    python scripts/w23/w23a_identity.py --type P1|DX|B --w W1|W2|W3 --trainable film|w2|all --cfg <設定>
        [--signal-val npz | --zero-ctx | --grasp-map zero|gt|pred|gt_pred --grasp-pred-val json]
        [--perturb] [--no-eval] [--ref-preds json.gz] --out <json>
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402  (import 時に cwd を third_party/Relation-DETR へ移す)

from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402
from stage2pilot.pd_eval import digest_non_iface  # noqa: E402

TASK_ID = "T-2026-11-01-stage2-w23-andrew"
W_TO_TRAINABLE = {"W1": "film", "W2": "w2", "W3": "all"}
FROZEN_PREFIXES = ("backbone.conv1.", "backbone.layer1.")   # 設定 freeze_indices=(0,) の凍結（stem と layer1）


def expected_names(model, w: str) -> set[str]:
    """SPEC §3.1 の定義から組んだ学ぶ集合（set_trainable とは別に、名前の接頭だけで組む）。"""
    names = [n for n, _ in model.named_parameters()]
    iface = {n for n in names if n.startswith("phase_iface.")}
    if w == "W1":
        return iface
    if w == "W2":
        last = len(model.transformer.decoder.layers) - 1
        pre = (f"transformer.decoder.layers.{last}.", f"transformer.decoder.class_head.{last}.",
               f"transformer.decoder.bbox_head.{last}.")
        return iface | {n for n in names if n.startswith(pre)}
    if w == "W3":
        return {n for n in names if not n.startswith(FROZEN_PREFIXES)}
    raise ValueError(w)


def set_check(model, w: str, trainable_arg: str) -> dict:
    t1b.set_trainable(model, trainable_arg)
    got = {n for n, p in model.named_parameters() if p.requires_grad}
    exp = expected_names(model, w)
    outside = sorted(n for n, _ in model.named_parameters() if n not in exp)
    mixed = outside[0] if outside else None
    numel = {n: p.numel() for n, p in model.named_parameters()}
    return {"w": w, "trainable_arg": trainable_arg, "n_names": len(got), "n_elements": int(sum(numel[n] for n in got)),
            "n_iface_elements": int(sum(numel[n] for n in got if n.startswith("phase_iface."))),
            "equal": got == exp, "only_in_trainable": sorted(got - exp), "only_in_expected": sorted(exp - got),
            "mixed_name": mixed, "equal_with_one_outside_mixed": (got | ({mixed} if mixed else set())) == exp if mixed else None,
            "names": sorted(got)}


def perturb(model, typ: str, scale: float = 0.05, seed: int = 1234) -> list[str]:
    g = torch.Generator().manual_seed(seed)
    iface = model.phase_iface
    if typ == "P1":
        params = [("phase_iface.mlp.-1.weight", iface.mlp[-1].weight), ("phase_iface.mlp.-1.bias", iface.mlp[-1].bias)]
    elif typ == "DX":
        params = [("phase_iface.alpha", iface.alpha)]
    else:
        params = [("phase_iface.weight", iface.weight)]
    with torch.no_grad():
        for _, p in params:
            p.copy_((torch.randn(p.shape, generator=g) * scale).to(p.device))
    return [n for n, _ in params]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=("P1", "DX", "B"))
    ap.add_argument("--w", required=True, choices=("W1", "W2", "W3"))
    ap.add_argument("--trainable", required=True, choices=("film", "w2", "all"))
    ap.add_argument("--arm", required=True)
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--det-ckpt", default=str(C.DET_CKPT))
    ap.add_argument("--signal-val", default=None)
    ap.add_argument("--zero-ctx", action="store_true")
    ap.add_argument("--grasp-map", default=None, choices=("zero", "gt", "pred", "gt_pred"))
    ap.add_argument("--grasp-pred-val", default=None)
    ap.add_argument("--perturb", action="store_true")
    ap.add_argument("--no-eval", action="store_true")
    ap.add_argument("--ref-preds", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    device = torch.device("cuda" if not a.no_eval else "cpu")
    torch.manual_seed(0)
    if a.grasp_map:
        from grasppilot import grasp_signals as G
        from grasppilot.pd_grasp import build_grasp_loader
        det_val = build_grasp_loader(t1b.EGO_ROOT, t1b.ANN_DIR, False, a.grasp_map, G.HTSIndex(("train", "val")),
                                     pred_view=a.grasp_pred_val)
    else:
        det_val = t1b.build_det_loader(train=False)
    stems = [Path(im["file_name"]).stem for im in det_val.dataset.coco.imgs.values()]
    videos = C.assert_no_test(stems, "w23a_identity")
    model = t1b.build_model(device, 42, a.cfg, ckpt_override=a.det_ckpt)
    t1b.register_classes(model, det_val)
    res = {"task_id": TASK_ID, "unofficial": True, "type": a.type, "w": a.w, "arm": a.arm, "cfg": a.cfg,
           "cfg_sha256": C.sha256(Path(a.cfg)), "det_ckpt_sha256": C.sha256(Path(a.det_ckpt)),
           "signal_val": a.signal_val, "zero_ctx": a.zero_ctx, "grasp_map": a.grasp_map, "grasp_pred_val": a.grasp_pred_val,
           "videos": videos, "n_images": len(stems)}
    res["trainable_set"] = set_check(model, a.w, a.trainable)
    if a.perturb:
        res["perturbed"] = perturb(model, a.type)
    res["non_interface_digest"] = digest_non_iface(model)
    if not a.no_eval:
        if a.grasp_map:
            imgid_to_ctx, dim, zero = {}, 1, True
        else:
            sig = t1b.load_signal_npz(a.signal_val)
            dim = next(iter(sig.values())).shape[0]
            imgid_to_ctx, miss = t1b.build_imgid_to_ctx(det_val.dataset.coco, sig, dim)
            if miss:
                raise SystemExit(f"信号の無いフレーム {miss}")
            zero = a.zero_ctx
        model.eval()
        m_ap, _, preds = t1b.eval_detection(model, det_val, imgid_to_ctx, device, zero, collect_predictions=True, dim=dim)
        res["eval_detection_mAP"] = m_ap
        res["metrics"] = M.summary(Path(t1b.ANN_DIR) / "instances_val.json", preds["results"])
        if a.ref_preds:
            res["diff_vs_ref"] = M.max_output_diff(preds["results"], M.load_results(a.ref_preds))
    C.write_json(a.out, res)
    ts = res["trainable_set"]
    print(json.dumps({"type": a.type, "w": a.w, "arm": a.arm, "perturb": a.perturb, "set_equal": ts["equal"],
                      "mixed_equal": ts["equal_with_one_outside_mixed"], "n_elements": ts["n_elements"],
                      "AP": res.get("metrics", {}).get("AP"), "diff": res.get("diff_vs_ref")}, ensure_ascii=False))


if __name__ == "__main__":
    main()
