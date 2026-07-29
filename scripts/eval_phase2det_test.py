#!/usr/bin/env python
"""test split での phase→det 検出評価（per-class AP・§9 の決定的検証）。

既存の収束済み検出器を **test split**（instances_test.json, 4265枚）で COCO 評価し、overall mAP と
per-class AP を出す。phase→det 注入（T1b-FiLM / T1b-CA / H-C-v1）が、rare∧工程特異術具の検出を
test で変えるか（val は rare 術具の実例が希少 → test の方が信頼できる）を確かめる。

評価対象（abs path・cwd=RELDETR でも壊れない）:
  s0_frozen      : 注入なしベースライン（warm-start 元の S0-frozen 検出器・seed42）
  t1b_film_inj   : FiLM 注入（test phase context あり, seed42）
  t1b_film_ctrl  : FiLM 対照（zero context, seed42）
  t1b_ca_inj     : CA 注入（test phase context あり, seed42）

3-seed H-C-v1 評価（--seed と --models hc_v1_inj/hc_v1_ctrl を併用）:
  hc_v1_inj   : H-C-v1 (CA + entropy gate) 注入（real ctx, --seed で per-seed ckpt）
  hc_v1_ctrl  : H-C-v1 対照（zero ctx, 同上）
  ※ best_t1b.pth が無い seed（init=best, 学習で改善せず）は S0-frozen ckpt に **恒等性で代替**
     （H-C 検出器に S0-frozen ckpt を load → phase 層は missing→zero-init→恒等。
       phase ctx を渡せば gate 込みで forward → 学習後 H-C-v1 と厳密等価）

実行（.venv-relation-detr）:
  # seed42 既存（互換維持）:
  CUDA_VISIBLE_DEVICES=0 python scripts/eval_phase2det_test.py --models s0_frozen,t1b_film_inj
  # H-C-v1 3-seed 追加（GPU 1 個で順次）:
  for S in 42 123 456; do
    CUDA_VISIBLE_DEVICES=0 python scripts/eval_phase2det_test.py --seed $S --models hc_v1_inj,hc_v1_ctrl
  done
"""
from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import sys
from pathlib import Path

import torch

# BODY は EGO_BODY / このファイルの位置から解決する。以前は特定ホストの絶対パスを
# ハードコードしていたため、別サーバーでは ckpt 探索が 0 件になり検証が不能だった。
BODY = Path(os.environ.get("EGO_BODY", Path(__file__).resolve().parents[1]))
RELDETR = BODY / "third_party" / "Relation-DETR"
sys.path.insert(0, str(RELDETR))
sys.path.insert(0, str(BODY / "scripts"))
os.chdir(RELDETR)

import run_artifacts as ra  # noqa: E402
from train_t1b import NUM_PHASES, build_imgid_to_ctx, ctx_for_targets, load_phase_ctx  # noqa: E402

ANN = str(BODY / "data/annotations/egosurgery_tool")
EGO = str(BODY / "data/raw/ego")
OUT_DIR = BODY / "experiments/analysis/step_c_coupling_analysis"
BASE_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery.py"
T1B_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b.py"
CA_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_ca.py"
HC_CFG = "configs/relation_detr/relation_detr_resnet50_egosurgery_t1b_hc.py"


def s0_ckpt_for(seed: int) -> str:
    return str(RELDETR / f"checkpoints/incoming/seed{seed}/best_ap.pth")


def t1b_ckpt_for(run_names: list[str], fallback: str) -> str:
    """``experiments/transfer/<run>/checkpoints/best_t1b.pth`` を候補順に探す。

    旧 flat レイアウト（run 直下の best_t1b.pth）も :func:`ra.find_checkpoint` が拾うので、
    保存先変更前に作られた run もそのまま評価できる。
    """
    for name in run_names:
        found = ra.find_checkpoint(ra.resolve_run_dir(name))
        if found is not None:
            return str(found)
    return fallback


def hc_ckpt_for(seed: int, tag: str) -> str:
    """H-C-v1 の best_t1b.pth path 解決。学習で改善しなかった seed は存在しない → S0-frozen ckpt で
    恒等代替（H-C 検出器に S0-frozen ckpt を load すると phase 層は missing→zero-init→恒等。
    phase ctx 入力で gate forward すれば学習後 H-C-v1 と厳密等価=学習で動いていないので）。"""
    return t1b_ckpt_for([f"hc_{tag}_seed{seed}", f"t1b_hc_all_{tag}_seed{seed}"],
                        s0_ckpt_for(seed))


def models_for_seed(seed: int) -> dict:
    """Per-seed の MODELS 辞書を返す。seed42 は既存互換、他 seed は H-C-v1 のみ用意。"""
    s0 = s0_ckpt_for(seed)
    base = {
        "s0_frozen":    dict(cfg=BASE_CFG, ckpt=s0, phase=None),
        "hc_v1_inj":    dict(cfg=HC_CFG, ckpt=hc_ckpt_for(seed, "inj"), phase="real"),
        "hc_v1_ctrl":   dict(cfg=HC_CFG, ckpt=hc_ckpt_for(seed, "ctrl"), phase="zero"),
    }
    if seed == 42:
        # 既存 seed42 互換: t1b_film/t1b_ca の評価キーを残す
        base.update({
            "t1b_film_inj":  dict(cfg=T1B_CFG, phase="real", ckpt=t1b_ckpt_for(
                ["t1b_film_seed42", "t1b_film_all_inj_seed42"], s0)),
            "t1b_film_ctrl": dict(cfg=T1B_CFG, phase="zero", ckpt=t1b_ckpt_for(
                ["t1b_film_zeroctx_seed42", "t1b_film_all_ctrl_seed42"], s0)),
            "t1b_ca_inj":    dict(cfg=CA_CFG, phase="real", ckpt=t1b_ckpt_for(
                ["t1b_ca_seed42", "t1b_ca_all_inj_seed42"], s0)),
        })
    return base


# 既存呼び出し互換（--seed なしのとき seed42）。
MODELS = models_for_seed(42)


def build_test_loader():
    from datasets.coco import CocoDetection
    from torch.utils import data
    from util.collate_fn import collate_fn

    ds = CocoDetection(img_folder=EGO, ann_file=f"{ANN}/instances_test.json", transforms=None, train=False)
    return data.DataLoader(ds, 1, shuffle=False, num_workers=4, collate_fn=collate_fn, pin_memory=True)


def load_model(cfg, ckpt, device):
    from util.lazy_load import Config
    from util.utils import load_checkpoint, load_state_dict

    model = Config(cfg).model
    ck = load_checkpoint(ckpt)
    if isinstance(ck, dict) and "model" in ck:
        ck = ck["model"]
    load_state_dict(model, ck)  # 非strict（不一致は警告のみ）
    return model.to(device).eval()


def register_classes(model, loader):
    from util.misc import encode_labels

    coco = loader.dataset.coco
    cat_ids = list(range(max(coco.cats.keys()) + 1))
    classes = tuple(coco.cats.get(c, {"name": "none"})["name"] for c in cat_ids)
    model.register_buffer("_classes_", torch.tensor(encode_labels(classes)))


@torch.no_grad()
def evaluate(model, loader, imgid_to_ctx, device, phase_mode, collect_predictions=False):
    """test 検出評価。``collect_predictions=True`` のときだけ per-image 予測も返す。

    ``train_t1b.eval_detection`` と同じ規約（既定の戻り値 arity は変えない）。
    """
    from util.coco_eval import CocoEvaluator
    from util.coco_utils import get_coco_api_from_dataset

    coco = get_coco_api_from_dataset(loader.dataset)
    ev = CocoEvaluator(coco, ["bbox"])
    has_phase = hasattr(model, "set_phase_context")
    for images, targets in loader:
        images = [img.to(device) for img in images]
        if has_phase:
            if phase_mode == "zero":
                ctx = torch.zeros(len(targets), NUM_PHASES, device=device)
            else:
                ctx = ctx_for_targets(targets, imgid_to_ctx, device, zero_ctx=False)
            model.set_phase_context(ctx)
        out = model(images)
        out = [{k: v.to("cpu") for k, v in t.items()} for t in out]
        ev.update({t["image_id"]: o for t, o in zip(targets, out)})
    ev.synchronize_between_processes()
    ev.accumulate()
    with contextlib.redirect_stdout(io.StringIO()):
        ev.summarize()
    bbox = ev.coco_eval["bbox"]
    names = [c["name"] for c in coco.loadCats(coco.getCatIds())]
    prec = bbox.eval["precision"]
    per = {}
    for ci, n in enumerate(names):
        v = prec[:, :, ci, 0, 2]
        v = v[v > -1]
        per[n] = float(v.mean()) if v.size else float("nan")
    if not collect_predictions:
        return float(bbox.stats[0]), per
    preds = {"results": ev.predictions["bbox"],
             "image_ids": sorted({int(i) for i in ev.img_ids})}
    return float(bbox.stats[0]), per, preds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", required=True, help="カンマ区切り（models_for_seed(seed) のキー）")
    ap.add_argument("--seed", type=int, default=42,
                    help="評価対象 seed（42/123/456）。seed42 既存出力は test_eval_{key}.json、"
                         "それ以外は test_eval_{key}_seed{S}.json として保存")
    ap.add_argument("--no-save-predictions", action="store_true",
                    help="per-image predictions を保存しない（既定は保存する）")
    ap.add_argument("--predictions-no-gzip", action="store_true",
                    help="predictions を gzip せず素の .json で保存する")
    args = ap.parse_args()
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    loader = build_test_loader()
    imgid_to_ctx, miss = build_imgid_to_ctx(loader.dataset.coco, load_phase_ctx("test"))
    print(f"[test-eval] seed={args.seed} test images={len(loader.dataset)} miss_ctx={miss}", flush=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    models = models_for_seed(args.seed)
    for key in args.models.split(","):
        if key not in models:
            print(f"[test-eval] SKIP {key}: seed{args.seed} で未定義 (available: {list(models)})", flush=True)
            continue
        m = models[key]
        if not Path(m["ckpt"]).exists():
            print(f"[test-eval] SKIP {key}: ckpt 無 {m['ckpt']}", flush=True)
            continue
        model = load_model(m["cfg"], m["ckpt"], device)
        register_classes(model, loader)
        save_preds = not args.no_save_predictions
        mAP, per, preds = evaluate(model, loader, imgid_to_ctx, device, m["phase"],
                                   collect_predictions=True)
        pred_path = None
        if save_preds:
            # ckpt を出した run に predictions を戻す（run 外の ckpt は評価専用 run へ）。
            run_dir = ra.run_dir_for_checkpoint(m["ckpt"], f"test_eval_{key}_seed{args.seed}")
            ra.ensure_layout(run_dir)
            pred_path = ra.save_predictions(
                run_dir, preds["results"], split="test", tag=key, best=True,
                compress=not args.predictions_no_gzip)
            ra.save_eval_meta(run_dir, {
                "split": "test", "ann_file": f"{ANN}/instances_test.json",
                "image_ids": preds["image_ids"], "topk": ra.EVAL_TOPK,
                "select_box_nums_for_evaluation": 300, "score_thr": 0.0, "limit": None,
            })
            print(f"[test-eval] predictions -> {ra.host_path(pred_path)}", flush=True)
        # H-C-v1 評価時に gate 統計を併記（解釈の助けに）
        gate_stat = {}
        if hasattr(model, "_last_gate_mean") and model._last_gate_mean is not None:
            gate_stat = {"last_gate_mean": model._last_gate_mean,
                         "last_entropy_mean": model._last_entropy_mean}
        res = {"model": key, "seed": args.seed, "split": "test", "ckpt": m["ckpt"], "phase": m["phase"],
               "mAP": mAP, "per_class_ap": per,
               "predictions": ra.host_path(pred_path) if pred_path else None, **gate_stat}
        # 出力ファイル名: seed42 既存互換のため seed42 のときだけ {key}.json、それ以外は {key}_seed{S}.json
        out_name = f"test_eval_{key}.json" if args.seed == 42 else f"test_eval_{key}_seed{args.seed}.json"
        (OUT_DIR / out_name).write_text(json.dumps(res, indent=2, ensure_ascii=False))
        print(f"[test-eval] {key}(seed{args.seed}): test mAP={mAP:.4f} -> {out_name}", flush=True)


if __name__ == "__main__":
    main()
