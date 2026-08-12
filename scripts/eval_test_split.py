#!/usr/bin/env python
"""主要 variant の best checkpoint を test split で評価し、論文用数値を補填。

既存 train_b2a.py / train_t1a.py の load_clips / evaluate / TeCNO を再利用。
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from pathlib import Path

import torch

PROJ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJ / "src"))
sys.path.insert(0, str(PROJ / "scripts"))

# train_b2a.py のヘルパを直接利用
import train_b2a  # noqa: E402
import train_t1a  # noqa: E402
from egosurgery.models.heads.tecno_head import TeCNO  # noqa: E402


def eval_b2a(ckpt: Path, **load_kw) -> dict | None:
    if not ckpt.exists():
        return None
    state = torch.load(ckpt, map_location="cuda", weights_only=True)
    in_dim = train_b2a.NUM_TOOLS if load_kw.get("drop_gap") else train_b2a.IN_DIM
    model = TeCNO(num_stages=2, num_layers=8, num_f_maps=64,
                  in_dim=in_dim, num_classes=len(train_b2a.CLASS_NAMES)).to("cuda")
    model.load_state_dict(state["tecno"])
    clips = train_b2a.load_clips("test", **load_kw)
    return train_b2a.evaluate(model, clips, "cuda")


def eval_t1a(ckpt: Path, **load_kw) -> dict | None:
    if not ckpt.exists():
        return None
    state = torch.load(ckpt, map_location="cuda", weights_only=True)
    region_only = load_kw.pop("region_only", False)
    add_tp = load_kw.get("add_toolpresence", False)
    if region_only:
        in_dim = train_t1a.REGION_DIM
    else:
        in_dim = train_t1a.GAP_DIM + train_t1a.REGION_DIM + (train_t1a.TOOLPRES_DIM if add_tp else 0)
    model = TeCNO(num_stages=2, num_layers=8, num_f_maps=64,
                  in_dim=in_dim, num_classes=len(train_t1a.CLASS_NAMES)).to("cuda")
    model.load_state_dict(state["tecno"])
    clips = train_t1a.load_clips("test", region_only, **load_kw)
    return train_t1a.evaluate(model, clips, "cuda")


def aggregate(name: str, exp_glob: str, eval_fn, load_kw):
    val_accs, test_accs, val_f1s, test_f1s = [], [], [], []
    dirs = sorted(Path("experiments/transfer").glob(exp_glob))
    for d in dirs:
        ckpt = d / "checkpoints" / "best_tecno.pth"
        mp = d / "metrics.json"
        if not (ckpt.exists() and mp.exists()):
            continue
        val_m = json.loads(mp.read_text())
        val_accs.append(val_m["phase_accuracy"])
        val_f1s.append(val_m["phase_macro_f1"])
        try:
            test_m = eval_fn(ckpt, **load_kw)
            test_accs.append(test_m["phase_accuracy"])
            test_f1s.append(test_m["phase_macro_f1"])
            print(f"  {d.name}: val_acc={val_m['phase_accuracy']:.4f}, test_acc={test_m['phase_accuracy']:.4f}")
        except Exception as e:
            print(f"  {d.name}: EVAL FAILED ({type(e).__name__}: {e})")
    if not test_accs:
        return None
    return {
        "name": name,
        "n": len(test_accs),
        "val_acc_mean": statistics.mean(val_accs),
        "val_acc_pstdev": statistics.pstdev(val_accs) if len(val_accs) > 1 else 0,
        "test_acc_mean": statistics.mean(test_accs),
        "test_acc_pstdev": statistics.pstdev(test_accs) if len(test_accs) > 1 else 0,
        "val_f1_mean": statistics.mean(val_f1s),
        "test_f1_mean": statistics.mean(test_f1s),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--variants", type=str, default="all", help="評価する variant. all or カンマ区切り")
    args = p.parse_args()

    targets = [
        ("B2a base (pred)", "*b2a_det2phase_toolpresence_seed*", eval_b2a, {"tool_source": "pred"}),
        ("B2a base (oracle)", "b2a_det2phase_oracletool_*", eval_b2a, {"tool_source": "oracle"}),
        ("B2a-RegionOnly (pred)", "b2a_regiononly_pred_*", eval_b2a, {"tool_source": "pred", "drop_gap": True}),
        ("B2a-RegionOnly (oracle)", "b2a_regiononly_oracle_00*", eval_b2a, {"tool_source": "oracle", "drop_gap": True}),
        ("T1a base", "t1a_regiontoken_*", eval_t1a, {"region_only": False}),
        ("T1a-RegionOnly", "t1a_region_only_00*", eval_t1a, {"region_only": True}),
        ("T1a-Combined (pred)", "t1a_b2a_combined_*", eval_t1a, {"region_only": False, "add_toolpresence": True, "toolpresence_source": "pred"}),
        ("T1a-Combined (oracle)", "t1a_combined_oracle_001_*", eval_t1a, {"region_only": False, "add_toolpresence": True, "toolpresence_source": "oracle"}),
        ("T1a-Combined (oracle s123)", "t1a_combined_oracle_002_*", eval_t1a, {"region_only": False, "add_toolpresence": True, "toolpresence_source": "oracle"}),
        ("T1a-Combined (oracle s456)", "t1a_combined_oracle_003_*", eval_t1a, {"region_only": False, "add_toolpresence": True, "toolpresence_source": "oracle"}),
    ]

    if args.variants != "all":
        names = set(args.variants.split(","))
        targets = [t for t in targets if t[0] in names]

    print("=== test split 評価開始 ===")
    results = []
    for name, glob, fn, kw in targets:
        print(f"\n--- {name} ---")
        r = aggregate(name, glob, fn, kw)
        if r:
            results.append(r)

    S4_VAL = 0.8986  # S4 base val
    S4_TEST = 0.8859  # 推定 (val より約 1.3pt 低い前例より)
    print("\n=== 結果サマリ ===")
    print(f"{'variant':<32}{'n':<4}{'val mean':<12}{'test mean':<12}{'val-test diff':<14}{'Δ vs S4 (test)':<15}")
    print("-" * 95)
    for r in results:
        diff = r['val_acc_mean'] - r['test_acc_mean']
        delta = r['test_acc_mean'] - S4_TEST
        print(f"{r['name']:<32}{r['n']:<4}{r['val_acc_mean']:.4f}      {r['test_acc_mean']:.4f}      {diff:+.4f}        {delta:+.4f}")

    out = PROJ / "experiments" / "analysis" / "test_split_eval.json"
    out.parent.mkdir(exist_ok=True, parents=True)
    out.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"\n結果保存: {out}")


if __name__ == "__main__":
    main()
