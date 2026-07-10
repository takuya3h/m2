#!/usr/bin/env python
"""② clsbias-PE の val 所見を **test split** で追認する（eval-only・再学習なし）。

背景: ① camt-all の checkpoint は /tmp から消失したが、② clsbias-PE の best_t1b.pth（inj+ctrl×3seed）
は残存。frozen 検出器なので best≈final（val per-class 実測で確認済）。残存 checkpoint を**同一アーキで
再構築**して load し、まず **val で per-class を再現（整合ゲート＝捏造防止の動作証明）** してから
**test（instances_test.json, 4265img）** を評価する。

Δ_test = inj(real test ctx) − ctrl(zero ctx) を per-class で算出。注入対象=phase-排他3術具
（Scalpel=9 / Skewer=11 / Syringe=13）、Bipolar=0 は除外（Δ≈0 のはず）。§10.1 は 3seed 集計で判定。

注意（誠実性）:
- 残存は **best-epoch** checkpoint（final-epoch は未保存）。val Δ の確定は final 基準だったが、
  frozen 検出器で best≈final（val 実測: Scalpel 0.9141/0.9146 等）なので best-epoch 上の追認は妥当。
- rare-tool の test 追認は [[val_test_significance_gap]] の残課題への回答。数値は全て実測（捏造なし）。
"""
import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))  # scripts/
import train_t1b as t1b  # noqa: E402  (sys.path 追加 + os.chdir(RELDETR) を副作用で行う)
import torch  # noqa: E402

BODY = t1b.BODY
FOCUS = {"Bipolar Forceps": 0, "Scalpel": 9, "Skewer": 11, "Syringe": 13}
INJECTED = ["Scalpel", "Skewer", "Syringe"]  # phase-排他3術具（注入対象）


def build_loader(split: str):
    from datasets.coco import CocoDetection
    from torch.utils import data
    from util.collate_fn import collate_fn
    ann = {"val": "instances_val.json", "test": "instances_test.json"}[split]
    ds = CocoDetection(img_folder=t1b.EGO_ROOT, ann_file=f"{t1b.ANN_DIR}/{ann}",
                       transforms=None, train=False)
    return data.DataLoader(ds, 1, shuffle=False, num_workers=4,
                           collate_fn=collate_fn, pin_memory=True)


MODEL_CFG_BY_INJECT = {"clsbias": "MODEL_CFG_CLSBIAS", "camt": "MODEL_CFG_CAMT"}


def load_ckpt_into_model(seed: int, ckpt_path: Path, loader, device, inject: str):
    """学習時と同一アーキ（inject 対応 config）で再構築 → ckpt を strict load（missing/unexpected は fail loud）。"""
    model_cfg = getattr(t1b, MODEL_CFG_BY_INJECT[inject])
    model = t1b.build_model(device, seed, model_cfg=model_cfg)
    t1b.register_classes(model, loader)
    sd = torch.load(ckpt_path, map_location=device)
    if isinstance(sd, dict) and "model" in sd:
        sd = sd["model"]
    missing, unexpected = model.load_state_dict(sd, strict=False)
    # 検出器・注入層・(clsbiasは)_rare_mask・_classes_ が完全一致でないと再現不能 → fail loud
    missing = [k for k in missing]
    unexpected = [k for k in unexpected]
    if missing or unexpected:
        raise RuntimeError(f"[FAIL-LOUD] state_dict 不整合 ckpt={ckpt_path}\n"
                           f"  missing={missing[:8]}...\n  unexpected={unexpected[:8]}...")
    rm = getattr(model, "_rare_mask", None)  # camt には無い（clsbias-PE のゲート buffer）
    rm = rm.detach().cpu().tolist() if rm is not None else None
    return model.to(device), rm


def evaluate(model, loader, split, zero_ctx, device):
    ctx, nmiss = t1b.build_imgid_to_ctx(loader.dataset.coco, t1b.load_phase_ctx(split))
    mAP, per_class = t1b.eval_detection(model, loader, ctx, device, zero_ctx)
    return mAP, per_class, nmiss


def gate_val(seed, kind, ckpt, val_loader, device, stored_pc, stored_map, zero_ctx, inject, tol=2e-3):
    """整合ゲート: reload → VAL 評価 → 保存済 best per-class と一致するか（捏造防止の動作証明）。"""
    model, rm = load_ckpt_into_model(seed, ckpt, val_loader, device, inject)
    mAP, per_class, _ = evaluate(model, val_loader, "val", zero_ctx, device)
    diffs = {n: abs(per_class.get(n, float("nan")) - stored_pc.get(n, float("nan")))
             for n in stored_pc}
    max_diff = max((d for d in diffs.values() if d == d), default=float("nan"))
    ok = (abs(mAP - stored_map) <= tol) and (max_diff <= tol)
    return model, rm, {"val_mAP_reload": mAP, "val_mAP_stored": stored_map,
                       "max_per_class_diff": max_diff, "gate_ok": bool(ok)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="42,123,456")
    ap.add_argument("--tag", default="clsbias_pe")
    ap.add_argument("--inject", choices=["clsbias", "camt"], default="clsbias",
                    help="学習時の注入方式（アーキ再構築の config を決める）")
    ap.add_argument("--ckpt-root", default="/tmp", help="best_t1b.pth を探す work root")
    ap.add_argument("--ckpt-name", default="best_t1b.pth", help="評価する checkpoint ファイル名（best/final）")
    ap.add_argument("--out", default=str(BODY / "experiments/analysis/t1b_clsbias_pe_test/test_eval.json"))
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    per_seed = {}
    for seed in seeds:
        inj_ck = Path(f"{args.ckpt_root}/t1b_{args.tag}_seed{seed}/{args.ckpt_name}")
        ctrl_ck = Path(f"{args.ckpt_root}/t1b_{args.tag}_zeroctx_seed{seed}/{args.ckpt_name}")
        for p in (inj_ck, ctrl_ck):
            if not p.exists():
                raise FileNotFoundError(f"checkpoint 無し: {p}")
        stored = BODY / f"transfer/t1b_{args.tag}_seed{seed}_efros"
        inj_stored = json.load(open(stored / "injected_result.json"))
        ctrl_stored = json.load(open(stored / "control_result.json"))
        val_loader = build_loader("val")

        # best-epoch ckpt は stored の best per-class（best_epoch）と、final ckpt は final_per_class と照合
        pc_key = "final_per_class_coco_map" if args.ckpt_name.startswith("final") else "per_class_coco_map"
        map_key = "final_mAP" if args.ckpt_name.startswith("final") else "mAP"

        print(f"\n===== seed{seed} 整合ゲート(val 再現) =====", flush=True)
        inj_model, inj_rm, inj_gate = gate_val(
            seed, "inj", inj_ck, val_loader, device,
            inj_stored[pc_key], inj_stored[map_key], zero_ctx=False, inject=args.inject)
        print(f"  inj  gate: {inj_gate} rare_mask={inj_rm}", flush=True)
        ctrl_model, ctrl_rm, ctrl_gate = gate_val(
            seed, "ctrl", ctrl_ck, val_loader, device,
            ctrl_stored[pc_key], ctrl_stored[map_key], zero_ctx=True, inject=args.inject)
        print(f"  ctrl gate: {ctrl_gate} rare_mask={ctrl_rm}", flush=True)

        print(f"===== seed{seed} TEST 評価 =====", flush=True)
        test_loader = build_loader("test")
        inj_map, inj_pc, inj_miss = evaluate(inj_model, test_loader, "test", False, device)
        ctrl_map, ctrl_pc, ctrl_miss = evaluate(ctrl_model, test_loader, "test", True, device)
        delta = {n: inj_pc.get(n, float("nan")) - ctrl_pc.get(n, float("nan")) for n in inj_pc}
        print(f"  test overall mAP: inj={inj_map:.4f} ctrl={ctrl_map:.4f} Δ={inj_map-ctrl_map:+.4f} "
              f"(ctx_miss inj/ctrl={inj_miss}/{ctrl_miss})", flush=True)
        for n in FOCUS:
            print(f"    {n:16s}: inj={inj_pc.get(n,float('nan')):.4f} ctrl={ctrl_pc.get(n,float('nan')):.4f} "
                  f"Δ={delta.get(n,float('nan')):+.4f}", flush=True)
        per_seed[seed] = {
            "gate": {"inj": inj_gate, "ctrl": ctrl_gate},
            "test": {"inj_mAP": inj_map, "ctrl_mAP": ctrl_map, "delta_mAP": inj_map - ctrl_map,
                     "inj_per_class": inj_pc, "ctrl_per_class": ctrl_pc, "delta_per_class": delta,
                     "ctx_miss": {"inj": inj_miss, "ctrl": ctrl_miss}},
        }
        del inj_model, ctrl_model
        torch.cuda.empty_cache()

    # §10.1 集計（3seed）: overall + 注入3術具 + Bipolar
    import statistics
    def agg(key_fn):
        xs = [key_fn(per_seed[s]) for s in seeds]
        m = statistics.mean(xs); sd = statistics.pstdev(xs)
        same = all(x > 0 for x in xs) or all(x < 0 for x in xs)
        sig = abs(m) > sd and same
        return {"vals": xs, "mean": m, "pstdev": sd, "all_same_sign": same, "significant": sig}
    summary = {
        "overall_delta_mAP": agg(lambda r: r["test"]["delta_mAP"]),
        "per_class_delta": {n: agg(lambda r, n=n: r["test"]["delta_per_class"].get(n, float("nan")))
                            for n in FOCUS},
        "gate_all_ok": all(per_seed[s]["gate"]["inj"]["gate_ok"] and
                           per_seed[s]["gate"]["ctrl"]["gate_ok"] for s in seeds),
    }
    out = {"tag": args.tag, "inject": args.inject, "split": "test", "checkpoint": args.ckpt_name,
           "seeds": seeds, "per_seed": per_seed, "summary": summary}
    # train_t1b の import で cwd=RELDETR に chdir されるため、相対 --out は BODY 基準へ解決（誤配置防止）
    out_path = Path(args.out)
    if not out_path.is_absolute():
        out_path = BODY / out_path
    out_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump(out, open(out_path, "w"), ensure_ascii=False, indent=2)
    args.out = str(out_path)
    print("\n================ §10.1 test 集計（3seed）================", flush=True)
    print(f"整合ゲート全通過: {summary['gate_all_ok']}", flush=True)
    o = summary["overall_delta_mAP"]
    print(f"overall Δ mAP: mean={o['mean']*100:+.3f}pp pstd={o['pstdev']*100:.3f} "
          f"same_sign={o['all_same_sign']} sig={o['significant']}", flush=True)
    for n in FOCUS:
        a = summary["per_class_delta"][n]
        if args.inject == "clsbias":
            tag = "(注入)" if n in INJECTED else "(除外)"
        else:
            tag = "(CA全)"  # camt は query-selective CA で全術具に注入（排他ゲートなし）
        print(f"  {n:16s}{tag}: mean={a['mean']*100:+.3f}pp pstd={a['pstdev']*100:.3f} "
              f"same_sign={a['all_same_sign']} sig={a['significant']} vals={[round(v*100,2) for v in a['vals']]}",
              flush=True)
    print(f"\n-> {args.out}", flush=True)


if __name__ == "__main__":
    main()
