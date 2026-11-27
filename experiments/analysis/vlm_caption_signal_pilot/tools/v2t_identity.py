"""Task D: V→T（P1・P2L）の学習集合・学習前恒等性・陽性対照（N(0, 0.05^2)）の検査。"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(PROJ / "scripts"))
import train_t1b as t1b  # noqa: E402

from stage2pilot import common as C  # noqa: E402
from stage2pilot import det_metrics as M  # noqa: E402
from stage2pilot.pd_eval import digest_non_iface  # noqa: E402

TASK_ID = "T-2026-11-26-vlm-caption-signal-pilot"
FROZEN_PREFIXES = ("backbone.conv1.", "backbone.layer1.")


def expected_names(model, w: str) -> set[str]:
    names = [n for n, _ in model.named_parameters()]
    iface = {n for n in names if n.startswith("phase_iface.")}
    if w == "W1":
        return iface
    if w == "W2":
        last = len(model.transformer.decoder.layers) - 1
        pre = (
            f"transformer.decoder.layers.{last}.",
            f"transformer.decoder.class_head.{last}.",
            f"transformer.decoder.bbox_head.{last}.",
        )
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
    return {
        "w": w, "trainable_arg": trainable_arg,
        "n_names": len(got), "n_elements": int(sum(numel[n] for n in got)),
        "n_iface_elements": int(sum(numel[n] for n in got if n.startswith("phase_iface."))),
        "equal": got == exp,
        "only_in_trainable": sorted(got - exp), "only_in_expected": sorted(exp - got),
        "mixed_name": mixed,
        "equal_with_one_outside_mixed": (got | ({mixed} if mixed else set())) == exp if mixed else None,
        "names": sorted(got),
    }


def perturb(model, typ: str, scale: float = 0.05, seed: int = 1234) -> list[str]:
    g = torch.Generator().manual_seed(seed)
    iface = model.phase_iface
    if typ == "P1":
        params = [("phase_iface.mlp.-1.weight", iface.mlp[-1].weight),
                  ("phase_iface.mlp.-1.bias", iface.mlp[-1].bias)]
    elif typ == "P2L":
        params = [("phase_iface.weight", iface.weight),
                  ("phase_iface.bias", iface.bias)]
    else:
        raise ValueError(typ)
    with torch.no_grad():
        for _, p in params:
            p.copy_((torch.randn(p.shape, generator=g) * scale).to(p.device))
    return [n for n, _ in params]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--type", required=True, choices=("P1", "P2L"))
    ap.add_argument("--w", required=True, choices=("W1", "W2", "W3"))
    ap.add_argument("--trainable", required=True, choices=("film", "w2", "all"))
    ap.add_argument("--arm", required=True)
    ap.add_argument("--cfg", required=True)
    ap.add_argument("--det-ckpt", default=str(C.DET_CKPT))
    ap.add_argument("--signal-val", required=True)
    ap.add_argument("--zero-ctx", action="store_true")
    ap.add_argument("--perturb", action="store_true")
    ap.add_argument("--no-eval", action="store_true")
    ap.add_argument("--ref-preds", default=None)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    device = torch.device("cuda" if not a.no_eval else "cpu")
    torch.manual_seed(0)
    det_val = t1b.build_det_loader(train=False)
    stems = [Path(im["file_name"]).stem for im in det_val.dataset.coco.imgs.values()]
    videos = C.assert_no_test(stems, "v2t_identity")
    model = t1b.build_model(device, 42, a.cfg, ckpt_override=a.det_ckpt)
    t1b.register_classes(model, det_val)
    res = {
        "task_id": TASK_ID, "unofficial": True, "type": a.type, "w": a.w, "arm": a.arm,
        "cfg": a.cfg, "cfg_sha256": C.sha256(Path(a.cfg)),
        "det_ckpt_sha256": C.sha256(Path(a.det_ckpt)),
        "signal_val": a.signal_val, "signal_val_sha256": C.sha256(Path(a.signal_val)),
        "zero_ctx": a.zero_ctx, "videos": videos, "n_images": len(stems),
    }
    res["trainable_set"] = set_check(model, a.w, a.trainable)
    if a.perturb:
        res["perturbed"] = perturb(model, a.type)
    res["non_interface_digest"] = digest_non_iface(model)
    if not a.no_eval:
        sig = t1b.load_signal_npz(a.signal_val)
        dim = next(iter(sig.values())).shape[0]
        imgid_to_ctx, miss = t1b.build_imgid_to_ctx(det_val.dataset.coco, sig, dim)
        if miss:
            raise SystemExit(f"信号の無いフレーム {miss}")
        model.eval()
        m_ap, _, preds = t1b.eval_detection(model, det_val, imgid_to_ctx, device, a.zero_ctx,
                                            collect_predictions=True, dim=dim)
        res["eval_detection_mAP"] = m_ap
        res["metrics"] = M.summary(Path(t1b.ANN_DIR) / "instances_val.json", preds["results"], preds["image_ids"])
        if a.ref_preds:
            res["diff_vs_ref"] = M.max_output_diff(preds["results"], M.load_results(a.ref_preds))
    C.write_json(a.out, res)
    ts = res["trainable_set"]
    print(json.dumps({
        "type": a.type, "w": a.w, "arm": a.arm, "perturb": a.perturb,
        "set_equal": ts["equal"], "mixed_equal": ts["equal_with_one_outside_mixed"],
        "AP": res.get("metrics", {}).get("AP"), "diff": res.get("diff_vs_ref"),
    }, ensure_ascii=False))


if __name__ == "__main__":
    main()
