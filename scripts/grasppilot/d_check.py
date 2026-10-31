"""案 D の補助の頭の確かめ（非公式 T-2026-11-01-grasp-pilot-d、Task C-2・G3）。数歩だけ。腕に数えない。

.venv-relation-detr で、重ねの BODY を EGO_BODY に置いて回す。cwd は台本が third_party/Relation-DETR へ移す。

1. データ: 元の CocoDetection（presets.detr）と GraspTargetCoco に同じ乱数の種で同じ項目を引かせ、画像・枠・ラベルが
   一致するか。反転の検出（p=1 で全て、p=0 で無し、p=0.5 で約半分）と、q が表の値（反転なら左右を入れ替えた値）か
2. 模型: 元の模型設定と d_model_config に同じ種で作らせ、頭を除くパラメータが一致するか。COCO の重みを読む前と後で
   要約値が変わるか（読み込みの記録）
3. 損失: 同じ batch・同じ種で、頭の無い元の模型と重み 0 の派生の模型の損失がすべて一致するか。重み 0.3 で
   全損失 − 検出の損失 = 0.3 × 補助損失 ≠ 0 か。頭のパラメータの勾配が 重み 0 で 0、0.3 で 0 でないか。
   対応づいた枠の数が正解の枠の数と一致するか。照合を外から計算し直すと取った indices と一致するか
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BODY = Path(os.environ["EGO_BODY"])
RELDETR = BODY / "third_party" / "Relation-DETR"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(RELDETR))
os.chdir(RELDETR)

import grasp_aux_d as G  # noqa: E402
import numpy as np  # noqa: E402
import torch  # noqa: E402


def build_models(weight, steplog):
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict
    os.environ["GRASP_AUX_WEIGHT"] = str(weight)
    os.environ["GRASP_STEPLOG"] = steplog or ""
    torch.manual_seed(42)
    base = Config(str(RELDETR / "configs/relation_detr/relation_detr_resnet50_egosurgery.py")).model
    torch.manual_seed(42)
    der = Config(str(HERE / "d_model_config.py")).model
    rec = {"init_digest_base": G.param_digest(base), "init_digest_derived_wo_head": G.param_digest(der, ("grasp_head",))}
    rec["init_equal"] = rec["init_digest_base"] == rec["init_digest_derived_wo_head"]
    ck = load_checkpoint(os.environ["RELDETR_COCO_CKPT"])
    load_state_dict(base, ck)
    load_state_dict(der, ck)
    rec["loaded_digest_base"] = G.param_digest(base)
    rec["loaded_digest_derived_wo_head"] = G.param_digest(der, ("grasp_head",))
    rec["loaded_equal"] = rec["loaded_digest_base"] == rec["loaded_digest_derived_wo_head"]
    rec["coco_changed_params"] = rec["init_digest_base"] != rec["loaded_digest_base"]
    return base, der, rec


def check_data(q_path, n_items):
    from datasets.coco import CocoDetection
    from transforms import presets
    ann = os.environ["EGO_ANN_DIR"] + "/instances_train.json"
    root = os.environ["EGO_ROOT"]
    orig = CocoDetection(img_folder=root, ann_file=ann, transforms=presets.detr, train=True)
    der = G.grasp_dataset_class()(img_folder=root, ann_file=ann, transforms=presets.detr, train=True, q_table=q_path)
    table = G.load_q_table(q_path)
    rng = np.random.default_rng(0)
    items = rng.choice(len(orig), n_items, replace=False).tolist()
    res = {"n_items": n_items, "len_orig": len(orig), "len_derived": len(der), "image_equal": 0, "boxes_equal": 0,
           "labels_equal": 0, "q_matches_table": 0, "flipped": 0, "boxes_kept": 0, "boxes_in_ann": 0,
           "ann_ids_subset": 0}
    for k, it in enumerate(items):
        seed_all(1000 + k)  # RandomSizeCrop は python の random を使う
        im0, t0 = orig[it]
        seed_all(1000 + k)
        im1, t1 = der[it]
        res["image_equal"] += int(torch.equal(im0, im1))
        res["boxes_equal"] += int(torch.equal(t0["boxes"], t1["boxes"]))
        res["labels_equal"] += int(torch.equal(t0["labels"], t1["labels"]))
        fl = bool(t1["grasp_flipped"])
        res["flipped"] += int(fl)
        want = np.stack([table[int(a)] for a in t1["grasp_ann_id"].tolist()]) if len(t1["grasp_ann_id"]) else np.zeros((0, 4))
        if fl:
            want = want[:, [1, 0, 2, 3]]
        res["q_matches_table"] += int(np.allclose(t1["grasp_q"].numpy(), want))
        anns = {a["id"] for a in der.coco.loadAnns(der.coco.getAnnIds([der.get_image_id(it)]))}
        res["ann_ids_subset"] += int(set(t1["grasp_ann_id"].tolist()) <= anns)
        res["boxes_kept"] += len(t1["boxes"])
        res["boxes_in_ann"] += len(anns)
    # 反転の検出の対照（同じ型の FlipProbe を p=1 と p=0 で）
    probe_cls = type(der._flip)
    for p in (1.0, 0.0):
        fp = probe_cls(p=p)
        x = torch.zeros(3, 4, 5)
        hits = 0
        for _ in range(20):
            fp(x)
            hits += int(fp.flipped)
        res[f"flip_probe_p{p}_hits_of_20"] = hits
    return res, der


def seed_all(seed):
    import random
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)


def to_device(batch, device):
    from util.misc import to_device as td
    return td(batch, device)


def losses_of(model, images, targets, seed):
    torch.manual_seed(seed)
    with torch.autocast(device_type="cuda", dtype=torch.float16):
        ld = model(images, targets)
    return ld


def orig_forward(model, images, targets):
    """派生の型の一つ上（元の RelationDETR）の forward をそのまま呼ぶ。フックも補助損失も無い。"""
    base_cls = [c for c in type(model).__mro__ if c.__name__ == "RelationDETR" and c is not type(model)][0]
    return base_cls.forward(model, images, targets)


def check_losses(base, der, dataset, n_batches, device):
    from util.collate_fn import collate_fn
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    base.to(device).train()
    der.to(device).train()
    der._grasp_keep_last = True
    out = []
    rng = np.random.default_rng(1)
    for b in range(n_batches):
        idx = rng.choice(len(dataset), 2, replace=False).tolist()
        seed_all(2000 + b)
        batch = collate_fn([dataset[i] for i in idx])
        images, targets = to_device(batch, device)
        rec = {"batch": b, "items": idx, "n_gt": int(sum(len(t["labels"]) for t in targets))}
        # 比べる相手も勾配を有効にして計算する（no_grad では演算の経路が変わりうる）。値だけ取り出してグラフを捨てる
        # 合計は main.py と同じく、テンソルのまま dict の順に足した fp32 の値を「__total__」に置く
        fl = lambda d: {**{k: float(v.detach()) for k, v in d.items()}, "__total__": float(sum(d.values()).detach())}  # noqa: E731
        ld0 = fl(losses_of(base, images, targets, 3000 + b))
        ld0_again = fl(losses_of(base, images, targets, 3000 + b))  # 同じ模型を二度（素の非決定性）
        der.grasp_weight = 0.0
        ld_plain = fl(losses_of(lambda i, t: orig_forward(der, i, t), images, targets, 3000 + b))  # 同じ実体の頭の無い経路
        rec["base_repeat_max_abs_diff"] = max(abs(ld0[k] - ld0_again[k]) for k in ld0)
        for w in (0.0, 0.3):
            der.grasp_weight = w
            der.zero_grad(set_to_none=True)
            ld = losses_of(der, images, targets, 3000 + b)
            tot = sum(ld.values())
            det = sum(v for k, v in ld.items() if k != "loss_grasp")
            tot.backward()
            gnorm = float(der.grasp_head.weight.grad.norm()) if der.grasp_head.weight.grad is not None else None
            last = der._grasp_last
            # 照合を外から計算し直す（最終層・主経路の出力）
            o, ts = last["output"], last["targets"]
            with torch.no_grad():
                re = [der.criterion.matcher(o["pred_boxes"][i], o["pred_logits"][i], t["boxes"], t["labels"])
                      for i, t in enumerate(ts)]
            same_idx = all(torch.equal(a[0].cpu(), c[0].cpu()) and torch.equal(a[1].cpu(), c[1].cpu())
                           for a, c in zip(last["indices"], re))
            n_matched = int(sum(len(s) for s, _ in last["indices"]))
            r = {"weight": w, "total": float(tot.detach()), "det": float(det.detach()),
                 "aux_ce": float(last["ce"].detach()), "total_minus_det": float((tot - det).detach()),
                 "head_grad_norm": gnorm, "n_matched": n_matched, "matched_eq_n_gt": n_matched == rec["n_gt"],
                 "indices_eq_recomputed": same_idx, "feat_len": int(last["feat"].shape[1]),
                 "nq": int(o["pred_logits"].shape[1])}
            if w == 0.0:
                keys0 = set(ld0) - {"__total__"}
                r["keys_equal_plus_grasp"] = set(ld) == keys0 | {"loss_grasp"}
                r["max_abs_diff_vs_base"] = max(abs(float(ld[k].detach()) - float(ld0[k])) for k in keys0)
                r["total_eq_base_total"] = float(tot.detach()) == ld0["__total__"]
                r["base_total"] = ld0["__total__"]
                r["max_abs_diff_vs_plain_same_instance"] = max(abs(float(ld[k].detach()) - ld_plain[k]) for k in keys0)
                r["total_eq_plain_total"] = float(tot.detach()) == ld_plain["__total__"]
                r["plain_total"] = ld_plain["__total__"]
            rec[f"w{w}"] = r
        out.append(rec)
        der._grasp_last = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--q", required=True, help="試走の標的の表（npz）")
    ap.add_argument("--out", required=True)
    ap.add_argument("--n-items", type=int, default=64)
    ap.add_argument("--n-batches", type=int, default=4)
    a = ap.parse_args()
    steplog = str(Path(a.out).with_suffix(".steplog.jsonl"))
    for p in (Path(steplog), Path(steplog).with_name("load_record.jsonl")):
        if p.exists():
            p.unlink()
    import hashlib
    res = {"task_id": "T-2026-11-01-grasp-pilot-d", "unofficial": True, "q": a.q,
           "q_sha256": hashlib.sha256(Path(a.q).read_bytes()).hexdigest(),
           "coco_ckpt": os.environ["RELDETR_COCO_CKPT"], "torch": torch.__version__}
    import models.bricks.ms_deform_attn as msda
    res["ms_deform_attn_ext"] = msda._C is not None
    res["data"], dataset = check_data(a.q, a.n_items)
    base, der, res["model"] = build_models(0.0, steplog)
    lr = Path(steplog).with_name("load_record.jsonl")
    res["model"]["load_record"] = [json.loads(x) for x in lr.read_text().splitlines()] if lr.exists() else []
    res["losses"] = check_losses(base, der, dataset, a.n_batches, torch.device("cuda"))
    L = res["losses"]
    res["verdict"] = {
        "data_identical": res["data"]["image_equal"] == res["data"]["boxes_equal"] == res["data"]["labels_equal"] == a.n_items,
        "q_matches_table": res["data"]["q_matches_table"] == a.n_items,
        "flip_probe_controls": res["data"]["flip_probe_p1.0_hits_of_20"] == 20 and res["data"]["flip_probe_p0.0_hits_of_20"] == 0,
        "init_equal": res["model"]["init_equal"], "coco_changed_params": res["model"]["coco_changed_params"],
        "w0_total_equal_base": all(r["w0.0"]["total_eq_base_total"] for r in L),
        "w0_max_abs_diff": max(r["w0.0"]["max_abs_diff_vs_base"] for r in L),
        "w0_total_equal_plain_same_instance": all(r["w0.0"]["total_eq_plain_total"] for r in L),
        "w0_max_abs_diff_plain_same_instance": max(r["w0.0"]["max_abs_diff_vs_plain_same_instance"] for r in L),
        "base_repeat_max_abs_diff": max(r["base_repeat_max_abs_diff"] for r in L),
        "w0_head_grad_zero": all(r["w0.0"]["head_grad_norm"] in (0.0, None) for r in L),
        "w03_aux_enters": all(abs(r["w0.3"]["total_minus_det"]) > 0 for r in L),
        "w03_head_grad_positive": all((r["w0.3"]["head_grad_norm"] or 0) > 0 for r in L),
        "matched_eq_n_gt": all(r[k]["matched_eq_n_gt"] for r in L for k in ("w0.0", "w0.3")),
        "indices_eq_recomputed": all(r[k]["indices_eq_recomputed"] for r in L for k in ("w0.0", "w0.3")),
    }
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n")
    print(json.dumps(res["verdict"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
